# Week 4 – Django-Leaflet Integration: Interactive Web Maps

## Overview

Week 4 extends the Week 3 Cities API by adding an interactive Leaflet.js frontend.

The Week 3 Django, PostGIS and REST API environment was reused and extended with:

- Leaflet.js
- Django templates
- static JavaScript and CSS files
- AJAX requests using the Fetch API
- interactive city markers
- marker popups
- city search
- map reset functionality
- responsive design
- frontend functional tests

The final result is a full-stack web mapping application where the Django REST API provides city data and Leaflet displays that data interactively in the browser.

---

## 1. Week 4 Project Setup

The completed Week 3 project was copied into a new `week4` directory.

This preserved the existing:

- Django project
- PostGIS database configuration
- Docker Compose environment
- Week 1 mapping application
- Week 2 spatial analysis application
- Week 3 Cities REST API

The Week 4 project was then used as the development environment for the Leaflet frontend.

![Week 4 project setup](01-week4-project-setup.png)

---

## 2. Docker Environment

The Week 4 Docker environment was started using Docker Compose.

```bash
docker compose up -d
docker compose ps
```

The environment contains:

- Django web service
- PostgreSQL/PostGIS database
- pgAdmin

The database health check confirmed that PostGIS was running successfully.

![Docker services](02-docker-services-w4.png)

---

## 3. Frontend Project Structure

New frontend directories were created for the Week 4 mapping interface:

```text
static/
├── css/
│   └── styles.css
├── images/
└── js/
    └── map.js

templates/
└── map.html
```

The `templates` directory stores the Django map template.

The `static` directory stores the JavaScript, CSS and image assets used by the Leaflet frontend.

![Frontend structure](03-frontend-structure.png)

---

## 4. Django Static File Configuration

The Django settings were updated to support project-level templates and static files.

The following static configuration was added:

```python
STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
```

The template configuration was updated so Django could locate:

```text
templates/map.html
```

using:

```python
"DIRS": [
    BASE_DIR / "templates",
],
```

CORS support was also retained so the frontend and REST API could communicate correctly during development.

![Static settings](04-static-settings.png)

---

## 5. Map URL Configuration

The main Django URL configuration was extended with a new route for the Leaflet map.

The Week 3 API routes and previous lab routes were preserved.

The Week 4 route was added using Django's `TemplateView`:

```python
path(
    'map/',
    TemplateView.as_view(template_name='map.html'),
    name='map'
),
```

The interactive map therefore became available at:

```text
http://localhost:8000/map/
```

![Map URL route](05-map-url-route.png)

---

## 6. Django Configuration Check

The Django project configuration was checked using:

```bash
docker compose run --rm web python manage.py check
```

The result was:

```text
System check identified no issues (0 silenced).
```

This confirmed that the Week 4 settings and URL configuration were valid.

![Django check](06-django-check.png)

---

## 7. Leaflet Map Template

A new Django template was created at:

```text
templates/map.html
```

The template contains:

- a Leaflet map container
- a city search input
- a Reset View button
- a search results area
- a city information box
- a loading message
- Leaflet CSS and JavaScript
- custom Week 4 CSS and JavaScript

Leaflet is loaded through a CDN, while the Week 4 application logic is loaded from Django static files.

![Map template](07-map-template.png)

---

## 8. Custom Map Styling

A custom stylesheet was created at:

```text
static/css/styles.css
```

The stylesheet provides styling for:

- the full-screen map
- the search panel
- search input
- Reset View button
- search results
- city popups
- map information box
- loading indicator
- responsive mobile layout

A media query was added so the interface remains usable on smaller screens.

![Map styles](08-map-styles.png)

---

## 9. Leaflet JavaScript Logic

The main map functionality was implemented in:

```text
static/js/map.js
```

The JavaScript is responsible for:

- initializing the Leaflet map
- loading a basemap
- fetching city data from the REST API
- creating city markers
- creating city popups
- filtering cities
- navigating to selected cities
- resetting the map
- updating the city count
- displaying loading state information

