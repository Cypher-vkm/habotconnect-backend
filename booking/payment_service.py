import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentGatewayError(Exception):
    """Raised when the mock payment gateway fails."""


def create_payment(*, amount, transaction_id):
    payload = {
        "amount": str(amount),
        "transaction_id": transaction_id,
    }

    try:
        response = requests.post(
            f"{settings.BASE_URL}/api/v1/mock-payment/",
            json=payload,
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        logger.exception("Payment gateway request failed")
        raise PaymentGatewayError(
            "Unable to process payment."
        ) from exc