from django.db.models import Q
from .models import Booking_Request


def has_booking_conflict(*, lsa, booking_date, start_time, end_time):
    """
    Two time intervals overlap when:
        existing.start < requested.end
        AND
        existing.end > requested.start

    We ignore CANCELLED and FAILED bookings because they no longer
    reserve the slot.
    """
    return Booking_Request.objects.filter(
        lsa=lsa,
        booking_date=booking_date,
    ).exclude(
        status__in=[
            Booking_Request.Status.CANCELLED,
            Booking_Request.Status.FAILED,
        ]
    ).filter(
        Q(start_time__lt=end_time) &
        Q(end_time__gt=start_time)
    ).exists()
