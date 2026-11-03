# HeritageConnect

HeritageConnect is a map of traditional craft makers and heritage trails in Dublin,
built for CMPU4058 Advanced Web Mapping, Assignment 1. It lets visitors find workshops
near a location, explore cultural areas and see which makers are close to a walking route.
Registered users can add a workshop and edit or delete their own entries.

The sample workshops are fictional and the cultural boundaries are approximate.

## Features

- Leaflet map with OpenStreetMap tiles, clustered markers, cultural regions and heritage routes.
- Search by name or place, and filter by craft type or cultural region.
- Search within a radius or find the nearest maker to a selected location.
- Find makers within 200 m or 500 m of a route and display the search corridor on the map.
- Registration, login and workshop management. Regions and routes are managed by staff.
- Responsive layout, labelled forms and keyboard support for the Add/Edit dialog.

## Screenshots

![Main map](docs/screenshots/A23-main-map.png)

![Artisans near a heritage route](docs/screenshots/A21-route-buffer-query.png)

More examples, including the mobile layout and Add Artisan form, are in
[docs/screenshots](docs/screenshots/).

## Technologies and structure

The application uses Django and GeoDjango with Django REST Framework, PostgreSQL/PostGIS,
Leaflet, Bootstrap 5 and JavaScript. Gunicorn runs Django, and Nginx handles incoming
requests and static files. PgAdmin is included for database management.

There are four Docker services on the `heritage_net` network (`172.28.0.0/24`):
Nginx, Django, PostGIS and PgAdmin. The database uses a named volume to retain its data.

![Architecture diagram](docs/architecture-diagram.png)

The models are in `heritage/models.py`, the API views and validation are in
`heritage/views.py` and `heritage/serializers.py`, and the map interface is in
`templates/heritage_map.html` and `static/`.

## Database and spatial queries

The three spatial models are artisan locations (Point), cultural regions (Polygon)
and heritage routes (LineString). They use SRID 4326 for GeoJSON and Leaflet.
Route lengths are calculated in EPSG:2157 so the measurements are in metres.

| Query | Purpose | Main operation |
|---|---|---|
| Radius search | Find makers within a distance of a point | `ST_DWithin` pre-filter and spherical distance |
| Nearest maker | Find the closest workshop | KNN candidate search and spherical distance |
| Containment | Find makers inside a cultural region | `ST_Within` |
| Intersection | Find routes crossing a region | `ST_Intersects` |
| Route buffer | Find makers close to a trail | `ST_Buffer` and `ST_DWithin` on geography |

Geometry fields have GiST indexes. Migration `0003` also adds indexes on the geography
casts used for route searches. With the small sample dataset, PostgreSQL may choose
sequential scans instead.

The [database schema documentation](docs/database-schema.md) includes the fields,
relationships and schema diagram. The `explain_spatial_queries` management command
shows example plans with sequential scans disabled for that session; it demonstrates
index availability rather than a performance benchmark.

## Running locally

Install Docker Desktop and Git, then download or clone this repository. Open a terminal
in the `heritageconnect` folder containing `compose.yaml`. Ports 8000 and 5050 must be free.

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

   Set `POSTGRES_PASSWORD`, `PGADMIN_DEFAULT_PASSWORD` and `DJANGO_SECRET_KEY` in `.env`.
   A secret key can be generated with:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   Keep `DJANGO_DEBUG=False` for the assessment setup. Do not commit or include the real
   `.env` in a submission ZIP.

2. Build and start the containers:

   ```bash
   docker compose up -d --build
   docker compose ps
   ```

   Wait for `web` and `db` to show as healthy. Django applies migrations and collects
   static files on startup.

