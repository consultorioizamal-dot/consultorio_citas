from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('admin-citas/', views.panel_admin, name='panel_admin'), 
    path('api/citas/', views.api_citas, name='api_citas'),
    path('admin-login/', views.login_admin, name='login_admin'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('api/horas_disponibles/', views.api_horas_disponibles, name='api_horas_disponibles'),
    
]
