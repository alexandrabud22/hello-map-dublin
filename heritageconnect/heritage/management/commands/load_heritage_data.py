from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, Polygon, LineString

from heritage.models import ArtisanLocation, CulturalRegion, HeritageRoute


class Command(BaseCommand):
    help = "Load sample spatial data for HeritageConnect"

    def handle(self, *args, **options):
        self.stdout.write("Loading HeritageConnect sample data...")

        # Clear existing sample data
        ArtisanLocation.objects.all().delete()
        HeritageRoute.objects.all().delete()
        CulturalRegion.objects.all().delete()

        # -------------------------------------------------
        # Cultural Region - Dublin City Centre
        # -------------------------------------------------
        dublin_region = CulturalRegion.objects.create(
            name="Dublin Cultural Quarter",
            region_type="Cultural District",
            description=(
                "A sample cultural region covering part of central Dublin "
                "for demonstrating polygon-based spatial queries."
            ),
            boundary=Polygon(
                (
                    (-6.2900, 53.3300),
                    (-6.2200, 53.3300),
                    (-6.2200, 53.3700),
                    (-6.2900, 53.3700),
                    (-6.2900, 53.3300),
                ),
                srid=4326,
            ),
        )

        # -------------------------------------------------
        # Artisan Locations
        # -------------------------------------------------
        ArtisanLocation.objects.create(
            name="Temple Bar Pottery Studio",
            artisan_name="Aoife Murphy",
            craft_type="POTTERY",
            description="Traditional handmade pottery and ceramic workshops.",
            address="Temple Bar, Dublin",
            location=Point(-6.2675, 53.3455, srid=4326),
            phone="",
            website="",
            opening_hours="10:00 - 18:00",
            region=dublin_region,
        )

        ArtisanLocation.objects.create(
            name="Dublin Weaving Workshop",
            artisan_name="Niamh Kelly",
            craft_type="WEAVING",
            description="Traditional textile weaving and craft demonstrations.",
            address="Smithfield, Dublin",
            location=Point(-6.2785, 53.3488, srid=4326),
            phone="",
            website="",
            opening_hours="09:30 - 17:30",
            region=dublin_region,
        )

        ArtisanLocation.objects.create(
            name="Celtic Woodcraft Studio",
            artisan_name="Sean O'Brien",
            craft_type="WOODCARVING",
            description="Hand-carved traditional wooden crafts.",
            address="Dublin 7",
            location=Point(-6.2860, 53.3560, srid=4326),
            phone="",
            website="",
            opening_hours="11:00 - 17:00",
            region=dublin_region,
        )

        # -------------------------------------------------
        # Heritage Route
        # -------------------------------------------------
        HeritageRoute.objects.create(
            name="Dublin Artisan Trail",
            route_type="CRAFT",
            description=(
                "A sample heritage route connecting traditional craft "
                "locations in central Dublin."
            ),
            path=LineString(
                (-6.2675, 53.3455),
                (-6.2785, 53.3488),
                (-6.2860, 53.3560),
                srid=4326,
            ),
            distance_km=3.20,
        )

        self.stdout.write(
            self.style.SUCCESS("HeritageConnect sample data loaded successfully.")
        )

        self.stdout.write(
            f"Cultural regions: {CulturalRegion.objects.count()}"
        )
        self.stdout.write(
            f"Artisan locations: {ArtisanLocation.objects.count()}"
        )
        self.stdout.write(
            f"Heritage routes: {HeritageRoute.objects.count()}"
        )