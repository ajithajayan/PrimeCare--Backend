from django.contrib import admin
from .models import DoctorAvailability,Transaction

# Register your models here.


admin.site.register(DoctorAvailability)
admin.site.register(Transaction)