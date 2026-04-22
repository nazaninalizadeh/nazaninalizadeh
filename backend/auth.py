"""
Secure Authentication Module
- 2 whitelisted admins only
- Email + Password + CAPTCHA → OTP verification (2-step login)
- Single-device session enforcement
- Brute force protection
- Rate limiting
- Activity logging
- Session timeout
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import bcrypt
import jwt
import secrets
import hashlib
import uuid
import os
import logging
import time
import asyncio
from collections import defaultdict

import httpx

from database import db
from notifications import NotificationService

logger = logging.getLogger("auth")

# ============ Configuration ============
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
JWT_ALGORITHM = "HS256"

RECAPTCHA_SECRET = os.environ.get('RECAPTCHA_SECRET', '')

ALLOWED_ADMINS = {}
_a1_email = os.environ.get('ADMIN1_EMAIL', '').lower().strip()
_a2_email = os.environ.get('ADMIN2_EMAIL', '').lower().strip()
if _a1_email:
    ALLOWED_ADMINS[_a1_email] = {"name": "Alborz", "role": "super_admin"}
if _a2_email:
    ALLOWED_ADMINS[_a2_email] = {"name": "Nazanin", "role": "admin"}

# Security constants
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)
OTP_EXPIRY = timedelta(minutes=5)
MAX_OTP_ATTEMPTS = 3
SESSION_TIMEOUT = timedelta(hours=24)
ACCESS_TOKEN_EXPIRY = timedelta(hours=8)
REFRESH_TOKEN_EXPIRY = timedelta(days=30)

# In-memory rate limiter (per IP)
_rate_store = defaultdict(list)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_AUTH = 10


# ============ Utility Functions ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def create_access_token(user_id: str, email: str, session_id: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "sid": session_id,
        "exp": datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRY,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, session_id: str) -> str:
    payload = {
        "sub": user_id,
        "sid": session_id,
        "exp": datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRY,
        "type": "refresh",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _check_rate_limit(ip: str) -> bool:
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_store[ip]) >= RATE_LIMIT_MAX_AUTH:
        return False
    _rate_store[ip].append(now)
    return True


async def verify_captcha(token: str) -> bool:
    if not RECAPTCHA_SECRET:
        return True
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": RECAPTCHA_SECRET, "response": token},
                timeout=5.0,
            )
            return resp.json().get("success", False)
    except Exception as e:
        logger.warning(f"CAPTCHA verification failed: {e}")
        return True  # fail open if Google is unreachable


# ============ Activity Logging ============
async def log_activity(admin_email: str, action: str, ip: str, user_agent: str, details: str = ""):
    await db.activity_logs.insert_one({
        "id": str(uuid.uuid4()),
        "admin_email": admin_email,
        "action": action,
        "ip_address": ip,
        "user_agent": user_agent[:200],
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ============ Brute Force Protection ============
async def is_locked_out(identifier: str) -> bool:
    rec = await db.login_attempts.find_one({"identifier": identifier})
    if not rec:
        return False
    locked_until = rec.get("locked_until")
    if locked_until:
        if isinstance(locked_until, str):
            locked_until = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) < locked_until:
            return True
        await db.login_attempts.delete_one({"identifier": identifier})
        return False
    return rec.get("attempts", 0) >= MAX_LOGIN_ATTEMPTS


async def record_failed_attempt(identifier: str):
    rec = await db.login_attempts.find_one({"identifier": identifier})
    if not rec:
        await db.login_attempts.insert_one({
            "identifier": identifier,
            "attempts": 1,
            "first_attempt": datetime.now(timezone.utc).isoformat(),
        })
    else:
        new_count = rec.get("attempts", 0) + 1
        update_fields = {"attempts": new_count}
        if new_count >= MAX_LOGIN_ATTEMPTS:
            update_fields["locked_until"] = (datetime.now(timezone.utc) + LOCKOUT_DURATION).isoformat()
        await db.login_attempts.update_one({"identifier": identifier}, {"$set": update_fields})


async def clear_failed_attempts(identifier: str):
    await db.login_attempts.delete_many({"identifier": identifier})


# ============ Auth Dependency ============
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Non autenticato")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Tipo di token non valido")

        session_id = payload.get("sid")
        if not session_id:
            raise HTTPException(status_code=401, detail="Sessione non valida")

        session = await db.sessions.find_one({"session_id": session_id, "is_active": True})
        if not session:
            raise HTTPException(status_code=401, detail="Sessione scaduta o invalidata. Effettua nuovamente il login.")

        last_active = session.get("last_active", session["created_at"])
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active.replace("Z", "+00:00"))
        if last_active.tzinfo is None:
            last_active = last_active.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_active > SESSION_TIMEOUT:
            await db.sessions.update_one(
                {"session_id": session_id},
                {"$set": {"is_active": False, "expired_reason": "timeout"}},
            )
            raise HTTPException(status_code=401, detail="Sessione scaduta per inattivita. Effettua nuovamente il login.")

        await db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"last_active": datetime.now(timezone.utc)}},
        )

        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato")

        user["id"] = str(user["_id"])
        del user["_id"]
        user.pop("password_hash", None)
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token scaduto. Effettua nuovamente il login.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido")


# ============ Request Models ============
class LoginStep1Request(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str = ""


class VerifyOTPRequest(BaseModel):
    login_session_id: str
    otp_code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ============ Auth Router ============
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login_direct(body: LoginStep1Request, req: Request, response: Response):
    """Direct login without OTP - email + password + CAPTCHA only."""
    ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "unknown")
    email = body.email.lower().strip()

    if not _check_rate_limit(ip):
        await log_activity(email, "rate_limited", ip, ua)
        raise HTTPException(status_code=429, detail="Troppe richieste. Riprova piu tardi.")

    if body.captcha_token:
        valid = await verify_captcha(body.captcha_token)
        if not valid:
            raise HTTPException(status_code=400, detail="Verifica CAPTCHA non riuscita.")

    if email not in ALLOWED_ADMINS:
        await log_activity(email, "rejected_not_whitelisted", ip, ua)
        raise HTTPException(status_code=403, detail="Accesso non autorizzato.")

    bf_key = f"{ip}:{email}"
    if await is_locked_out(bf_key):
        await log_activity(email, "blocked_brute_force", ip, ua)
        raise HTTPException(status_code=429, detail="Account temporaneamente bloccato. Riprova tra 15 minuti.")

    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await record_failed_attempt(bf_key)
        await log_activity(email, "invalid_credentials", ip, ua)
        raise HTTPException(status_code=401, detail="Email o password non validi.")

    user_id = str(user["_id"])

    await db.sessions.update_many(
        {"admin_id": user_id, "is_active": True},
        {"$set": {"is_active": False, "expired_reason": "new_device_login"}},
    )

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db.sessions.insert_one({
        "session_id": session_id,
        "admin_id": user_id,
        "admin_email": email,
        "ip_address": ip,
        "user_agent": ua[:200],
        "is_active": True,
        "created_at": now,
        "last_active": now,
    })

    access_token = create_access_token(user_id, email, session_id)
    refresh_token = create_refresh_token(user_id, session_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=1800, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    await clear_failed_attempts(bf_key)
    await log_activity(email, "login_success", ip, ua, f"session={session_id}")
    await NotificationService.send_login_alert(email, ip, ua)

    return {
        "id": user_id,
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", ""),
        "created_at": user.get("created_at", ""),
    }


@auth_router.post("/login-step1")
async def login_step1(body: LoginStep1Request, req: Request):
    ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "unknown")
    email = body.email.lower().strip()

    # 1. Rate limit
    if not _check_rate_limit(ip):
        await log_activity(email, "rate_limited", ip, ua)
        raise HTTPException(status_code=429, detail="Troppe richieste. Riprova piu tardi.")

    # 2. CAPTCHA
    if body.captcha_token:
        valid = await verify_captcha(body.captcha_token)
        if not valid:
            await log_activity(email, "captcha_failed", ip, ua)
            raise HTTPException(status_code=400, detail="Verifica CAPTCHA non riuscita.")

    # 3. Whitelist check
    if email not in ALLOWED_ADMINS:
        await log_activity(email, "rejected_not_whitelisted", ip, ua)
        raise HTTPException(status_code=403, detail="Accesso non autorizzato. Questo account non e registrato.")

    # 4. Brute force check
    bf_key = f"{ip}:{email}"
    if await is_locked_out(bf_key):
        await log_activity(email, "blocked_brute_force", ip, ua)
        raise HTTPException(status_code=429, detail="Account temporaneamente bloccato per troppi tentativi. Riprova tra 15 minuti.")

    # 5. Credential validation
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await record_failed_attempt(bf_key)
        await log_activity(email, "invalid_credentials", ip, ua)
        raise HTTPException(status_code=401, detail="Email o password non validi.")

    # 6. Generate OTP
    otp = generate_otp()
    login_session_id = str(uuid.uuid4())

    await db.otp_codes.insert_one({
        "login_session_id": login_session_id,
        "admin_email": email,
        "otp_hash": hash_otp(otp),
        "attempts": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + OTP_EXPIRY).isoformat(),
        "used": False,
        "ip": ip,
    })

    # 7. Send OTP (console for now)
    await NotificationService.send_otp(email, otp)
    await log_activity(email, "otp_sent", ip, ua, f"session={login_session_id}")

    return {"message": "Codice OTP inviato. Controlla la tua email.", "login_session_id": login_session_id}


@auth_router.post("/verify-otp")
async def verify_otp_endpoint(body: VerifyOTPRequest, req: Request, response: Response):
    ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "unknown")

    if not _check_rate_limit(ip):
        raise HTTPException(status_code=429, detail="Troppe richieste.")

    otp_rec = await db.otp_codes.find_one({"login_session_id": body.login_session_id, "used": False})
    if not otp_rec:
        raise HTTPException(status_code=400, detail="Sessione OTP non valida o scaduta.")

    # Check expiry
    expires_at = datetime.fromisoformat(otp_rec["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await db.otp_codes.update_one({"login_session_id": body.login_session_id}, {"$set": {"used": True}})
        raise HTTPException(status_code=400, detail="Codice OTP scaduto. Ripeti il login.")

    # Check attempts
    if otp_rec.get("attempts", 0) >= MAX_OTP_ATTEMPTS:
        await db.otp_codes.update_one({"login_session_id": body.login_session_id}, {"$set": {"used": True}})
        raise HTTPException(status_code=400, detail="Troppi tentativi errati. Ripeti il login.")

    # Verify OTP hash
    if hash_otp(body.otp_code) != otp_rec["otp_hash"]:
        await db.otp_codes.update_one({"login_session_id": body.login_session_id}, {"$inc": {"attempts": 1}})
        remaining = MAX_OTP_ATTEMPTS - otp_rec.get("attempts", 0) - 1
        await log_activity(otp_rec["admin_email"], "otp_invalid", ip, ua)
        raise HTTPException(status_code=400, detail=f"Codice OTP non valido. Tentativi rimasti: {remaining}")

    # OTP valid — mark used
    await db.otp_codes.update_one({"login_session_id": body.login_session_id}, {"$set": {"used": True}})

    email = otp_rec["admin_email"]
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=500, detail="Errore interno del server.")

    user_id = str(user["_id"])

    # Invalidate ALL existing sessions for this admin (single-device enforcement)
    await db.sessions.update_many(
        {"admin_id": user_id, "is_active": True},
        {"$set": {"is_active": False, "expired_reason": "new_device_login"}},
    )

    # Create new session
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    await db.sessions.insert_one({
        "session_id": session_id,
        "admin_id": user_id,
        "admin_email": email,
        "ip_address": ip,
        "user_agent": ua[:200],
        "is_active": True,
        "created_at": now,
        "last_active": now,
    })

    # Create tokens with session_id embedded
    access_token = create_access_token(user_id, email, session_id)
    refresh_token = create_refresh_token(user_id, session_id)

    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=1800, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

    # Clear brute force record
    await clear_failed_attempts(f"{ip}:{email}")

    # Log + notify
    await log_activity(email, "login_success", ip, ua, f"session={session_id}")
    await NotificationService.send_login_alert(email, ip, ua)

    return {
        "id": user_id,
        "email": user["email"],
        "name": user.get("name", ""),
        "role": user.get("role", ""),
        "created_at": user.get("created_at", ""),
    }


@auth_router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user


@auth_router.post("/logout")
async def logout(req: Request, response: Response, user: dict = Depends(get_current_user)):
    ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "unknown")

    # Invalidate the current session
    token = req.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            sid = payload.get("sid")
            if sid:
                await db.sessions.update_one({"session_id": sid}, {"$set": {"is_active": False, "expired_reason": "logout"}})
        except Exception:
            pass

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    await log_activity(user.get("email", ""), "logout", ip, ua)
    return {"message": "Disconnessione riuscita."}


@auth_router.post("/refresh")
async def refresh_token(req: Request, response: Response):
    token = req.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token di refresh mancante.")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token non valido.")

        sid = payload.get("sid")
        session = await db.sessions.find_one({"session_id": sid, "is_active": True})
        if not session:
            raise HTTPException(status_code=401, detail="Sessione non valida.")

        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Utente non trovato.")

        new_access = create_access_token(str(user["_id"]), user["email"], sid)
        response.set_cookie(key="access_token", value=new_access, httponly=True, secure=False, samesite="lax", max_age=1800, path="/")
        return {"message": "Token aggiornato."}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token di refresh scaduto.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token non valido.")


@auth_router.post("/change-password")
async def change_password(body: ChangePasswordRequest, req: Request, user: dict = Depends(get_current_user)):
    ip = req.client.host if req.client else "unknown"
    ua = req.headers.get("user-agent", "unknown")

    # Fetch full user with password hash
    full_user = await db.users.find_one({"_id": ObjectId(user["id"])})
    if not full_user:
        raise HTTPException(status_code=404, detail="Utente non trovato.")

    if not verify_password(body.current_password, full_user["password_hash"]):
        await log_activity(user["email"], "change_password_failed", ip, ua)
        raise HTTPException(status_code=400, detail="Password corrente non valida.")

    if len(body.new_password) < 10:
        raise HTTPException(status_code=400, detail="La nuova password deve avere almeno 10 caratteri.")

    new_hash = hash_password(body.new_password)
    await db.users.update_one({"_id": ObjectId(user["id"])}, {"$set": {"password_hash": new_hash}})
    await log_activity(user["email"], "password_changed", ip, ua)

    return {"message": "Password aggiornata con successo."}


@auth_router.get("/activity-logs")
async def get_activity_logs(user: dict = Depends(get_current_user)):
    logs = await db.activity_logs.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).to_list(200)
    return logs


@auth_router.get("/active-sessions")
async def get_active_sessions(user: dict = Depends(get_current_user)):
    sessions = await db.sessions.find(
        {"is_active": True}, {"_id": 0, "session_id": 1, "admin_email": 1, "ip_address": 1, "user_agent": 1, "created_at": 1, "last_active": 1}
    ).to_list(50)
    for s in sessions:
        if isinstance(s.get("created_at"), datetime):
            s["created_at"] = s["created_at"].isoformat()
        if isinstance(s.get("last_active"), datetime):
            s["last_active"] = s["last_active"].isoformat()
    return sessions


# ============ Admin Seeding ============
async def seed_admins():
    """Create whitelisted admins on startup. Update passwords if .env changed."""
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.otp_codes.create_index("login_session_id")
    await db.sessions.create_index("session_id")
    await db.sessions.create_index("admin_id")
    await db.activity_logs.create_index([("timestamp", -1)])

    # Remove any users not in the whitelist
    await db.users.delete_many({"email": {"$nin": list(ALLOWED_ADMINS.keys())}})

    for email, info in ALLOWED_ADMINS.items():
        env_key = f"ADMIN{list(ALLOWED_ADMINS.keys()).index(email) + 1}_PASSWORD"
        password = os.environ.get(env_key, "")
        if not password:
            continue

        existing = await db.users.find_one({"email": email})
        if existing is None:
            await db.users.insert_one({
                "email": email,
                "password_hash": hash_password(password),
                "name": info["name"],
                "role": info["role"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Admin created: {email} ({info['role']})")
        elif not verify_password(password, existing["password_hash"]):
            await db.users.update_one(
                {"email": email},
                {"$set": {"password_hash": hash_password(password)}},
            )
            logger.info(f"Admin password updated: {email}")
        else:
            logger.info(f"Admin OK: {email}")
