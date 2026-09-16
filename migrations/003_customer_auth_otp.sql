-- Intra Aura: customer email OTP authentication
-- Safe to run on an existing PostgreSQL database.

ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS auth_otps (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    purpose VARCHAR(30) NOT NULL,
    target VARCHAR(255) NOT NULL,
    code_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    resend_count INTEGER NOT NULL DEFAULT 0,
    last_sent_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_auth_otps_user_id ON auth_otps(user_id);
CREATE INDEX IF NOT EXISTS ix_auth_otps_purpose ON auth_otps(purpose);
CREATE INDEX IF NOT EXISTS ix_auth_otps_target ON auth_otps(target);
CREATE INDEX IF NOT EXISTS ix_auth_otps_expires_at ON auth_otps(expires_at);

CREATE TABLE IF NOT EXISTS auth_login_attempts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(200) NOT NULL,
    client_key VARCHAR(255) NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TIMESTAMP,
    last_attempt_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_auth_login_attempts_email ON auth_login_attempts(email);
CREATE INDEX IF NOT EXISTS ix_auth_login_attempts_client_key ON auth_login_attempts(client_key);
CREATE UNIQUE INDEX IF NOT EXISTS ux_auth_login_attempts_email_client
ON auth_login_attempts(email, client_key);

-- Existing customers are kept usable without forcing a historical OTP.
UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL;
