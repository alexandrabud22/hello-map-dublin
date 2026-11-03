import re

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import ArtisanLocation, CulturalRegion, HeritageRoute

# Limit workshop coordinates to a box around Ireland.
IRELAND_BOUNDS = {
    "min_lng": -10.8,
    "max_lng": -5.3,
    "min_lat": 51.3,
    "max_lat": 55.5,
}

PHONE_PATTERN = re.compile(r"^[0-9+\-() ]{6,20}$")

def validate_not_blank(value, field_label):
    if not value or not value.strip():
        raise serializers.ValidationError(f"{field_label} cannot be blank.")
    return value.strip()

def validate_geometry_is_valid(geometry):

    # Reject shapes with problems such as crossing polygon edges.
    if geometry is not None and not geometry.valid:
        raise serializers.ValidationError(
            f"Invalid geometry: {geometry.valid_reason}"
        )
    return geometry

# Reject the wrong geometry type before it reaches the database.
def validate_geometry_type(geometry, expected_type):

    if geometry is None:
        raise serializers.ValidationError("A geometry is required.")
    if geometry.geom_type != expected_type:
        raise serializers.ValidationError(
            f"Geometry must be a {expected_type}, not a {geometry.geom_type}."
        )
    if geometry.srid not in (None, 4326):
        geometry.transform(4326)
    return geometry

class CulturalRegionSerializer(GeoFeatureModelSerializer):
    artisan_count = serializers.SerializerMethodField()

    class Meta:
        model = CulturalRegion
        geo_field = "boundary"
        fields = (
            "id",
            "name",
            "region_type",
            "description",
            "artisan_count",
            "created_at",
            "updated_at",
        )

    def get_artisan_count(self, obj):
        return obj.artisans.count()

    def validate_name(self, value):
        return validate_not_blank(value, "Region name")

    def validate_boundary(self, value):
        validate_geometry_type(value, "Polygon")
        return validate_geometry_is_valid(value)

class ArtisanLocationSerializer(GeoFeatureModelSerializer):
    craft_type_display = serializers.CharField(
        source="get_craft_type_display", read_only=True
    )
    region_name = serializers.CharField(
        source="region.name", read_only=True, default=None
    )
    owner_username = serializers.CharField(
        source="owner.username", read_only=True, default=None
    )

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
        read_only_fields = ("owner", "created_at", "updated_at")

    def validate_name(self, value):
        return validate_not_blank(value, "Workshop name")

    def validate_artisan_name(self, value):
        return validate_not_blank(value, "Artisan name")

    def validate_address(self, value):
        return validate_not_blank(value, "Address")

    def validate_phone(self, value):
        value = (value or "").strip()
        if value and not PHONE_PATTERN.match(value):
            raise serializers.ValidationError(
                "Phone may only contain digits, spaces, +, -, ( and )."
            )
        return value

    def validate_location(self, value):
        validate_geometry_type(value, "Point")

        lng, lat = value.x, value.y
        bounds = IRELAND_BOUNDS

        if not (
            bounds["min_lng"] <= lng <= bounds["max_lng"]
            and bounds["min_lat"] <= lat <= bounds["max_lat"]
        ):
            raise serializers.ValidationError(
                "Artisan locations must be in Ireland."
            )
        return value

    def validate(self, attrs):

        region = attrs.get("region", getattr(self.instance, "region", None))
        location = attrs.get(
            "location", getattr(self.instance, "location", None)
        )

        # A chosen region must actually contain the workshop.
        if region and location and not region.boundary.contains(location):
            raise serializers.ValidationError(
                {"region": f"This location is not inside {region.name}."}
            )
        return attrs

class HeritageRouteSerializer(GeoFeatureModelSerializer):
    route_type_display = serializers.CharField(
        source="get_route_type_display", read_only=True
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

    def validate_name(self, value):
        return validate_not_blank(value, "Route name")

    def validate_path(self, value):
        validate_geometry_type(value, "LineString")
        validate_geometry_is_valid(value)
        if value is not None and value.num_points < 2:
            raise serializers.ValidationError(
                "A route needs at least two points."
            )
        return value
