from users import models
from users.models import Users
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@shared_task(bind=True)
def send_mail_func(self, user_id, message):
    user = Users.objects.get(user_id=user_id)
    #timezone.localtime(users.date_time) + timedelta(days=2)
    mail_subject = f"Hi {user.username}! You just got a notification "
    to_email = user.email
    send_mail(
        subject = mail_subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[to_email],
        fail_silently=False,
    )
    return "Done"