# OTPCart Telegram Bot — v9 (Integrated with Gmail Auto-Verification)

A Telegram OTP-number bot powered by OTPDoctor, with a full **Wallet System**,
**Admin Control Panel**, **Top Services**, **Swiggy Checker**, **Multi-SMS**,
an improved **cancellation system**, a robust **Auto-Retry** engine, and now
**Gmail-based automatic payment verification** for wallet recharges.

## 🆕 What's new in v9 (this release)

### Gmail Auto-Verification (integrated from payment_verify_bot)
When a user submits their Transaction ID (UTR) for a wallet recharge, the bot
now **automatically verifies** it by searching your Gmail for matching payment-
alert emails — no admin action needed!

**How it works:**
1. User pays via UPI → your bank sends a credit alert email to your Gmail
2. User submits their UTR to the bot
3. Bot searches Gmail via IMAP for an email containing that exact UTR
4. If found and the amount matches → **wallet credited instantly** ✅
5. If Gmail not configured, UTR not found, or amount can't be parsed →
   **falls back to manual admin approval** (existing flow preserved)

**Security:**
- Each UTR can only be used once (prevents double-claiming)
- Amount validation: email amount must be ≥ requested amount
- All auto-approvals are logged and admin is notified
- Gmail credentials are never hardcoded — only env vars

### Bug fixes in this release
1. **`_safe_cb` UTF-8 truncation bug** — previous version could split multi-byte
   characters at byte 64, producing invalid callback_data. Now truncates at valid
   UTF-8 boundaries and appends a short hash for uniqueness.
2. **Hardcoded API key removed** — `OTP_API_KEY` no longer has a hardcoded
   fallback. Admin must set it via env var or admin panel.
3. **`gmail_checker` error handling** — IMAP login/search/fetch failures now
   return structured errors instead of crashing the bot.
4. **Recharge session cleanup** — stale `awaiting_txn_id`/`awaiting_recharge_amount`
   flags auto-expire after 10 minutes (configurable via `RECHARGE_SESSION_TTL`).

---

## 📋 Setup

### 1. Telegram Bot
1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → copy the **token**
2. Set `BOT_TOKEN` in your `.env` or Railway Variables

### 2. OTPDoctor API
1. Get an API key from [OTPDoctor](https://www.otpdoctor.in/)
2. Set `OTP_API_KEY` in env vars (or change it later via admin panel)

### 3. Gmail Auto-Verification (optional but recommended)
1. Turn on 2-Step Verification: https://myaccount.google.com/security
2. Create an app password: https://myaccount.google.com/apppasswords
3. Set these env vars:
   - `GMAIL_ADDRESS=your-email@gmail.com`
   - `GMAIL_APP_PASSWORD=your16charapppassword`
   - `SENDER_FILTER=alerts@yourbank.com` (optional, recommended)
   - `EMAIL_LOOKBACK_HOURS=48` (optional, default 48)

> If Gmail is not configured, the bot uses manual admin approval (same as before).

### 4. Run locally
```bash
pip install -r requirements.txt
cp .env.example .env        # fill in your values
python bot.py
```

### 5. Deploy on Railway
1. Push to a GitHub repo
2. Railway → New Project → Deploy from GitHub repo
3. Set all env vars in the Variables tab
4. Attach a Volume at `/data` and set `DB_PATH=/data/bot.db`

---

## 🔧 Configuration (env vars)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | — | Telegram bot token |
| `OTP_API_KEY` | ✅ | — | OTPDoctor API key |
| `ADMIN_IDS` | ✅ | — | Comma-separated admin Telegram IDs |
| `GMAIL_ADDRESS` | ❌ | — | Gmail for auto-verification |
| `GMAIL_APP_PASSWORD` | ❌ | — | Gmail app password (16 chars) |
| `IMAP_HOST` | ❌ | `imap.gmail.com` | IMAP server |
| `SENDER_FILTER` | ❌ | — | Filter emails by sender |
| `EMAIL_LOOKBACK_HOURS` | ❌ | `48` | Hours to search back |
| `DB_PATH` | ❌ | `bot.db` | SQLite DB path |

---

## 📁 Files

| File | Purpose |
|------|---------|
| `bot.py` | Main bot: handlers, wallet, admin panel, OTP flow, auto-verify |
| `gmail_checker.py` | IMAP search + amount extraction for auto-verification |
| `database.py` | SQLite persistence (users, wallets, services, tx, used_utrs) |
| `keyboards.py` | All inline keyboards (user + admin + wallet) |
| `otp_api.py` | OTPDoctor API wrapper |
| `storage.py` | In-memory active-order tracking |
| `config.py` | All config from env vars |
| `checkers.py` | Swiggy Checker integration |