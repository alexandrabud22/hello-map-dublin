"""
HeritageConnect data model (the "M" in MVC).

Three spatial tables, one for each PostGIS geometry type:
  CulturalRegion  - POLYGON     (areas such as The Liberties)
  ArtisanLocation - POINT       (individual makers / workshops)
  HeritageRoute   - LINESTRING  (walking / craft trails)

All geometries are stored in WGS84 (SRID 4326, latitude/longitude) so
they can be sent straight to Leaflet as GeoJSON. GeoDjango creates a
GiST spatial index on every geometry field automatically
(spatial_index=True is the default), which keeps spatial queries fast.
"""

from django.contrib.auth.models import User
from django.contrib.gis.db import models


# Irish Transverse Mercator - a projected CRS measured in metres.
# Used whenever we need accurate lengths/distances in Ireland.
IRISH_TM_SRID = 2157


class CulturalRegion(models.Model):
    name = models.CharField(max_length=150)
    region_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    boundary = models.PolygonField(srid=4326, spatial_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ArtisanLocation(models.Model):
    CRAFT_TYPES = [
        ("POTTERY", "Pottery"),
        ("WEAVING", "Weaving"),
        ("WOODCARVING", "Woodcarving"),
        ("TEXTILES", "Traditional Textiles"),
        ("JEWELLERY", "Jewellery"),
        ("LEATHER", "Leatherwork"),
        ("PAINTING", "Traditional Painting"),
        ("OTHER", "Other"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="artisan_locations",
    )

    name = models.CharField(max_length=150)
    artisan_name = models.CharField(max_length=150)

    craft_type = models.CharField(
        max_length=50,
        choices=CRAFT_TYPES,
        default="OTHER",
    )

    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)

    location = models.PointField(srid=4326, spatial_index=True)

    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.CharField(max_length=255, blank=True)

    region = models.ForeignKey(
        CulturalRegion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="artisans",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_craft_type_display()}"

    def save(self, *args, **kwargs):
        """
        If no region was chosen, find it spatially: the cultural region
        whose polygon contains this point (PostGIS ST_Contains).
        """
        if self.region_id is None and self.location is not None:
            self.region = (
                CulturalRegion.objects
                .filter(boundary__contains=self.location)
                .first()
            )
        super().save(*args, **kwargs)


class HeritageRoute(models.Model):
    ROUTE_TYPES = [
        ("WALKING", "Walking Route"),
        ("CRAFT", "Craft Trail"),
        ("CULTURAL", "Cultural Route"),
        ("CYCLING", "Cycling Route"),
        ("OTHER", "Other"),
    ]

    name = models.CharField(max_length=150)

    route_type = models.CharField(
        max_length=50,
        choices=ROUTE_TYPES,
        default="CULTURAL",
    )

    description = models.TextField(blank=True)

    path = models.LineStringField(srid=4326, spatial_index=True)

    # Calculated automatically from the geometry in save().
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Calculate the route length in km. Degrees are not a distance,
        so the line is projected to Irish Transverse Mercator (metres).
        """
        if self.path is not None:
            metric_path = self.path.transform(IRISH_TM_SRID, clone=True)
            self.distance_km = round(metric_path.length / 1000, 2)
        super().save(*args, **kwargs)