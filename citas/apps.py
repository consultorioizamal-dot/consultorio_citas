from django.apps import AppConfig
from django.contrib.auth.models import User

class CitasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "citas"

    def ready(self):
        username = "Monica"
        password = "ConsultorioIza"
        email = "consultorioizamal@gmail.com"

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            print("✅ Superusuario creado con éxito")
