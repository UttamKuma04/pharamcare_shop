import os
import importlib.util
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
WHITENOISE_AVAILABLE = importlib.util.find_spec('whitenoise') is not None
DJANGO_PROMETHEUS_AVAILABLE = importlib.util.find_spec('django_prometheus') is not None


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def redis_url_with_ssl_cert_reqs(url):
    if not url or not url.startswith('rediss://'):
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault('ssl_cert_reqs', 'CERT_REQUIRED')
    return urlunsplit(parts._replace(query=urlencode(query)))


SECRET_KEY = os.getenv('SECRET_KEY', 'unsafe-dev-secret-key-change-me')

DEBUG = env_flag('DEBUG', False)
if 'RENDER' in os.environ:
    DEBUG = False

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'http://127.0.0.1:8000,http://localhost:8000',
    ).split(',')
    if origin.strip()
]


RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

SECURE_SSL_REDIRECT = env_flag('SECURE_SSL_REDIRECT', not DEBUG)
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
SESSION_COOKIE_SECURE = env_flag('SESSION_COOKIE_SECURE', not DEBUG)
CSRF_COOKIE_SECURE = env_flag('CSRF_COOKIE_SECURE', not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = env_flag('SECURE_CONTENT_TYPE_NOSNIFF', True)
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', 31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_flag(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    SECURE_HSTS_SECONDS > 0 and not DEBUG,
)
SECURE_HSTS_PRELOAD = env_flag(
    'SECURE_HSTS_PRELOAD',
    SECURE_HSTS_SECONDS > 0 and SECURE_HSTS_INCLUDE_SUBDOMAINS and not DEBUG,
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'products',
    'cart',
    'accounts',
    'django_extensions',
    'Chatbot',
]

if DJANGO_PROMETHEUS_AVAILABLE:
    INSTALLED_APPS.insert(0, 'django_prometheus')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'products:home'
LOGOUT_REDIRECT_URL = 'products:home'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DJANGO_PROMETHEUS_AVAILABLE:
    MIDDLEWARE.insert(0, 'django_prometheus.middleware.PrometheusBeforeMiddleware')
    MIDDLEWARE.append('django_prometheus.middleware.PrometheusAfterMiddleware')

if WHITENOISE_AVAILABLE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'mr_doctor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mr_doctor.wsgi.application'

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
DATABASE_SSL_REQUIRE = env_flag('DATABASE_SSL_REQUIRE', False)

USE_SQLITE = not DATABASE_URL

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    database_config = {
        'default': DATABASE_URL,
        'conn_max_age': 600,
    }
    if DATABASE_SSL_REQUIRE and not DATABASE_URL.startswith('sqlite'):
        database_config['ssl_require'] = True

    DATABASES = {
        'default': dj_database_url.config(**database_config)
    }

REDIS_URL = os.getenv('REDIS_URL')
CELERY_BROKER_URL = redis_url_with_ssl_cert_reqs(
    os.getenv('CELERY_BROKER_URL', REDIS_URL or 'redis://localhost:6379/1')
)
CELERY_RESULT_BACKEND = redis_url_with_ssl_cert_reqs(
    os.getenv('CELERY_RESULT_BACKEND', REDIS_URL or 'redis://localhost:6379/1')
)
CELERY_TASK_DEFAULT_QUEUE = os.getenv('CELERY_TASK_DEFAULT_QUEUE', 'mr_doctor')
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
PRODUCT_CACHE_TTL = int(os.getenv('PRODUCT_CACHE_TTL', '300'))
PRODUCT_DETAIL_CACHE_TTL = int(os.getenv('PRODUCT_DETAIL_CACHE_TTL', '600'))

if REDIS_URL and importlib.util.find_spec('django_redis'):
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'KEY_PREFIX': 'mr_doctor',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            },
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'mr-doctor-local-cache',
        }
    }



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True




STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

if WHITENOISE_AVAILABLE:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



#<<<<<<<<<<<<<<<SMTP SET-UP>>>>>>>>>>>>>>>>>>
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.brevo.com'
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False') == 'True'
EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '20'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@pharmacare.local")

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
