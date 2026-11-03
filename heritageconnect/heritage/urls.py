from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArtisanLocationViewSet,
    CulturalRegionViewSet,
    HeritageRouteViewSet,
)

# The router creates the usual CRUD URLs for each resource.
router = DefaultRouter()
router.register("artisans", ArtisanLocationViewSet, basename="artisan")
router.register("regions", CulturalRegionViewSet, basename="region")
router.register("routes", HeritageRouteViewSet, basename="heritage-route")

urlpatterns = [
    path("", include(router.urls)),
]
