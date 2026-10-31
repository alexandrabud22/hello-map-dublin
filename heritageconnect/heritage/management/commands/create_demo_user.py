"""
Create (or reset) a demo account for markers / testers.

    docker compose exec web python manage.py create_demo_user

  * Username: demo   (normal user - NOT staff, cannot change regions/routes)
  * Password: value of DEMO_USER_PASSWORD in .env, or the default below
  * Also creates one artisan owned by the demo user, so Edit/Delete
    can be tried immediately.

This is a local demonstration account only. Never reuse this password.
"""

import os

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from heritage.models import ArtisanLocation


DEMO_USERNAME = "demo"
DEFAULT_DEMO_PASSWORD = "HeritageDemo2026!"


class Command(BaseCommand):
    help = "Create or reset the 'demo' user and a sample artisan it owns."

    def handle(self, *args, **options):
        password = os.getenv("DEMO_USER_PASSWORD", DEFAULT_DEMO_PASSWORD)

        user, created = User.objects.get_or_create(username=DEMO_USERNAME)
        user.set_password(password)
        user.is_staff = False
        user.is_superuser = False
        user.save()

        artisan, _ = ArtisanLocation.objects.update_or_create(
            owner=user,
            name="Demo Basket Weaver",
            defaults={
                "artisan_name": "Demo User",
                "craft_type": "WEAVING",
                "address": "Meath Street, Dublin 8",
                "location": Point(-6.2780, 53.3405, srid=4326),
                "opening_hours": "10:00 - 16:00",
                "description": (
                    "Artisan owned by the demo account - try Edit or "
                    "Delete on it."
                ),
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Reset'} user '{DEMO_USERNAME}' "
            f"with an artisan in {artisan.region or 'no region'}."
        ))