3. Load the sample data and demo account:

   ```bash
   docker compose exec web python manage.py load_heritage_data
   docker compose exec web python manage.py create_demo_user
   ```

   To manage regions and routes through Django admin, create an administrator:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. Open [the application](http://localhost:8000/).

| Service | Local address |
|---|---|
| Map | http://localhost:8000/ |
| API | http://localhost:8000/api/heritage/ |
| Swagger API documentation | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |
| PgAdmin | http://localhost:5050/ |

In PgAdmin, register the database with host `db`, port `5432`, and the database name,
username and password from `.env`.

The demo login is `demo` / `HeritageDemo2026!`, unless `DEMO_USER_PASSWORD` was changed.
It owns Meath Street Basketry, which can be used to try editing. This account is for local
assessment only.

Use `docker compose logs -f web` to inspect application logs. Stop with
`docker compose down` and start again with `docker compose up -d`. The database volume
is retained; adding `-v` to the stop command deletes the volumes and their data.

Code is built into the image, so rebuild after changes. For development with source
mounts and reload, set `DJANGO_DEBUG=True` and use:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up -d
```

## Using the map

Click a marker or an artisan card to view workshop details. Use the search box and craft
filter to narrow the list, or select a cultural region to show makers inside its boundary.

For a nearby search, click the map to choose a location, select a radius and press
**Search Nearby**. **Find Nearest** uses the selected point too. The app can also use
browser location if permission is granted.

In **Heritage routes**, choose **Show on map** or **Artisans within 200 m**. Route popups
also offer a 500 m search. Use the layer checkboxes to hide or show map layers and
**Reset map** to return to the initial view.

To add a workshop, register or log in and select **Add Artisan**. Enter an address or
choose a point on the small map, complete the required fields and save. Your own entries
have Edit and Delete controls. Staff can also manage entries through Django admin.

## API

The [Swagger documentation](http://localhost:8000/api/docs/) lists the endpoints and
parameters. Spatial records are returned as GeoJSON. List endpoints use pagination
with 20 records per page.

| Endpoint under `/api/heritage/` | Purpose |
|---|---|
| `artisans/` and `artisans/{id}/` | List, create, read, update and delete workshops |
| `artisans/within_radius/?lat=53.3498&lng=-6.2603&radius=3` | Radius search in kilometres |
| `artisans/nearest/?lat=53.3498&lng=-6.2603` | Nearest workshop |
| `regions/` and `regions/{id}/` | Cultural region records |
| `regions/{id}/artisans/` | Makers inside a region |
| `routes/` and `routes/{id}/` | Heritage route records |
| `routes/intersecting_region/?region_id=1` | Routes intersecting a region |
| `routes/{id}/artisans_nearby/?distance=200` | Makers near a route, distance in metres |

Anyone can read. Logged-in users can create workshops; only their owner or staff can
update or delete them. Region and route writes require staff access. API writes use
session authentication and a CSRF token.

## Testing

Run the automated tests with:

```bash
docker compose exec web python manage.py test heritage -v 2
```

The test suite in `heritage/tests.py` covers spatial queries, permissions, validation,
malformed geometry, model calculations and page responses. Django runs these against
a separate temporary PostGIS database.

The existing manual testing record covers Chrome and Safari on macOS, an iPhone-sized
Chrome DevTools viewport, workshop CRUD, combined filters, route buffers and dialog
keyboard behaviour. Evidence screenshots are in `docs/screenshots/`, including
[Lighthouse](docs/screenshots/A30-lighthouse-accessibility.png),
[data after restart](docs/screenshots/A28-data-persists-after-restart.png) and
[query plans](docs/screenshots/A29-spatial-index-query-plans.png).
The recorded desktop Lighthouse accessibility score is 100; this does not replace a
full manual accessibility review.

## Security and deployment notes

Secrets are read from environment variables. The default setup disables Django debug
mode, runs Django as a non-root user and exposes only Nginx and PgAdmin on the host.
Write permissions are checked by the API. SQL values are parameterised, and user text
is escaped before being inserted into HTML.

The application is deployed locally for this assignment. It has not been tested on a
cloud host. To deploy on a Linux VM, install Docker, copy the project, configure `.env`
and run the same build commands. Set the domain in `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS`, configure HTTPS in Nginx, and restrict access to PgAdmin.
Enable `DJANGO_SECURE_COOKIES=True` only after HTTPS is configured.

## Limitations

- Sample makers are fictional and cultural boundaries are approximate single polygons.
- Routes are stored in advance, rather than calculated live. They use OpenStreetMap
  street data and OSRM walking routes.
- Tiles and address lookup need internet access. Address lookup uses public Nominatim;
  choosing a point on the map is an alternative.
- The local deployment uses HTTP, without a TLS certificate.
- The small dataset is useful for demonstrating features, but does not establish
  performance with a large number of workshops.
- The configured PostGIS image uses amd64 emulation on Apple Silicon.

## Sources and acknowledgements

Project setup follows the CMPU4058 lab exercises from Weeks 1–4.

Map data is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
with address lookup from Nominatim. Route geometry was calculated using
[OSRM](https://project-osrm.org/) on the FOSSGIS server (`routing.openstreetmap.de`)
and is stored in `heritage/data/heritage_routes.geojson`.

Libraries include [Django](https://www.djangoproject.com/),
[Django REST Framework](https://www.django-rest-framework.org/),
[GeoDjango/PostGIS](https://postgis.net/),
[Leaflet](https://leafletjs.com/),
[Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster),
[Bootstrap](https://getbootstrap.com/),
[djangorestframework-gis](https://github.com/openwisp/django-rest-framework-gis) and
[drf-spectacular](https://drf-spectacular.readthedocs.io/).
The containers use the Python, PostGIS, PgAdmin and Nginx images.
