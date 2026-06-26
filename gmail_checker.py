"""
gmail_checker.py — Reads payment-alert emails from Gmail via IMAP and checks
whether a given transaction ID (UTR/RRN) appears in any recent message.
Also extracts the amount so the bot can match it against the expected price.

Integrated into OTP-VER9 to auto-verify wallet recharges.

No third-party deps — uses Python's built-in imaplib + email.

Bug fixes vs. original payment_verify_bot version:
  • Robust IMAP login error handling (returns structured error, not exception)
  • Handles IMAP SELECT failures (rare but possible on locked mailbox)
  • More flexible UTR matching (also matches short alphanumeric IDs)
  • Safe HTML stripping that preserves amounts inside markup
  • Returns a structured dict with explicit error field
"""

from __future__ import annotations

import email
import imaplib
import logging
import re
from datetime import datetime, timedelta, timezone
from email.header import decode_header

import config

logger = logging.getLogger(__name__)

# Matches "Rs. 100", "Rs 100.00", "INR 1,000", "₹100", "Rs.100/-", etc.
_AMOUNT_RE = re.compile(
    r"(?:Rs\.?|INR|₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.IGNORECASE
)


def _decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out


def _body_text(msg) -> str:
    """Flatten a possibly-multipart email into plain text."""
    chunks = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ("text/plain", "text/html"):
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    chunks.append(payload.decode(charset, errors="ignore"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="ignore"))
    text = "\n".join(chunks)
    # strip basic HTML tags so "₹100" inside markup is still matchable
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def _extract_amount(text: str):
    m = _AMOUNT_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def find_transaction(txn_id: str) -> dict:
    """
    Returns dict(found=bool, amount=float|None, subject=str, date=str, error=str|None).
    True only if a recent email's text contains the exact txn_id.

    Never raises on network/IMAP errors — returns {"found": False, "error": "..."}.
    """
    txn_id = (txn_id or "").strip()
    result = {
        "found": False,
        "amount": None,
        "subject": "",
        "date": "",
        "error": None,
    }

    if not txn_id:
        result["error"] = "empty_txn_id"
        return result

    # Skip Gmail check entirely if not configured — caller can fall back to admin
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        result["error"] = "gmail_not_configured"
        return result

    imap = None
    try:
        imap = imaplib.IMAP4_SSL(config.IMAP_HOST, timeout=15)
        try:
            imap.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
        except imaplib.IMAP4.error as e:
            result["error"] = f"imap_login_failed: {e}"
            logger.warning("Gmail login failed: %s", e)
            return result

        try:
            status, _ = imap.select("INBOX")
            if status != "OK":
                result["error"] = "imap_select_failed"
                logger.warning("IMAP SELECT INBOX failed: %s", status)
                return result
        except Exception as e:
            result["error"] = f"imap_select_error: {e}"
            logger.warning("IMAP SELECT error: %s", e)
            return result

        since = (
            datetime.now(timezone.utc)
            - timedelta(hours=config.EMAIL_LOOKBACK_HOURS)
        ).strftime("%d-%b-%Y")

        criteria = ["SINCE", since]
        if config.SENDER_FILTER:
            criteria += ["FROM", config.SENDER_FILTER]

        try:
            status, data = imap.search(None, *criteria)
        except Exception as e:
            result["error"] = f"imap_search_error: {e}"
            logger.warning("IMAP SEARCH error: %s", e)
            return result

        if status != "OK" or not data or not data[0]:
            return result  # found=False, no error

        ids = data[0].split()
        # newest first, cap how many we inspect
        for eid in reversed(ids[-80:]):
            try:
                status, msg_data = imap.fetch(eid, "(RFC822)")
            except Exception as e:
                logger.debug("IMAP fetch failed for %s: %s", eid, e)
                continue
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            try:
                msg = email.message_from_bytes(msg_data[0][1])
            except Exception as e:
                logger.debug("Email parse failed for %s: %s", eid, e)
                continue
            text = _body_text(msg)
            if txn_id and txn_id in text:
                result["found"] = True
                result["amount"] = _extract_amount(text)
                result["subject"] = _decode(msg.get("Subject"))
                result["date"] = msg.get("Date", "")
                break
        return result
    except Exception as e:
        # Catch-all so the caller can fall back to admin approval
        result["error"] = f"unexpected: {e}"
        logger.exception("Unexpected error in find_transaction")
        return result
    finally:
        if imap is not None:
            try:
                imap.logout()
            except Exception:
                pass
