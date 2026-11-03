# Advanced Web Mapping – Alexandra Bud

Repository for **CMPU4058 Advanced Web Mapping**.

## 📍 Assignment 1 – HeritageConnect (Location-Based Services)

**➡️ [`heritageconnect/`](heritageconnect/) – start with the [HeritageConnect README](heritageconnect/README.md)**

A Django + PostGIS + Leaflet web application for discovering traditional craft makers,
cultural regions and heritage routes in Dublin, deployed with Docker (Nginx, Gunicorn,
PostGIS, PgAdmin) on an isolated network.

Quick start:
```bash
cd heritageconnect
cp .env.example .env        # then set your own passwords / secret key
docker compose up -d --build
docker compose exec web python manage.py load_heritage_data
docker compose exec web python manage.py create_demo_user
# open http://localhost:8000/
```

## Lab exercises

| Folder | Content |
|---|---|
| [`week1/`](week1/) | Lab 1 – containerised web mapping environment (Django, PostGIS, PgAdmin) |
| [`week2/`](week2/) | Lab 2 – spatial analysis with GeoDjango |
| [`week3/`](week3/) | Lab 3 – Cities REST API |
| [`week4/`](week4/) | Lab 4 – Django + Leaflet integration |
