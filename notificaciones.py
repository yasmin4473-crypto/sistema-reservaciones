import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from config import TWILIO_SID, TWILIO_TOKEN, TWILIO_NUM, GMAIL_USER, GMAIL_PASS

def mandar_email(destinatario, nombre, fecha, hora, servicio):
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = destinatario
        msg["Subject"] = "Tu reservacion esta confirmada"

        cuerpo = f"""
Hola {nombre},

Tu reservacion ha sido confirmada:

Fecha:    {fecha}
Hora:     {hora}
Servicio: {servicio}

Si necesitas cancelar responde este email.

Te esperamos!
        """

        msg.attach(MIMEText(cuerpo, "plain"))
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(GMAIL_USER, GMAIL_PASS)
        servidor.send_message(msg)
        servidor.quit()
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