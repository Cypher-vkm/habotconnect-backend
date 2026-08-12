from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from .models import (
    Booking_Request,
    LSA_Profile,
    Parent,
    Payment,
    Skill,
)


class BookingAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.parent = Parent.objects.create(
            name="Rahul",
            email="rahul@example.com",
            phone_number="9876543210",
        )

        self.lsa = LSA_Profile.objects.create(
            name="Sarah",
            email="sarah@example.com",
            phone="9876500000",
            hourly_rate=Decimal("600.00"),
        )

        self.skill = Skill.objects.create(
            name="Mathematics"
        )

        self.lsa.skills.add(self.skill)

    def booking_payload(self, **overrides):
        payload = {
            "parent": self.parent.id,
            "lsa": self.lsa.id,
            "booking_date": "2026-08-13",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
        }

        payload.update(overrides)

        return payload

    # ============================================================
    # BOOKING TESTS
    # ============================================================

    def test_create_booking(self):
        response = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            Booking_Request.objects.count(),
            1,
        )

    def test_reject_invalid_time_range(self):
        response = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(
                start_time="11:00:00",
                end_time="10:00:00",
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_reject_overlapping_booking(self):
        first = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(
                start_time="10:30:00",
                end_time="11:30:00",
            ),
            format="json",
        )

        self.assertEqual(
            second.status_code,
            409,
        )

    def test_allow_adjacent_booking(self):
        first = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(),
            format="json",
        )

        self.assertEqual(
            first.status_code,
            201,
        )

        second = self.client.post(
            "/api/v1/bookings/",
            self.booking_payload(
                start_time="11:00:00",
                end_time="12:00:00",
            ),
            format="json",
        )

        self.assertEqual(
            second.status_code,
            201,
        )

    # ============================================================
    # LSA SEARCH TESTS
    # ============================================================

    def test_search_lsa_by_skill(self):
        response = self.client.get(
            "/api/v1/lsas/search/?skill=Mathematics"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            len(response.data),
            1,
        )

        self.assertEqual(
            response.data[0]["name"],
            "Sarah",
        )

    def test_lsa_search_avoids_n_plus_one(self):
        # Create five additional LSAs with the same skill.
        for number in range(5):
            lsa = LSA_Profile.objects.create(
                name=f"LSA {number}",
                email=f"lsa{number}@example.com",
                phone="9876500000",
                hourly_rate=Decimal("600.00"),
            )

            lsa.skills.add(self.skill)

        # Capture all database queries executed by the API request.
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                "/api/v1/lsas/search/?skill=Mathematics"
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        # Sarah + 5 additional LSAs = 6 results.
        self.assertEqual(
            len(response.data),
            6,
        )

        # prefetch_related("skills") should keep the query count
        # small instead of generating one query per LSA.
        self.assertLessEqual(
            len(queries),
            3,
        )

    # ============================================================
    # PAYMENT MODEL TEST
    # ============================================================

    def test_payment_is_one_to_one(self):
        booking = Booking_Request.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            booking_date=date(2026, 8, 13),
            start_time=time(13, 0),
            end_time=time(14, 0),
        )

        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-001",
            amount=Decimal("600.00"),
        )

        with self.assertRaises(Exception):
            Payment.objects.create(
                booking=booking,
                transaction_id="TXN-002",
                amount=Decimal("600.00"),
            )

    # ============================================================
    # PAYMENT API TEST
    # ============================================================

    @patch("booking.views.create_payment")
    def test_create_payment(self, mock_create_payment):
        mock_create_payment.return_value = {
            "transaction_id": "TXN-TEST-001",
            "amount": "600.00",
            "status": "SUCCESS",
        }

        booking = Booking_Request.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            booking_date=date(2026, 8, 14),
            start_time=time(10, 0),
            end_time=time(11, 0),
            status=Booking_Request.Status.PENDING,
        )

        response = self.client.post(
            "/api/v1/payments/",
            {
                "booking_id": booking.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            response.data["transaction_id"],
            "TXN-TEST-001",
        )

        self.assertEqual(
            response.data["status"],
            "PENDING",
        )

        payment = Payment.objects.get(
            booking=booking
        )

        self.assertEqual(
            payment.transaction_id,
            "TXN-TEST-001",
        )

        mock_create_payment.assert_called_once()

    # ============================================================
    # PAYMENT WEBHOOK TEST
    # ============================================================

    def test_payment_webhook_confirms_booking(self):
        booking = Booking_Request.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            booking_date=date(2026, 8, 14),
            start_time=time(12, 0),
            end_time=time(13, 0),
            status=Booking_Request.Status.PENDING,
        )

        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-WEBHOOK-001",
            amount=Decimal("600.00"),
            status=Payment.Status.PENDING,
        )

        response = self.client.post(
            "/api/v1/payments/webhook/",
            {
                "transaction_id": "TXN-WEBHOOK-001",
                "status": "SUCCESS",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payment = Payment.objects.get(
            transaction_id="TXN-WEBHOOK-001"
        )

        booking.refresh_from_db()

        self.assertEqual(
            payment.status,
            Payment.Status.SUCCESS,
        )

        self.assertEqual(
            booking.status,
            Booking_Request.Status.CONFIRMED,
        )

    # ============================================================
    # WEBHOOK IDEMPOTENCY TEST
    # ============================================================

    def test_duplicate_webhook_is_idempotent(self):
        booking = Booking_Request.objects.create(
            parent=self.parent,
            lsa=self.lsa,
            booking_date=date(2026, 8, 14),
            start_time=time(14, 0),
            end_time=time(15, 0),
            status=Booking_Request.Status.PENDING,
        )

        Payment.objects.create(
            booking=booking,
            transaction_id="TXN-IDEMPOTENT-001",
            amount=Decimal("600.00"),
            status=Payment.Status.PENDING,
        )

        payload = {
            "transaction_id": "TXN-IDEMPOTENT-001",
            "status": "SUCCESS",
        }

        first = self.client.post(
            "/api/v1/payments/webhook/",
            payload,
            format="json",
        )

        second = self.client.post(
            "/api/v1/payments/webhook/",
            payload,
            format="json",
        )

        self.assertEqual(
            first.status_code,
            200,
        )

        self.assertEqual(
            second.status_code,
            200,
        )

        self.assertEqual(
            Payment.objects.filter(
                transaction_id="TXN-IDEMPOTENT-001"
            ).count(),
            1,
        )

        booking.refresh_from_db()

        self.assertEqual(
            booking.status,
            Booking_Request.Status.CONFIRMED,
        )