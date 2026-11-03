from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import ArtisanLocation, CulturalRegion, HeritageRoute

@admin.register(ArtisanLocation)
class ArtisanLocationAdmin(GISModelAdmin):
    list_display = (
        "name",
        "artisan_name",
        "craft_type",
        "address",
        "region",
        "created_at",
    )

    list_filter = (
        "craft_type",
        "region",
    )

    search_fields = (
        "name",
        "artisan_name",
        "address",
    )

@admin.register(CulturalRegion)
class CulturalRegionAdmin(GISModelAdmin):
    list_display = (
        "name",
        "region_type",
        "created_at",
    )

    search_fields = (
        "name",
        "region_type",
    )

@admin.register(HeritageRoute)
class HeritageRouteAdmin(GISModelAdmin):
    list_display = (
        "name",
        "route_type",
        "distance_km",
        "created_at",
    )

    list_filter = (
        "route_type",
    )

    search_fields = (
        "name",
        "description",
    )
