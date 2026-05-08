from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run migrations and seed demo data for first deployment."

    def handle(self, *args, **options):
        self.stdout.write("Running migrations...")
        call_command("migrate", verbosity=1)

        self.stdout.write("Seeding demo data...")
        call_command("seed_demo")

        self.stdout.write(self.style.SUCCESS("Database setup complete."))
