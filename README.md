# Lab 1 Submission Evidence

## 1. Docker Compose services running with PostGIS health check passing

![docker compose ps output](screenshots/docker_compose_ps_healthy.png)

The `db`, `pgadmin`, and `web` containers all running, with `db` showing a healthy status from its PostGIS health check.

## 2. The Hello Map in the browser

![Hello Map with markers and popup](screenshots/map_with_markers_and_popup.png)

The Leaflet map centred on Dublin, showing markers for Trinity College Dublin, Dublin Castle, and Temple Bar, with the Dublin Castle popup open.

## 3. pgAdmin connected to the Hello Map PostGIS server

![pgAdmin connected to PostGIS server](screenshots/pgadmin_connected_server.png)

The `Hello Map PostGIS` server registered and connected in pgAdmin, showing the live database dashboard.

## 4. Result of SELECT PostGIS_Version();

![PostGIS version query result](screenshots/postgis_version_query.png)

The PostGIS version query run in pgAdmin's Query Tool, confirming PostGIS 3.4 is installed and working.

## 5. Django admin site logged in as administrator

![Django admin logged in](screenshots/django_admin_logged_in.png)

The Django administration dashboard, logged in with the superuser account created during setup.
