from django.core.validators import MinValueValidator
from django.db import models


class Parent(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"], name="idx_parent_email"),
        ]

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class LSA_Profile(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    skills = models.ManyToManyField(Skill, related_name="lsas", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email"], name="idx_lsa_email"),
        ]

    def __str__(self):
        return self.name


class Booking_Request(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        FAILED = "FAILED", "Failed"

    parent = models.ForeignKey(
        Parent,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    lsa = models.ForeignKey(
        LSA_Profile,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["lsa", "booking_date"],
                name="idx_booking_lsa_date",
            ),
            models.Index(
                fields=["lsa", "booking_date", "start_time", "end_time"],
                name="idx_booking_lsa_datetime",
            ),
            models.Index(
                fields=["status"],
                name="idx_booking_status",
            ),
        ]

    def __str__(self):
        return f"Booking #{self.pk}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    booking = models.OneToOneField(
        Booking_Request,
        on_delete=models.CASCADE,
        related_name="payment",
    )
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["transaction_id"], name="idx_payment_transaction"),
        ]

    def __str__(self):
        return self.transaction_id
