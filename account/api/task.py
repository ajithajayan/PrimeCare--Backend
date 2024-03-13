from celery import shared_task
from Backend.celery import app

from django.core.mail import send_mail


@shared_task()
def sent_otp(body, mail, header="OTP AUTHENTICATING Elder Care"):
    # Task logic here
    send_mail(
            header,
            body,
            "ajithajayan222aa@gmail.com",
            [mail],
            fail_silently=False,
        )

    return f'Mail send'