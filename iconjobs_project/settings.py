from pathlib import Path
import os

# Central configuration file for the IconJobs Django project. Every major
# setting — installed apps, database, static files, authentication redirects —
# lives here. Django reads this on startup, so changes here affect the entire
# platform.

# BASE_DIR points to the root of the project (two levels up from this file).
# Everything else that needs an absolute path builds on top of it.
BASE_DIR = Path(__file__).resolve().parent.parent

# The secret key is pulled from an environment variable in production.
# The fallback string is intentionally labelled as dev-only so it's never
# accidentally used on a live server.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-local-dev-only-not-for-production')

# DEBUG=True means Django shows full error pages. Must be False in production.
DEBUG = True

# Wildcard host is fine for local development; lock this down before deploying.
ALLOWED_HOSTS = ['*']

# The three custom apps I built: accounts (users/profiles), jobs (listings &
# applications), and chat (messaging). The Django built-ins above them handle
# admin, auth, sessions, etc.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'jobs',
    'chat',
]

# Middleware runs on every request/response cycle, in order. Security,
# sessions, CSRF protection, authentication, flash messages, and
# clickjacking prevention are all handled here automatically.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'iconjobs_project.urls'

# Template configuration — tells Django where to look for HTML files.
# DIRS points to the top-level /templates folder I created. APP_DIRS=True
# also allows each app to have its own templates/ subfolder if needed.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'iconjobs_project.wsgi.application'

# Using SQLite for development — lightweight, no server required, the DB
# file just sits in the project root as db.sqlite3.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Django's built-in password validators enforce minimum standards so users
# can't register with weak passwords like "password" or "12345678".
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# British English locale and London timezone so timestamps appear correctly
# for the target audience. USE_TZ=True stores all datetimes as UTC internally.
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JS, images baked into the codebase).
# STATICFILES_DIRS is the source folder during development; STATIC_ROOT is
# where collectstatic dumps everything for production serving.
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files are user uploads (profile pictures, CVs, documents).
# They're stored separately from static files so they persist across deploys.
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# BigAutoField is the default primary key type from Django 3.2 onwards.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Where Django redirects unauthenticated users trying to reach a
# @login_required view, and where it sends users after login/logout.
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
