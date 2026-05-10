import os
import base64
import uuid
from datetime import datetime, timedelta

import resend
from twilio.rest import Client
from icalendar import Calendar, Event

from cliente_config import NEGOCIO_NOMBRE, NEGOCIO_DIRECCION, NEGOCIO_EMAIL

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUM   = os.environ.get("TWILIO_WHATSAPP_NUM")
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