The existing Week 3 API endpoint was used:

```javascript
const API_URL = "/api/cities/";
```

![Map JavaScript](09-map-javascript.png)

---

## 10. Cities API Verification

Before connecting the frontend to the map, the Week 3 Cities API was tested directly.

The endpoint:

```text
http://localhost:8000/api/cities/
```

returned:

```text
HTTP 200 OK
```

and:

```text
count: 20
```

The response contained city records such as:

- Paris
- London
- Madrid
- Barcelona
- Dublin
- Berlin
- Rome
- Vienna

This confirmed that the backend API was available for the Leaflet frontend.

![API data](10-api-data.png)

---

## 11. Static File Verification

Django static-file serving was tested directly in the browser.

The JavaScript file was accessible at:

```text
http://localhost:8000/static/js/map.js
```

The stylesheet was accessible at:

```text
http://localhost:8000/static/css/styles.css
```

Both files loaded successfully without a 404 error.

![Static files](11-static-files.png)

---

## 12. Interactive Leaflet Map

The completed map was accessed at:

```text
http://localhost:8000/map/
```

The application successfully displayed:

- a geographic basemap
- 20 city markers
- city search controls
- Reset View functionality
- city count information

The map automatically fitted the view to the available city data.

![Interactive map](12-interactive-map.png)

---

## 13. City Marker Popups

Each city is displayed as an interactive Leaflet circle marker.

Clicking a marker opens a popup containing city information.

Popup information includes:

- city name
- country
- region
- population
- coordinates
- capital status

This allows users to explore the API data directly from the map.

![City popup](13-city-popup.png)

---

## 14. City Search Functionality

The city search field filters cities using either:

- city name
- country name

For example, searching for:

```text
Dublin
```

filters the map to Dublin and displays the matching search result.

Selecting the result moves the map to the city location.

![City search](14-city-search.png)

---

## 15. Frontend-Backend Communication

Chrome Developer Tools were used to verify communication between the Leaflet frontend and the Django REST API.

The browser console showed:

```text
Week 4 map.js loaded
DOM loaded. Starting map...
Fetching city data from: /api/cities/
API response status: 200
API data received: Object
```

This confirmed that:

- JavaScript loaded successfully
- the DOM initialized correctly
- the REST API request was successful
- city data was received by the frontend

The only browser warning was a missing favicon, which does not affect application functionality.

![Browser console](15-browser-console.png)

---

## 16. Automated Frontend Tests

Functional tests were created in:

```text
tests/test_frontend.py
```

The tests verify that:

- the map page loads successfully
- the `Cities Web Map` content is present
- Leaflet is included
- the search input exists
- the Reset View button exists
- the JavaScript static file is referenced
- the CSS static file is referenced

The test suite was run using:

```bash
docker compose run --rm web python manage.py test
```

The result was:

```text
Ran 3 tests in 0.006s

OK
```

![Frontend tests](16-frontend-tests.png)

---

## 17. Responsive Design Testing

Chrome Developer Tools device emulation was used to test the application on a mobile-sized viewport.

The application remained usable on an iPhone-sized display.

The responsive version retained:

- the interactive map
- city markers
- the search panel
- Reset View
- city information

This confirmed that the responsive CSS rules were working correctly.

![Responsive map](17-responsive-map.png)

---

## 18. Network and Performance Testing

Chrome Developer Tools Network tab was used to inspect the API request.

The city API request returned:

```text
Status: 200
Type: fetch
Size: approximately 3.6 kB
Time: approximately 72 ms
```

The overall page load completed in under one second in the local Docker development environment.

This confirmed that frontend-backend communication was functioning efficiently for the sample dataset.

![Network performance](18-network-performance.png)

---

## 19. Database Migration Synchronisation

During validation, Django reported that the current `City` model contained a field change not yet represented in a migration.

A new migration was created:

```text
cities_api/migrations/0002_alter_city_founded_year.py
```

