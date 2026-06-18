import os
import base64
import uuid
import json
from datetime import datetime, timedelta
from io import BytesIO

import resend
from twilio.rest import Client
from icalendar import Calendar, Event
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from cliente_config import NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_EMAIL

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUM   = os.environ.get("TWILIO_WHATSAPP_NUM")
TWILIO_SMS_NUM = os.environ.get("TWILIO_PHONE_NUMBER")
RESEND_KEY   = os.environ.get("RESEND_API_KEY")

resend.api_key = RESEND_KEY


def _parse_datetime(fecha_str, hora_str):
    """
    Convierte fecha 'YYYY-MM-DD' y hora '10:00 AM' / '1:00 PM' a datetime.
    """
    dt_str = f"{fecha_str} {hora_str.upper().strip()}"
    for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    # Ultimo recurso: solo la fecha sin hora
    return datetime.strptime(fecha_str, "%Y-%m-%d")


def _google_cal_url(dt_start, dt_end, servicio):
    """
    Construye la URL de Google Calendar con formato iCal YYYYMMDDTHHMMSS/YYYYMMDDTHHMMSS.
    """
    fmt = "%Y%m%dT%H%M%S"
    fechas_ical = f"{dt_start.strftime(fmt)}/{dt_end.strftime(fmt)}"
    nombre_enc  = NEGOCIO_NOMBRE.replace(" ", "+")
    dir_enc     = NEGOCIO_DIRECCION.replace(" ", "+").replace(",", "%2C")
    serv_enc    = servicio.replace(" ", "+")
    return (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text=Reservacion+en+{nombre_enc}"
        f"&dates={fechas_ical}"
        f"&details=Servicio:+{serv_enc}"
        f"&location={dir_enc}"
    )


def _build_ics(dt_start, dt_end, servicio):
    """
    Genera los bytes de un archivo .ics usando la libreria icalendar.
    """
    cal = Calendar()
    cal.add("prodid", f"-//{NEGOCIO_NOMBRE}//Reservaciones//ES")
    cal.add("version", "2.0")

    event = Event()
    event.add("uid", str(uuid.uuid4()))
    event.add("summary", f"Reservacion en {NEGOCIO_NOMBRE}")
    event.add("dtstart", dt_start)
    event.add("dtend", dt_end)
    event.add("description", f"Servicio: {servicio}")
    event.add("location", NEGOCIO_DIRECCION)

    cal.add_component(event)
    return cal.to_ical()


