import json
import math

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.gis.db.models.functions import Distance, GeometryDistance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import connection
from django.shortcuts import redirect, render

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import ArtisanLocation, CulturalRegion, HeritageRoute
from .permissions import IsOwnerOrReadOnly, IsStaffOrReadOnly
from .serializers import (
    ArtisanLocationSerializer,
    CulturalRegionSerializer,
    HeritageRouteSerializer,
)

MAX_RADIUS_KM = 50

DEFAULT_BUFFER_M = 200
MAX_BUFFER_M = 2000

class InvalidParameter(ValueError):
    pass

def get_float_param(params, name, minimum, maximum):

    raw_value = params.get(name)

    if raw_value in (None, ""):
        raise InvalidParameter(f"'{name}' is required.")

    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        raise InvalidParameter(f"'{name}' must be a valid number.")

    if not minimum <= value <= maximum:
        raise InvalidParameter(
            f"'{name}' must be between {minimum} and {maximum}."
        )

    return value

def get_point_from_params(params):

    lat = get_float_param(params, "lat", -90, 90)
    lng = get_float_param(params, "lng", -180, 180)
    return lat, lng, Point(lng, lat, srid=4326)

def degrees_covering_km(km, latitude):

    km_per_degree = 111.32 * max(math.cos(math.radians(latitude)), 0.01)
    return km / km_per_degree

LAT_PARAM = OpenApiParameter(
    "lat", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True,
    description="Latitude in WGS84 (-90 to 90), e.g. 53.3498",
)
LNG_PARAM = OpenApiParameter(
    "lng", OpenApiTypes.FLOAT, OpenApiParameter.QUERY, required=True,
    description="Longitude in WGS84 (-180 to 180), e.g. -6.2603",
)
FILTER_PARAMS = [
    OpenApiParameter(
        "search", OpenApiTypes.STR, OpenApiParameter.QUERY,
        description="Optional text filter (name, maker, address, craft)",
    ),
    OpenApiParameter(
        "craft_type", OpenApiTypes.STR, OpenApiParameter.QUERY,
        description="Optional craft filter, e.g. POTTERY or WEAVING",
    ),
    OpenApiParameter(
        "region", OpenApiTypes.INT, OpenApiParameter.QUERY,
        description="Optional cultural region id",
    ),
]

def bad_request(message):
    return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

def register_view(request):
    if request.user.is_authenticated:
        return redirect("heritage-map")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("heritage-map")
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})