The migration was then applied successfully.

Verification showed:

```text
cities_api
 [X] 0001_initial
 [X] 0002_alter_city_founded_year
```

A final migration check reported:

```text
No changes detected
```

This confirmed that the Django models and database migration state were synchronized.

---

## 20. Final Validation

Final validation confirmed that:

- the PostGIS database was healthy
- pgAdmin was running
- Django was running
- the Cities API was working
- 20 city records were available
- the interactive Leaflet map was working
- static JavaScript and CSS files loaded correctly
- city markers were displayed
- city search worked
- Reset View worked
- responsive design worked
- the API returned HTTP 200
- all frontend tests passed
- Django reported no system-check issues
- no pending model migrations remained

The final test output included:

```text
Ran 3 tests in 0.006s

OK
```

and:

```text
System check identified no issues (0 silenced).
```

![Final validation](19-final-validation.png)

---

## Challenges Encountered and Solutions

### Missing Week 4 Environment File

When Week 4 was first started, Docker Compose reported that several environment variables were missing.

The Week 4 directory contained `.env.example`, but not the actual `.env` file.

The original Week 3 `.env` file was located in the previous Lab 3 project and copied into the Week 4 project.

This restored the database, Django and pgAdmin configuration.

The `.env` file remains excluded from Git.

---

### Missing Cities Database Table

The Cities API initially returned:

```text
ProgrammingError
relation "cities_api_city" does not exist
```

The Week 4 Docker environment was using a fresh database volume.

The database migrations and city loading command were therefore run.

The city loader successfully created:

```text
Created: 20 cities
Updated: 0 cities
Total: 20 cities in database
```

After this, the `/api/cities/` endpoint returned HTTP 200 successfully.

---

### OpenStreetMap Tile Access Error

The original OpenStreetMap tile URL returned:

```text
403 Access blocked
```

Although the city markers and API data were working, the background map tiles were unavailable.

The basemap was replaced with another Leaflet-compatible tile provider.

---

### Basemap API Key Error

A second attempted basemap returned an API key warning.

The application was then configured to use the Esri World Street Map tile service:

```javascript
L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    {
        attribution: "Tiles &copy; Esri",
        maxZoom: 19
    }
).addTo(map);
```

This successfully displayed the geographic basemap.

---

### Pending City Model Migration

Django reported that the `cities_api` model contained a change to the `founded_year` field that was not represented by an existing migration.

The migration was created and applied:

```text
0002_alter_city_founded_year
```

A final dry-run migration check returned:

```text
No changes detected
```

---

## Technologies Used

- Python
- Django
- GeoDjango
- Django REST Framework
- PostgreSQL
- PostGIS
- Docker
- Docker Compose
- pgAdmin
- JavaScript
- Fetch API
- Leaflet.js
- HTML
- CSS
- Esri map tiles

---

## Key Features

The completed Week 4 application includes:

- interactive web mapping
- REST API integration
- AJAX / Fetch API communication
- dynamic city markers
- city information popups
- city search
- country search
- map navigation
- Reset View
- responsive layout
- browser console debugging
- network request validation
- automated frontend tests

---

## Future Enhancements

Possible future improvements include:

- marker clustering
- GeoJSON layer support
- city heatmaps
- multiple basemap options
- population-based marker sizes
- country filters
- capital-city filters
- map legends
- custom marker icons
- city detail pages
- user-selected spatial queries
- API authentication
- production static-file hosting
- improved caching

---

## Conclusion

Week 4 successfully connected the Week 3 Django REST API to an interactive Leaflet.js frontend.

The completed application demonstrates a full-stack web mapping workflow where:

- Django provides the web application
- Django REST Framework provides city data
- PostGIS stores geographic information
- JavaScript fetches the API data
- Leaflet displays the geographic data interactively
- users can search, navigate and inspect city information
- Docker provides a reproducible development environment

The result is a complete containerized web mapping application that combines backend spatial data with an interactive browser-based map.