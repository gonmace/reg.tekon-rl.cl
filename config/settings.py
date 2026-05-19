import os
import sys
from datetime import timedelta
from pathlib import Path

from decouple import config, Csv
from import_export.formats.base_formats import XLSX, CSV as ExportCSV

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*'] if DEBUG else config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

ADMIN_URL = config('ADMIN_URL', default='admin/')

# ── Apps ─────────────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'adminsortable2',
    'axes',
    'tailwind',
    'theme',
    'simple_history',
    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'crispy_forms',
    'crispy_daisyui',
    'django_tables2',
    'admin_sort',
    'users',
    'core',
    'photos',
    'reg_txtss',
    'pdf_reports',
    'registros',
    'dashboard',
    'actividades',
    'widgets',
]

# ── Middleware ────────────────────────────────────────────────────────────────

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'csp.middleware.CSPMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

if DEBUG:
    INSTALLED_APPS += ['django_browser_reload']
    MIDDLEWARE += ['django_browser_reload.middleware.BrowserReloadMiddleware']
    INTERNAL_IPS = ['127.0.0.1', '::1']
    if sys.platform == 'win32':
        NPM_BIN_PATH = r'C:\Program Files\nodejs\npm.cmd'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ── URLs y templates ──────────────────────────────────────────────────────────

ROOT_URLCONF = 'config.urls'

TAILWIND_APP_NAME = 'theme'
TAILWIND_CSS_PATH = 'css/dist/styles.css'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.menu_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Base de datos ─────────────────────────────────────────────────────────────

if config('POSTGRES_DB', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('POSTGRES_DB'),
            'USER': config('POSTGRES_USER'),
            'PASSWORD': config('POSTGRES_PASSWORD'),
            'HOST': config('POSTGRES_HOST', default='localhost'),
            'PORT': config('POSTGRES_PORT', default='5432'),
            'OPTIONS': {'connect_timeout': 10},
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Validadores de contraseña ─────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── I18n ──────────────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static y media ────────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
WHITENOISE_MANIFEST_STRICT = False

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Autenticación ─────────────────────────────────────────────────────────────

AUTH_USER_MODEL = 'users.User'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# ── Email ─────────────────────────────────────────────────────────────────────

if config('EMAIL_HOST', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
    EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@localhost'

SITE_URL = config('SITE_URL', default='http://localhost:8000')

# ── Seguridad ─────────────────────────────────────────────────────────────────

CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

if DEBUG:
    _dev_ports = ['8000', '8001', '8002', '8008', '8012', '8080']
    _dev_trusted = []
    for _h in ALLOWED_HOSTS:
        if _h in ('*', 'testserver'):
            continue
        _dev_trusted.append(f'http://{_h}')
        for _p in _dev_ports:
            _dev_trusted.append(f'http://{_h}:{_p}')
    CSRF_TRUSTED_ORIGINS = list(set(CSRF_TRUSTED_ORIGINS + _dev_trusted))

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

X_FRAME_OPTIONS = 'DENY'

# ── Redis y caché ─────────────────────────────────────────────────────────────

REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ── django-axes (protección brute-force) ─────────────────────────────────────

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']

if DEBUG:
    AXES_ENABLED = False
else:
    AXES_HANDLER = 'axes.handlers.cache.AxesCacheHandler'
    AXES_CACHE = 'default'

# ── Content Security Policy ───────────────────────────────────────────────────
# unsafe-inline necesario por los scripts/estilos inline en los templates actuales

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://unpkg.com", "https://cdnjs.cloudflare.com")
CSP_STYLE_SRC = ("'self'", "https://fonts.googleapis.com", "https://cdnjs.cloudflare.com", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "blob:", "https://maps.googleapis.com", "https://maps.gstatic.com", "https://*.tile.openstreetmap.org", "https://server.arcgisonline.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com", "https://cdnjs.cloudflare.com")
CSP_CONNECT_SRC = (
    ("'self'",) if not DEBUG
    else ("'self'", "ws://localhost:*", "ws://127.0.0.1:*")
)

# ── DRF ──────────────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# ── Crispy Forms ──────────────────────────────────────────────────────────────

CRISPY_ALLOWED_TEMPLATE_PACKS = 'daisyui'
CRISPY_TEMPLATE_PACK = 'daisyui'

# ── Import/Export ─────────────────────────────────────────────────────────────

EXPORT_FORMATS = [XLSX, ExportCSV]

# ── Logging ───────────────────────────────────────────────────────────────────

if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {'console': {'class': 'logging.StreamHandler'}},
        'root': {'handlers': ['console'], 'level': 'INFO'},
    }
else:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'root': {'handlers': ['console'], 'level': 'INFO'},
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
