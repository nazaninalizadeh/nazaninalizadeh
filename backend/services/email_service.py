"""Email service — single send_email() helper.

- Uses Resend when RESEND_API_KEY is set in the environment.
- Falls back to console-log mock when the key is missing/empty so the rest of the
  reminder pipeline keeps working in dev.
- Always non-blocking from FastAPI's perspective (Resend SDK is sync, so we run it
  in a thread).
"""
from __future__ import annotations

import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger("email_service")

DEFAULT_SENDER = os.environ.get("SENDER_EMAIL") or "onboarding@resend.dev"


def _is_real_send_enabled() -> bool:
    key = os.environ.get("RESEND_API_KEY") or ""
    return bool(key.strip()) and key.strip() != "YOUR_KEY_HERE"


async def send_email(to: str, subject: str, html_body: str, *, from_addr: Optional[str] = None) -> dict:
    """Send a transactional email.

    Returns a dict with at least: { "status": "sent" | "mocked" | "error", "id": str|None, "to": str }.
    Never raises — if anything fails it logs and returns status="error".
    """
    sender = from_addr or DEFAULT_SENDER
    if not to or "@" not in to:
        logger.warning(f"Email skipped: invalid recipient '{to}'")
        return {"status": "error", "id": None, "to": to, "reason": "invalid_recipient"}

    if not _is_real_send_enabled():
        # Mock path: log to console exactly like before so the existing pipeline
        # remains observable when no key is configured.
        logger.info(
            "\n" + "=" * 60 +
            f"\n[EMAIL MOCK] To: {to}\nFrom: {sender}\nSubject: {subject}\n" +
            "-" * 60 +
            f"\n{html_body}\n" + "=" * 60
        )
        return {"status": "mocked", "id": None, "to": to}

    # Real Resend send
    try:
        import resend  # imported lazily so missing pkg doesn't break the mock path
        resend.api_key = os.environ.get("RESEND_API_KEY", "")
        params = {
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html_body,
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        email_id = result.get("id") if isinstance(result, dict) else None
        logger.info(f"[EMAIL SENT] id={email_id} to={to} subject='{subject}'")
        return {"status": "sent", "id": email_id, "to": to}
    except Exception as e:
        logger.error(f"[EMAIL ERROR] to={to} subject='{subject}' err={e}")
        return {"status": "error", "id": None, "to": to, "reason": str(e)}