class ArtisanLocationViewSet(viewsets.ModelViewSet):

    queryset = (
        ArtisanLocation.objects
        .select_related("region", "owner")
        .order_by("name")
    )
    serializer_class = ArtisanLocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    search_fields = [
        "name", "artisan_name", "address", "description", "craft_type",
    ]
    filterset_fields = ["craft_type", "region", "owner"]
    ordering_fields = ["name", "created_at", "craft_type"]

    # Take the owner from the login session, not the submitted form.
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        parameters=[
            LAT_PARAM,
            LNG_PARAM,
            OpenApiParameter(
                "radius", OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                required=True,
                description=f"Search radius in km (0.01 to {MAX_RADIUS_KM})",
            ),
            *FILTER_PARAMS,
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"])
    # Use the index to narrow the search, then check the distance in kilometres.
    def within_radius(self, request):

        try:
            lat, lng, user_point = get_point_from_params(request.query_params)
            radius = get_float_param(
                request.query_params, "radius", 0.01, MAX_RADIUS_KM
            )
        except InvalidParameter as error:
            return bad_request(str(error))

        artisans = (
            self.filter_queryset(self.get_queryset())
            .filter(
                location__dwithin=(
                    user_point,
                    degrees_covering_km(radius, lat),
                )
            )
            .filter(location__distance_lte=(user_point, D(km=radius)))
            .annotate(distance=Distance("location", user_point))
            .order_by("distance")
        )

        serializer = self.get_serializer(artisans, many=True)

        return Response(
            {
                "center": {"lat": lat, "lng": lng},
                "radius_km": radius,
                "count": len(serializer.data["features"]),
                "results": serializer.data,
            }
        )

    @extend_schema(
        parameters=[LAT_PARAM, LNG_PARAM, *FILTER_PARAMS],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=["get"])
    # Find nearby candidates with the index, then compare their distances.
    def nearest(self, request):

        try:
            lat, lng, user_point = get_point_from_params(request.query_params)
        except InvalidParameter as error:
            return bad_request(str(error))

        filtered = self.filter_queryset(self.get_queryset())
        candidates = (
            filtered
            .order_by(GeometryDistance("location", user_point))[:5]
        )
        artisan = (
            self.get_queryset()
            .filter(id__in=[c.id for c in candidates])
            .annotate(distance=Distance("location", user_point))
            .order_by("distance")
            .first()
        )

        if artisan is None:
            return Response(
                {"error": "No artisan locations found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(artisan)

        return Response(
            {
                "center": {"lat": lat, "lng": lng},
                "distance_km": round(artisan.distance.km, 3),
                "artisan": serializer.data,
            }
        )

class CulturalRegionViewSet(viewsets.ModelViewSet):

    queryset = CulturalRegion.objects.all().order_by("name")
    serializer_class = CulturalRegionSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "region_type", "description"]
    ordering_fields = ["name"]

    @extend_schema(
        parameters=[],
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    # Return workshop points inside this region polygon.
    def artisans(self, request, pk=None):

        region = self.get_object()

        artisans = (
            ArtisanLocation.objects
            .select_related("region", "owner")
            .filter(location__within=region.boundary)
            .order_by("name")
        )

        serializer = ArtisanLocationSerializer(
            artisans, many=True, context={"request": request}
        )

        return Response(
            {
                "region": {
                    "id": region.id,
                    "name": region.name,
                    "region_type": region.region_type,
                },
                "count": len(serializer.data["features"]),
                "artisans": serializer.data,
            }
        )

class HeritageRouteViewSet(viewsets.ModelViewSet):

    queryset = HeritageRoute.objects.all().order_by("name")
    serializer_class = HeritageRouteSerializer
    permission_classes = [IsStaffOrReadOnly]
    search_fields = ["name", "description"]
    filterset_fields = ["route_type"]
    ordering_fields = ["name", "distance_km"]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "region_id", OpenApiTypes.INT, OpenApiParameter.QUERY,
                required=True,
                description="Id of the cultural region to test against",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=False, methods=["get"])
    # Find routes that cross or touch the chosen region.
    def intersecting_region(self, request):

        region_id = request.query_params.get("region_id", "")

        if not region_id.isdigit():
            return bad_request("'region_id' must be a positive whole number.")

        try:
            region = CulturalRegion.objects.get(id=int(region_id))
        except CulturalRegion.DoesNotExist:
            return Response(
                {"error": "Cultural region not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        routes = (
            HeritageRoute.objects
            .filter(path__intersects=region.boundary)
            .order_by("name")
        )

        serializer = self.get_serializer(routes, many=True)

        return Response(
            {
                "region": {
                    "id": region.id,
                    "name": region.name,
                    "region_type": region.region_type,
                },
                "count": len(serializer.data["features"]),
                "routes": serializer.data,
            }
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "distance", OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                description=(
                    f"Buffer distance in metres (10 to {MAX_BUFFER_M}, "
                    f"default {DEFAULT_BUFFER_M})"
                ),
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=["get"])
    # Use metres to find workshops near a route and draw its buffer.
    def artisans_nearby(self, request, pk=None):

        route = self.get_object()

        try:
            if request.query_params.get("distance") in (None, ""):
                distance_m = DEFAULT_BUFFER_M
            else:
                distance_m = get_float_param(
                    request.query_params, "distance", 10, MAX_BUFFER_M
                )
        except InvalidParameter as error:
            return bad_request(str(error))

        artisan_table = ArtisanLocation._meta.db_table
        route_table = HeritageRoute._meta.db_table

        # Pass user values separately from SQL text.
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT ST_AsGeoJSON(
                    ST_Buffer(r.path::geography, %s)::geometry, 6
                )
                FROM {route_table} AS r
                WHERE r.id = %s
                """,
                [distance_m, route.id],
            )
            buffer_geojson = json.loads(cursor.fetchone()[0])

            cursor.execute(
                f"""
                SELECT a.id,
                       ST_Distance(a.location::geography,
                                   r.path::geography) AS distance_m
                FROM {artisan_table} AS a
                JOIN {route_table} AS r ON r.id = %s
                WHERE ST_DWithin(a.location::geography,
                                 r.path::geography, %s)
                ORDER BY distance_m
                """,
                [route.id, distance_m],
            )
            rows = cursor.fetchall()

        distances = {artisan_id: dist for artisan_id, dist in rows}
        artisans_by_id = (
            ArtisanLocation.objects
            .select_related("region", "owner")
            .in_bulk(distances.keys())
        )
        artisans = [artisans_by_id[artisan_id] for artisan_id, _ in rows]

        serializer = ArtisanLocationSerializer(
            artisans, many=True, context={"request": request}
        )
        features = serializer.data["features"]

        for feature, artisan in zip(features, artisans):
            feature["properties"]["distance_to_route_m"] = round(
                distances[artisan.id]
            )

        return Response(
            {
                "route": {
                    "id": route.id,
                    "name": route.name,
                    "distance_km": route.distance_km,
                },
                "buffer_m": distance_m,
                "buffer": buffer_geojson,
                "count": len(artisans),
                "artisans": serializer.data,
            }
        )
