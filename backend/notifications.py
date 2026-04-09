"""
Pluggable Notification Service.

Currently: Console/log output.
Future: Resend, SendGrid, WhatsApp Business API.

To add a real email provider later:
1. Install the SDK (e.g. `pip install resend`)
2. Set env vars (RESEND_API_KEY, SENDER_EMAIL, etc.)
3. Implement the method body with the real API call
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("notifications")


class NotificationService:

    @staticmethod
    async def send_otp(email: str, otp: str):
        logger.info("=" * 60)
        logger.info(f"[OTP]  Destinatario: {email}")
        logger.info(f"[OTP]  Codice OTP:   {otp}")
        logger.info(f"[OTP]  Scadenza:     5 minuti")
        logger.info(f"[OTP]  Orario:       {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        logger.info("=" * 60)

    @staticmethod
    async def send_login_alert(email: str, ip: str, user_agent: str):
        logger.info("=" * 60)
        logger.info(f"[LOGIN ALERT]  Admin: {email}")
        logger.info(f"[LOGIN ALERT]  IP:    {ip}")
        logger.info(f"[LOGIN ALERT]  UA:    {user_agent[:80]}")
        logger.info(f"[LOGIN ALERT]  Ora:   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info("=" * 60)

    @staticmethod
    async def send_reminder(email: str, subject: str, message: str):
        logger.info(f"[REMINDER] To: {email} | Subject: {subject}")
        logger.info(f"[REMINDER] {message}")

    @staticmethod
    async def send_whatsapp(phone: str, message: str):
        logger.info(f"[WHATSAPP] To: {phone} | Message: {message}")
        logger.info("[WHATSAPP] *** WhatsApp integration not configured yet ***")

    @staticmethod
    async def send_birthday(email: str, name: str):
        logger.info(f"[BIRTHDAY] Auguri a {name} ({email})!")
