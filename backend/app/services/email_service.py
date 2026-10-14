"""Transactional email for verification, password reset, and two-step login.

Production prefers SendLiberty (Gmail OAuth, no domain), then Resend, then SMTP.
Development logs the message when no provider is set.
"""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.exceptions.errors import EmailDeliveryError

logger = get_logger(__name__, component="email_service")


def _html_shell(title: str, body: str, extra: str = "") -> str:
    return f"""<!DOCTYPE html>
<html><body style="font-family:Segoe UI,system-ui,sans-serif;background:#efece6;color:#141414;padding:24px;">
  <div style="max-width:480px;margin:0 auto;background:#fff;padding:28px;border:1px solid #e4dfd6;">
    <p style="letter-spacing:0.16em;text-transform:uppercase;font-size:12px;color:#5c574e;">Talent Lens</p>
    <h1 style="font-size:22px;font-weight:500;">{title}</h1>
    <p style="line-height:1.5;">{body}</p>
    {extra}
    <p style="font-size:13px;color:#5c574e;">If you did not request this, you can ignore this email.</p>
  </div>
</body></html>"""


class EmailService:
    """Send account emails through Resend, SMTP, or the local logger."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def _has_provider(self) -> bool:
        return bool(self._settings.sendliberty_key) or bool(self._settings.resend_api_key) or bool(self._settings.smtp_host)

    async def send_verification(self, to: str, code: str, link: str) -> None:
        extra = (
            f'<p style="font-size:28px;letter-spacing:0.3em;font-weight:600;">{code}</p>'
            f'<p><a href="{link}">Verify my email</a></p>'
        )
        await self._send(
            to=to,
            subject="Verify your Talent Lens account",
            html=_html_shell("Verify your email", "Use this code or open the link to activate your account.", extra),
            text=f"Your Talent Lens verification code is {code}. Or open: {link}",
        )

    async def send_password_reset(self, to: str, code: str, link: str) -> None:
        extra = (
            f'<p style="font-size:28px;letter-spacing:0.3em;font-weight:600;">{code}</p>'
            f'<p><a href="{link}">Reset my password</a></p>'
        )
        await self._send(
            to=to,
            subject="Reset your Talent Lens password",
            html=_html_shell("Reset your password", "Use this code or open the link. It expires soon.", extra),
            text=f"Your Talent Lens reset code is {code}. Or open: {link}",
        )

    async def send_two_factor(self, to: str, code: str) -> None:
        extra = f'<p style="font-size:28px;letter-spacing:0.3em;font-weight:600;">{code}</p>'
        await self._send(
            to=to,
            subject="Your Talent Lens sign-in code",
            html=_html_shell("Two-step verification", "Enter this code to finish signing in or changing 2-step settings.", extra),
            text=f"Your Talent Lens sign-in code is {code}.",
        )

    async def _send(self, to: str, subject: str, html: str, text: str) -> None:
        if self._settings.sendliberty_key:
            await self._send_sendliberty(to, subject, html, text)
            return
        if self._settings.resend_api_key:
            await self._send_resend(to, subject, html)
            return
        if self._settings.smtp_host:
            self._send_smtp(to, subject, html, text)
            return
        if self._settings.is_production:
            raise EmailDeliveryError("Email is not configured. Set SENDLIBERTY_API_KEY, RESEND_API_KEY, or SMTP_HOST.")
        logger.info("Email (dev, not sent) to=%s subject=%s body=%s", to, subject, text)

    async def _send_sendliberty(self, to: str, subject: str, html: str, text: str) -> None:
        key = self._settings.sendliberty_key or ""
        payload: dict[str, str] = {
            "to": to,
            "subject": subject,
            "html": html,
            "text": text,
        }
        from_address = self._settings.email_from.strip()
        if from_address and "localhost" not in from_address.lower():
            payload["from"] = from_address
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://sendliberty.com/api/send",
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": key,
                        "Authorization": f"Bearer {key}",
                    },
                    json=payload,
                )
            if response.status_code >= 400:
                logger.error("SendLiberty rejected email status=%s body=%s", response.status_code, response.text)
                raise EmailDeliveryError("Could not send email. Try again in a moment.")
        except EmailDeliveryError:
            raise
        except Exception as exc:
            logger.exception("SendLiberty request failed.")
            raise EmailDeliveryError("Could not send email. Try again in a moment.") from exc

    async def _send_resend(self, to: str, subject: str, html: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {self._settings.resend_api_key}"},
                    json={
                        "from": self._settings.email_from,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                    },
                )
            if response.status_code >= 400:
                logger.error("Resend rejected email status=%s body=%s", response.status_code, response.text)
                raise EmailDeliveryError("Could not send email. Try again in a moment.")
        except EmailDeliveryError:
            raise
        except Exception as exc:
            logger.exception("Resend request failed.")
            raise EmailDeliveryError("Could not send email. Try again in a moment.") from exc

    def _send_smtp(self, to: str, subject: str, html: str, text: str) -> None:
        message = EmailMessage()
        message["From"] = self._settings.email_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        try:
            with smtplib.SMTP(self._settings.smtp_host or "", self._settings.smtp_port, timeout=12) as smtp:
                smtp.starttls()
                if self._settings.smtp_username and self._settings.smtp_password:
                    smtp.login(self._settings.smtp_username, self._settings.smtp_password)
                smtp.send_message(message)
        except Exception as exc:
            logger.exception("SMTP send failed.")
            raise EmailDeliveryError("Could not send email. Try again in a moment.") from exc
