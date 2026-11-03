# HeritageConnect

My project is HeritageConnect, a location-based application for finding traditional craft
makers and heritage trails in Dublin. It is for CMPU4058 Advanced Web Mapping, Assignment 1.
Visitors can find nearby workshops, explore cultural areas and find makers along a walking
route. Registered users can add, edit and delete their own workshop.

The sample makers are made-up examples and the area boundaries are approximate.

## What the app does

- Leaflet map with OpenStreetMap tiles, clustered markers, cultural regions and heritage routes.
- Search by name or place, and filter by craft type or cultural region.
- Search within a radius or find the nearest maker to a selected location.
- Find makers within 200 m or 500 m of a route. The shaded area shows the search distance.
- Users can register, log in and manage their own workshop. Staff manage regions and routes.
- The layout changes for smaller screens. Forms have labels and the Add/Edit window supports keyboard use.

## Screenshots

![Main map](docs/screenshots/A23-main-map.png)

![Artisans near a heritage route](docs/screenshots/A21-route-buffer-query.png)

More examples, including the mobile layout and Add Artisan form, are in
[docs/screenshots](docs/screenshots/).

## How it works

The map uses Leaflet and OpenStreetMap, with Bootstrap 5 and JavaScript for the interface.
Django and GeoDjango handle the application, and Django REST Framework provides the API.
PostgreSQL with PostGIS stores the data.

Gunicorn runs Django. Nginx receives browser requests and serves files such as CSS and
JavaScript. PgAdmin is used to view and manage the database.

The four Docker containers are Nginx, Django, PostGIS and PgAdmin. They communicate through
the `heritage_net` network (`172.28.0.0/24`). A named volume keeps the database data when
the containers are stopped and started again.

![Architecture diagram](docs/architecture-diagram.png)

The models are in `heritage/models.py`, the API views and validation are in
`heritage/views.py` and `heritage/serializers.py`, and the map interface is in
`templates/heritage_map.html` and `static/`.

## Database and spatial queries

Workshops are stored as points, cultural areas as polygons and heritage routes as lines.
They use SRID 4326, which stores longitude and latitude coordinates. The API sends the
locations to Leaflet as GeoJSON.

For route lengths, the line is converted to EPSG:2157 to measure it in metres, then the
length is divided by 1,000 to get kilometres.

| Query | Purpose | Main operation |
|---|---|---|
| Radius search | Find makers within a distance of a point | `ST_DWithin` pre-filter and spherical distance |
| Nearest maker | Find the closest workshop | KNN candidate search and spherical distance |
| Containment | Find makers inside a cultural region | `ST_Within` |
| Intersection | Find routes crossing a region | `ST_Intersects` |
| Route buffer | Find makers close to a trail | `ST_Buffer` and `ST_DWithin` on geography |

The spatial fields have GiST indexes to help with location searches. Migration `0003`
also adds indexes for the route searches that measure distance in metres. With this small
dataset, PostgreSQL may read all the rows because that can be quicker than using an index.

The [database schema documentation](docs/database-schema.md) includes the fields,
relationships and schema diagram. The `explain_spatial_queries` management command
shows which indexes the queries can use. It temporarily discourages full-table scans,
so the output is an index check, not a measurement of how fast the app is.

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

   Wait for `web` and `db` to show as healthy. On startup, Django sets up the database tables
   from the migrations and gathers the CSS, JavaScript and other static files.

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
`docker compose down` and start again with `docker compose up -d`. The saved data stays
in the database volume. Adding `-v` to the stop command deletes the volumes and their data.

Rebuild the image after changing the code. For development, the following command uses
the files from the project folder directly. Set `DJANGO_DEBUG=True` to enable reload:

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

Open the [Swagger documentation](http://localhost:8000/api/docs/) to see and try the API
endpoints. Locations are returned as GeoJSON. Lists return 20 records per page.

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

Anyone can view the data. Users must log in to add a workshop, and only the owner or
staff can edit or delete it. Only staff can change regions and routes. Requests that
change data use the login session and a CSRF token.

## Testing

Run the automated tests with:

```bash
docker compose exec web python manage.py test heritage -v 2
```

The tests in `heritage/tests.py` check that location searches work, users can only change
workshops they have permission to change, and incorrect information is rejected. They
also check invalid shapes, route-length calculations and whether pages load. Django uses
a separate temporary database for the tests, so they do not change the saved workshops.

The project testing notes cover Chrome and Safari on macOS and a phone-sized view in
Chrome DevTools. They include adding, editing and deleting workshops, combining filters,
searching near routes and using the Add/Edit window with a keyboard.

Screenshots are in `docs/screenshots/`, including
[Lighthouse](docs/screenshots/A30-lighthouse-accessibility.png),
[data after restart](docs/screenshots/A28-data-persists-after-restart.png) and
[query plans](docs/screenshots/A29-spatial-index-query-plans.png).
The saved Lighthouse result shows an accessibility score of 100 on desktop. That does
not mean every accessibility issue has been checked.

## Security and deployment

Passwords and the Django secret key are set in `.env`. Debug mode is off in the default
setup. Django runs as a non-root user, and only Nginx and PgAdmin have ports open on the
computer.

The API checks permissions before allowing changes. SQL values are passed separately
from the query text, and workshop text is escaped before it is displayed as HTML.

This version runs locally in Docker. It has not been tested on a cloud server. To deploy on a Linux VM, install Docker, copy the project, configure `.env`
and run the same build commands. Set the domain in `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS`, configure HTTPS in Nginx, and restrict access to PgAdmin.
Enable `DJANGO_SECURE_COOKIES=True` only after HTTPS is configured.

## Known limitations

- The makers are made-up examples. Cultural boundaries are approximate and each area is one polygon.
- Routes are stored in advance, rather than calculated live. They use OpenStreetMap
  street data and OSRM walking routes.
- Tiles and address lookup need internet access. Address lookup uses public Nominatim;
  choosing a point on the map is an alternative.
- The local deployment uses HTTP, without a TLS certificate.
- The dataset is small, so it has not shown how well the app works with a large number
  of workshops.
- The configured PostGIS image uses amd64 emulation on Apple Silicon.

## Credits

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
