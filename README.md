# HabotConnect Backend

Junior Python Backend Developer hiring project.

## Stack

- Python
- Django
- Django REST Framework
- PostgreSQL 18
- requests
- pytest / Django TestCase

## Current API

### Booking

```text
POST /api/v1/bookings/
```

Creates a booking request after validating the requested time and checking for overlapping bookings.

### LSA Search

```text
GET /api/v1/lsas/search/?skill=Mathematics
```

Searches LSAs by skill.

### Payment

```text
POST /api/v1/payments/
```

Creates a payment for a booking.

### Payment Webhook

```text
POST /api/v1/payments/webhook/
```

Processes payment status updates and confirms the associated booking after a successful payment.

## Core Design

```text
Parent 1:N Booking_Request
LSA_Profile 1:N Booking_Request
Booking_Request 1:1 Payment
LSA_Profile M:N Skill
```

## Booking Rules

- Booking end time must be after start time.
- Overlapping bookings for the same LSA are rejected.
- Adjacent bookings are allowed.
- Invalid booking time ranges return a validation error.
- Conflicting booking requests return HTTP `409 Conflict`.

## LSA Search

LSAs can be searched by skill:

```text
GET /api/v1/lsas/search/?skill=Mathematics
```

The search uses:

```python
prefetch_related("skills")
```

to avoid N+1 database queries when returning LSA skills.

## Payment Flow

1. A parent creates a booking request.
2. The booking starts with `PENDING` status.
3. A payment is created for the booking.
4. The payment receives a transaction ID.
5. The payment webhook updates the payment status.
6. A successful payment changes the booking status to `CONFIRMED`.
7. Repeated webhook requests for the same transaction are handled idempotently.
8. Each booking can have only one payment.

## PostgreSQL Configuration

The project uses PostgreSQL 18 as the database.

Configure the following environment variables:

```text
USE_POSTGRES=1
POSTGRES_DB=habotconnect
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-password>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Do not commit real database credentials to the repository.

## Development

Create and activate a virtual environment:

```powershell
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run database migrations:

```powershell
python manage.py migrate
```

Start the development server:

```powershell
python manage.py runserver
```

## Testing

Run the automated test suite:

```powershell
python manage.py test
```

The test suite covers:

- Booking creation
- Invalid time-range validation
- Overlapping booking prevention
- Adjacent booking support
- LSA skill search
- Payment one-to-one constraint
- N+1 query protection
- Payment creation
- Successful payment webhook
- Webhook idempotency

The current test suite contains **10 automated tests**.

## CI

GitHub Actions automatically runs the Django test suite when changes are pushed to the repository.

## Project Structure

```text
habotconnect-backend/
├── .github/
│   └── workflows/
│       └── django-tests.yml
├── booking/
│   ├── migrations/
│   ├── admin.py
│   ├── models.py
│   ├── payment_service.py
│   ├── serializers.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── README.md
....