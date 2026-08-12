# HabotConnect Backend

Junior Python Backend Developer hiring project.

## Stack

- Python
- Django
- Django REST Framework
- PostgreSQL (planned production database)
- requests
- pytest / Django TestCase

## Current API

- `POST /api/v1/bookings/`
- `GET /api/v1/lsas/search/?skill=Mathematics`

## Core design

Parent 1:N Booking_Request  
LSA_Profile 1:N Booking_Request  
Booking_Request 1:1 Payment  
LSA_Profile M:N Skill

## Development

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

The initial development configuration uses SQLite so the project can be bootstrapped immediately. PostgreSQL configuration will be added before final submission.
