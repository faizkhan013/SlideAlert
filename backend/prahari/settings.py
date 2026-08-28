"""
Django settings for the PRAHARI (NER Landslide Early Warning) backend.

This is a development configuration — before deploying, at minimum:
  - set a real SECRET_KEY via an environment variable
  - set DEBUG = False
  - set ALLOWED_HOSTS to your real domain(s)
  - replace CORS_ALLOW_ALL_ORIGINS with CORS_ALLOWED_ORIGINS listing your
    frontend's real origin(s)
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "django-insecure-change-me-before-deploying"
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]  # tighten this for production

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "monitoring",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "prahari.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "prahari.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---- CORS (so the frontend, served from a different origin, can call this API) ----
# Dev-friendly default: allow all origins. Restrict this before deploying.
CORS_ALLOW_ALL_ORIGINS = True
# In production, prefer something like:
# CORS_ALLOWED_ORIGINS = ["https://your-frontend-domain.com"]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# How long a cached rainfall reading is considered fresh before we
# re-fetch it from Open-Meteo (see monitoring/services.py).
RAINFALL_CACHE_MINUTES = int(os.environ.get("RAINFALL_CACHE_MINUTES", "30"))

# ---- AI/ML MODULE INTEGRATION CONFIGURATION ----
SLIDELAND_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
if SLIDELAND_DIR not in sys.path:
    sys.path.append(SLIDELAND_DIR)

SLIDEALERT_DEMO_MODE = os.environ.get("SLIDEALERT_DEMO_MODE", "True") == "True"

