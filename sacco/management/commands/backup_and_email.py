import os
import subprocess
from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Backup the database to .sql and email it as an attachment.'

    def handle(self, *args, **kwargs):
        # Settings
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.BASE_DIR, 'db_backups')
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')

        # Dump SQLite DB to .sql
        dump_cmd = f"sqlite3 {db_path} .dump > {backup_file}"
        result = subprocess.run(dump_cmd, shell=True)
        if result.returncode != 0:
            self.stderr.write('Database dump failed!')
            return

        # Email settings
        subject = f"Database Backup {timestamp}"
        body = "Attached is the latest database backup in .sql format."
        recipient = getattr(settings, 'BACKUP_EMAIL_RECIPIENT', None)
        if not recipient:
            self.stderr.write('No BACKUP_EMAIL_RECIPIENT set in settings.')
            return

        email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])
        email.attach_file(backup_file)
        try:
            email.send()
            self.stdout.write(f"Backup emailed to {recipient} successfully.")
        except Exception as e:
            self.stderr.write(f"Failed to send email: {e}")

        # Optionally remove old backups or keep only N latest
