from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.template.loader import get_template
from django.templatetags.static import static

from .models import Cita

import pandas as pd
from xhtml2pdf import pisa
from datetime import datetime, time, timedelta
from django.utils.dateparse import parse_date
from django.core.mail import send_mail

# Google Calendar
from googleapiclient.discovery import build
from google.oauth2 import service_account

#--- 
import os
from django.conf import settings

#-- form de correo 
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import os
from django.conf import settings

#--- 
from django.core.mail import EmailMultiAlternatives


#-- 
from django.http import JsonResponse
from .models import Cita

SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'citas/citaspsicologia-6a32198a3750.json')


# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')

# ---------------- GENERAR HORAS DISPONIBLES ----------------
def generar_horas_disponibles(fecha_seleccionada):
    inicio = time(15, 0)
    fin = time(21, 0)

    horas = []
    hora_actual = datetime.combine(datetime.today(), inicio)
    hora_fin = datetime.combine(datetime.today(), fin)

    if fecha_seleccionada:
        while hora_actual <= hora_fin:
            horas.append(hora_actual.strftime("%H:%M"))
            hora_actual += timedelta(hours=1)

        # Filtrar horas ocupadas en la BD
        citas = Cita.objects.filter(fecha=fecha_seleccionada)
        ocupadas = [c.hora.strftime("%H:%M") for c in citas]
        horas = [h for h in horas if h not in ocupadas]

    # Convertir a 12h para el frontend
    horas_12h = [datetime.strptime(h, "%H:%M").strftime("%I:%M %p") for h in horas]
    return horas_12h

# ---------------- API HORAS DISPONIBLES ----------------
def api_horas_disponibles(request):
    fecha = request.GET.get("fecha")
    horas = []
    mensaje = ""
    if fecha:
        fecha_obj = parse_date(fecha)
        if fecha_obj.weekday() >= 5:  # sábado=5, domingo=6
            mensaje = "No se atiende fines de semana"
        else:
            horas = generar_horas_disponibles(fecha_obj)
    return JsonResponse({"horas": horas, "mensaje": mensaje})

#---- CORREO ELECTRONICO CLIENTE

def notificar_cliente_email(cita):
    """
    Envía un correo al cliente con el template email_confirmacion.html,
    incluyendo el logo del consultorio y la imagen de lineamientos embebidos.
    """
    # Determinar imagen de lineamientos según edad
    img_filename = 'lineamientos_mayor.jpg' if cita.edad == 'mayor' else 'lineamientos_menor.jpg'
    img_path = os.path.join(settings.BASE_DIR, 'citas', 'media', img_filename)
    
    # Ruta del logo
    logo_path = os.path.join(settings.BASE_DIR, 'citas', 'media', 'logo_consultorio.png')

    # Renderizar el HTML del correo
    html_content = render_to_string('email_confirmacion.html', {
        'nombre': cita.nombre,
        'fecha': cita.fecha.strftime("%d/%m/%Y"),
        'hora': cita.hora.strftime("%I:%M %p"),
        'servicio': cita.servicio,
        'edad': cita.edad,
    })

    # Crear el objeto EmailMessage
    email = EmailMessage(
        subject=f'Confirmación de cita - {cita.servicio}',
        body=html_content,
        from_email='consultorioizamal@gmail.com',
        to=[cita.correo],
    )
    email.content_subtype = "html"

    # Adjuntar imagen de lineamientos embebida
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            lineamientos_img = MIMEImage(f.read())
            lineamientos_img.add_header('Content-ID', 'lineamientos_img')  # sin <>
            lineamientos_img.add_header('Content-Disposition', 'inline', filename=img_filename)
            email.attach(lineamientos_img)

    # Adjuntar logo del consultorio embebido
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            logo_img = MIMEImage(f.read())
            logo_img.add_header('Content-ID', 'logo_consultorio')  # sin <>
            logo_img.add_header('Content-Disposition', 'inline', filename='logo_consultorio.png')
            email.attach(logo_img)

    # Enviar el correo
    email.send()


# ---------------- AGENDAR CITA ----------------
def agendar_cita(request):
    horas_disponibles = []
    today_str = datetime.today().date().isoformat()

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()
        servicio = request.POST.get('servicio', '').strip()
        es_mayor = request.POST.get('es_mayor', 'si')
        fecha_str = request.POST.get('fecha', '')
        hora_str = request.POST.get('hora', '')

        if not (nombre and telefono and servicio and fecha_str and hora_str):
            messages.error(request, "Por favor completa todos los campos.")
            return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

        fecha = parse_date(fecha_str)
        try:
            # Convertir hora 12h a 24h
            hora = datetime.strptime(hora_str, "%I:%M %p").time()
        except ValueError:
            messages.error(request, "La hora no es válida.")
            return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

        if fecha.weekday() >= 5:
            messages.error(request, "Solo se atiende de lunes a viernes.")
            return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

        if Cita.objects.filter(fecha=fecha, hora=hora).exists():
            messages.error(request, "Esa fecha y hora ya está reservada. Elige otra.")
            return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

        edad = 'mayor' if es_mayor == 'si' else 'menor'

        # Crear cita
        cita = Cita.objects.create(
            nombre=nombre,
            telefono=telefono,
            correo=correo,
            fecha=fecha,
            hora=hora,
            edad=edad,
            servicio=servicio,
            primera_vez=False
        )

        #-- correo del cliente
        notificar_cliente_email(cita)

        # Notificar psicóloga
        notificar_psicologa(cita)
        # Crear evento en Google Calendar
        crear_evento_google_calendar(cita)

        messages.success(request, "¡Cita reservada exitosamente y notificación enviada, PORFAVOR ¡¡IMPORTANTE REVISAR SU CORREO!!")
        return redirect('agendar_cita')

    return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

