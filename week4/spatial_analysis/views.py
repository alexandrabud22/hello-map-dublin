from django.shortcuts import render, get_object_or_404
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D

from .models import (
    DublinAdminArea,
    DublinRoad,
    DublinPOI,
    LandUseZone,
)

def spatial_analysis_dashboard(request):
    """Dashboard showing spatial analysis of Dublin data"""

    context = {
        'total_admin_areas': DublinAdminArea.objects.count(),
        'total_roads': DublinRoad.objects.count(),
        'total_pois': DublinPOI.objects.count(),
        'total_zones': LandUseZone.objects.count(),

        'admin_areas': DublinAdminArea.objects.all(),
        'major_roads': DublinRoad.objects.filter(
            road_type__in=['motorway', 'main_street']
        ).order_by('-speed_limit'),
        'attractions': DublinPOI.objects.filter(
            poi_type__in=['attraction', 'historic']
        ).order_by('-rating'),
        'zones': LandUseZone.objects.all(),
    }

    return render(request, 'spatial_analysis/dashboard.html', context)

def poi_detail(request, pk):
    poi = get_object_or_404(DublinPOI, pk=pk)

    nearby_roads = (
        DublinRoad.objects
        .filter(geom__distance_lte=(poi.geom, D(m=500)))
        .annotate(distance=Distance('geom', poi.geom))
        .order_by('distance')[:5]
    )

    context = {
        'poi': poi,
        'nearby_roads': nearby_roads,
    }

    return render(
        request,
        'spatial_analysis/poi_detail.html',
        context
    )

    return render(request, 'spatial_analysis/poi_detail.html', context)