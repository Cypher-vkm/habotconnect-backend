from django.contrib import admin
from .models import Booking_Request, LSA_Profile, Parent, Payment, Skill

admin.site.register(Parent)
admin.site.register(LSA_Profile)
admin.site.register(Skill)
admin.site.register(Booking_Request)
admin.site.register(Payment)
