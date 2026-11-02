"""
Add GiST indexes on the geography casts of the point and line columns.

The buffer query (routes/{id}/artisans_nearby) measures in metres with
ST_DWithin(location::geography, path::geography, metres). A normal GiST
index on the geometry column cannot be used for an expression on
::geography, so these "expression indexes" make that query
index-assisted as the data grows.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("heritage", "0002_artisanlocation_owner"),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS heritage_artisan_location_geog_gist "
                "ON heritage_artisanlocation USING GIST ((location::geography));"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS heritage_artisan_location_geog_gist;"
            ),
        ),
        migrations.RunSQL(
            sql=(
                "CREATE INDEX IF NOT EXISTS heritage_route_path_geog_gist "
                "ON heritage_heritageroute USING GIST ((path::geography));"
            ),
            reverse_sql=(
                "DROP INDEX IF EXISTS heritage_route_path_geog_gist;"
            ),
        ),
    ]
