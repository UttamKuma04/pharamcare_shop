from celery import shared_task
from django.core.mail import EmailMultiAlternatives


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, subject, body, from_email, to_email, html_body=None):
    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_body:
        email_message.attach_alternative(html_body, 'text/html')
    try:
        email_message.send()
    except Exception as exc:
        raise self.retry(exc=exc)
