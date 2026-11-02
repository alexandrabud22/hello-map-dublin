"""
Show the PostgreSQL query plans for the spatial queries.

    docker compose exec web python manage.py explain_spatial_queries

Why "enable_seqscan = off"?
With only ~15 rows PostgreSQL correctly decides that reading the whole
table is faster than using an index, so a normal EXPLAIN shows
"Seq Scan". Turning sequential scans off for this session only forces
the planner to show HOW it would use the spatial indexes once the
tables are large. It changes nothing permanently.
"""

from django.core.management.base import BaseCommand
from django.db import connection

from heritage.models import HeritageRoute


QUERIES = [
    (
        "1. Radius search - GiST index on location (ST_DWithin pre-filter)",
        """
        SELECT id FROM heritage_artisanlocation
        WHERE ST_DWithin(location, ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326), 0.045)
          AND ST_DistanceSphere(location, ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)) <= 3000
        """,
    ),
    (
        "2. Nearest artisan - KNN '<->' ordered by the GiST index",
        """
        SELECT id FROM heritage_artisanlocation
        ORDER BY location <-> ST_SetSRID(ST_MakePoint(-6.2603, 53.3498), 4326)
        LIMIT 5
        """,
    ),
    (
        "3. Containment - artisans inside a region (ST_Within)",
        """
        SELECT a.id FROM heritage_artisanlocation a
        JOIN heritage_culturalregion r ON ST_Within(a.location, r.boundary)
        WHERE r.id = (SELECT min(id) FROM heritage_culturalregion)
        """,
    ),
    (
        "4. Intersection - routes crossing a region (ST_Intersects)",
        """
        SELECT t.id FROM heritage_heritageroute t
        JOIN heritage_culturalregion r ON ST_Intersects(t.path, r.boundary)
        WHERE r.id = (SELECT min(id) FROM heritage_culturalregion)
        """,
    ),
    (
        "5. Buffer - artisans within 200 m of a route (geography index)",
        """
        SELECT a.id FROM heritage_artisanlocation a
        JOIN heritage_heritageroute r ON r.id = %(route_id)s
        WHERE ST_DWithin(a.location::geography, r.path::geography, 200)
        """,
    ),
]


class Command(BaseCommand):
    help = "Print EXPLAIN plans showing spatial index usage."

    def handle(self, *args, **options):
        route = HeritageRoute.objects.order_by("id").first()
        params = {"route_id": route.id if route else 0}

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE tablename LIKE 'heritage_%%' AND indexdef ILIKE '%%gist%%' "
                "ORDER BY indexname"
            )
            self.stdout.write(self.style.MIGRATE_HEADING("Spatial (GiST) indexes"))
            for (name,) in cursor.fetchall():
                self.stdout.write(f"  - {name}")

            cursor.execute("SET enable_seqscan = off")  # this connection only

            for title, sql in QUERIES:
                self.stdout.write("")
                self.stdout.write(self.style.MIGRATE_HEADING(title))
                cursor.execute("EXPLAIN " + sql, params)
                for (line,) in cursor.fetchall():
                    marker = "  <-- index" if "Index" in line else ""
                    self.stdout.write(f"  {line}{marker}")

            cursor.execute("RESET enable_seqscan")
