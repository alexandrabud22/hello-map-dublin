import json
from pathlib import Path

from django.contrib.gis.geos import LineString, Point, Polygon
from django.core.management.base import BaseCommand
from django.db import transaction

from heritage.models import ArtisanLocation, CulturalRegion, HeritageRoute

REGIONS = [
    {
        "name": "Temple Bar",
        "region_type": "Historic Quarter",
        "description": (
            "Cobbled cultural quarter between Dame Street and the "
            "Liffey, home to galleries, studios and craft markets."
        ),
        "boundary": [
            (-6.2710, 53.3456), (-6.2650, 53.3463), (-6.2590, 53.3469),
            (-6.2594, 53.3446), (-6.2650, 53.3441), (-6.2706, 53.3437),
        ],
    },
    {
        "name": "The Liberties",
        "region_type": "Craft & Market District",
        "description": (
            "One of Dublin's oldest neighbourhoods, historically known "
            "for weaving, brewing, distilling and antiques."
        ),
        "boundary": [
            (-6.2900, 53.3432), (-6.2800, 53.3438), (-6.2720, 53.3432),
            (-6.2712, 53.3385), (-6.2790, 53.3365), (-6.2905, 53.3380),
        ],
    },
    {
        "name": "Smithfield & Stoneybatter",
        "region_type": "Urban Village",
        "description": (
            "Former market district north of the Liffey with a strong "
            "community of independent makers."
        ),
        "boundary": [
            (-6.2930, 53.3462), (-6.2735, 53.3460), (-6.2725, 53.3530),
            (-6.2800, 53.3580), (-6.2920, 53.3570),
        ],
    },
    {
        "name": "Docklands",
        "region_type": "Waterfront Regeneration",
        "description": (
            "Regenerated port area around the Grand Canal Dock and "
            "North Wall, mixing maritime heritage with new studios."
        ),
        "boundary": [
            (-6.2500, 53.3480), (-6.2280, 53.3500), (-6.2280, 53.3420),
            (-6.2350, 53.3385), (-6.2440, 53.3400), (-6.2500, 53.3445),
        ],
    },
]

ROUTES_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "heritage_routes.geojson"
)

def load_route_features():
    with open(ROUTES_FILE, encoding="utf-8") as file:
        return json.load(file)["features"]

ARTISANS = [

    ("Temple Bar Pottery Studio", "Aoife Murphy", "POTTERY",
     "Temple Bar, Dublin 2", -6.2675, 53.3455, "10:00 - 18:00",
     "Traditional handmade pottery and ceramic workshops."),
    ("Cow's Lane Print Studio", "Ciara Byrne", "PAINTING",
     "Cow's Lane, Dublin 8", -6.2695, 53.3448, "11:00 - 17:00",
     "Hand-printed Irish landscapes and Celtic designs."),

    ("Thomas Street Textiles", "Orla Doyle", "TEXTILES",
     "Thomas Street, Dublin 8", -6.2815, 53.3433, "09:30 - 17:00",
     "Traditional Irish tweed and woven textiles."),
    ("Francis Street Woodturners", "Declan Walsh", "WOODCARVING",
     "Francis Street, Dublin 8", -6.2752, 53.3412, "10:00 - 18:00",
     "Hand-turned bowls and furniture from Irish hardwoods."),
    ("Coombe Leather Works", "Padraig Nolan", "LEATHER",
     "The Coombe, Dublin 8", -6.2768, 53.3393, "10:00 - 17:30",
     "Hand-stitched leather goods using traditional methods."),

    ("Dublin Weaving Workshop", "Niamh Kelly", "WEAVING",
     "Smithfield, Dublin 7", -6.2785, 53.3488, "09:30 - 17:30",
     "Traditional textile weaving and craft demonstrations."),
    ("Celtic Woodcraft Studio", "Sean O'Brien", "WOODCARVING",
     "Dublin 7", -6.2860, 53.3560, "11:00 - 17:00",
     "Hand-carved traditional wooden crafts."),
    ("Stoneybatter Silversmiths", "Grainne Ryan", "JEWELLERY",
     "Manor Street, Dublin 7", -6.2848, 53.3527, "10:00 - 18:00",
     "Silver jewellery inspired by Celtic knotwork."),

    ("Grand Canal Glass & Clay", "Eoin Fitzgerald", "POTTERY",
     "Grand Canal Dock, Dublin 2", -6.2385, 53.3412, "10:00 - 16:00",
     "Contemporary ceramics and studio glass."),
    ("North Wall Sail & Canvas", "Siobhan Keane", "TEXTILES",
     "North Wall Quay, Dublin 1", -6.2330, 53.3470, "09:00 - 17:00",
     "Canvas bags and goods made with old sail-making skills."),

    ("Portobello Bookbinders", "Liam Brennan", "OTHER",
     "Portobello, Dublin 8", -6.2650, 53.3315, "11:00 - 17:00",
     "Hand-bound notebooks and book restoration."),
    ("Phibsborough Stained Glass", "Maeve Duffy", "PAINTING",
     "Phibsborough, Dublin 7", -6.2730, 53.3600, "10:00 - 16:00",
     "Stained glass panels in traditional Irish styles."),
]

class Command(BaseCommand):
    help = "Load HeritageConnect sample regions, routes and artisans."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Loading HeritageConnect sample data...")

        sample_names = [artisan[0] for artisan in ARTISANS]
        deleted_artisans, _ = (
            ArtisanLocation.objects
            .filter(owner__isnull=True, name__in=sample_names)
            .delete()
        )
        HeritageRoute.objects.all().delete()
        CulturalRegion.objects.all().delete()

        for region in REGIONS:
            ring = region["boundary"] + [region["boundary"][0]]
            boundary = Polygon(ring, srid=4326)
            if not boundary.valid:
                raise ValueError(f"{region['name']}: {boundary.valid_reason}")

            CulturalRegion.objects.create(
                name=region["name"],
                region_type=region["region_type"],
                description=region["description"],
                boundary=boundary,
            )

        for feature in load_route_features():
            properties = feature["properties"]

            HeritageRoute.objects.create(
                name=properties["name"],
                route_type=properties["route_type"],
                description=properties["description"],
                path=LineString(
                    feature["geometry"]["coordinates"], srid=4326
                ),
            )

        for (name, artisan, craft, address, lng, lat,
             hours, description) in ARTISANS:

            ArtisanLocation.objects.create(
                name=name,
                artisan_name=artisan,
                craft_type=craft,
                address=address,
                location=Point(lng, lat, srid=4326),
                opening_hours=hours,
                description=description,
            )

        relinked = 0
        for artisan in ArtisanLocation.objects.exclude(
            owner__isnull=True, name__in=sample_names
        ):
            artisan.region = (
                CulturalRegion.objects
                .filter(boundary__contains=artisan.location)
                .first()
            )
            artisan.save(update_fields=["region"])
            relinked += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done: {CulturalRegion.objects.count()} regions, "
            f"{HeritageRoute.objects.count()} routes, "
            f"{len(ARTISANS)} sample artisans "
            f"(replaced {deleted_artisans} old sample rows), "
            f"{relinked} other artisans kept and re-linked."
        ))
