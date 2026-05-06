import os
import resend
from twilio.rest import Client

TWILIO_SID   = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_NUM   = os.environ.get("TWILIO_WHATSAPP_NUM")
RESEND_KEY   = os.environ.get("RESEND_API_KEY")

resend.api_key = RESEND_KEY

def mandar_email(destinatario, nombre, fecha, hora, servicio):
    try:
        resend.Emails.send({
            "from": "Drivft Reservaciones <reservaciones@getdrivftllc.com>",
            "to": destinatario,
            "subject": "Tu reservacion esta confirmada",
            "html": f"""
            <h2>Hola {nombre}!</h2>
            <p>Tu reservacion ha sido confirmada:</p>
            <ul>
                <li><strong>Fecha:</strong> {fecha}</li>
                <li><strong>Hora:</strong> {hora}</li>
                <li><strong>Servicio:</strong> {servicio}</li>
            </ul>
            <p>Si necesitas cancelar responde este email.</p>
            <p>Te esperamos!</p>
            """
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