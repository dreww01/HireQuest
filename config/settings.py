# Django settings for Job Hunt Bot

from pathlib import Path
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Environment variables
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-74(_#=3w4bn#j67mi75pom7*s^n1bekcnhwy_4v89#xkl0d)5j')
DEBUG = env('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Unfold Admin
UNFOLD = {
    "SITE_TITLE": "Job Hunt Bot Admin",
    "SITE_HEADER": "Job Hunt Bot",
    "SITE_URL": "/",
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "168 85 247",
            "600": "147 51 234",
            "700": "126 34 206",
            "800": "107 33 168",
            "900": "88 28 135",
            "950": "59 7 100",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
    },
}

# GitHub API
GITHUB_TOKEN = env('GITHUB_TOKEN', default='')
GITHUB_SCRAPING_ENABLED = False
GITHUB_SEARCH_KEYWORDS = env('GITHUB_SEARCH_KEYWORDS', default='paid,contract,freelance,hire,bounty')
GITHUB_MAX_AGE_DAYS = env.int('GITHUB_MAX_AGE_DAYS', default=14)

# Job Board Scraping
SCRAPING_ENABLED = env.bool('SCRAPING_ENABLED', default=True)
SCRAPE_INTERVAL_MINUTES = env.int('SCRAPE_INTERVAL_MINUTES', default=60)
MAX_JOBS_PER_SOURCE = env.int('MAX_JOBS_PER_SOURCE', default=20)
JOB_MAX_AGE_DAYS = env.int('JOB_MAX_AGE_DAYS', default=7)

# Hugging Face API
HUGGINGFACE_API_KEY = env('HUGGINGFACE_API_KEY', default='')
HUGGINGFACE_MODEL = env('HUGGINGFACE_MODEL', default='meta-llama/Llama-3.2-1B-Instruct')

# Telegram Bot
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='')
TELEGRAM_CHAT_ID = env('TELEGRAM_CHAT_ID', default='')

# Site Configuration
SITE_BASE_URL = env('SITE_BASE_URL', default='http://localhost:8000')
JOB_KEYWORDS = env('JOB_KEYWORDS', default='python,django,wordpress,web scraping,automation,backend,api')

# Django Cron
CRON_CLASSES = ['jobs.cron.PollJobsCronJob']

# User Profile
USER_PROFILE = {
    'skills': 'Python, Django, web scraping, automation, REST APIs',
    'pricing': '$50-100/hour depending on scope',
    'availability': 'Available for projects starting immediately',
    'tone': 'Professional but friendly, concise'
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'job_hunt_bot.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': env('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'integrations': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'utils': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'jobs': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
    },
}


def validate_api_credentials_on_startup():
    # Validates API credentials and logs warnings for missing services
    import logging
    from utils.validators import check_optional_service

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("API CREDENTIALS VALIDATION")
    logger.info("=" * 60)

    github_configured = check_optional_service('GitHub', {'GITHUB_TOKEN': GITHUB_TOKEN})
    telegram_configured = check_optional_service('Telegram', {
        'TELEGRAM_BOT_TOKEN': TELEGRAM_BOT_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    })
    hf_configured = check_optional_service('Hugging Face', {'HUGGINGFACE_API_KEY': HUGGINGFACE_API_KEY})

    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info(f"GitHub: {'✓ Configured' if github_configured else '✗ Not configured (60 req/hr limit)'}")
    logger.info(f"Telegram: {'✓ Configured' if telegram_configured else '✗ Not configured'}")
    logger.info(f"Hugging Face: {'✓ Configured' if hf_configured else '✗ Not configured'}")
    logger.info(f"Job Boards: ✓ Enabled (RSS + Web Scraping)")
    logger.info("=" * 60)

    if not telegram_configured:
        logger.warning("Telegram not configured - bot cannot send alerts")
    if not hf_configured:
        logger.warning("Hugging Face not configured - AI qualification disabled")


# Run validation on startup
import sys
SKIP_VALIDATION_COMMANDS = ['migrate', 'makemigrations', 'collectstatic', 'createsuperuser', 'shell', 'check']
if not any(arg in sys.argv for arg in SKIP_VALIDATION_COMMANDS):
    try:
        validate_api_credentials_on_startup()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during API credentials validation: {str(e)}")
