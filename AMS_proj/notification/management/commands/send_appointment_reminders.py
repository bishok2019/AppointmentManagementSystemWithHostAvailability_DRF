# notification/management/commands/send_appointment_reminders.py
from django.core.management.base import BaseCommand
from notification.tasks import notify_hosts_of_upcoming_appointments

class Command(BaseCommand):
    help = 'Send notifications for upcoming appointments'

    def handle(self, *args, **options):
        notify_hosts_of_upcoming_appointments()
        self.stdout.write(self.style.SUCCESS('Successfully sent appointment reminders'))