# HeritageConnect

My project is a location-based app for finding traditional craft makers and heritage
trails in Dublin, for CMPU4058 Advanced Web Mapping, Assignment 1. Visitors can find
nearby workshops, explore cultural areas and find makers along a walking route.
Registered users can add, edit and delete their own workshops.

## Features

- Interactive map with workshop markers, cultural areas and heritage routes.
- Text search, craft filters, nearby search and nearest workshop search.
- Workshops inside a cultural region or within 200 m / 500 m of a route.
- Login, registration and workshop CRUD, with owner and staff permissions.
- Responsive layout and keyboard support for the Add/Edit window.

![HeritageConnect map](docs/screenshots/A23-main-map.png)

More [screenshots](docs/screenshots/) include the mobile layout and route buffer search.

## Technology and architecture

Django, GeoDjango, Django REST Framework, PostgreSQL/PostGIS, Leaflet, OpenStreetMap,
Bootstrap 5 and JavaScript.

Four Docker containers run Nginx, Django/Gunicorn, PostGIS and PgAdmin on the
`heritage_net` network (`172.28.0.0/24`). Nginx receives browser requests, Django handles
the API and PostGIS stores the data. A named volume keeps the database between restarts.

![Architecture](docs/architecture-diagram.png)

Workshops are points, cultural regions are polygons and routes are lines. Coordinates
use SRID 4326; route lengths use EPSG:2157 for measurements in metres. The spatial fields
have GiST indexes, with extra geography indexes for route searches.

The five spatial queries are radius search, nearest workshop, containment, intersection
and route buffering. The [database schema](docs/database-schema.md) has the field details
and relationships.

## Local setup

Docker Desktop must be installed and running. Extract the submitted ZIP or clone the
repository, then open a terminal in the `heritageconnect` folder containing `compose.yaml`.
The application uses ports 8000 and 5050.

### 1. Configure the environment

Create the local configuration file:

```bash
cp .env.example .env
```

In `.env`, replace the placeholder values for `POSTGRES_PASSWORD`,
`PGADMIN_DEFAULT_PASSWORD` and `DJANGO_SECRET_KEY`. Use a long random value for the
secret key. If Python 3 is available, this command generates one:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

The other values can remain as supplied for local assessment, including
`DJANGO_DEBUG=False` and `DJANGO_SECURE_COOKIES=False`.

### 2. Start the application

```bash
docker compose up -d --build
docker compose ps
```

The first build may take a few minutes. Wait until `web` and `db` show as healthy.
Database migrations and static file collection run automatically during startup.

### 3. Load the demonstration data

On a fresh setup, run:

```bash
docker compose exec web python manage.py load_heritage_data
docker compose exec web python manage.py create_demo_user
```

This loads the sample workshops, four cultural regions and three routes, and creates
the demo account. Open [HeritageConnect](http://localhost:8000/).

**Demo login:** `demo` / `HeritageDemo2026!`, unless `DEMO_USER_PASSWORD` was changed
in `.env`. This account owns Meath Street Basketry for testing edit and delete.

| Page | Address |
|---|---|
| Application | http://localhost:8000/ |
| API documentation | http://localhost:8000/api/docs/ |
| Django admin | http://localhost:8000/admin/ |
| PgAdmin | http://localhost:5050/ |

An administrator account can be created to assess region and route management:

```bash
docker compose exec web python manage.py createsuperuser
```

For PgAdmin, sign in with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` from
`.env`. Register a server using host `db`, port `5432`, and the `POSTGRES_DB`,
`POSTGRES_USER` and `POSTGRES_PASSWORD` values from the same file.

### Stopping and restarting

```bash
docker compose down
docker compose up -d
```

The database volume retains the saved data between runs, so the sample data does not
need to be loaded again. Startup errors can be checked with `docker compose logs web`.

## Using the app

Click a marker or workshop card for details. Use the search box and craft or region
filters to narrow the results. For **Search Nearby**, click a point on the map, choose
a radius and search. **Find Nearest** uses the same point.

Choose **Artisans within 200 m** under Heritage routes to see makers near a trail.
Route popups also offer 500 m. **Reset map** clears the search.

Log in and choose **Add Artisan** to add a workshop. Enter an address or select its
location on the small map. Your own entries have Edit and Delete buttons. Staff can
also manage workshops, regions and routes through Django admin.

## API and tests

The [Swagger page](http://localhost:8000/api/docs/) documents the CRUD and spatial endpoints
under `/api/heritage/`. The main resources are `artisans/`, `regions/` and `routes/`.
Spatial data is returned as GeoJSON, and lists have 20 records per page. Changes require
login and a CSRF token; workshop edits and deletes are limited to the owner or staff.

```bash
docker compose exec web python manage.py test heritage -v 2
```

The tests check location searches, permissions, incorrect inputs, invalid geometry and
route lengths using a separate temporary database. Screenshots include
[accessibility results](docs/screenshots/A30-lighthouse-accessibility.png),
[data after restart](docs/screenshots/A28-data-persists-after-restart.png) and
[spatial query plans](docs/screenshots/A29-spatial-index-query-plans.png).

## Limitations and deployment

The sample makers are fictional, cultural boundaries are approximate and routes are
stored rather than calculated live. Map tiles and address lookup need internet access.
The dataset is small, so large-scale performance has not been tested.

This version runs locally over HTTP. Cloud deployment has not been tested. A Linux VM
would use the same Docker setup, with the domain added to allowed hosts and CSRF origins,
HTTPS configured in Nginx and PgAdmin access restricted. Secure cookies should only be
enabled after HTTPS is working.

## Credits

Project setup is based on the CMPU4058 lab exercises (Weeks 1–4).
Map data is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright),
with address lookup from Nominatim. Stored route geometry uses [OSRM](https://project-osrm.org/)
walking routes from the FOSSGIS server (`routing.openstreetmap.de`).

Libraries: [Django](https://www.djangoproject.com/),
[Django REST Framework](https://www.django-rest-framework.org/),
[PostGIS](https://postgis.net/), [Leaflet](https://leafletjs.com/),
[Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster),
[Bootstrap](https://getbootstrap.com/),
[djangorestframework-gis](https://github.com/openwisp/django-rest-framework-gis) and
[drf-spectacular](https://drf-spectacular.readthedocs.io/).
Docker images: Python, PostGIS, PgAdmin and Nginx.
