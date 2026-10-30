from django.contrib.gis.db import models
from django.contrib.auth.models import User


class CulturalRegion(models.Model):
    name = models.CharField(max_length=150)
    region_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    boundary = models.PolygonField(srid=4326)

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

    location = models.PointField(srid=4326)

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

    path = models.LineStringField(srid=4326)

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