"""
Django settings for suggestio_backend project.

Generated by 'django-admin startproject' using Django 5.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv() # load .env vars

FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', '')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.getenv('DEBUG', 0))

INTERNAL_IPS = [  # debug toolbar
    '127.0.0.1',
]

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']
ALLOWED_HOSTS += os.getenv('ALLOWED_HOSTS', []).split(' ')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.postgres', # postgres integration
    'debug_toolbar',
    'encrypted_model_fields',  # encryption for refresh auth tokens of SpotifyAPI
    'django_bootstrap5',

    'dev.apps.DevConfig',
    'suggestio.apps.SuggestioConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'debug_toolbar.middleware.DebugToolbarMiddleware',  # debug toolbar

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'suggestio_backend.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'suggestio_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

_old_DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',   # Используется PostgreSQL
        #'NAME': 'postgres',
        'NAME': os.getenv('POSTGRES_NAME'), # Имя базы данных
        #'USER': 'postgres',
        'USER': os.getenv('POSTGRES_USER'), # Имя пользователя
        #'PASSWORD': 'postgres',
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'), # Пароль пользователя
        #'HOST': 'pgdb',
        'HOST': os.getenv('PGSQL_HOST'), # Наименование контейнера для базы данных в Docker Compose
        #'PORT': '5432',
        'PORT': os.getenv('PGSQL_PORT'),  # Порт базы данных
    }
}

REDIS_ADDR = os.getenv("REDIS_ADDR", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        #"LOCATION": "redis://127.0.0.1:6379/1",
        "LOCATION": f"redis://{REDIS_ADDR}:{REDIS_PORT}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
#STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = 'suggestio:suggestio-index'
LOGIN_URL = 'auth:login'

LOG_FILE_NAME = BASE_DIR / os.getenv('LOG_FILE_NAME')
LOG_FILE_SIZE = int(os.getenv('LOG_FILE_SIZE_BYTES')) * 1024 * 1024  # макс размер 1 лога в байтах
LOG_FILE_COUNT = int(os.getenv('LOG_FILES_ROTATION_COUNT'))  # сколько файлов будет в ротации + 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {  # когда включен дебаг режим
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'verbose': {
          'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
          # asctime - время, levelname - название уровня, т.е. INFO, DEBUG итд
          # name - имя логера, message - сообщение логеру
        },
    },
    'handlers': {
        'console': {  # в консоль
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'logfile': {  # в файл
            # логфайл с ротацией(запись в новый и перенос записей в старый)
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_NAME,
            'maxBytes': LOG_FILE_SIZE,
            'backupCount': LOG_FILE_COUNT,
            'formatter': 'verbose'
        }
    },
    'root': {
        'handlers': ['console', 'logfile'],
        'level': 'DEBUG'
    }
}
