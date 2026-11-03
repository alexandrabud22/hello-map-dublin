# HeritageConnect – my notes (plain English)

## What it is
A map of Dublin for finding craft makers (potters, weavers, jewellers...) and heritage walks.
Visitors browse and search. Makers can log in and add their own workshop.

## How to start it
1. Open Docker Desktop.
2. In the terminal:
   ```
   cd "/Users/alexandra/Documents/Y4/Advanced Web Mapping/hello-map-dublin/heritageconnect"
   docker compose up -d
   ```
3. Open http://localhost:8000
4. Demo login: demo / HeritageDemo2026!

After changing code: `docker compose up -d --build`
To stop: `docker compose down` (never add `-v`, that deletes the database)

## The 4 containers (like 4 rooms in one building)
- **nginx** – the front door. Every visitor comes in here. Sends the CSS/JS files and adds safety settings.
- **web** – Django, the brain. Handles every request.
- **db** – PostgreSQL + PostGIS, the database. Stores the map data and answers location questions.
- **pgadmin** – a tool to look inside the database (http://localhost:5050).

They talk over my own private network (subnet 172.28.0.0/24).
The database has no outside door – only nginx (port 8000) and pgadmin (port 5050) are open.

## The 3 kinds of map data
- **Point** = an artisan (one spot)
- **Polygon** = a cultural region, like Temple Bar (an area with edges)
- **Line** = a heritage route (a walking path)

All use normal GPS coordinates (SRID 4326).
Each has a **spatial index** = like a book index, so searches are fast.

## The 5 location questions my app can answer
| Question | Button / page | Where in the code |
|---|---|---|
| Who is within X km of here? | Search Nearby | `views.py` → `def within_radius` |
| Who is the closest? | Find Nearest | `views.py` → `def nearest` |
| Who is inside this area? | Cultural region filter | `views.py` → `location__within` |
| Which routes cross this area? | API only | `views.py` → `path__intersects` |
| Who is within 200 m of this walk? | Route → "within 200 m" | `views.py` → `def artisans_nearby` |

## MVC (how Django is organised)
- **Model** = the data → `heritage/models.py`
- **View** = what the user sees → the map page (`templates/heritage_map.html`, `static/js/heritage_map.js`)
- **Controller** = the code that handles requests → `heritage/views.py`

## How the app stays safe
- Passwords are in `.env`, which never goes on GitHub (`.env.example` has fake values).
- DEBUG is off, so error pages don't show my code.
- Only the owner can edit/delete their workshop; only admins can change regions and routes.
- Bad input is rejected (e.g. phone "abc", a location outside Ireland).
- Typed code in forms is shown as text, not run (escapeHtml).
- Data is kept in a Docker volume, so it survives restarts.

## Useful commands
| What | Command |
|---|---|
| Is everything running? | `docker compose ps` |
| Run the 33 tests | `docker compose exec web python manage.py test heritage` |
| Show the indexes being used | `docker compose exec web python manage.py explain_spatial_queries` |
| Show the private network | `docker network inspect heritage_net` |
| Reset the demo account | `docker compose exec web python manage.py create_demo_user` |
| Reload the sample data | `docker compose exec web python manage.py load_heritage_data` |
| See errors | `docker compose logs web` |

## Things I'd improve next
- HTTPS (a security certificate)
- More real makers instead of examples
- Split the big JavaScript file into smaller files