# ---------------- LOGIN Y PANEL ADMIN ----------------
def login_admin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('panel_admin')
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'login.html')

def panel_admin(request):
    citas = aplicar_filtros(request)
    return render(request, 'panel_admin.html', {'citas': citas, 'request': request})

def api_citas(request):
    citas = Cita.objects.all()
    eventos = [{'title': c.servicio, 'start': f'{c.fecha}T{c.hora}', 'allDay': False} for c in citas]
    return JsonResponse(eventos, safe=False)

# ---------------- EXPORTACIÓN ----------------
def aplicar_filtros(request):
    citas = Cita.objects.all().order_by('fecha', 'hora')
    tipo = request.GET.get("tipo")
    f1 = request.GET.get("fecha_inicio")
    f2 = request.GET.get("fecha_fin")

    if tipo == "dia" and f1:
        citas = citas.filter(fecha=f1)
    elif tipo == "mes" and f1:
        citas = citas.filter(fecha__month=datetime.strptime(f1, "%Y-%m-%d").month)
    elif tipo == "anio" and f1:
        citas = citas.filter(fecha__year=datetime.strptime(f1, "%Y-%m-%d").year)
    elif tipo == "rango" and f1 and f2:
        citas = citas.filter(fecha__range=[f1, f2])
    return citas

def exportar_excel(request):
    citas = aplicar_filtros(request).values()
    df = pd.DataFrame(citas)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=citas.xlsx'
    df.to_excel(response, index=False)
    return response

def exportar_pdf(request):
    citas = aplicar_filtros(request)
    template = get_template('reporte_pdf.html')
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    logo_url = request.build_absolute_uri(static('img/logo_consultorio.png'))

    html = template.render({'citas': citas, 'fecha_actual': fecha_actual, 'logo_url': logo_url})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_citas.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar el PDF')
    return response

# ---------------- GOOGLE CALENDAR ----------------
SERVICE_ACCOUNT_FILE = 'citas/citaspsicologia-6a32198a3750.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']

def crear_evento_google_calendar(cita):
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=credentials)

    start_datetime = datetime.combine(cita.fecha, cita.hora)
    end_datetime = start_datetime + timedelta(hours=1)

    event = {
        'summary': f"Cita con {cita.nombre}",
        'description': f"Servicio: {cita.servicio}\nTeléfono: {cita.telefono}",
        'start': {
            'dateTime': start_datetime.isoformat(),
            'timeZone': 'America/Merida',
        },
        'end': {
            'dateTime': end_datetime.isoformat(),
            'timeZone': 'America/Merida',
        },
    }

    event = service.events().insert(calendarId='consultorioizamal@gmail.com', body=event).execute()
    print(f"Evento creado: {event.get('htmlLink')}")

# ---------------- NOTIFICACIÓN POR EMAIL ----------------

def notificar_psicologa(cita):
    asunto = f"Nueva cita agendada: {cita.nombre}"

    # Mensaje en texto plano (fallback)
    mensaje_texto = f"""
Se ha agendado una nueva cita:

Nombre: {cita.nombre}
Teléfono: {cita.telefono}
Correo: {cita.correo}
Fecha: {cita.fecha}
Hora: {cita.hora}
Servicio: {cita.servicio}
"""

    # Construimos la URL del panel de administración
    panel_url = f"{settings.BASE_URL}/admin-citas/"

    # Mensaje en HTML con el botón funcional
    mensaje_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Nueva Cita Agendada</title>
</head>
<body style="font-family: Arial, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px;">
    <table align="center" width="600" style="background-color: #ffffff; border-radius: 10px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <tr>
            <td align="center" style="padding-bottom: 20px;">
                <h2 style="color: #2c3e50;">📅 Nueva Cita Agendada</h2>
            </td>
        </tr>
        <tr>
            <td style="color: #333333; font-size: 15px; line-height: 1.6;">
                <p>Se ha registrado una nueva cita en tu consultorio.</p>
                <p><strong>Nombre del paciente:</strong> {cita.nombre}</p>
                <p><strong>Teléfono:</strong> {cita.telefono}</p>
                <p><strong>Correo:</strong> {cita.correo}</p>
                <p><strong>Fecha:</strong> {cita.fecha}</p>
                <p><strong>Hora:</strong> {cita.hora}</p>
                <p><strong>Servicio:</strong> {cita.servicio}</p>
            </td>
        </tr>
        <tr>
            <td align="center" style="padding-top: 30px;">
                <a href="{settings.BASE_URL}/admin-citas/" 
                   style="background-color: #3498db; color: white; padding: 12px 25px; 
                          border-radius: 6px; text-decoration: none; font-weight: bold;">
                    Ver en el sistema
                </a>
            </td>
        </tr>
        <tr>
            <td align="center" style="padding-top: 40px; font-size: 12px; color: #7f8c8d;">
                Este correo es una notificación automática. No respondas a este mensaje.
            </td>
        </tr>
    </table>
</body>
</html>
"""
    # Configuración del correo
    email = EmailMultiAlternatives(
        asunto,
        mensaje_texto,
        'consultorioizamal@gmail.com',
        ['consultorioizamal@gmail.com']  # correo de la psicóloga
    )
    email.attach_alternative(mensaje_html, "text/html")
    email.send()