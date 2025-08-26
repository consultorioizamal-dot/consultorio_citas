from django.db import models

class Cita(models.Model):
    EDAD_OPCIONES = [
        ('mayor', 'Mayor de edad'),
        ('menor', 'Menor de edad'),
    ]

    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, default='0000000000')  
    correo = models.EmailField(max_length=100, blank=True, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    edad = models.CharField(max_length=10, choices=EDAD_OPCIONES, default='mayor')  # default corregido
    servicio = models.CharField(max_length=100, default='General')  # default corregido
    primera_vez = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} - {self.servicio} ({self.fecha} {self.hora})"