def mandar_email(destinatario, nombre, fecha, hora, servicio):
    """
    Envia email de confirmacion con boton de Google Calendar y archivo .ics adjunto.
    """
    try:
        dt_start = _parse_datetime(fecha, hora)
        dt_end   = dt_start + timedelta(hours=1)
    except Exception:
        dt_start = dt_end = datetime.now()

    cal_url  = _google_cal_url(dt_start, dt_end, servicio)
    ics_data = _build_ics(dt_start, dt_end, servicio)
    ics_b64  = base64.b64encode(ics_data).decode()

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:560px;margin:0 auto;background:#f9f9f9;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">
      <div style="background:linear-gradient(135deg,#5C3D8F,#7B5EA7);padding:36px 32px 28px;text-align:center;">
        <div style="font-size:48px;margin-bottom:8px;">✅</div>
        <h1 style="color:#fff;font-size:22px;margin:0 0 6px;">Reservacion Confirmada</h1>
        <p style="color:rgba(255,255,255,0.85);font-size:14px;margin:0;">{NEGOCIO_NOMBRE}</p>
      </div>
      <div style="padding:28px 32px;">
        <p style="font-size:15px;color:#333;margin:0 0 20px;">Hola <strong>{nombre}</strong>, tu reservacion ha sido recibida exitosamente. Aqui estan los detalles:</p>
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:24px;">
          <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;width:40%;">Servicio</td><td style="padding:10px 14px;color:#333;">{servicio}</td></tr>
          <tr><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Fecha</td><td style="padding:10px 14px;color:#333;">{fecha}</td></tr>
          <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Hora</td><td style="padding:10px 14px;color:#333;">{hora}</td></tr>
        </table>
        <div style="text-align:center;margin-bottom:24px;">
          <a href="{cal_url}" target="_blank"
             style="display:inline-block;padding:13px 28px;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;box-shadow:0 4px 12px rgba(92,61,143,0.30);">
            📅 Agregar a Google Calendar
          </a>
        </div>
        <p style="font-size:12px;color:#aaa;text-align:center;margin:0;">Tambien adjuntamos un archivo .ics para agregarlo a cualquier calendario.</p>
      </div>
      <div style="background:#f3eeff;padding:16px 32px;text-align:center;">
        <p style="font-size:12px;color:#888;margin:0;">{NEGOCIO_NOMBRE} &bull; {NEGOCIO_DIRECCION}</p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": f"{NEGOCIO_NOMBRE} <reservaciones@getdrivftllc.com>",
            "to": destinatario,
            "subject": f"Reservacion confirmada — {NEGOCIO_NOMBRE}",
            "html": html,
            "attachments": [
                {
                    "filename": "reservacion.ics",
                    "content": ics_b64,
                }
            ],
        })
        print(f"[Email] Confirmacion enviada a {destinatario}")
        return True
    except Exception as e:
        print(f"[Email] Error: {e}")
        return False


def mandar_whatsapp(destinatario, nombre, fecha, hora, servicio):
    """
    Envia mensaje de confirmacion por WhatsApp usando Twilio.
    """
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_NUM]):
        print("[WhatsApp] Credenciales Twilio no configuradas")
        return False
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        num = destinatario.strip().replace(" ", "").replace("-", "")
        if not num.startswith("+"):
            num = "+" + num
        body = (
            f"Hola {nombre}! Tu reservacion en {NEGOCIO_NOMBRE} ha sido confirmada.\n\n"
            f"Servicio: {servicio}\nFecha: {fecha}\nHora: {hora}\n\n"
            "Si necesitas cambiar o cancelar, respondenos por aqui."
        )
        client.messages.create(
            body=body,
            from_=f"whatsapp:{TWILIO_NUM}",
            to=f"whatsapp:{num}",
        )
        print(f"[WhatsApp] Confirmacion enviada a {destinatario}")
        return True
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        return False


def mandar_sms_confirmacion(destinatario, nombre, fecha, hora, servicio):
    """
    Envia SMS de confirmacion inmediata al cliente via Twilio (SMS regular, no WhatsApp).
    Se llama desde app.py justo despues de guardar la reservacion.
    """
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_SMS_NUM]):
        print("[SMS Confirmacion] Credenciales Twilio no configuradas (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)")
        return False
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        num = destinatario.strip().replace(" ", "").replace("-", "")
        if not num.startswith("+"):
            num = "+" + num
        body = (
            f"Drivft: ¡Hola {nombre}! Tu cita para {servicio} está confirmada "
            f"para el {fecha} a las {hora}. "
            "Te mandaremos un recordatorio mañana. "
            "Reply STOP to unsubscribe."
        )
        client.messages.create(
            body=body,
            from_=TWILIO_SMS_NUM,
            to=num,
        )
        print(f"[SMS Confirmacion] Enviado a {destinatario}")
        return True
    except Exception as e:
        print(f"[SMS Confirmacion] Error: {e}")
        return False


