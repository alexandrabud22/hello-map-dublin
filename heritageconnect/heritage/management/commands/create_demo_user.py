import os

from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from heritage.models import ArtisanLocation

DEMO_USERNAME = "demo"
# This password is for the local demo account only.
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

        # Remove the old demo entry before setting up the current one.
        ArtisanLocation.objects.filter(
            owner=user, name="Demo Basket Weaver"
        ).delete()

        # Running the command again updates the same workshop.
        artisan, _ = ArtisanLocation.objects.update_or_create(
            owner=user,
            name="Meath Street Basketry",
            defaults={
                "artisan_name": "Róisín Daly",
                "craft_type": "WEAVING",
                "address": "Meath Street, Dublin 8",
                "location": Point(-6.2780, 53.3405, srid=4326),
                "opening_hours": "10:00 - 16:00",
                "description": (
                    "Hand-woven willow baskets and traditional Irish creels."
                ),
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Reset'} user '{DEMO_USERNAME}' "
            f"with an artisan in {artisan.region or 'no region'}."
        ))
