# Customer Authentication Email OTP Setup

Intra Aura customer authentication uses:

- **Signup:** Email + password, with email OTP verification before activation.
- **Login:** Email + password only. No mobile login and no login OTP.
- **Forgot password:** Email OTP, then a new password.
- **Mobile number:** Contact information only.

## Required SMTP environment variables

Add these to the local `.env` file (do not commit the file):

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

Optional authentication limits already have safe defaults in `app/config/settings.py`:

```env
OTP_EXPIRY_MINUTES=10
OTP_RESEND_COOLDOWN_SECONDS=60
OTP_MAX_ATTEMPTS=5
OTP_MAX_RESENDS=5
LOGIN_MAX_FAILED_ATTEMPTS=5
LOGIN_LOCK_MINUTES=15
```

## Gmail

If Gmail is used, the SMTP password must be a Google **App Password**, not the normal Gmail account password. The Google account must have 2-Step Verification enabled before an App Password can be created.

Never put SMTP credentials in Python source code, templates, JavaScript, Git, or screenshots.

## PostgreSQL

Run:

```text
migrations/003_customer_auth_otp.sql
```

The migration is idempotent for the authentication tables/column and preserves existing customer accounts.

## Local test

After adding SMTP settings:

```bash
uvicorn app.main:app --reload
```

Then:

1. Open `/account/register`.
2. Create a new customer account.
3. Check the email inbox for the 6-digit OTP.
4. Enter the OTP on the verification page.
5. Log in with email + password.
6. Test Forgot Password separately.

The application never displays or logs the OTP itself.
