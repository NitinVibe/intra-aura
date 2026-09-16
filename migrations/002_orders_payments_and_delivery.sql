-- INTRA AURA: orders + Razorpay + delivery snapshot upgrade
-- Safe to run more than once on PostgreSQL.

ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(30) NOT NULL DEFAULT 'Pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS razorpay_order_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS razorpay_payment_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_verified_at TIMESTAMP NULL;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS stock_released BOOLEAN NOT NULL DEFAULT FALSE;

-- Existing orders were created by the pre-payment flow. Do not release their stock
-- automatically through the new payment/cancellation workflow.
UPDATE orders SET stock_released = TRUE WHERE stock_released = FALSE;

ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_name VARCHAR(150);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_email VARCHAR(200);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_phone VARCHAR(30);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_address VARCHAR(300);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_area_street VARCHAR(200);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_landmark VARCHAR(200);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_city VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_state VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_pincode VARCHAR(6);

CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_razorpay_order_id
    ON orders (razorpay_order_id)
    WHERE razorpay_order_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_razorpay_payment_id
    ON orders (razorpay_payment_id)
    WHERE razorpay_payment_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS payment_settings (
    id INTEGER PRIMARY KEY,
    provider VARCHAR(30) NOT NULL DEFAULT 'razorpay',
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mode VARCHAR(10) NOT NULL DEFAULT 'test',
    key_id VARCHAR(150),
    key_secret VARCHAR(500),
    webhook_secret VARCHAR(500),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO payment_settings (id, provider, enabled, mode)
VALUES (1, 'razorpay', FALSE, 'test')
ON CONFLICT (id) DO NOTHING;