def notificar_dueno(nombre_cliente, fecha, hora, servicio, canal):
    """
    Envia notificacion instantanea al dueno cuando llega una nueva reservacion.
    """
    destinatario = os.environ.get("GMAIL_USER") or NEGOCIO_EMAIL
    if not destinatario:
        print("[Dueno] No hay email de destino configurado (GMAIL_USER / NEGOCIO_EMAIL)")
        return False

    canal_emoji = "📱 WhatsApp" if canal == "whatsapp" else "🌐 Web"
    base_url    = os.environ.get("APP_URL", "")
    panel_url   = f"{base_url}/panel"

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:0 auto;background:#f9f9f9;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">
      <div style="background:linear-gradient(135deg,#3D2560,#5C3D8F);padding:32px;text-align:center;">
        <div style="font-size:44px;margin-bottom:8px;">🔔</div>
        <h1 style="color:#fff;font-size:20px;margin:0 0 4px;">Nueva Reservacion</h1>
        <p style="color:rgba(255,255,255,0.80);font-size:13px;margin:0;">{NEGOCIO_NOMBRE}</p>
      </div>
      <div style="padding:28px 32px;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:24px;">
          <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;width:40%;">Cliente</td><td style="padding:10px 14px;color:#333;">{nombre_cliente}</td></tr>
          <tr><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Fecha</td><td style="padding:10px 14px;color:#333;">{fecha}</td></tr>
          <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Hora</td><td style="padding:10px 14px;color:#333;">{hora}</td></tr>
          <tr><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Servicio</td><td style="padding:10px 14px;color:#333;">{servicio}</td></tr>
          <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Canal</td><td style="padding:10px 14px;color:#333;">{canal_emoji}</td></tr>
        </table>
        <div style="text-align:center;">
          <a href="{panel_url}" target="_blank"
             style="display:inline-block;padding:13px 28px;background:linear-gradient(135deg,#3D2560,#5C3D8F);color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;box-shadow:0 4px 12px rgba(61,37,96,0.35);">
            📊 Ver panel
          </a>
        </div>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": f"{NEGOCIO_NOMBRE} <reservaciones@getdrivftllc.com>",
            "to": destinatario,
            "subject": f"🔔 Nueva reservacion — {nombre_cliente}",
            "html": html,
        })
        print(f"[Dueno] Notificacion enviada a {destinatario}")
        return True
    except Exception as e:
        print(f"[Dueno] Error enviando notificacion: {e}")
        return False


