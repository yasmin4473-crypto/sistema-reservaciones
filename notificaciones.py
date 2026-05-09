import os
import base64
import uuid
from datetime import datetime, timedelta

import resend
from twilio.rest import Client
from icalendar import Calendar, Event

from cliente_config import NEGOCIO_NOMBRE, NEGOCIO_DIRECCION

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
    # Último recurso: solo la fecha sin hora
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
    Genera los bytes de un archivo .ics usando la librería icalendar.
    Campos: título, fecha/hora de inicio, duración 1 hora, servicio y dirección.
    """
    cal = Calendar()
    cal.add("PRODID", "-//Drivft LLC//Reservaciones//ES")
    cal.add("VERSION", "2.0")
    cal.add("CALSCALE", "GREGORIAN")
    cal.add("METHOD", "REQUEST")

    event = Event()
    event.add("SUMMARY",     f"Reservacion en {NEGOCIO_NOMBRE}")
    event.add("DTSTART",     dt_start)
    event.add("DTEND",       dt_end)
    event.add("DESCRIPTION", f"Servicio: {servicio}")
    event.add("LOCATION",    NEGOCIO_DIRECCION)
    event.add("UID",         str(uuid.uuid4()))

    cal.add_component(event)
    return cal.to_ical()


def mandar_email(destinatario, nombre, fecha, hora, servicio):
    try:
        # ── Parsear fecha/hora ──────────────────────────────────────
        dt_start = _parse_datetime(fecha, hora)
        dt_end   = dt_start + timedelta(hours=1)

        # ── Google Calendar URL ─────────────────────────────────────
        cal_url = _google_cal_url(dt_start, dt_end, servicio)

        # ── Archivo .ics en memoria (base64 para Resend) ────────────
        ics_bytes = _build_ics(dt_start, dt_end, servicio)
        ics_b64   = base64.b64encode(ics_bytes).decode("utf-8")

        # ── HTML del email ──────────────────────────────────────────
        html = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08)">

          <!-- Header -->
          <div style="background:linear-gradient(135deg,#5C3D8F,#7C3AED);padding:32px 36px;text-align:center">
            <p style="font-size:40px;margin:0 0 12px">🗓️</p>
            <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:0 0 6px">Reservacion Confirmada</h1>
            <p style="color:rgba(255,255,255,0.8);font-size:14px;margin:0">{NEGOCIO_NOMBRE}</p>
          </div>

          <!-- Body -->
          <div style="padding:32px 36px">
            <p style="font-size:16px;color:#1a1a2e;margin:0 0 24px">
              Hola <strong>{nombre}</strong>, tu reservacion ha sido confirmada:
            </p>

            <!-- Tabla de detalles -->
            <table style="width:100%;border-collapse:collapse;border-radius:10px;overflow:hidden;margin-bottom:28px">
              <tr style="background:#f5f3ff">
                <td style="padding:13px 18px;font-size:12px;font-weight:700;color:#5C3D8F;text-transform:uppercase;letter-spacing:1px;width:36%">Fecha</td>
                <td style="padding:13px 18px;font-size:14px;color:#1a1a2e">{fecha}</td>
              </tr>
              <tr>
                <td style="padding:13px 18px;font-size:12px;font-weight:700;color:#5C3D8F;text-transform:uppercase;letter-spacing:1px">Hora</td>
                <td style="padding:13px 18px;font-size:14px;color:#1a1a2e">{hora}</td>
              </tr>
              <tr style="background:#f5f3ff">
                <td style="padding:13px 18px;font-size:12px;font-weight:700;color:#5C3D8F;text-transform:uppercase;letter-spacing:1px">Servicio</td>
                <td style="padding:13px 18px;font-size:14px;color:#1a1a2e">{servicio}</td>
              </tr>
              <tr>
                <td style="padding:13px 18px;font-size:12px;font-weight:700;color:#5C3D8F;text-transform:uppercase;letter-spacing:1px">Ubicacion</td>
                <td style="padding:13px 18px;font-size:14px;color:#1a1a2e">{NEGOCIO_DIRECCION}</td>
              </tr>
            </table>

            <!-- Botón Google Calendar -->
            <table style="width:100%;border-collapse:collapse;margin-bottom:28px">
              <tr>
                <td align="center">
                  <a href="{cal_url}" target="_blank"
                     style="display:inline-block;background:#4285F4;color:#ffffff;font-size:14px;font-weight:600;text-decoration:none;padding:13px 28px;border-radius:8px;letter-spacing:0.2px">
                    📅 Agregar a Google Calendar
                  </a>
                </td>
              </tr>
              <tr>
                <td align="center" style="padding-top:10px;font-size:12px;color:#9d8ec4">
                  También adjuntamos un archivo .ics para Outlook, Apple Calendar u otro.
                </td>
              </tr>
            </table>

            <p style="font-size:14px;color:#718096;line-height:1.6;margin:0 0 8px">
              Si necesitas cancelar o hacer cambios, responde este email.
            </p>
            <p style="font-size:15px;color:#1a1a2e;font-weight:600;margin:0">¡Te esperamos! 🙌</p>
          </div>

          <!-- Footer -->
          <div style="background:#f9f7ff;padding:20px 36px;text-align:center;border-top:1px solid #e9e3ff">
            <p style="font-size:12px;color:#9d8ec4;margin:0">
              {NEGOCIO_NOMBRE} · {NEGOCIO_DIRECCION}
            </p>
          </div>

        </div>
        """

        resend.Emails.send({
            "from": f"{NEGOCIO_NOMBRE} <reservaciones@getdrivftllc.com>",
            "to": destinatario,
            "subject": f"✅ Reservacion confirmada — {fecha} {hora}",
            "html": html,
            "attachments": [
                {
                    "filename": "reservacion.ics",
                    "content": ics_b64,
                }
            ],
        })
        print(f"Email enviado a {destinatario}")
        return True

    except Exception as e:
        print(f"Error enviando email: {e}")
        return False


def mandar_whatsapp(numero_cliente, nombre, fecha, hora, servicio):
    try:
        cliente = Client(TWILIO_SID, TWILIO_TOKEN)
        mensaje = cliente.messages.create(
            from_=TWILIO_NUM,
            to=f"whatsapp:+1{numero_cliente}",
            body=f"Hola {nombre}, tu reservacion esta confirmada!\n\nFecha: {fecha}\nHora: {hora}\nServicio: {servicio}\n\nSi necesitas cambiarla respondenos."
        )
        print(f"WhatsApp enviado a {numero_cliente}")
        return True
    except Exception as e:
        print(f"Error enviando WhatsApp: {e}")
        return False
