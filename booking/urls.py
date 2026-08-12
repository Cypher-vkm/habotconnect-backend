from django.urls import path

from .views import (
    BookingCreateView,
    LSASearchView,
    MockPaymentGatewayView,
    PaymentCreateView,
    PaymentWebhookView,
)

urlpatterns = [
    path(
        "bookings/",
        BookingCreateView.as_view(),
        name="booking-create",
    ),
    path(
        "lsas/search/",
        LSASearchView.as_view(),
        name="lsa-search",
    ),
    path(
        "payments/",
        PaymentCreateView.as_view(),
        name="payment-create",
    ),
    path(
        "payments/webhook/",
        PaymentWebhookView.as_view(),
        name="payment-webhook",
    ),
    path(
        "mock-payment/",
        MockPaymentGatewayView.as_view(),
        name="mock-payment",
    ),
]