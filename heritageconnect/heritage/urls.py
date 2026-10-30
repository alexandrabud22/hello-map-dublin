from django.urls import include, path
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from heritage.views import register_view

from .views import (
    ArtisanLocationViewSet,
    CulturalRegionViewSet,
    HeritageRouteViewSet,
)


router = DefaultRouter()
router.register(
    "artisans",
    ArtisanLocationViewSet,
    basename="artisan",
)

router.register(
    "regions",
    CulturalRegionViewSet,
    basename="region",
)

router.register(
    "routes",
    HeritageRouteViewSet,
    basename="heritage-route",
)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),

    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    path(
        "accounts/register/",
        register_view,
        name="register",
    ),
]