import base64
import hashlib
import hmac
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request as URLRequest, urlopen


RAZORPAY_API = "https://api.razorpay.com/v1"


class RazorpayError(Exception):
    """Raised when a Razorpay API call fails."""


def _auth_header(key_id: str, key_secret: str) -> str:
    token = base64.b64encode(
        f"{key_id}:{key_secret}".encode("utf-8")
    ).decode("ascii")
    return f"Basic {token}"


def _request(
    method: str,
    path: str,
    key_id: str,
    key_secret: str,
    payload: dict | None = None,
):
    body = None
    headers = {
        "Authorization": _auth_header(key_id, key_secret),
        "Accept": "application/json",
    }

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = URLRequest(
        f"{RAZORPAY_API}{path}",
        data=body,
        headers=headers,
        method=method.upper(),
    )

    try:
        with urlopen(req, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8")
            detail = json.loads(raw)
        except Exception:
            detail = {"error": {"description": str(exc)}}
        description = (
            detail.get("error", {}).get("description")
            if isinstance(detail, dict)
            else None
        )
        raise RazorpayError(description or "Razorpay API request failed") from exc
    except URLError as exc:
        raise RazorpayError(
            "Could not connect to Razorpay. Please try again."
        ) from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise RazorpayError(
            "Razorpay returned an invalid response."
        ) from exc


def create_order(
    key_id: str,
    key_secret: str,
    *,
    amount: Decimal,
    receipt: str,
    notes: dict | None = None,
):
    paise = int((Decimal(amount) * 100).quantize(Decimal("1")))
    return _request(
        "POST",
        "/orders",
        key_id,
        key_secret,
        {
            "amount": paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {},
        },
    )


def fetch_payment(key_id: str, key_secret: str, payment_id: str):
    return _request(
        "GET",
        f"/payments/{payment_id}",
        key_id,
        key_secret,
    )


def capture_payment(
    key_id: str,
    key_secret: str,
    payment_id: str,
    *,
    amount: Decimal,
):
    paise = int((Decimal(amount) * 100).quantize(Decimal("1")))
    return _request(
        "POST",
        f"/payments/{payment_id}/capture",
        key_id,
        key_secret,
        {
            "amount": paise,
            "currency": "INR",
        },
    )


def verify_checkout_signature(
    order_id: str,
    payment_id: str,
    signature: str,
    key_secret: str,
) -> bool:
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        key_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(
    raw_body: bytes,
    signature: str,
    webhook_secret: str,
) -> bool:
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
