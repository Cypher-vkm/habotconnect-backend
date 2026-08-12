from decimal import Decimal

from django.db import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking_Request, LSA_Profile, Payment
from .payment_service import PaymentGatewayError, create_payment
from .serializers import BookingCreateSerializer, LSASearchSerializer
from .services import has_booking_conflict


class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        if has_booking_conflict(
            lsa=data["lsa"],
            booking_date=data["booking_date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
        ):
            return Response(
                {
                    "detail": (
                        "The LSA already has a booking "
                        "that overlaps this time."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        booking = serializer.save(
            status=Booking_Request.Status.PENDING
        )

        return Response(
            {
                "id": booking.id,
                "parent_id": booking.parent_id,
                "lsa_id": booking.lsa_id,
                "booking_date": booking.booking_date,
                "start_time": booking.start_time,
                "end_time": booking.end_time,
                "status": booking.status,
            },
            status=status.HTTP_201_CREATED,
        )


class LSASearchView(APIView):
    def get(self, request):
        skill = request.query_params.get("skill")

        if skill:
            queryset = (
                LSA_Profile.objects
                .filter(skills__name__iexact=skill)
                .prefetch_related("skills")
                .distinct()
            )
        else:
            queryset = (
                LSA_Profile.objects
                .prefetch_related("skills")
                .all()
            )

        serializer = LSASearchSerializer(queryset, many=True)

        return Response(serializer.data)


class MockPaymentGatewayView(APIView):
    """
    Local mock of an external payment gateway.
    """

    def post(self, request):
        amount = request.data.get("amount")
        transaction_id = request.data.get("transaction_id")

        if not amount or not transaction_id:
            return Response(
                {
                    "detail": "amount and transaction_id are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "transaction_id": transaction_id,
                "amount": str(amount),
                "status": "SUCCESS",
            },
            status=status.HTTP_200_OK,
        )


class PaymentCreateView(APIView):
    def post(self, request):
        booking_id = request.data.get("booking_id")

        if not booking_id:
            return Response(
                {"detail": "booking_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            booking = Booking_Request.objects.get(
                id=booking_id
            )
        except Booking_Request.DoesNotExist:
            return Response(
                {"detail": "Booking not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(booking, "payment"):
            return Response(
                {"detail": "Payment already exists for this booking."},
                status=status.HTTP_409_CONFLICT,
            )

        transaction_id = f"TXN-{booking.id}"

        try:
            gateway_response = create_payment(
                amount=booking.lsa.hourly_rate,
                transaction_id=transaction_id,
            )
        except PaymentGatewayError as exc:
            booking.status = Booking_Request.Status.FAILED
            booking.save(update_fields=["status"])

            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            payment = Payment.objects.create(
                booking=booking,
                transaction_id=gateway_response["transaction_id"],
                amount=Decimal(gateway_response["amount"]),
                status=Payment.Status.PENDING,
            )
        except IntegrityError:
            return Response(
                {"detail": "Payment already processed."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "payment_id": payment.id,
                "booking_id": booking.id,
                "transaction_id": payment.transaction_id,
                "amount": str(payment.amount),
                "status": payment.status,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentWebhookView(APIView):
    """
    Handles payment gateway webhook events.

    Repeated webhook events are safe because the transaction_id
    is unique.
    """

    def post(self, request):
        transaction_id = request.data.get("transaction_id")
        payment_status = request.data.get("status")

        if not transaction_id or not payment_status:
            return Response(
                {
                    "detail": (
                        "transaction_id and status are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.select_related(
                "booking"
            ).get(transaction_id=transaction_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Idempotency:
        # If SUCCESS webhook arrives again, don't create
        # another payment or change anything unnecessarily.
        if payment.status == Payment.Status.SUCCESS:
            return Response(
                {
                    "detail": "Webhook already processed.",
                    "status": payment.status,
                },
                status=status.HTTP_200_OK,
            )

        if payment_status == "SUCCESS":
            payment.status = Payment.Status.SUCCESS
            payment.save(update_fields=["status", "updated_at"])

            booking = payment.booking
            booking.status = Booking_Request.Status.CONFIRMED
            booking.save(update_fields=["status"])

        elif payment_status == "FAILED":
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])

            booking = payment.booking
            booking.status = Booking_Request.Status.FAILED
            booking.save(update_fields=["status"])

        else:
            return Response(
                {"detail": "Invalid payment status."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "transaction_id": payment.transaction_id,
                "payment_status": payment.status,
                "booking_status": payment.booking.status,
            },
            status=status.HTTP_200_OK,
        )