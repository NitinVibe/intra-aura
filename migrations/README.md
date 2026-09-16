# INTRA AURA database upgrades

This project does not use Alembic.

Run the SQL files manually in the PostgreSQL database used by `DATABASE_URL`, in order:

1. `001_add_user_delivery_profile.sql`
2. `002_orders_payments_and_delivery.sql`

The second migration adds:
- order payment state
- Razorpay order/payment IDs
- payment verification timestamp
- stock reservation/release flag
- order delivery-address snapshot
- `payment_settings` table

Razorpay secrets are stored server-side in `payment_settings` and are never rendered to customers. Use HTTPS in production and do not commit real Razorpay secrets to Git.
