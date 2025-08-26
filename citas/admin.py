from django.contrib import admin
from .models import Cita

# Personalizar títulos del admin
admin.site.site_header = "Consultorio - Administración"
admin.site.site_title = "Consultorio Admin"
admin.site.index_title = "Panel de Control de Citas"

# Traducción de botones y etiquetas
admin.site.site_url = None  # Oculta link al sitio principal

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo', 'servicio', 'fecha', 'hora', 'edad')
    list_filter = ('fecha', 'edad', 'servicio')
    search_fields = ('nombre', 'correo', 'telefono')
    ordering = ('fecha', 'hora')
    date_hierarchy = 'fecha'
    list_per_page = 20

class CitaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo', 'servicio', 'fecha', 'hora', 'edad')
    list_filter = ('fecha', 'edad', 'servicio')
    search_fields = ('nombre', 'correo', 'telefono')
    ordering = ('fecha', 'hora')
    date_hierarchy = 'fecha'
    list_per_page = 20

    class Media:
        css = {
            'all': ('consultorio_citas/static/admin_custom/admin.css',)  # ruta de tu CSS
        }
