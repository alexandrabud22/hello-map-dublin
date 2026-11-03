from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ("heritage", "0002_artisanlocation_owner"),
    ]

    # These indexes support the route searches that measure distance in metres.
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
