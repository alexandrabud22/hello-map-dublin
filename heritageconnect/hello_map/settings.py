"""
Django settings for HeritageConnect (project package: hello_map).

All secrets and environment-specific values are read from environment
variables, which Docker Compose loads from the .env file.
See .env.example for the full list.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = (
    os.getenv("SECRET_KEY")
    or os.getenv("DJANGO_SECRET_KEY")
)

if not SECRET_KEY:
    raise RuntimeError(
        "Django SECRET_KEY is not configured. "
        "Check the .env and compose.yaml files."
    )


def env_list(name, default=""):
    """Read a comma-separated environment variable as a list."""
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


# DEBUG is OFF unless explicitly turned on (safe default).
DEBUG = (
    os.getenv("DEBUG", os.getenv("DJANGO_DEBUG", "False")).lower()
    in ("true", "1", "yes")
)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# Origins allowed to send forms/API writes (needed behind Nginx on :8000).
CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000",
)


INSTALLED_APPS = [
    # Django applications
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",

    # Third-party applications
    "rest_framework",
    "rest_framework_gis",
    "django_filters",
    "corsheaders",
    "drf_spectacular",

    # Project applications
    "mapping",
    "spatial_analysis",
    "cities_api",
    "heritage",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    # CORS middleware should appear before CommonMiddleware.
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "hello_map.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",

        # Week 4:
        # Allows Django to find templates/map.html
        "DIRS": [
            BASE_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "hello_map.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ["DATABASE_NAME"],
        "USER": os.environ["DATABASE_USER"],
        "PASSWORD": os.environ["DATABASE_PASSWORD"],
        "HOST": os.environ["DATABASE_HOST"],
        "PORT": os.environ["DATABASE_PORT"],
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],

    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],

    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],

    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),

    "PAGE_SIZE": 20,

    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],

    "DEFAULT_SCHEMA_CLASS": (
        "drf_spectacular.openapi.AutoSchema"
    ),

    # Rate limiting - protects the API from abuse / scraping.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/minute",
        "user": "300/minute",
    },
}

# CORS: the front end is served from the same origin as the API, so no
# cross-origin access is needed. Extra origins can be added via .env.
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", "")
CORS_ALLOW_CREDENTIALS = False


# =========================================================
# Security settings
# =========================================================

# Browser-side protections (also reinforced by Nginx headers).
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"

# Session cookie cannot be read by JavaScript.
SESSION_COOKIE_HTTPONLY = True
# Note: CSRF_COOKIE_HTTPONLY stays False because heritage_map.js reads
# the csrftoken cookie to send the X-CSRFToken header.

SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 hours

# Behind Nginx: trust X-Forwarded-Proto so Django knows if HTTPS was used.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Only enable these when the site is served over HTTPS
# (set DJANGO_SECURE_COOKIES=True). Local Docker runs on plain HTTP.
if os.getenv("DJANGO_SECURE_COOKIES", "False").lower() == "true":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_SSL_REDIRECT = True


# =========================================================
# Logging - errors go to the container log
# (view with: docker compose logs web)
# =========================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


SPECTACULAR_SETTINGS = {
    "TITLE": "HeritageConnect API",
    "DESCRIPTION": (
        "RESTful API for Dublin artisan locations, cultural regions "
        "and heritage routes, with spatial queries (radius, nearest, "
        "containment, intersection)."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
LOGIN_REDIRECT_URL = "/heritage/"
LOGOUT_REDIRECT_URL = "/heritage/"
LOGIN_URL = "/accounts/login/"