def mandar_solicitud_resena(destinatario, nombre, negocio_nombre, google_maps_url):
    """
    Envia solicitud de resena de Google 24h despues de la reservacion.
    """
    if not google_maps_url:
        print("[Resena] GOOGLE_MAPS_REVIEW_URL no configurado, se omite el envio.")
        return False

    html = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:520px;margin:0 auto;background:#f9f9f9;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">
      <div style="background:linear-gradient(135deg,#5C3D8F,#7B5EA7);padding:32px;text-align:center;">
        <div style="font-size:44px;margin-bottom:8px;">⭐</div>
        <h1 style="color:#fff;font-size:20px;margin:0 0 4px;">Como fue tu experiencia?</h1>
        <p style="color:rgba(255,255,255,0.80);font-size:13px;margin:0;">{negocio_nombre}</p>
      </div>
      <div style="padding:28px 32px;text-align:center;">
        <p style="font-size:15px;color:#333;margin:0 0 20px;">Hola <strong>{nombre}</strong>! Esperamos que tu reservacion haya sido excelente. Tu opinion nos ayuda a mejorar y a que otros clientes nos encuentren.</p>
        <a href="{google_maps_url}" target="_blank"
           style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;box-shadow:0 4px 12px rgba(92,61,143,0.30);margin-bottom:20px;">
          ⭐ Dejar mi resena en Google
        </a>
        <p style="font-size:12px;color:#aaa;margin:0;">Solo toma 30 segundos y significa mucho para nosotros!</p>
      </div>
      <div style="background:#f3eeff;padding:16px 32px;text-align:center;">
        <p style="font-size:12px;color:#888;margin:0;">{negocio_nombre} &bull; {NEGOCIO_DIRECCION}</p>
      </div>
    </div>
    """

    try:
        resend.Emails.send({
            "from": f"{negocio_nombre} <reservaciones@getdrivftllc.com>",
            "to": destinatario,
            "subject": f"Como fue tu experiencia en {negocio_nombre}? ⭐",
            "html": html,
        })
        print(f"[Resena] Solicitud enviada a {destinatario}")
        return True
    except Exception as e:
        print(f"[Resena] Error enviando solicitud: {e}")
        return False


def mandar_sms_recordatorio(destinatario, nombre, fecha, hora, servicio):
    """
    Envia recordatorio SMS via Twilio 24h antes de la cita.
    Se llama desde app.py con threading.Timer(86400).
    """
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_NUM]):
        print("[SMS Recordatorio] Credenciales Twilio no configuradas")
        return False
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        num = destinatario.strip().replace(" ", "").replace("-", "")
        if not num.startswith("+"):
            num = "+" + num
        body = (
            f"Recordatorio: Tienes una cita manana en {NEGOCIO_NOMBRE}\n"
            f"Servicio: {servicio}\n"
            f"Fecha: {fecha}  Hora: {hora}\n"
            "Responde si necesitas cambiar o cancelar."
        )
        client.messages.create(
            body=body,
            from_=f"whatsapp:{TWILIO_NUM}",
            to=f"whatsapp:{num}",
        )
        print(f"[SMS Recordatorio] Enviado a {destinatario}")
        return True
    except Exception as e:
        print(f"[SMS Recordatorio] Error: {e}")
        return False


def mandar_recordatorio_sms(destinatario, nombre, fecha, hora, servicio):
    """
    Envia recordatorio SMS 24h antes de la reservacion usando Twilio.
    """
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_NUM]):
        print("[SMS Recordatorio] Credenciales Twilio no configuradas")
        return False

    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        num = destinatario.strip().replace(" ", "").replace("-", "")
        if not num.startswith("+"):
            num = "+" + num

        body = (
            f"Recordatorio: Tu cita en {NEGOCIO_NOMBRE} es "
            f"HOY a las {hora}\nServicio: {servicio}\n\n"
            "Llama si necesitas cambiar o cancelar."
        )

        client.messages.create(
            body=body,
            from_=f"whatsapp:{TWILIO_NUM}",
            to=f"whatsapp:{num}",
        )
        print(f"[SMS Recordatorio] Recordatorio enviado a {destinatario}")
        return True
    except Exception as e:
        print(f"[SMS Recordatorio] Error: {e}")
        return False


def generar_factura_reservacion_pdf(nombre, servicio, fecha, hora, monto_servicio=0):
    """
    Genera PDF de factura para una reservacion con datos del cliente y servicio.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=24, textColor=colors.HexColor('#5C3D8F'), spaceAfter=4)
    story.append(Paragraph(NEGOCIO_NOMBRE, header_style))
    story.append(Paragraph(NEGOCIO_DIRECCION, styles['Normal']))
    story.append(Paragraph(NEGOCIO_EMAIL, styles['Normal']))
    story.append(Spacer(1, 20))

    # Linea separadora
    story.append(Table([['']], colWidths=[500], rowHeights=[2], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#5C3D8F'))])))
    story.append(Spacer(1, 20))

    # Titulo
    title_style = ParagraphStyle('title', fontSize=18, textColor=colors.HexColor('#1A1A2E'), spaceAfter=20)
    story.append(Paragraph("CONFIRMACION DE RESERVACION", title_style))

    # Info de la reservacion
    fecha_factura = datetime.now().strftime("%B %d, %Y")
    info_data = [
        ['Fecha de Confirmacion:', fecha_factura],
        ['Cliente:', nombre],
        ['Servicio:', servicio],
        ['Fecha de Cita:', fecha],
        ['Hora de Cita:', hora],
    ]
    info_table = Table(info_data, colWidths=[200, 300])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#F5F0FF'), colors.white]),
        ('PADDING', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#5C3D8F')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 30))

    # Detalle de pago
    story.append(Paragraph("Detalle de Pago", ParagraphStyle('sub', fontSize=14, textColor=colors.HexColor('#5C3D8F'), spaceAfter=10)))

    # Mostrar monto de servicio si esta disponible
    deposito = monto_servicio * 0.5 if monto_servicio > 0 else 0  # 50% deposit
    saldo = monto_servicio - deposito

    service_data = [
        ['Descripcion', 'Monto'],
        [f'Servicio: {servicio}', f'${monto_servicio:,.2f}' if monto_servicio > 0 else 'A Determinar'],
    ]

    if monto_servicio > 0:
        service_data.extend([
            [f'Deposito Requerido (50%)', f'${deposito:,.2f}'],
            [f'Saldo Pendiente', f'${saldo:,.2f}'],
        ])

    service_table = Table(service_data, colWidths=[350, 150])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#5C3D8F')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F0FF')]),
        ('PADDING', (0,0), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D1C4E9')),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(service_table)
    story.append(Spacer(1, 20))

    # Footer
    story.append(Spacer(1, 20))
    story.append(Paragraph("Gracias por tu reservacion! Te esperamos.",
                          ParagraphStyle('footer', fontSize=12, textColor=colors.HexColor('#888888'), alignment=1)))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"{NEGOCIO_NOMBRE} &bull; {NEGOCIO_EMAIL}",
                          ParagraphStyle('footer2', fontSize=10, textColor=colors.HexColor('#aaaaaa'), alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer


def enviar_email_con_factura(destinatario, nombre, fecha, hora, servicio, monto_servicio=0):
    """
    Envia email de confirmacion con factura PDF adjunta.
    """
    try:
        pdf_buffer = generar_factura_reservacion_pdf(nombre, servicio, fecha, hora, monto_servicio)

        dt_start = _parse_datetime(fecha, hora)
        dt_end   = dt_start + timedelta(hours=1)

        cal_url  = _google_cal_url(dt_start, dt_end, servicio)
        ics_data = _build_ics(dt_start, dt_end, servicio)
        ics_b64  = base64.b64encode(ics_data).decode()

        deposito = monto_servicio * 0.5 if monto_servicio > 0 else 0
        saldo = monto_servicio - deposito

        # Crear info de pago fuera del f-string para evitar backslashes en expresiones
        pago_info = f'<p style="font-size:13px;color:#555;margin:0 0 16px;"><strong>Informacion de Pago:</strong><br>Deposito (50%): ${deposito:,.2f}<br>Saldo Pendiente: ${saldo:,.2f}</p>' if monto_servicio > 0 else ""

        html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:560px;margin:0 auto;background:#f9f9f9;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">
          <div style="background:linear-gradient(135deg,#5C3D8F,#7B5EA7);padding:36px 32px 28px;text-align:center;">
            <div style="font-size:48px;margin-bottom:8px;">✅</div>
            <h1 style="color:#fff;font-size:22px;margin:0 0 6px;">Reservacion Confirmada</h1>
            <p style="color:rgba(255,255,255,0.85);font-size:14px;margin:0;">{NEGOCIO_NOMBRE}</p>
          </div>
          <div style="padding:28px 32px;">
            <p style="font-size:15px;color:#333;margin:0 0 20px;">Hola <strong>{nombre}</strong>, tu reservacion ha sido confirmada. Aqui estan los detalles:</p>
            <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:24px;">
              <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;width:40%;">Servicio</td><td style="padding:10px 14px;color:#333;">{servicio}</td></tr>
              <tr><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Fecha</td><td style="padding:10px 14px;color:#333;">{fecha}</td></tr>
              <tr style="background:#f3eeff;"><td style="padding:10px 14px;font-weight:600;color:#5C3D8F;">Hora</td><td style="padding:10px 14px;color:#333;">{hora}</td></tr>
            </table>
            {pago_info}
            <div style="text-align:center;margin-bottom:24px;">
              <a href="{cal_url}" target="_blank"
                 style="display:inline-block;padding:13px 28px;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;box-shadow:0 4px 12px rgba(92,61,143,0.30);">
                📅 Agregar a Google Calendar
              </a>
            </div>
            <p style="font-size:12px;color:#aaa;text-align:center;margin:0;">Tu factura esta adjunta en PDF.</p>
          </div>
          <div style="background:#f3eeff;padding:16px 32px;text-align:center;">
            <p style="font-size:12px;color:#888;margin:0;">{NEGOCIO_NOMBRE} &bull; {NEGOCIO_DIRECCION}</p>
          </div>
        </div>
        """

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        import smtplib

        # Prepare PDF attachment
        pdf_data = pdf_buffer.read()

        try:
            resend.Emails.send({
                "from": f"{NEGOCIO_NOMBRE} <reservaciones@getdrivftllc.com>",
                "to": destinatario,
                "subject": f"Reservacion confirmada — {NEGOCIO_NOMBRE}",
                "html": html,
                "attachments": [
                    {
                        "filename": "reservacion_confirmacion.pdf",
                        "content": base64.b64encode(pdf_data).decode(),
                    }
                ],
            })
            print(f"[Email con Factura] Enviado a {destinatario}")
            return True
        except Exception as e:
            print(f"[Email con Factura] Error con Resend: {e}")
            return False

    except Exception as e:
        print(f"[Email con Factura] Error: {e}")
        return False


def generar_reporte_pdf(reservaciones_mes, mes_label):
    """
    Genera PDF del reporte mensual usando ReportLab.
    Incluye: total reservaciones, servicios mas populares,
    ingresos estimados y tasa de cancelacion.
    Retorna BytesIO listo para adjuntar en email.
    """
    from collections import Counter

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────────
    story.append(Paragraph(
        NEGOCIO_NOMBRE,
        ParagraphStyle('rpt_hdr', fontSize=22, textColor=colors.HexColor('#5C3D8F'),
                       spaceAfter=4, fontName='Helvetica-Bold')
    ))
    story.append(Paragraph(
        f"Reporte Mensual — {mes_label}",
        ParagraphStyle('rpt_sub', fontSize=13, textColor=colors.HexColor('#888888'), spaceAfter=2)
    ))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        ParagraphStyle('rpt_gen', fontSize=10, textColor=colors.HexColor('#aaaaaa'), spaceAfter=16)
    ))

    # Línea divisoria
    story.append(Table(
        [['']],
        colWidths=[520], rowHeights=[2],
        style=TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#5C3D8F'))])
    ))
    story.append(Spacer(1, 20))

    # ── Estadísticas ─────────────────────────────────────────
    total      = len(reservaciones_mes)
    ingresos   = total * 8  # $8 por reserva (Pay per Lead)
    canceladas = len([r for r in reservaciones_mes if r.get("estado") == "cancelada"])
    tasa_cx    = (canceladas / total * 100) if total > 0 else 0
    web_cnt    = len([r for r in reservaciones_mes if r.get("canal") == "web"])
    wa_cnt     = len([r for r in reservaciones_mes if r.get("canal") == "whatsapp"])
    serv_cnt   = Counter(r.get("servicio", "") for r in reservaciones_mes if r.get("servicio"))
    top_svc    = serv_cnt.most_common(1)[0] if serv_cnt else ("N/A", 0)

    data = [
        ['Metrica',                             'Valor'],
        ['Total Reservaciones',                  str(total)],
        ['Ingresos Estimados (Pay per Lead)',     f'${ingresos:,}'],
        ['Servicio Mas Popular',                  f'{top_svc[0]}  ({top_svc[1]} reservas)'],
        ['Tasa de Cancelacion',                   f'{canceladas} canceladas  ({tasa_cx:.1f}%)'],
        ['Reservaciones por Web',                 str(web_cnt)],
        ['Reservaciones por WhatsApp',            str(wa_cnt)],
    ]

    resumen = Table(data, colWidths=[340, 180])
    resumen.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1,  0), colors.HexColor('#5C3D8F')),
        ('TEXTCOLOR',      (0, 0), (-1,  0), colors.white),
        ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F0FF')]),
        ('PADDING',        (0, 0), (-1, -1), 10),
        ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#D1C4E9')),
        ('ALIGN',          (1, 0), ( 1, -1), 'CENTER'),
        ('FONTNAME',       (0, 1), ( 0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR',      (0, 1), ( 0, -1), colors.HexColor('#3D2560')),
    ]))
    story.append(resumen)
    story.append(Spacer(1, 30))

    # ── Top servicios ────────────────────────────────────────
    if serv_cnt:
        story.append(Paragraph(
            "Top Servicios del Mes",
            ParagraphStyle('sec_tit', fontSize=14, textColor=colors.HexColor('#5C3D8F'),
                           spaceAfter=10, fontName='Helvetica-Bold')
        ))
        svc_data = [['Servicio', 'Reservaciones']] + [
            [svc, str(cnt)] for svc, cnt in serv_cnt.most_common(5)
        ]
        svc_table = Table(svc_data, colWidths=[380, 140])
        svc_table.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), colors.HexColor('#3D2560')),
            ('TEXTCOLOR',      (0, 0), (-1,  0), colors.white),
            ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
            ('FONTSIZE',       (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F0FF')]),
            ('PADDING',        (0, 0), (-1, -1), 9),
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#D1C4E9')),
            ('ALIGN',          (1, 0), ( 1, -1), 'CENTER'),
        ]))
        story.append(svc_table)
        story.append(Spacer(1, 20))

    # ── Footer ───────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        f"{NEGOCIO_NOMBRE}  |  Reporte generado automaticamente el 1ro de cada mes",
        ParagraphStyle('rpt_foot', fontSize=9, textColor=colors.HexColor('#aaaaaa'), alignment=1)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def enviar_reporte_mensual(destinatario_email):
    """
    Envia reporte mensual con estadisticas de reservaciones al dueno.
    Se ejecuta el 1ro de cada mes a las 8am.
    """
    from collections import Counter

    try:
        # Cargar reservaciones
        archivo_reservaciones = "reservaciones.json"
        if not os.path.exists(archivo_reservaciones):
            print("[Reporte] Archivo de reservaciones no encontrado")
            return False

        with open(archivo_reservaciones, "r", encoding="utf-8") as f:
            reservaciones = json.load(f)

        # Filtrar por mes anterior
        hoy = datetime.now()
        mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        reservas_mes = [r for r in reservaciones if r.get("fecha", "").startswith(mes_anterior)]

        # Calcular estadisticas
        total_reservas = len(reservas_mes)
        ingresos_totales = total_reservas * 8  # $8 por reserva (Pay per Lead)

        # Servicio mas popular
        serv_cnt = Counter(r.get("servicio", "") for r in reservas_mes if r.get("servicio"))
        servicio_popular = serv_cnt.most_common(1)[0] if serv_cnt else ("N/A", 0)

        # Tasa de cancelacion
        canceladas = len([r for r in reservas_mes if r.get("estado") == "cancelada"])
        tasa_cancelacion = (canceladas / total_reservas * 100) if total_reservas > 0 else 0

        # Canales
        web_count = len([r for r in reservas_mes if r.get("canal") == "web"])
        whatsapp_count = len([r for r in reservas_mes if r.get("canal") == "whatsapp"])

        mes_label = hoy.strftime("%B %Y")

        html = f"""
        <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:620px;margin:0 auto;background:#f9f9f9;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">
          <div style="background:linear-gradient(135deg,#3D2560,#5C3D8F);padding:40px 32px;text-align:center;">
            <div style="font-size:48px;margin-bottom:8px;">📊</div>
            <h1 style="color:#fff;font-size:26px;margin:0 0 4px;">Reporte Mensual</h1>
            <p style="color:rgba(255,255,255,0.85);font-size:14px;margin:0;">{mes_label}</p>
          </div>
          <div style="padding:40px 32px;">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:32px;">
              <div style="background:#f3eeff;border-radius:12px;padding:24px;text-align:center;border-left:4px solid #5C3D8F;">
                <div style="font-size:32px;color:#5C3D8F;font-weight:bold;margin-bottom:4px;">{total_reservas}</div>
                <div style="font-size:13px;color:#666;">Total de Reservaciones</div>
              </div>
              <div style="background:#f3eeff;border-radius:12px;padding:24px;text-align:center;border-left:4px solid #5C3D8F;">
                <div style="font-size:32px;color:#5C3D8F;font-weight:bold;margin-bottom:4px;">${ingresos_totales:,}</div>
                <div style="font-size:13px;color:#666;">Ingresos Totales</div>
              </div>
            </div>

            <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:32px;">
              <tr style="background:#f3eeff;"><td style="padding:12px 14px;font-weight:600;color:#5C3D8F;">Metrica</td><td style="padding:12px 14px;font-weight:600;color:#5C3D8F;text-align:right;">Valor</td></tr>
              <tr style="border-bottom:1px solid #e0e0e0;"><td style="padding:12px 14px;color:#333;">Servicio Mas Popular</td><td style="padding:12px 14px;color:#333;text-align:right;font-weight:500;">{servicio_popular[0]} ({servicio_popular[1]} reservas)</td></tr>
              <tr style="background:#f3eeff;border-bottom:1px solid #e0e0e0;"><td style="padding:12px 14px;color:#333;">Tasa de Cancelacion</td><td style="padding:12px 14px;color:#333;text-align:right;font-weight:500;">{tasa_cancelacion:.1f}% ({canceladas} de {total_reservas})</td></tr>
              <tr style="border-bottom:1px solid #e0e0e0;"><td style="padding:12px 14px;color:#333;">Reservaciones por Web</td><td style="padding:12px 14px;color:#333;text-align:right;font-weight:500;">{web_count} (🌐)</td></tr>
              <tr style="background:#f3eeff;"><td style="padding:12px 14px;color:#333;">Reservaciones por WhatsApp</td><td style="padding:12px 14px;color:#333;text-align:right;font-weight:500;">{whatsapp_count} (📱)</td></tr>
            </table>

            <p style="font-size:13px;color:#666;margin:0;text-align:center;">Este reporte se genera automaticamente el 1ro de cada mes.</p>
          </div>
          <div style="background:#f3eeff;padding:16px 32px;text-align:center;">
            <p style="font-size:12px;color:#888;margin:0;">{NEGOCIO_NOMBRE} &bull; Reservaciones</p>
          </div>
        </div>
        """

        # Generar PDF adjunto con generar_reporte_pdf()
        pdf_buffer = generar_reporte_pdf(reservas_mes, mes_label)
        pdf_b64 = base64.b64encode(pdf_buffer.read()).decode()

        resend.Emails.send({
            "from": f"{NEGOCIO_NOMBRE} <reservaciones@getdrivftllc.com>",
            "to": destinatario_email,
            "subject": f"📊 Reporte Mensual — {mes_label}",
            "html": html,
            "attachments": [
                {
                    "filename": f"reporte_{mes_anterior}.pdf",
                    "content": pdf_b64,
                }
            ],
        })

        print(f"[Reporte Mensual] Enviado a {destinatario_email}")
        return True

    except Exception as e:
        print(f"[Reporte Mensual] Error: {e}")
        return False
