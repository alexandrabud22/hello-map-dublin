from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render

from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
)

from .permissions import IsOwnerOrReadOnly

from .models import ArtisanLocation, CulturalRegion, HeritageRoute
from .serializers import (
    ArtisanLocationSerializer,
    CulturalRegionSerializer,
    HeritageRouteSerializer,
)

def register_view(request):
    if request.user.is_authenticated:
        return redirect("heritage-map")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(
                request,
                user
            )

            return redirect(
                "heritage-map"
            )
    else:
        form = UserCreationForm()

    return render(
        request,
        "registration/register.html",
        {
            "form": form
        }
    )

class ArtisanLocationViewSet(viewsets.ModelViewSet):
    queryset = ArtisanLocation.objects.select_related("region").all()
    serializer_class = ArtisanLocationSerializer

    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )

    @action(detail=False, methods=["get"])
    def within_radius(self, request):
        """
        Return artisan locations within a specified radius.

        Example:
        /api/heritage/artisans/within_radius/
        ?lat=53.3498
        &lng=-6.2603
        &radius=3
        """

        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
            radius = float(request.query_params.get("radius"))
        except (TypeError, ValueError):
            return Response(
                {
                    "error": "lat, lng and radius must be valid numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if radius <= 0:
            return Response(
                {
                    "error": "radius must be greater than 0."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_point = Point(lng, lat, srid=4326)

        artisans = (
            ArtisanLocation.objects
            .select_related("region")
            .filter(
                location__distance_lte=(
                    user_point,
                    D(km=radius),
                )
            )
        )

        serializer = self.get_serializer(
            artisans,
            many=True,
        )

        return Response(
            {
                "center": {
                    "lat": lat,
                    "lng": lng,
                },
                "radius_km": radius,
                "count": artisans.count(),
                "results": serializer.data,
            }
        )

    @action(detail=False, methods=["get"])
    def nearest(self, request):
        """
        Return the nearest artisan location to a given point.

        Example:
        /api/heritage/artisans/nearest/
        ?lat=53.3498
        &lng=-6.2603
        """

        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
        except (TypeError, ValueError):
            return Response(
                {
                    "error": "lat and lng must be valid numbers."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_point = Point(lng, lat, srid=4326)

        artisan = (
            ArtisanLocation.objects
            .select_related("region")
            .annotate(
                distance=Distance("location", user_point)
            )
            .order_by("distance")
            .first()
        )

        if artisan is None:
            return Response(
                {
                    "error": "No artisan locations found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(artisan)

        return Response(
            {
                "center": {
                    "lat": lat,
                    "lng": lng,
                },
                "distance_km": round(artisan.distance.km, 3),
                "artisan": serializer.data,
            }
        )


class CulturalRegionViewSet(viewsets.ModelViewSet):
    queryset = CulturalRegion.objects.all()
    serializer_class = CulturalRegionSerializer

    @action(detail=True, methods=["get"])
    def artisans(self, request, pk=None):
        """
        Return artisan locations contained inside a cultural region.

        Example:
        /api/heritage/regions/1/artisans/
        """

        region = self.get_object()

        artisans = (
            ArtisanLocation.objects
            .select_related("region")
            .filter(location__within=region.boundary)
        )

        serializer = ArtisanLocationSerializer(
            artisans,
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "region": {
                    "id": region.id,
                    "name": region.name,
                    "region_type": region.region_type,
                },
                "count": artisans.count(),
                "artisans": serializer.data,
            }
        )

class HeritageRouteViewSet(viewsets.ModelViewSet):
    queryset = HeritageRoute.objects.all()
    serializer_class = HeritageRouteSerializer

    @action(detail=False, methods=["get"])
    def intersecting_region(self, request):
        """
        Return heritage routes that intersect a cultural region.

        Example:
        /api/heritage/routes/intersecting_region/?region_id=1
        """

        region_id = request.query_params.get("region_id")

        if not region_id:
            return Response(
                {
                    "error": "region_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            region = CulturalRegion.objects.get(id=region_id)
        except CulturalRegion.DoesNotExist:
            return Response(
                {
                    "error": "Cultural region not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        routes = HeritageRoute.objects.filter(
            path__intersects=region.boundary
        )

        serializer = self.get_serializer(
            routes,
            many=True,
        )

        return Response(
            {
                "region": {
                    "id": region.id,
                    "name": region.name,
                    "region_type": region.region_type,
                },
                "count": routes.count(),
                "routes": serializer.data,
            }
        )