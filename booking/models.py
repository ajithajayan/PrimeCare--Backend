from django.db import models

from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.core.validators import MinValueValidator
from account.models import Doctor




class DoctorAvailability(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_available(self):
        return not self.is_booked
    def is_cancelled(self):
        return self.is_cancelled




class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    transaction_id = models.CharField(max_length=200, verbose_name="Transaction ID", unique=True, primary_key=True)
    payment_id = models.CharField(max_length=200, verbose_name="Payment ID")
    order_id = models.CharField(max_length=200, verbose_name="Order ID",null=True,blank=True)
    signature = models.CharField(max_length=500, verbose_name="Signature", blank=True, null=True)
    amount = models.IntegerField(verbose_name="Amount")
    doctor_id = models.CharField(max_length=200, verbose_name="Doctor ID")
    patient_id = models.CharField(max_length=200, verbose_name="Patient ID") 
    booked_date = models.DateField()
    booked_from_time = models.TimeField()
    booked_to_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Auto-generate transaction ID greater than the last one
            last_transaction = Transaction.objects.order_by('-transaction_id').first()
            if last_transaction:
                last_id = int(last_transaction.transaction_id)
                self.transaction_id = str(last_id + 1)
            else:
                self.transaction_id = '121212'

        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.transaction_id)

     