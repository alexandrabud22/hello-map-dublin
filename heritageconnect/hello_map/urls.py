from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

from heritage.views import register_view


urlpatterns = [
    # HeritageConnect
    path(
        "api/heritage/",
        include("heritage.urls"),
    ),

    path(
        "heritage/",
        TemplateView.as_view(
            template_name="heritage_map.html"
        ),
        name="heritage-map",
    ),

    # Authentication
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

    # Django admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # Week 2 spatial analysis
    path(
        "spatial/",
        include("spatial_analysis.urls"),
    ),

    # Week 3 Cities API
    path(
        "api/cities/",
        include("cities_api.urls"),
    ),

    # API documentation
    path(
        "api/schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),

    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(
            url_name="schema"
        ),
        name="swagger-ui",
    ),

    # Week 4 map
    path(
        "map/",
        TemplateView.as_view(
            template_name="map.html"
        ),
        name="map",
    ),

    # Week 4 home page
    path(
        "",
        TemplateView.as_view(
            template_name="map.html"
        ),
        name="map_home",
    ),

    # Week 1 map routes
    path(
        "",
        include("mapping.urls"),
    ),
]