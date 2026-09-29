from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Week 2 spatial analysis
    path('spatial/', include('spatial_analysis.urls')),

    # Week 3 Cities API
    path('api/cities/', include('cities_api.urls')),

    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    # Week 1 map
    path('', include('mapping.urls')),
]