"""
HeritageConnect views (the "controller" layer of the MVC pattern).

- register_view: HTML view for creating a user account.
- ArtisanLocationViewSet, CulturalRegionViewSet, HeritageRouteViewSet:
  REST API endpoints (CRUD) plus custom spatial query endpoints.
"""

import json

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import connection
from django.shortcuts import redirect, render

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


# Largest search radius the API accepts. Keeps queries fast and
# stops someone asking for "every artisan within 10,000 km".
MAX_RADIUS_KM = 50

# Limits for the route buffer query (metres).
DEFAULT_BUFFER_M = 200
MAX_BUFFER_M = 2000


# =========================================================
# Query-parameter validation helpers
# =========================================================

class InvalidParameter(ValueError):
    """Raised when a query parameter is missing or out of range."""


def get_float_param(params, name, minimum, maximum):
    """
    Read a query parameter as a float and check it is within
    [minimum, maximum]. Raises InvalidParameter with a clear message.
    """
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
    """Build a WGS84 Point from ?lat=..&lng=.. query parameters."""
    lat = get_float_param(params, "lat", -90, 90)
    lng = get_float_param(params, "lng", -180, 180)

    # GEOS uses (x, y) = (longitude, latitude) order.
    return lat, lng, Point(lng, lat, srid=4326)


def bad_request(message):
    return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)


# =========================================================
# Account registration (HTML view)
# =========================================================

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


# =========================================================
# Artisan locations (Point geometry)
# =========================================================

class ArtisanLocationViewSet(viewsets.ModelViewSet):
    """
    CRUD for artisan locations.

    Anyone can read. Logged-in users can create artisans, and only
    the owner (or a staff user) can edit or delete them.
    """

    queryset = (
        ArtisanLocation.objects
        .select_related("region", "owner")
        .order_by("name")
    )
    serializer_class = ArtisanLocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        # The owner is always the logged-in user, never taken from
        # the request body, so users cannot create items as someone else.
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def within_radius(self, request):
        """
        Spatial query 1 - PROXIMITY / RADIUS SEARCH (spherical distance).

        Return artisans within `radius` km of a point, nearest first.

        Example:
        /api/heritage/artisans/within_radius/?lat=53.3498&lng=-6.2603&radius=3
        """
        try:
            lat, lng, user_point = get_point_from_params(request.query_params)
            radius = get_float_param(
                request.query_params, "radius", 0.01, MAX_RADIUS_KM
            )
        except InvalidParameter as error:
            return bad_request(str(error))

        artisans = (
            self.get_queryset()
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

    @action(detail=False, methods=["get"])
    def nearest(self, request):
        """
        Spatial query 2 - NEAREST NEIGHBOUR (ORDER BY distance).

        Return the single closest artisan to a point.

        Example:
        /api/heritage/artisans/nearest/?lat=53.3498&lng=-6.2603
        """
        try:
            lat, lng, user_point = get_point_from_params(request.query_params)
        except InvalidParameter as error:
            return bad_request(str(error))

        artisan = (
            self.get_queryset()
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


# =========================================================
# Cultural regions (Polygon geometry)
# =========================================================

class CulturalRegionViewSet(viewsets.ModelViewSet):
    """
    Curated cultural regions. Read-only for the public;
    only staff users can create, edit or delete regions.
    """

    queryset = CulturalRegion.objects.all().order_by("name")
    serializer_class = CulturalRegionSerializer
    permission_classes = [IsStaffOrReadOnly]

    @action(detail=True, methods=["get"])
    def artisans(self, request, pk=None):
        """
        Spatial query 3 - CONTAINMENT (ST_Within).

        Return artisans whose location lies inside this region's polygon.

        Example:
        /api/heritage/regions/1/artisans/
        """
        region = self.get_object()  # returns 404 automatically if missing

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


# =========================================================
# Heritage routes (LineString geometry)
# =========================================================

class HeritageRouteViewSet(viewsets.ModelViewSet):
    """
    Curated heritage routes. Read-only for the public;
    only staff users can create, edit or delete routes.
    """

    queryset = HeritageRoute.objects.all().order_by("name")
    serializer_class = HeritageRouteSerializer
    permission_classes = [IsStaffOrReadOnly]

    @action(detail=False, methods=["get"])
    def intersecting_region(self, request):
        """
        Spatial query 4 - INTERSECTION (ST_Intersects).

        Return routes that cross or touch a cultural region.

        Example:
        /api/heritage/routes/intersecting_region/?region_id=1
        """
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

    @action(detail=True, methods=["get"])
    def artisans_nearby(self, request, pk=None):
        """
        Spatial query 5 - BUFFER (ST_Buffer + ST_DWithin on geography).

        Return artisans within `distance` metres of this route - i.e.
        makers you could visit while walking the trail - plus the buffer
        polygon itself so the map can draw the corridor.

        Example:
        /api/heritage/routes/1/artisans_nearby/?distance=200
        """
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

        # Casting to ::geography makes PostGIS measure in metres on the
        # Earth's surface instead of in degrees. Values are passed as
        # query parameters (%s), never pasted into the SQL string, which
        # prevents SQL injection.
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
