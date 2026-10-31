"""
HeritageConnect URL configuration.

    /                      -> redirects to the map
    /heritage/             -> HeritageConnect map (Leaflet front end)
    /api/heritage/         -> REST API (see heritage/urls.py)
    /api/docs/             -> Swagger UI (OpenAPI documentation)
    /accounts/...          -> login / logout / register
    /admin/                -> Django admin (staff only)
"""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from heritage.views import register_view


urlpatterns = [
    # Home page -> map
    path(
        "",
        RedirectView.as_view(pattern_name="heritage-map", permanent=False),
        name="home",
    ),

    # Front end (View layer: Django template + Leaflet)
    path(
        "heritage/",
        TemplateView.as_view(template_name="heritage_map.html"),
        name="heritage-map",
    ),

    # REST API
    path("api/heritage/", include("heritage.urls")),

    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),

    # Authentication
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", register_view, name="register"),

    # Django admin
    path("admin/", admin.site.urls),
]
