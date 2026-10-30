from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (
    ArtisanLocation,
    CulturalRegion,
    HeritageRoute,
)


class CulturalRegionSerializer(
    GeoFeatureModelSerializer
):
    class Meta:
        model = CulturalRegion
        geo_field = "boundary"

        fields = (
            "id",
            "name",
            "region_type",
            "description",
            "created_at",
            "updated_at",
        )


class ArtisanLocationSerializer(
    GeoFeatureModelSerializer
):
    craft_type_display = serializers.CharField(
        source="get_craft_type_display",
        read_only=True
    )

    region_name = serializers.CharField(
        source="region.name",
        read_only=True
    )

    owner_username = serializers.SerializerMethodField()

    def get_owner_username(self, obj):
        if obj.owner:
            return obj.owner.username

        return None

    class Meta:
        model = ArtisanLocation
        geo_field = "location"

        fields = (
            "id",
            "owner",
            "owner_username",
            "name",
            "artisan_name",
            "craft_type",
            "craft_type_display",
            "description",
            "address",
            "phone",
            "website",
            "opening_hours",
            "region",
            "region_name",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "owner",
            "owner_username",
        )


class HeritageRouteSerializer(
    GeoFeatureModelSerializer
):
    route_type_display = serializers.CharField(
        source="get_route_type_display",
        read_only=True
    )

    class Meta:
        model = HeritageRoute
        geo_field = "path"

        fields = (
            "id",
            "name",
            "route_type",
            "route_type_display",
            "description",
            "distance_km",
            "created_at",
            "updated_at",
        )