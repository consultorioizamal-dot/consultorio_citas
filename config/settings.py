from pathlib import Path
import os
import dj_database_url  # 👈 instalar con `pip install dj-database-url`

BASE_DIR = Path(__file__).resolve().parent.parent

# 🔑 Seguridad
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", 
    "django-insecure-a-m1m$wz8k+d(0sy5f-841&x_vx%n40#0obis351y63i0h34$r"
)

# 🔧 Debug controlado por variable de entorno
DEBUG = os.environ.get("DEBUG", "False") == "True"

# 🌐 Hosts permitidos (Render asigna uno con .onrender.com)
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    ".onrender.com",  # Render
]

# Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    "citas",  # 👈 tu app real
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # 👈 para servir estáticos en Render
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

# 📦 Base de datos: Render usará Postgres
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://consultorio_db_fuqq_user:Wyk8HQ4Kqr9LrcONW6LxbnwBxerYf9vp@dpg-d2mh25p5pdvs738r7up0-a.oregon-postgres.render.com/consultorio_db_fuqq',
        conn_max_age=600,
        ssl_require=True
    )
}

# 🔑 Passwords
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 🌍 Internacionalización
LANGUAGE_CODE = "es"
TIME_ZONE = "America/Merida"
USE_I18N = True
USE_TZ = True

# 📂 Archivos estáticos
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # en desarrollo
STATIC_ROOT = BASE_DIR / "staticfiles"    # en producción
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 📂 Archivos multimedia
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# 🔗 Base URL
BASE_URL = os.environ.get("BASE_URL", "https://consultorio-citas.onrender.com/admin-citas/
")

# 📧 Email (Gmail)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "consultorioizamal@gmail.com"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "wysr ohhp micj mwle")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
