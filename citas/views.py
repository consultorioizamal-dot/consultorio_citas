from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.template.loader import get_template, render_to_string
from django.templatetags.static import static
from django.conf import settings

from .models import Cita

import pandas as pd
from xhtml2pdf import pisa
from datetime import datetime, time, timedelta
from django.utils.dateparse import parse_date
from django.core.mail import EmailMessage, EmailMultiAlternatives
from email.mime.image import MIMEImage

# Google Calendar
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os

#-- temporal
from django.contrib.auth.models import User

def crear_superusuario_temporal(request):
    if not User.objects.filter(username='Monica').exists():
        User.objects.create_superuser('Monica', 'admin@correo.com', 'ConsultorioIza')
        return HttpResponse("Superusuario creado!")
    return HttpResponse("Ya existe el superusuario")



# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')

# ---------------- HORAS DISPONIBLES ----------------
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

        citas = Cita.objects.filter(fecha=fecha_seleccionada)
        ocupadas = [c.hora.strftime("%H:%M") for c in citas]
        horas = [h for h in horas if h not in ocupadas]

    horas_12h = [datetime.strptime(h, "%H:%M").strftime("%I:%M %p") for h in horas]
    return horas_12h

def api_horas_disponibles(request):
    fecha = request.GET.get("fecha")
    horas = []
    mensaje = ""
    if fecha:
        fecha_obj = parse_date(fecha)
        if fecha_obj.weekday() >= 5:
            mensaje = "No se atiende fines de semana"
        else:
            horas = generar_horas_disponibles(fecha_obj)
    return JsonResponse({"horas": horas, "mensaje": mensaje})

# ---------------- CORREO CLIENTE ----------------
def notificar_cliente_email(cita):
    try:
        img_filename = 'lineamientos_mayor.jpg' if cita.edad == 'mayor' else 'lineamientos_menor.jpg'
        img_path = os.path.join(settings.MEDIA_ROOT, img_filename)
        logo_path = os.path.join(settings.MEDIA_ROOT, 'logo_consultorio.png')

        html_content = render_to_string('email_confirmacion.html', {
            'nombre': cita.nombre,
            'fecha': cita.fecha.strftime("%d/%m/%Y"),
            'hora': cita.hora.strftime("%I:%M %p"),
            'servicio': cita.servicio,
            'edad': cita.edad,
        })

        email = EmailMessage(
            subject=f'Confirmación de cita - {cita.servicio}',
            body=html_content,
            from_email=settings.EMAIL_HOST_USER,
            to=[cita.correo],
        )
        email.content_subtype = "html"

        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                lineamientos_img = MIMEImage(f.read())
                lineamientos_img.add_header('Content-ID', 'lineamientos_img')
                lineamientos_img.add_header('Content-Disposition', 'inline', filename=img_filename)
                email.attach(lineamientos_img)

        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_img = MIMEImage(f.read())
                logo_img.add_header('Content-ID', 'logo_consultorio')
                logo_img.add_header('Content-Disposition', 'inline', filename='logo_consultorio.png')
                email.attach(logo_img)

        email.send()
    except Exception as e:
        print(f"[ERROR] Enviando correo al cliente: {e}")

# ---------------- GOOGLE CALENDAR ----------------


# ---------------- NOTIFICACIÓN PSICÓLOGA ----------------
def notificar_psicologa(cita):
    try:
        asunto = f"Nueva cita agendada: {cita.nombre}"
        mensaje_texto = f"""
Se ha agendado una nueva cita:

Nombre: {cita.nombre}
Teléfono: {cita.telefono}
Correo: {cita.correo}
Fecha: {cita.fecha}
Hora: {cita.hora}
Servicio: {cita.servicio}
"""
        panel_url = f"{settings.BASE_URL}/admin-citas/"

        mensaje_html = render_to_string('email_psicologa.html', {
            'cita': cita,
            'panel_url': panel_url
        })

        email = EmailMultiAlternatives(
            asunto,
            mensaje_texto,
            settings.EMAIL_HOST_USER,
            [settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(mensaje_html, "text/html")
        email.send()
    except Exception as e:
        print(f"[ERROR] Enviando correo a psicóloga: {e}")

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

        notificar_cliente_email(cita)
        notificar_psicologa(cita)

        messages.success(request, "¡Cita reservada exitosamente! Revisa tu correo.")
        return redirect('agendar_cita')

    return render(request, 'agendar_cita.html', {'horas_disponibles': horas_disponibles, 'today': today_str})

# ---------------- LOGIN Y PANEL ADMIN ----------------
def login_admin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            return redirect('panel_admin')
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
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
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
