import os

# ── Telegram ──────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]

# ── OTPDoctor ─────────────────────────────────────────────────────────────────
# SECURITY FIX: removed hardcoded fallback key. Empty default forces the admin to
# set OTP_API_KEY via env var or admin panel. The bot will refuse to purchase
# numbers if no key is configured.
OTP_API_KEY = os.getenv("OTP_API_KEY", "")
OTP_BASE_URL = "https://www.otpdoctor.in/stubs/handler_api.php"

# ── Swiggy Checker ────────────────────────────────────────────────────────────
CHECKER_API_URL = os.getenv("CHECKER_API_URL", "https://checker.otpcart.xyz/api/check-swiggy")
# Default service id used by the Swiggy Checker (admin can change at runtime via panel)
SWIGGY_SERVICE_ID = os.getenv("SWIGGY_SERVICE_ID", "swiggy")

# ── Gmail auto-verification (NEW: integrated from payment_verify_bot) ────────
# If both GMAIL_ADDRESS and GMAIL_APP_PASSWORD are set, the bot will
# automatically verify wallet recharges by reading payment-alert emails.
# If unset, the bot falls back to manual admin approval (existing flow).
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
SENDER_FILTER = os.getenv("SENDER_FILTER", "")  # e.g. "alerts@hdfcbank.net"
EMAIL_LOOKBACK_HOURS = int(os.getenv("EMAIL_LOOKBACK_HOURS", "48") or 48)

# ── Timing ────────────────────────────────────────────────────────────────────
OTP_POLL_INTERVAL = 2     # seconds between status checks (real-time monitoring)
OTP_TIMEOUT = 180         # wait up to 3 minutes (180 s) before auto-cancel & refund
MULTI_SMS_TIMEOUT = 1200  # seconds to keep number alive after first OTP (20 min)

CANCEL_ALLOWED_AFTER = 180          # users may cancel only after 3 minutes (180 s)
SWIGGY_REGISTERED_CANCEL_DELAY = 300  # auto-cancel a registered Swiggy number after 5 min

# Swiggy Checker search engine
SWIGGY_RETRY_MAX = 30   # max purchase+check cycles while hunting an unregistered number
SWIGGY_CHECK_DELAY = 1  # seconds between Swiggy search cycles (kept low for speed)

# ── Auto-Retry ────────────────────────────────────────────────────────────────
RETRY_INTERVAL = 2   # seconds between purchase retries
RETRY_MAX = 10        # maximum retry attempts on provider errors (spec: max 10)
# Provider error keywords that trigger an auto-retry
RETRY_ERROR_KEYWORDS = [
    "NO_NUMBERS", "NO_NUMBER", "NO NUMBER", "NO STOCK", "NO_STOCK",
    "TRY_AGAIN", "TRY AGAIN", "TEMPORARY", "TEMP_ERROR",
    "PROVIDER", "LIMIT", "WAIT", "AVAILABLE", "BUSY",
]

# ── UX / Limits ───────────────────────────────────────────────────────────────
RECENTLY_USED_MAX = 5  # max recently-used entries stored per user

# ── Recharge session cleanup ──────────────────────────────────────────────────
# Auto-clear stale "awaiting_txn_id" / "awaiting_recharge_amount" flags after
# this many seconds so a user who abandons the flow doesn't get stuck.
RECHARGE_SESSION_TTL = 600  # 10 minutes
