from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ArtisanLocationViewSet,
    CulturalRegionViewSet,
    HeritageRouteViewSet,
)


# The router builds the standard REST endpoints for each ViewSet:
#   GET/POST          /api/heritage/<resource>/
#   GET/PUT/PATCH/DELETE /api/heritage/<resource>/<id>/
# plus the custom spatial @action endpoints defined in views.py.
router = DefaultRouter()
router.register("artisans", ArtisanLocationViewSet, basename="artisan")
router.register("regions", CulturalRegionViewSet, basename="region")
router.register("routes", HeritageRouteViewSet, basename="heritage-route")


# Authentication URLs (login / logout / register) live in
# hello_map/urls.py so that each URL name is defined only once.
urlpatterns = [
    path("", include(router.urls)),
]
