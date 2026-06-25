from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify, session, redirect, url_for, make_response
from flask_cors import CORS
from notificaciones import (
    mandar_email, mandar_whatsapp, mandar_solicitud_resena, notificar_dueno,
    mandar_recordatorio_sms, mandar_sms_recordatorio,
    enviar_email_con_factura, enviar_reporte_mensual,
    mandar_sms_confirmacion,
)
from cliente_config import (
    NEGOCIO_NOMBRE, NEGOCIO_SLOGAN, NEGOCIO_EMOJI,
    NEGOCIO_TELEFONO, NEGOCIO_EMAIL, NEGOCIO_DIRECCION, NEGOCIO_WHATSAPP,
    COLOR_PRIMARIO, COLOR_SECUNDARIO,
    COLOR_FONDO_INICIO, COLOR_FONDO_FIN,
    SERVICIOS, SERVICIOS_EMOJIS, SERVICIOS_DESCRIPCIONES,
    HORAS_DISPONIBLES,
    SOBRE_NOSOTROS_TITULO, SOBRE_NOSOTROS_TEXTO, STATS,
    FOTO_HERO, FOTO_NOSOTROS, FOTOS_GALERIA,
    GOOGLE_MAPS_EMBED,
    FAQ, CHATBOT_BIENVENIDA_ES, CHATBOT_BIENVENIDA_EN,
    CHATBOT_NO_ENTIENDO_ES, CHATBOT_NO_ENTIENDO_EN,
    GOOGLE_MAPS_REVIEW_URL,
)
import json, os, threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

_EASTERN = ZoneInfo("America/New_York")
import stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def generar_factura_pdf(nombre, email, paquete, monto, numero_factura):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle('header', fontSize=24, textColor=colors.HexColor('#5C3D8F'), spaceAfter=4)
    story.append(Paragraph("DRIVFT LLC", header_style))
    story.append(Paragraph("Digital Services & Automation Agency", styles['Normal']))
    story.append(Paragraph("contact@getdrivftllc.com | getdrivftllc.com", styles['Normal']))
    story.append(Spacer(1, 20))

    # Linea separadora
    story.append(Table([['']], colWidths=[500], rowHeights=[2], style=TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#5C3D8F'))])))
    story.append(Spacer(1, 20))

    # Titulo
    title_style = ParagraphStyle('title', fontSize=18, textColor=colors.HexColor('#1A1A2E'), spaceAfter=20)
    story.append(Paragraph("INVOICE / FACTURA", title_style))

    # Info de la factura
    from datetime import datetime
    fecha = datetime.now().strftime("%B %d, %Y")
    info_data = [
        ['Invoice Number / Numero:', f'#{numero_factura}'],
        ['Date / Fecha:', fecha],
        ['Client / Cliente:', nombre],
        ['Email:', email],
        ['Package / Paquete:', paquete.title()],
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

    # Detalle del servicio
    story.append(Paragraph("Services / Servicios", ParagraphStyle('sub', fontSize=14, textColor=colors.HexColor('#5C3D8F'), spaceAfter=10)))
    
    precios = {
        "basic": {"setup": 500, "mensual": 175, "desc": "Booking system + Dashboard + Email + Chatbot"},
        "standard": {"setup": 900, "mensual": 275, "desc": "Basic + WhatsApp + SMS + Monthly Reports"},
        "professional": {"setup": 2000, "mensual": 350, "desc": "Standard + Website + Google Reviews + Domain"},
    }
    p = precios.get(paquete, precios["basic"])

    service_data = [
        ['Description', 'Amount'],
        [f"{paquete.title()} Package - Setup Fee\n{p['desc']}", f"${monto:,.2f}"],
        [f"Monthly maintenance (starting next month)", f"${p['mensual']}/mo"],
    ]
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

    # Total
    total_data = [['TOTAL PAID / TOTAL PAGADO', f'${monto:,.2f}']]
    total_table = Table(total_data, colWidths=[350, 150])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#5C3D8F')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 13),
        ('PADDING', (0,0), (-1,-1), 12),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 40))

    # Footer
    story.append(Paragraph("Thank you for your business! / Gracias por su preferencia!", ParagraphStyle('footer', fontSize=12, textColor=colors.HexColor('#888888'), alignment=1)))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Drivft LLC | contact@getdrivftllc.com | getdrivftllc.com", ParagraphStyle('footer2', fontSize=10, textColor=colors.HexColor('#aaaaaa'), alignment=1)))

    doc.build(story)
    buffer.seek(0)
    return buffer


def enviar_factura_email(nombre, email_cliente, paquete, monto, numero_factura):
    try:
        pdf_buffer = generar_factura_pdf(nombre, email_cliente, paquete, monto, numero_factura)
        
        msg = MIMEMultipart()
        msg['From'] = os.environ.get("GMAIL_USER")
        msg['To'] = email_cliente
        msg['Subject'] = f"Invoice #{numero_factura} — Drivft LLC"
        
        cuerpo = f"""
Hola {nombre},

Gracias por elegir Drivft LLC! Tu pago fue procesado exitosamente.

Paquete: {paquete.title()}
Monto: ${monto:,.2f}
Factura: #{numero_factura}

Adjunto encontraras tu factura en PDF. Nos pondremos en contacto contigo en menos de 24 horas para comenzar tu proyecto.

Drivft LLC
contact@getdrivftllc.com
        """
        msg.attach(MIMEText(cuerpo, 'plain'))
        
        pdf_attachment = MIMEBase('application', 'pdf')
        pdf_attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(pdf_attachment)
        pdf_attachment.add_header('Content-Disposition', f'attachment; filename=Drivft_Invoice_{numero_factura}.pdf')
        msg.attach(pdf_attachment)
        
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(os.environ.get("GMAIL_USER"), os.environ.get("GMAIL_PASSWORD"))
        servidor.send_message(msg)
        servidor.quit()
        print(f"Factura enviada a {email_cliente}")
        return True
    except Exception as e:
        print(f"Error enviando factura: {e}")
        return False

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("SECRET_KEY", "drivft-dev-secret-2026")

ARCHIVO          = "reservaciones.json"
CLIENTES_ARCHIVO = "clientes.json"
_reservaciones_lock = threading.Lock()  # guards all read-modify-write on reservaciones.json


def _programar_reporte_mensual():
    """
    Programa el reporte mensual para ejecutarse el 1ro de cada mes a las 8am.
    """
    def _ejecutar_reporte():
        try:
            destinatario = os.environ.get("GMAIL_USER") or NEGOCIO_EMAIL
            if destinatario:
                enviar_reporte_mensual(destinatario)
        except Exception as e:
            print(f"[Reporte Programado] Error: {e}")

        # Reprogramar para el proximo mes
        _programar_reporte_mensual()

    ahora = datetime.now()

    # Siguiente dia 1 del mes
    if ahora.month == 12:
        proximo_mes = ahora.replace(year=ahora.year + 1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
    else:
        proximo_mes = ahora.replace(month=ahora.month + 1, day=1, hour=8, minute=0, second=0, microsecond=0)

    # Si ya paso hoy las 8am del 1ro, programar para el proximo mes
    if ahora.day == 1 and ahora.hour >= 8:
        if ahora.month == 12:
            proximo_mes = ahora.replace(year=ahora.year + 1, month=1, day=1, hour=8, minute=0, second=0, microsecond=0)
        else:
            proximo_mes = ahora.replace(month=ahora.month + 1, day=1, hour=8, minute=0, second=0, microsecond=0)

    delay = (proximo_mes - ahora).total_seconds()

    if delay > 0:
        print(f"[Reporte Mensual] Programado para {proximo_mes.strftime('%Y-%m-%d %H:%M:%S')} (en {delay:.0f}s)")
        t = threading.Timer(delay, _ejecutar_reporte)
        t.daemon = True
        t.start()


def cargar_clientes():
    if not os.path.exists(CLIENTES_ARCHIVO):
        return []
    with open(CLIENTES_ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_clientes(lista):
    with open(CLIENTES_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)


def _login_ok():
    """Devuelve True si la sesión actual está autenticada (panel cliente)."""
    return session.get("autenticado") is True


def _admin_ok():
    """Devuelve True si la sesión admin está autenticada."""
    return session.get("admin_autenticado") is True


def cargar():
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar(lista):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)


def _render_index():
    """Lee index.html e inyecta los valores de cliente_config.py."""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    opciones_servicios = "\n".join(
        f'        <option value="{s}">{s}</option>' for s in SERVICIOS
    )
    opciones_horas = "\n".join(
        f'        <option>{h}</option>' for h in HORAS_DISPONIBLES
    )

    reemplazos = {
        "{{NEGOCIO_NOMBRE}}":     NEGOCIO_NOMBRE,
        "{{NEGOCIO_SLOGAN}}":     NEGOCIO_SLOGAN,
        "{{NEGOCIO_EMOJI}}":      NEGOCIO_EMOJI,
        "{{NEGOCIO_TELEFONO}}":   NEGOCIO_TELEFONO,
        "{{NEGOCIO_DIRECCION}}":  NEGOCIO_DIRECCION,
        "{{COLOR_PRIMARIO}}":     COLOR_PRIMARIO,
        "{{COLOR_SECUNDARIO}}":   COLOR_SECUNDARIO,
        "{{COLOR_FONDO_INICIO}}": COLOR_FONDO_INICIO,
        "{{COLOR_FONDO_FIN}}":    COLOR_FONDO_FIN,
        "{{SERVICIOS_OPTIONS}}":     opciones_servicios,
        "{{HORAS_OPTIONS}}":         opciones_horas,
        "{{CHATBOT_BIENVENIDA_ES}}": CHATBOT_BIENVENIDA_ES,
        # Markers que antes aparecían visibles en pantalla
        "{{SECCION_RESERVA}}":    "Tu reservación",
        "{{LABEL_SERVICIO}}":     "Servicio",
        "{{BTN_RESERVAR}}":       "Reservar",
        "{{SERVICIO_EJEMPLO}}":   SERVICIOS[0] if SERVICIOS else "Servicio",
        "{{TEXTO_EXITO}}":        "¡Reservación confirmada!",
        # Stripe / depósito
        "{{STRIPE_PUBLIC_KEY}}":  os.environ.get("STRIPE_PUBLIC_KEY", ""),
        "{{DEPOSITO_MONTO}}":     "25",
    }

    for marcador, valor in reemplazos.items():
        html = html.replace(marcador, valor)

    # Diagnóstico: detectar markers que quedaron sin reemplazar
    import re as _re
    sin_reemplazar = _re.findall(r'\{\{[A-Z_]+\}\}', html)
    if sin_reemplazar:
        print(f"[render_index] ⚠️  Markers sin reemplazar: {sin_reemplazar}")
    else:
        print("[render_index] ✅ Todos los markers reemplazados OK (v2)")

    response = make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def _render_web():
    """Lee web.html e inyecta todos los valores de cliente_config.py."""
    with open("web.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Hero: foto real o gradiente de color si no hay URL
    if FOTO_HERO:
        hero_bg = f"linear-gradient(rgba(0,0,0,0.55), rgba(0,0,0,0.70)), url('{FOTO_HERO}') center/cover"
    else:
        hero_bg = f"linear-gradient(135deg, {COLOR_PRIMARIO} 0%, {COLOR_SECUNDARIO} 100%)"

    # Nosotros: foto real o gradiente suave de fondo
    if FOTO_NOSOTROS:
        nosotros_bg = f"url('{FOTO_NOSOTROS}') center/cover"
    else:
        nosotros_bg = f"linear-gradient(135deg, {COLOR_PRIMARIO}22, {COLOR_SECUNDARIO}44)"

    # Cards de servicios
    emojis = SERVICIOS_EMOJIS + ["⭐"] * len(SERVICIOS)
    descs  = SERVICIOS_DESCRIPCIONES + [""] * len(SERVICIOS)
    servicios_cards = "\n".join(
        f"""      <div class="service-card">
        <span class="service-icon">{emojis[i]}</span>
        <h3>{s}</h3>
        <p>{descs[i]}</p>
      </div>"""
        for i, s in enumerate(SERVICIOS)
    )

    # Galería: fotos reales o placeholders de gradiente
    _paleta = ["#E8D5F5", "#D5E8F5", "#F5E8D5", "#D5F5E8", "#F5D5E8", "#E8F5D5"]
    if FOTOS_GALERIA:
        galeria_html = "\n".join(
            f'      <div class="gallery-item"><img src="{url}" alt="Galería {i+1}" loading="lazy"></div>'
            for i, url in enumerate(FOTOS_GALERIA)
        )
    else:
        galeria_html = "\n".join(
            f'      <div class="gallery-item"><div class="gallery-placeholder" style="background:{_paleta[i%6]}">{NEGOCIO_EMOJI}</div></div>'
            for i in range(6)
        )

    # Stats de Sobre Nosotros
    stats_html = "\n".join(
        f'        <div class="about-stat"><span>{num}</span><p>{label}</p></div>'
        for num, label in STATS
    )

    reemplazos = {
        "{{NEGOCIO_NOMBRE}}":         NEGOCIO_NOMBRE,
        "{{NEGOCIO_SLOGAN}}":         NEGOCIO_SLOGAN,
        "{{NEGOCIO_EMOJI}}":          NEGOCIO_EMOJI,
        "{{NEGOCIO_TELEFONO}}":       NEGOCIO_TELEFONO,
        "{{NEGOCIO_EMAIL}}":          NEGOCIO_EMAIL,
        "{{NEGOCIO_DIRECCION}}":      NEGOCIO_DIRECCION,
        "{{NEGOCIO_WHATSAPP}}":       NEGOCIO_WHATSAPP,
        "{{COLOR_PRIMARIO}}":         COLOR_PRIMARIO,
        "{{COLOR_SECUNDARIO}}":       COLOR_SECUNDARIO,
        "{{HERO_BG_IMAGE}}":          hero_bg,
        "{{NOSOTROS_BG_STYLE}}":      nosotros_bg,
        "{{SOBRE_NOSOTROS_TITULO}}":  SOBRE_NOSOTROS_TITULO,
        "{{SOBRE_NOSOTROS_TEXTO}}":   SOBRE_NOSOTROS_TEXTO,
        "{{SERVICIOS_CARDS}}":        servicios_cards,
        "{{GALERIA_FOTOS}}":          galeria_html,
        "{{STATS_HTML}}":             stats_html,
        "{{GOOGLE_MAPS_EMBED}}":      GOOGLE_MAPS_EMBED,
        "{{CHATBOT_BIENVENIDA_ES}}":  CHATBOT_BIENVENIDA_ES,
    }

    for marcador, valor in reemplazos.items():
        html = html.replace(marcador, valor)

    response = make_response(html)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route("/web")
def web():
    return _render_web()


def _render_landing():
    """Sirve landing.html (página principal Drivft) sin caché."""
    with open("landing.html", "r", encoding="utf-8") as f:
        html = f.read()
    response = make_response(html)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route("/landing")
def landing():
    return _render_landing()


@app.route("/demo")
def demo():
    return _render_index()


@app.route("/")
def inicio():
    return _render_index()


# ─── DEPÓSITO OPCIONAL (Stripe) ──────────────────────────
@app.route("/crear-deposito", methods=["POST"])
def crear_deposito():
    try:
        datos  = request.json or {}
        intent = stripe.PaymentIntent.create(
            amount=2500,   # $25.00 USD
            currency="usd",
            metadata={
                "cliente":  datos.get("nombre", ""),
                "email":    datos.get("email", ""),
                "servicio": datos.get("servicio", ""),
            }
        )
        return jsonify({"client_secret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── RUTA 1: Formulario web ───────────────────────────────
@app.route("/reservar", methods=["POST"])
def reservar():
    datos = request.json
    datos["id"]     = datetime.now().strftime("%Y%m%d%H%M%S")
    datos["estado"] = "confirmada"
    datos["creada"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    datos["canal"]  = "web"

    with _reservaciones_lock:
        reservaciones = cargar()
        reservaciones.append(datos)
        guardar(reservaciones)
        print(f"[/reservar] Guardadas {len(reservaciones)} reservaciones en disco.")

    # ── Notificación instantánea al dueño ───────────────────────
    notificar_dueno(datos["nombre"], datos["fecha"], datos["hora"], datos["servicio"], "web")

    # ── SMS de confirmacion inmediata al cliente ─────────────────
    if datos.get("telefono"):
        mandar_sms_confirmacion(
            datos["telefono"], datos["nombre"],
            datos["fecha"], datos["hora"], datos["servicio"]
        )

    if datos.get("email"):
        # ── Email de confirmacion con factura PDF ─────────────────
        enviar_email_con_factura(
            datos["email"],
            datos["nombre"],
            datos["fecha"],
            datos["hora"],
            datos["servicio"]
        )

        # ── Solicitud de reseña 24 h después ────────────────────────
        if GOOGLE_MAPS_REVIEW_URL:
            t = threading.Timer(
                86400,
                mandar_solicitud_resena,
                args=[datos["email"], datos["nombre"], NEGOCIO_NOMBRE, GOOGLE_MAPS_REVIEW_URL],
            )
            t.daemon = True
            t.start()
            print(f"[Reseña] Timer 24h programado para {datos['email']}")

    if datos.get("telefono"):
        mandar_whatsapp(datos["telefono"], datos["nombre"], datos["fecha"], datos["hora"], datos["servicio"])

        # ── SMS Recordatorio 24h después de la reservación ─────────
        t_sms = threading.Timer(
            86400,
            mandar_sms_recordatorio,
            args=[datos["telefono"], datos["nombre"], datos["fecha"], datos["hora"], datos["servicio"]]
        )
        t_sms.daemon = True
        t_sms.start()
        print(f"[SMS Recordatorio] Timer 24h programado para {datos['telefono']}")

    print(f"✅ Nueva reservación: {datos['nombre']} — {datos['fecha']} {datos['hora']}")
    return jsonify({"ok": True})


# ─── AI BOOKING ENGINE ───────────────────────────────────
# Per-number state: { numero: { nombre, fecha, hora, servicio, pendiente_confirmacion } }
_booking_state: dict = {}

_BOOKING_SYSTEM_PROMPT = f"""You are a friendly booking assistant for {NEGOCIO_NOMBRE} — {NEGOCIO_SLOGAN}.

{{DATE_CONTEXT}}
Available services: {", ".join(SERVICIOS)}
Available time slots: {", ".join(HORAS_DISPONIBLES)}

Your job is to collect 4 pieces of information to book an appointment:
  1. Client name
  2. Date (convert relative dates like "tomorrow", "next Monday", "mañana" to YYYY-MM-DD)
  3. Time (match to one of the available slots above)
  4. Service (match to one of the available services above)

Rules:
- CRITICAL: Once you have determined the user's language from ANY message in the conversation, continue responding in that SAME language for the rest of the conversation, even if later messages are short or ambiguous (like a single word). Do not switch languages mid-conversation unless the user clearly switches first. If the user writes in English, respond in English. If in Spanish, respond in Spanish. Do not default to Spanish.
- Ask for missing fields one at a time in a natural, friendly way.
- When you have all 4 fields, summarize and ask for confirmation. Example:
  "Perfecto! Tu cita queda así:\n👤 {'{nombre}'}\n📅 {'{fecha}'}\n⏰ {'{hora}'}\n💆 {'{servicio}'}\n\n¿Confirmas? (sí / no)"
- ONLY output a JSON block when the user has confirmed. Format (nothing else, no prose):
  BOOKING_JSON:{{"nombre":"{'{nombre}'}", "fecha":"YYYY-MM-DD", "hora":"{'{hora}'}", "servicio":"{'{servicio}'}"}}.
- If the user says something off-topic, answer briefly then bring them back to booking.
- Keep replies concise (under 280 chars for SMS friendliness).
- For greetings like "hola" or "hi", give a warm welcome and ask how you can help.
- SERVICE NAMES: When referring to services in conversation and in BOOKING_JSON, translate or describe them naturally in the user's language. Do NOT repeat the raw Spanish service name to an English-speaking user (e.g. "Bot de WhatsApp" → "WhatsApp Bot", "Pagina Web Profesional" → "Professional Website", "Sistema de Reservaciones" → "Booking System", "Chatbot con IA" → "AI Chatbot").
"""


def _detect_lang(text: str):
    """
    Heuristic language detector for booking conversations.
    Returns 'en', 'es', or None if the signal is too weak to decide.
    """
    es_chars = sum(1 for c in text if c in "áéíóúñÁÉÍÓÚÑ¿¡")
    words = set(text.lower().split())
    _es = {"hola", "cita", "quiero", "necesito", "para", "una", "reserva",
           "gracias", "buenos", "buenas", "servicio", "mañana", "fecha",
           "hora", "nombre", "también", "cómo", "tengo", "quisiera", "bueno"}
    _en = {"hello", "hi", "hey", "want", "need", "book", "appointment",
           "schedule", "please", "thanks", "thank", "tomorrow", "yes",
           "the", "my", "would", "like", "when", "what", "how", "i", "can"}
    score_es = es_chars * 2 + len(words & _es)
    score_en = len(words & _en)
    if score_es > score_en:
        return "es"
    if score_en > score_es:
        return "en"
    return None

def _call_openrouter(messages: list) -> str:
    """Call OpenRouter and return the assistant reply text, or '' on failure."""
    if not _OPENROUTER_API_KEY:
        return ""
    payload = json.dumps({
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.4,
    }).encode("utf-8")
    try:
        req = _urllib_req.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {_OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://getdrivftllc.com",
                "X-Title": NEGOCIO_NOMBRE,
            },
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[AI Booking] OpenRouter error: {e}")
        return ""


def _save_booking(nombre, fecha, hora, servicio, telefono, canal, idioma="es"):
    """Persist booking and trigger all notifications. Returns the saved record."""
    nueva = {
        "id":       datetime.now().strftime("%Y%m%d%H%M%S"),
        "nombre":   nombre,
        "email":    "",
        "telefono": telefono,
        "fecha":    fecha,
        "hora":     hora,
        "servicio": servicio,
        "estado":   "confirmada",
        "creada":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "canal":    canal,
    }
    with _reservaciones_lock:
        reservaciones = cargar()
        reservaciones.append(nueva)
        guardar(reservaciones)
        print(f"[_save_booking] Guardadas {len(reservaciones)} reservaciones en disco. Última: {nueva}")
    notificar_dueno(nombre, fecha, hora, servicio, canal)
    if canal == "whatsapp":
        mandar_whatsapp(telefono, nombre, fecha, hora, servicio)
    else:
        mandar_sms_confirmacion(telefono, nombre, fecha, hora, servicio, idioma)
    t = threading.Timer(86400, mandar_sms_recordatorio,
                        args=[telefono, nombre, fecha, hora, servicio])
    t.daemon = True
    t.start()
    print(f"[AI Booking] Reservación guardada: {nombre} — {fecha} {hora} ({canal})")
    return nueva


def process_booking_message(mensaje: str, numero: str, canal: str) -> str:
    """
    Natural-language booking via AI. Maintains per-number conversation state.
    Returns the text to send back to the user.
    """
    # ── Retrieve or init conversation history for this number ──
    # NOTE: All messages — including greetings — go through the history-aware path
    # so that the AI always has full context (language, prior turns) on every call.
    state = _booking_state.setdefault(numero, {"history": []})
    history = state["history"]

    # Detect and persist conversation language — first clear signal wins.
    # Subsequent ambiguous messages (like "sí", "yes") don't override.
    if "idioma" not in state:
        detected = _detect_lang(mensaje)
        if detected:
            state["idioma"] = detected

    # Build system prompt with today's date
    _now = datetime.now(_EASTERN)
    date_ctx = (
        f"Today's date is {_now.strftime('%Y-%m-%d')} ({_now.strftime('%A')}). "
        f"Tomorrow's date is {(_now + timedelta(days=1)).strftime('%Y-%m-%d')}."
    )
    system = _BOOKING_SYSTEM_PROMPT.replace("{DATE_CONTEXT}", date_ctx)
    print("=== SYSTEM PROMPT ===\n" + system + "\n=== END ===")

    # Append user message and call AI
    history.append({"role": "user", "content": mensaje})
    messages = [{"role": "system", "content": system}] + history

    reply = _call_openrouter(messages)

    if not reply:
        if state.get("idioma") == "en":
            return (
                f"{NEGOCIO_EMOJI} Hi! I'm the assistant for {NEGOCIO_NOMBRE}. "
                f"How can I help you? I can book an appointment for you."
            )
        return (
            f"{NEGOCIO_EMOJI} ¡Hola! Soy el asistente de {NEGOCIO_NOMBRE}. "
            f"¿En qué te puedo ayudar? Puedo agendar una cita para ti."
        )

    # ── Check if AI returned a finalized booking JSON ──
    if reply.startswith("BOOKING_JSON:"):
        try:
            raw = reply[len("BOOKING_JSON:"):].strip()
            data = json.loads(raw)
            _idioma = state.get("idioma", "es")
            _save_booking(
                nombre   = data.get("nombre", "Cliente"),
                fecha    = data["fecha"],
                hora     = data["hora"],
                servicio = data["servicio"],
                telefono = numero,
                canal    = canal,
                idioma   = _idioma,
            )
            # Reset state after successful booking
            _booking_state.pop(numero, None)
            if _idioma == "en":
                return (
                    f"✅ Booking confirmed, {data.get('nombre', '')}!\n"
                    f"📅 {data['fecha']} at {data['hora']}\n"
                    f"💆 {data['servicio']}\n\n"
                    f"We'll see you at {NEGOCIO_NOMBRE}. You'll get a reminder tomorrow."
                )
            return (
                f"✅ ¡Reservación confirmada, {data.get('nombre', '')}!\n"
                f"📅 {data['fecha']} a las {data['hora']}\n"
                f"💆 {data['servicio']}\n\n"
                f"Te esperamos en {NEGOCIO_NOMBRE}. Recibirás un recordatorio mañana."
            )
        except Exception as e:
            print(f"[AI Booking] Error parsing booking JSON: {e} — raw: {reply}")
            _booking_state.pop(numero, None)
            if state.get("idioma") == "en":
                return "There was an error saving your appointment. Please try again."
            return "Hubo un error al guardar tu cita. Por favor intenta de nuevo."

    # ── Normal conversational reply — store assistant turn in history ──
    history.append({"role": "assistant", "content": reply})

    # Trim history to last 10 turns to avoid token bloat
    if len(history) > 10:
        state["history"] = history[-10:]

    return reply


# ─── RUTA 2: WhatsApp entrante (Twilio webhook) ───────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp_entrante():
    mensaje = request.form.get("Body", "").strip()
    numero  = request.form.get("From", "")
    # Normalize to E.164 digits only for state key
    numero_key = numero.replace("whatsapp:", "").strip()

    respuesta = process_booking_message(mensaje, numero_key, "whatsapp")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""
    return xml, 200, {"Content-Type": "text/xml"}


# ─── RUTA 3: Panel del dueño ──────────────────────────────
@app.route("/panel")
def panel():
    if not _login_ok():
        return redirect(url_for("panel_login"))
    reservaciones = cargar()
    hoy       = datetime.now().strftime("%Y-%m-%d")
    hoy_lista = [r for r in reservaciones if r.get("fecha") == hoy]
    todas     = sorted(reservaciones, key=lambda x: x.get("creada", ""), reverse=True)
    web_count = len([r for r in reservaciones if r.get("canal") == "web"])
    wp_count  = len([r for r in reservaciones if r.get("canal") == "whatsapp"])

    # ── Analytics ──────────────────────────────────────────────
    from collections import Counter
    from datetime import timedelta as _td
    hoy_dt     = datetime.now().date()
    ultimos7   = [(hoy_dt - _td(days=i)) for i in range(6, -1, -1)]
    dias_keys  = [d.strftime("%Y-%m-%d") for d in ultimos7]
    dias_lbl   = [d.strftime("%d/%m") for d in ultimos7]
    conta_dias = {k: 0 for k in dias_keys}
    for _r in reservaciones:
        if _r.get("fecha") in conta_dias:
            conta_dias[_r["fecha"]] += 1
    chart_labels_js = json.dumps(dias_lbl)
    chart_data_js   = json.dumps([conta_dias[k] for k in dias_keys])

    serv_cnt = Counter(_r.get("servicio", "") for _r in reservaciones if _r.get("servicio"))
    top_serv, top_serv_n = serv_cnt.most_common(1)[0] if serv_cnt else ("Sin datos", 0)

    top_canal_label = "WhatsApp" if wp_count > web_count else "Web"
    top_canal_emoji = "📱" if wp_count > web_count else "🌐"
    top_canal_n     = max(web_count, wp_count) if (web_count or wp_count) else 0

    hora_cnt = Counter(_r.get("hora", "") for _r in reservaciones if _r.get("hora"))
    peak_hora, peak_hora_n = hora_cnt.most_common(1)[0] if hora_cnt else ("Sin datos", 0)

    # ── Reporte mensual ────────────────────────────────────────
    TARIFA_POR_RESERVA = 8          # $8 por reservación (Pay per Lead)
    mes_actual = datetime.now().strftime("%Y-%m")
    mes_label  = datetime.now().strftime("%B %Y").capitalize()
    reservas_mes = [r for r in reservaciones if r.get("fecha", "").startswith(mes_actual)]
    total_mes    = len(reservas_mes)
    monto_mes    = total_mes * TARIFA_POR_RESERVA

    # Pre-compute badge class strings to avoid backslashes inside f-string expressions
    rows_html = ""
    for r in todas:
        canal = r.get("canal", "web")
        if canal == "whatsapp":
            badge_cls = "badge-wp"
        elif canal == "sms":
            badge_cls = "badge-sms"
        else:
            badge_cls = "badge-web"
        rows_html += f"""
    <tr class="fila" data-canal="{canal}" data-fecha="{r.get('fecha','')}">
      <td><span class="td-name">{r.get('nombre','')}</span><br><span class="td-sub">{r.get('email','')}</span></td>
      <td>{r.get('servicio','')}</td>
      <td class="td-mono">{r.get('fecha','')}</td>
      <td class="td-mono td-bold">{r.get('hora','')}</td>
      <td><span class="badge {badge_cls}">{canal}</span></td>
      <td class="td-mono">{r.get('telefono','—')}</td>
      <td><span class="badge badge-confirmed">Confirmada</span></td>
    </tr>"""

    today_html = ""
    for r in sorted(hoy_lista, key=lambda x: x.get("hora", "")):
        today_html += f"""
    <div class="today-row">
      <div>
        <div class="today-name">{r.get('nombre','')}</div>
        <div class="today-svc">{r.get('servicio','')}</div>
      </div>
      <div class="today-time">{r.get('hora','')}</div>
    </div>"""

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NEGOCIO_NOMBRE} — Panel</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box }}
    body {{ font-family:'Plus Jakarta Sans',sans-serif; background:#FAFAF7; color:#0D0D0D; min-height:100vh }}

    /* ── Header ── */
    .hdr {{ background:#FAFAF7; border-bottom:1px solid rgba(13,13,13,0.08);
            padding:0 48px; height:56px; display:flex; align-items:center;
            justify-content:space-between; position:sticky; top:0; z-index:10 }}
    .hdr-brand {{ font-family:'Space Grotesk',sans-serif; font-size:15px; font-weight:700;
                  color:#0D0D0D; letter-spacing:-0.3px }}
    .hdr-right {{ display:flex; align-items:center; gap:20px }}
    .hdr-date {{ font-size:13px; color:#A3A3A3 }}
    .hdr-logout {{ font-size:13px; color:#A3A3A3; text-decoration:none; transition:color .15s }}
    .hdr-logout:hover {{ color:#0D0D0D }}

    /* ── Page shell ── */
    .page {{ max-width:1100px; margin:0 auto; padding:56px 48px 96px }}

    /* ── Section labels ── */
    .eyebrow {{ font-family:'Space Grotesk',sans-serif; font-size:11px; font-weight:600;
                color:#A3A3A3; text-transform:uppercase; letter-spacing:.08em; margin-bottom:20px }}

    /* ── Stat grid — numbers only, dividers between columns ── */
    .stat-grid {{ display:grid; grid-template-columns:repeat(4,1fr);
                  border-top:1px solid rgba(13,13,13,0.08);
                  border-bottom:1px solid rgba(13,13,13,0.08);
                  margin-bottom:72px }}
    .stat-cell {{ padding:32px 0 28px; padding-right:32px }}
    .stat-cell + .stat-cell {{ padding-left:32px; border-left:1px solid rgba(13,13,13,0.08) }}
    .stat-num {{ font-family:'Space Grotesk',sans-serif; font-size:56px; font-weight:700;
                 line-height:1; letter-spacing:-2px; color:#0D0D0D }}
    .stat-num.accent {{ color:#5B5BF6 }}
    .stat-lbl {{ font-size:13px; color:#6B6B6B; margin-top:8px; font-weight:500 }}
    .stat-sub {{ font-size:12px; color:#A3A3A3; margin-top:3px }}

    /* ── Chart — no box, just floating ── */
    .chart-wrap {{ margin-bottom:72px }}
    .chart-canvas-wrap {{ position:relative; height:180px; margin-top:12px }}

    /* ── Analytics row ── */
    .analytics-grid {{ display:grid; grid-template-columns:repeat(3,1fr);
                       border-top:1px solid rgba(13,13,13,0.08);
                       border-bottom:1px solid rgba(13,13,13,0.08);
                       margin-bottom:72px }}
    .analytics-cell {{ padding:28px 0; padding-right:32px }}
    .analytics-cell + .analytics-cell {{ padding-left:32px; border-left:1px solid rgba(13,13,13,0.08) }}
    .analytics-num {{ font-family:'Space Grotesk',sans-serif; font-size:28px; font-weight:700;
                      letter-spacing:-0.5px; color:#0D0D0D; line-height:1.2; word-break:break-word }}

    /* ── Monthly ── */
    .monthly-grid {{ display:grid; grid-template-columns:1fr 1fr auto;
                     gap:40px; align-items:end; margin-bottom:72px }}
    .monthly-num {{ font-family:'Space Grotesk',sans-serif; font-size:48px; font-weight:700;
                    letter-spacing:-2px; line-height:1 }}
    .monthly-num.purple {{ color:#5B5BF6 }}
    .monthly-num.green  {{ color:#16A34A }}

    /* ── Today list ── */
    .today-wrap {{ margin-bottom:72px }}
    .today-row {{ display:flex; justify-content:space-between; align-items:center;
                  padding:16px 0; border-bottom:1px solid rgba(13,13,13,0.06) }}
    .today-row:first-child {{ border-top:1px solid rgba(13,13,13,0.06) }}
    .today-name {{ font-family:'Space Grotesk',sans-serif; font-size:14px; font-weight:600 }}
    .today-svc  {{ font-size:12px; color:#6B6B6B; margin-top:2px }}
    .today-time {{ font-family:'Space Grotesk',sans-serif; font-size:14px; font-weight:700;
                   color:#5B5BF6 }}

    /* ── Table ── */
    .table-wrap {{ margin-bottom:72px }}
    .table-controls {{ display:flex; align-items:center; gap:12px; margin-bottom:20px; flex-wrap:wrap }}
    .search-bar {{ flex:1; min-width:200px; padding:9px 14px;
                   border:1px solid rgba(13,13,13,0.12); border-radius:8px;
                   font-size:13px; font-family:'Plus Jakarta Sans',sans-serif;
                   background:#fff; outline:none; transition:border .15s }}
    .search-bar:focus {{ border-color:#5B5BF6 }}
    .filters {{ display:flex; gap:6px; flex-wrap:wrap }}
    .filter-btn {{ padding:6px 14px; border-radius:6px; border:1px solid rgba(13,13,13,0.12);
                   background:#fff; font-size:12px; font-weight:600; cursor:pointer;
                   color:#6B6B6B; font-family:'Space Grotesk',sans-serif; transition:all .15s }}
    .filter-btn.active {{ background:#0D0D0D; color:#fff; border-color:#0D0D0D }}
    .filter-btn:hover:not(.active) {{ border-color:#0D0D0D; color:#0D0D0D }}
    .refresh-btn {{ margin-left:auto; padding:7px 14px; border-radius:6px;
                    border:1px solid rgba(13,13,13,0.12); background:#fff;
                    font-size:12px; font-weight:600; cursor:pointer; color:#6B6B6B;
                    font-family:'Space Grotesk',sans-serif; transition:all .15s; white-space:nowrap }}
    .refresh-btn:hover {{ border-color:#0D0D0D; color:#0D0D0D }}
    table {{ width:100%; border-collapse:collapse }}
    thead tr {{ border-bottom:1px solid rgba(13,13,13,0.08) }}
    th {{ font-family:'Space Grotesk',sans-serif; font-size:11px; font-weight:600;
          color:#A3A3A3; text-transform:uppercase; letter-spacing:.07em;
          padding:0 0 12px; text-align:left }}
    td {{ padding:14px 0; font-size:13px; color:#0D0D0D;
          border-bottom:1px solid rgba(13,13,13,0.05) }}
    tr:hover td {{ color:#5B5BF6 }}
    th + th, td + td {{ padding-left:20px }}
    .td-name {{ font-weight:600; font-size:14px }}
    .td-sub  {{ font-size:11px; color:#A3A3A3 }}
    .td-mono {{ font-family:'Space Grotesk',sans-serif }}
    .td-bold {{ font-weight:700 }}
    .badge {{ font-size:11px; padding:3px 9px; border-radius:5px; font-weight:600;
              font-family:'Space Grotesk',sans-serif; display:inline-block }}
    .badge-web       {{ background:rgba(91,91,246,.08);  color:#5B5BF6 }}
    .badge-wp        {{ background:rgba(34,197,94,.1);   color:#16A34A }}
    .badge-sms       {{ background:rgba(249,115,22,.1);  color:#EA580C }}
    .badge-confirmed {{ background:rgba(13,13,13,.06);   color:#6B6B6B }}
    .empty {{ padding:48px 0; color:#A3A3A3; font-size:14px }}

    /* ── Responsive ── */
    @media(max-width:768px) {{
      .hdr {{ padding:0 20px }}
      .page {{ padding:32px 20px 64px }}
      .stat-grid {{ grid-template-columns:repeat(2,1fr) }}
      .stat-cell + .stat-cell:nth-child(3) {{ border-left:none; padding-left:0 }}
      .stat-num {{ font-size:40px }}
      .analytics-grid {{ grid-template-columns:1fr }}
      .analytics-cell + .analytics-cell {{ border-left:none; padding-left:0;
                                           border-top:1px solid rgba(13,13,13,0.08) }}
      .monthly-grid {{ grid-template-columns:1fr 1fr; gap:24px }}
      th + th, td + td {{ padding-left:12px }}
    }}
    @media(max-width:480px) {{
      .stat-grid {{ grid-template-columns:1fr 1fr }}
      .monthly-grid {{ grid-template-columns:1fr }}
    }}
  </style>
</head>
<body>

<header class="hdr">
  <span class="hdr-brand">{NEGOCIO_EMOJI} {NEGOCIO_NOMBRE}</span>
  <div class="hdr-right">
    <span class="hdr-date">{datetime.now(_EASTERN).strftime("%d/%m/%Y")}</span>
    <a href="/panel-logout" class="hdr-logout">Salir</a>
  </div>
</header>

<div class="page">

  <!-- ── Stats ── -->
  <div class="stat-grid">
    <div class="stat-cell">
      <div class="stat-num accent">{len(hoy_lista)}</div>
      <div class="stat-lbl">Reservas hoy</div>
      <div class="stat-sub">{datetime.now(_EASTERN).strftime("%A %d de %B")}</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num">{len(todas)}</div>
      <div class="stat-lbl">Total reservaciones</div>
      <div class="stat-sub">Histórico completo</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num">{web_count}</div>
      <div class="stat-lbl">Vía formulario web</div>
      <div class="stat-sub">{round(web_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
    <div class="stat-cell">
      <div class="stat-num">{wp_count}</div>
      <div class="stat-lbl">Vía WhatsApp / SMS</div>
      <div class="stat-sub">{round(wp_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
  </div>

  <!-- ── Chart ── -->
  <div class="chart-wrap">
    <div class="eyebrow">Reservaciones — últimos 7 días</div>
    <div class="chart-canvas-wrap">
      <canvas id="barChart"></canvas>
    </div>
  </div>

  <!-- ── Analytics ── -->
  <div class="analytics-grid">
    <div class="analytics-cell">
      <div class="eyebrow" style="margin-bottom:10px">Servicio más solicitado</div>
      <div class="analytics-num">{top_serv}</div>
      <div class="stat-sub" style="margin-top:6px">{top_serv_n} reservación(es)</div>
    </div>
    <div class="analytics-cell">
      <div class="eyebrow" style="margin-bottom:10px">Canal más usado</div>
      <div class="analytics-num">{top_canal_label}</div>
      <div class="stat-sub" style="margin-top:6px">{top_canal_n} reservación(es)</div>
    </div>
    <div class="analytics-cell">
      <div class="eyebrow" style="margin-bottom:10px">Hora pico</div>
      <div class="analytics-num">{peak_hora}</div>
      <div class="stat-sub" style="margin-top:6px">{peak_hora_n} reservación(es)</div>
    </div>
  </div>

  <!-- ── Monthly report ── -->
  <div style="margin-bottom:72px">
    <div class="eyebrow">Reporte mensual — {mes_label}</div>
    <div class="monthly-grid">
      <div>
        <div class="stat-sub" style="margin-bottom:8px">Reservas del mes</div>
        <div class="monthly-num purple">{total_mes}</div>
        <div class="stat-sub" style="margin-top:6px">reservaciones confirmadas</div>
      </div>
      <div>
        <div class="stat-sub" style="margin-bottom:8px">Monto a cobrar</div>
        <div class="monthly-num green">${monto_mes}</div>
        <div class="stat-sub" style="margin-top:6px">{total_mes} × $8 por reservación</div>
      </div>
      <div>
        <a href="/api/reporte-mensual" target="_blank"
           style="display:inline-flex;align-items:center;gap:6px;padding:10px 18px;
                  background:#0D0D0D;color:#fff;border-radius:8px;text-decoration:none;
                  font-size:13px;font-weight:600;font-family:'Space Grotesk',sans-serif;
                  white-space:nowrap">
          Descargar JSON ↗
        </a>
      </div>
    </div>
  </div>

  <!-- ── Today ── -->
  <div class="today-wrap">
    <div class="eyebrow">Reservas de hoy</div>
    {today_html if today_html else '<div class="stat-sub">No hay reservas para hoy.</div>'}
  </div>

  <!-- ── All bookings ── -->
  <div class="table-wrap">
    <div class="eyebrow" style="margin-bottom:16px">Todas las reservaciones</div>
    <div class="table-controls">
      <input class="search-bar" type="text" id="search" placeholder="Buscar por nombre, servicio, fecha…" onkeyup="filtrar()">
      <div class="filters">
        <button class="filter-btn active" onclick="setFiltro('todos',this)">Todos</button>
        <button class="filter-btn" onclick="setFiltro('hoy',this)">Hoy</button>
        <button class="filter-btn" onclick="setFiltro('web',this)">Web</button>
        <button class="filter-btn" onclick="setFiltro('whatsapp',this)">WhatsApp</button>
      </div>
      <button class="refresh-btn" onclick="location.reload()">↺ Actualizar</button>
    </div>

    {"<table><thead><tr><th>Nombre</th><th>Servicio</th><th>Fecha</th><th>Hora</th><th>Canal</th><th>Teléfono</th><th>Estado</th></tr></thead><tbody>" + rows_html + "</tbody></table>"
     if todas else f'<div class="empty">{NEGOCIO_EMOJI} No hay reservaciones aún.</div>'}
  </div>

</div>

<script>
  let filtroActual = 'todos';
  const HOY = '{hoy}';
  function filtrar() {{
    const texto = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.fila').forEach(fila => {{
      const match = fila.textContent.toLowerCase().includes(texto);
      const matchFiltro =
        filtroActual === 'todos' ? true :
        filtroActual === 'hoy'   ? fila.dataset.fecha === HOY :
        fila.dataset.canal === filtroActual;
      fila.style.display = match && matchFiltro ? '' : 'none';
    }});
  }}
  function setFiltro(f, btn) {{
    filtroActual = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filtrar();
  }}
</script>

<script>
  (function() {{
    var ctx = document.getElementById('barChart');
    if (!ctx) return;
    new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels: {chart_labels_js},
        datasets: [{{
          label: 'Reservaciones',
          data: {chart_data_js},
          backgroundColor: 'rgba(91,91,246,0.12)',
          borderColor: '#5B5BF6',
          borderWidth: 1.5,
          borderRadius: 4,
          borderSkipped: false
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }}, tooltip: {{ callbacks: {{
          label: function(ctx) {{ return ' ' + ctx.parsed.y + ' reservaciones'; }}
        }} }} }},
        scales: {{
          y: {{ beginAtZero:true, ticks:{{ stepSize:1, color:'#A3A3A3',
                font:{{ family:'Plus Jakarta Sans', size:11 }} }},
                grid:{{ color:'rgba(13,13,13,0.05)' }}, border:{{ display:false }} }},
          x: {{ ticks:{{ color:'#A3A3A3', font:{{ family:'Plus Jakarta Sans', size:11 }} }},
                grid:{{ display:false }}, border:{{ display:false }} }}
        }}
      }}
    }});
  }})();
</script>

</body>
</html>
"""
    return html


# ─── RUTA 4: Chatbot bilingüe ─────────────────────────────
import urllib.request as _urllib_req

_OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

_SYSTEM_PROMPT = f"""You are a friendly, concise assistant for {NEGOCIO_NOMBRE} — {NEGOCIO_SLOGAN}.

Business info:
- Name: {NEGOCIO_NOMBRE}
- Address: {NEGOCIO_DIRECCION}
- Phone: {NEGOCIO_TELEFONO}
- Email: {NEGOCIO_EMAIL}
- Services: {', '.join(SERVICIOS)}
- Hours: Monday–Friday, 9am–6pm EST
- Packages: Basic $500 setup + $175/mo | Standard $900 setup + $275/mo | Professional $2,000 setup + $350/mo
- Booking link: /demo

Rules:
1. CRITICAL: Once you have determined the user's language from ANY message in the conversation, continue responding in that SAME language for the rest of the conversation, even if later messages are short or ambiguous (like a single word). Do not switch languages mid-conversation unless the user clearly switches first. If the user writes in English, respond in English. If in Spanish, respond in Spanish. Do not default to Spanish.
2. Be concise — 2 to 3 sentences maximum.
3. If asked about booking or reservations, share the link: /demo
4. If you don't know something, say to contact us at {NEGOCIO_EMAIL}.
5. Never make up information not listed above.
"""

def obtener_respuesta_chatbot(mensaje):
    """Lógica central del chatbot AI. Recibe el texto del usuario y devuelve
    (respuesta_texto, idioma). La usan tanto /chat (web) como /sms (Twilio)."""
    mensaje = (mensaje or "").strip()

    # ── DEBUG ────────────────────────────────────────────
    key = _OPENROUTER_API_KEY
    print(f"[CHAT] mensaje='{mensaje}'")
    print(f"[CHAT] OPENROUTER_API_KEY={'SET ('+key[:8]+'...)' if key else 'NO CONFIGURADA'}")
    # ─────────────────────────────────────────────────────

    if not mensaje:
        print("[CHAT] mensaje vacío → bienvenida")
        return CHATBOT_BIENVENIDA_ES, "es"

    if not _OPENROUTER_API_KEY:
        print("[CHAT] API key ausente → fallback")
        return "El chatbot no está configurado aún. Escríbenos a " + NEGOCIO_EMAIL, "es"

    payload = json.dumps({
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": mensaje},
        ],
        "max_tokens": 120,
        "temperature": 0.5,
    }).encode("utf-8")

    for intento in range(1, 3):
        print(f"[CHAT] Llamando a OpenRouter (intento {intento}/2)...")
        try:
            req = _urllib_req.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {_OPENROUTER_API_KEY}",
                    "Content-Type":  "application/json",
                    "HTTP-Referer":  "https://getdrivftllc.com",
                    "X-Title":       NEGOCIO_NOMBRE,
                },
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=10) as resp:
                resultado = json.loads(resp.read().decode("utf-8"))

            respuesta = resultado["choices"][0]["message"]["content"].strip()
            print(f"[CHAT] OpenRouter OK → '{respuesta[:60]}...'")
            return respuesta, "auto"

        except _urllib_req.HTTPError as e:
            if e.code == 429:
                print(f"[CHAT] 429 rate limit (intento {intento}/2) — {'reintentando en 2s' if intento < 2 else 'usando fallback'}")
                if intento < 2:
                    import time; time.sleep(2)
                    continue
            else:
                print(f"[CHAT] HTTP {e.code}: {e}")
            break
        except Exception as e:
            print(f"[CHAT] OpenRouter ERROR: {type(e).__name__}: {e}")
            break

    # ── Fallback: respuestas predefinidas del FAQ ────────
    print("[CHAT] Usando fallback FAQ predefinido")
    mensaje_lower = mensaje.lower()
    _en = {"what","how","where","when","price","pricing","cost","book","booking",
           "hello","hi","hey","hours","open","location","service","services",
           "phone","call","contact","help","info","need","want"}
    palabras = set(mensaje_lower.replace("?","").replace("!","").replace(",","").split())
    score_en = len(palabras & _en)
    score_es = 2 if any(c in mensaje_lower for c in "áéíóúñ¿¡") else 0
    for entrada in FAQ:
        if any(kw in mensaje_lower for kw in entrada["keywords_en"]): score_en += 1
        if any(kw in mensaje_lower for kw in entrada["keywords_es"]): score_es += 1
    idioma = "en" if score_en > score_es else "es"

    for entrada in FAQ:
        kws = entrada[f"keywords_{idioma}"]
        if any(kw in mensaje_lower for kw in kws):
            return entrada[f"respuesta_{idioma}"], idioma

    no_entiendo = CHATBOT_NO_ENTIENDO_EN if idioma == "en" else CHATBOT_NO_ENTIENDO_ES
    return no_entiendo, idioma


# ─── Link de reserva de Puerto Rico's Finest (Netlify) ───
# 👉 PEGA AQUÍ la URL de Netlify. Ej: "https://puerto-ricos-finest.netlify.app"
RESERVA_LINK_PR = "https://tiny-yeot-f15684.netlify.app/"


# ─── RUTA: Chatbot web (formulario) ──────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data    = request.json or {}
    mensaje = data.get("mensaje", "").strip()
    respuesta, idioma = obtener_respuesta_chatbot(mensaje)
    return jsonify({"respuesta": respuesta, "idioma": idioma})


# ─── RUTA: SMS entrante (Twilio webhook) ─────────────────
from twilio.twiml.messaging_response import MessagingResponse

@app.route("/sms", methods=["POST"])
def sms_entrante():
    mensaje = request.form.get("Body", "").strip()
    numero  = request.form.get("From", "").strip()

    respuesta = process_booking_message(mensaje, numero, "sms")

    twiml = MessagingResponse()
    twiml.message(respuesta)
    return str(twiml)


# ─── REPORTE MENSUAL API ─────────────────────────────────
@app.route("/api/reporte-mensual", methods=["GET"])
def api_reporte_mensual():
    TARIFA_POR_RESERVA = 8
    mes_actual  = datetime.now().strftime("%Y-%m")
    mes_label   = datetime.now().strftime("%B %Y").capitalize()
    reservaciones   = cargar()
    reservas_mes    = [r for r in reservaciones if r.get("fecha", "").startswith(mes_actual)]
    total_reservas  = len(reservas_mes)
    monto_total     = total_reservas * TARIFA_POR_RESERVA
    return jsonify({
        "mes":            mes_label,
        "periodo":        mes_actual,
        "total_reservas": total_reservas,
        "tarifa":         f"${TARIFA_POR_RESERVA} por reservacion",
        "monto_total":    f"${monto_total}",
        "reservas":       reservas_mes,
    })


# ─── PAGOS CON STRIPE ────────────────────────────────────
@app.route("/pagar", methods=["GET"])
def pagar():
    paquete = request.args.get("paquete", "basic")
    precios = {
        "basic":             {"setup": 50000,  "mensual": 17500, "nombre": "Basic Package"},
        "standard":          {"setup": 90000,  "mensual": 27500, "nombre": "Standard Package"},
        "professional":      {"setup": 200000, "mensual": 35000, "nombre": "Professional Package"},
        "basic-lead":        {"setup": 0,      "mensual": 0,     "nombre": "Basic Lead — Pay per Lead"},
        "standard-lead":     {"setup": 30000,  "mensual": 0,     "nombre": "Standard Lead — $10/reservacion"},
        "professional-lead": {"setup": 50000,  "mensual": 0,     "nombre": "Professional Lead — $14/reservacion"},
    }
    p = precios.get(paquete, precios["basic"])

    # ── Basic Lead: setup gratuito, sin formulario de pago ──
    if paquete == "basic-lead":
        return f"""<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Basic Lead — Drivft LLC</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#134e4a,#065f46);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
            .card{{background:white;border-radius:20px;padding:2.5rem 2rem;width:100%;max-width:480px;box-shadow:0 20px 60px rgba(0,0,0,0.25)}}
            .badge{{display:inline-block;background:#dcfce7;color:#166534;font-size:13px;font-weight:600;padding:5px 14px;border-radius:20px;margin-bottom:16px}}
            h1{{font-size:22px;color:#111;margin-bottom:4px}}
            .sub{{font-size:14px;color:#888;margin-bottom:20px}}
            .info-box{{background:#f0fdf4;border:1.5px solid #86efac;border-radius:12px;padding:16px;margin-bottom:22px}}
            .info-box strong{{display:block;font-size:14px;font-weight:700;color:#14532d;margin-bottom:4px}}
            .info-box p{{font-size:13px;color:#166534;line-height:1.65;margin:0}}
            label{{font-size:13px;font-weight:500;color:#444;display:block;margin-bottom:5px}}
            input{{width:100%;padding:10px 14px;border:1.5px solid #e0e0e0;border-radius:8px;font-size:14px;margin-bottom:14px;outline:none;font-family:'Segoe UI',sans-serif}}
            input:focus{{border-color:#16a34a;box-shadow:0 0 0 3px rgba(22,163,74,0.1)}}
            button{{width:100%;padding:14px;background:linear-gradient(135deg,#16a34a,#059669);color:white;border:none;border-radius:10px;font-size:15px;font-weight:600;cursor:pointer;font-family:'Segoe UI',sans-serif;margin-top:4px}}
            button:disabled{{opacity:0.6;cursor:not-allowed}}
            #error{{color:#ef4444;font-size:13px;margin-bottom:10px;display:none}}
            .success{{display:none;text-align:center;padding:16px 0}}
            .success .check{{font-size:52px;margin-bottom:12px}}
            .success h2{{font-size:20px;color:#14532d;margin-bottom:8px}}
            .success p{{font-size:14px;color:#6b7280;line-height:1.6}}
            .footer{{margin-top:20px;text-align:center;font-size:12px;color:#aaa}}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">🌱 Setup 100% gratuito</div>
            <h1>Drivft LLC</h1>
            <p class="sub">Basic Lead — Pay per Lead</p>
            <div class="info-box">
                <strong>¿Cómo funciona?</strong>
                <p>Setup gratis — solo pagas <strong>$7 por cada reservación real</strong> que tu sistema genere. Te contactaremos en menos de 24 horas para configurarlo todo.</p>
            </div>

            <form id="lead-form">
                <label>Nombre completo</label>
                <input type="text" id="nombre" placeholder="Juan García" required>
                <label>Email</label>
                <input type="email" id="email" placeholder="tu@email.com" required>
                <label>Teléfono</label>
                <input type="tel" id="telefono" placeholder="(305) 000-0000">
                <label>Nombre de tu negocio</label>
                <input type="text" id="negocio" placeholder="Mi Restaurante LLC" required>
                <div id="error">Hubo un error. Intenta de nuevo.</div>
                <button type="submit" id="btn">📩 Empezar gratis — me contactan en 24h</button>
            </form>

            <div class="success" id="success">
                <div class="check">🎉</div>
                <h2>¡Listo! Te contactamos pronto</h2>
                <p>Recibimos tu información. Un especialista de Drivft LLC te escribirá en menos de 24 horas para configurar tu sistema sin costo.</p>
            </div>

            <p class="footer">Powered by <strong>Drivft LLC</strong> · contact@getdrivftllc.com</p>
        </div>

        <script>
            document.getElementById('lead-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const btn = document.getElementById('btn');
                btn.disabled = true;
                btn.textContent = 'Enviando...';
                document.getElementById('error').style.display = 'none';

                const datos = {{
                    nombre:   document.getElementById('nombre').value,
                    email:    document.getElementById('email').value,
                    telefono: document.getElementById('telefono').value,
                    negocio:  document.getElementById('negocio').value,
                }};

                try {{
                    const res = await fetch('/contacto-lead', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(datos)
                    }});
                    if (res.ok) {{
                        document.getElementById('lead-form').style.display = 'none';
                        document.getElementById('success').style.display = 'block';
                    }} else {{
                        throw new Error('server error');
                    }}
                }} catch {{
                    document.getElementById('error').style.display = 'block';
                    btn.disabled = false;
                    btn.textContent = '📩 Empezar gratis — me contactan en 24h';
                }}
            }});
        </script>
    </body>
    </html>"""

    # ── Crear PaymentIntent server-side para inyectar client_secret ──
    try:
        intent = stripe.PaymentIntent.create(
            amount=p['setup'],
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={"paquete": paquete, "nombre": p['nombre']},
        )
        client_secret = intent.client_secret
    except Exception as e:
        print(f"[PAGAR] Stripe error al crear intent: {e}")
        client_secret = ""

    plan_labels = {
        "basic":        {"es": "Plan Inicio",      "en": "Starter Plan"},
        "standard":     {"es": "Plan Crecimiento", "en": "Growth Plan"},
        "professional": {"es": "Plan Pro",         "en": "Pro Plan"},
    }
    plan_label_es = plan_labels.get(paquete, {}).get("es", p['nombre'])
    plan_label_en = plan_labels.get(paquete, {}).get("en", p['nombre'])
    precio_label = ("Setup fee único + $" + str(p['mensual']//100) + "/mes después"
                    if p['mensual'] else "Pago único de configuración")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{plan_label_es} — Drivft LLC</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        *, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
        :root {{
            --bg:     #FAFAF7;
            --card:   #FFFFFF;
            --dark:   #0D0D0D;
            --purple: #5B5BF6;
            --purp-h: #4747e0;
            --gray:   #6B7280;
            --border: #E5E7EB;
            --r:      14px;
        }}
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--bg);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px 16px;
            color: var(--dark);
        }}

        /* ── Header bar ── */
        .pay-header {{
            width: 100%; max-width: 460px;
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 24px;
        }}
        .pay-logo {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 20px; font-weight: 700; color: var(--dark);
            text-decoration: none; letter-spacing: -.03em;
        }}
        .pay-back {{
            font-size: 13px; color: var(--gray); text-decoration: none;
            display: flex; align-items: center; gap: 4px;
            transition: color .15s;
        }}
        .pay-back:hover {{ color: var(--dark); }}

        /* ── Card ── */
        .pay-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 36px 32px;
            width: 100%; max-width: 460px;
            box-shadow: 0 4px 32px rgba(0,0,0,.06);
        }}

        /* ── Plan summary ── */
        .plan-row {{
            display: flex; align-items: center; justify-content: space-between;
            background: var(--bg); border: 1px solid var(--border);
            border-radius: var(--r); padding: 16px 18px; margin-bottom: 28px;
        }}
        .plan-name {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 15px; font-weight: 600; color: var(--dark);
        }}
        .plan-sub {{
            font-size: 12px; color: var(--gray); margin-top: 2px;
        }}
        .plan-price {{
            text-align: right;
        }}
        .plan-price-val {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 26px; font-weight: 700; color: var(--purple);
            letter-spacing: -.03em;
        }}
        .plan-price-note {{
            font-size: 11px; color: var(--gray); margin-top: 1px;
        }}

        /* ── Section label ── */
        .section-label {{
            font-size: 11px; font-weight: 700; text-transform: uppercase;
            letter-spacing: .08em; color: var(--gray); margin-bottom: 12px;
        }}

        /* ── Inputs ── */
        .field {{ margin-bottom: 14px; }}
        .field label {{
            display: block; font-size: 13px; font-weight: 600;
            color: var(--dark); margin-bottom: 6px;
        }}
        .field input {{
            width: 100%; padding: 11px 14px;
            border: 1.5px solid var(--border); border-radius: 10px;
            font-size: 14px; font-family: 'Plus Jakarta Sans', sans-serif;
            color: var(--dark); background: #fff; outline: none;
            transition: border-color .2s, box-shadow .2s;
        }}
        .field input:focus {{
            border-color: var(--purple);
            box-shadow: 0 0 0 3px rgba(91,91,246,.12);
        }}
        .field input::placeholder {{ color: #9CA3AF; }}

        /* ── Stripe element wrapper ── */
        .stripe-wrap {{
            border: 1.5px solid var(--border); border-radius: 10px;
            padding: 13px 14px; background: #fff; margin-bottom: 20px;
            transition: border-color .2s, box-shadow .2s;
        }}
        .stripe-wrap.focused {{
            border-color: var(--purple);
            box-shadow: 0 0 0 3px rgba(91,91,246,.12);
        }}

        /* ── Divider ── */
        .divider {{ height: 1px; background: var(--border); margin: 22px 0; }}

        /* ── Pay button ── */
        #btn {{
            width: 100%; padding: 15px;
            background: var(--purple); color: #fff;
            border: none; border-radius: 12px;
            font-size: 15px; font-weight: 700;
            font-family: 'Plus Jakarta Sans', sans-serif;
            cursor: pointer; transition: background .2s, transform .15s;
            margin-top: 4px;
        }}
        #btn:hover:not(:disabled) {{ background: var(--purp-h); transform: translateY(-1px); }}
        #btn:disabled {{ opacity: .55; cursor: not-allowed; transform: none; }}

        /* ── Trust badges ── */
        .trust {{
            display: flex; align-items: center; justify-content: center;
            gap: 18px; margin-top: 20px; flex-wrap: wrap;
        }}
        .trust-item {{
            display: flex; align-items: center; gap: 5px;
            font-size: 12px; color: var(--gray);
        }}

        /* ── Error / loading ── */
        #error {{
            color: #DC2626; font-size: 13px; min-height: 18px;
            margin-bottom: 10px; line-height: 1.4;
        }}
        #loading {{
            text-align: center; padding: 40px 0;
            font-size: 14px; color: var(--gray);
        }}
        .spinner {{
            display: inline-block; width: 20px; height: 20px;
            border: 2px solid var(--border); border-top-color: var(--purple);
            border-radius: 50%; animation: spin .7s linear infinite;
            margin-right: 8px; vertical-align: middle;
        }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

        @media (max-width: 500px) {{
            .pay-card {{ padding: 28px 20px; }}
        }}
    </style>
</head>
<body>

    <div class="pay-header">
        <a href="/" class="pay-logo">Drivft</a>
        <a href="/#precios" class="pay-back">← Cambiar plan</a>
    </div>

    <div class="pay-card">

        <!-- Plan summary -->
        <div class="plan-row">
            <div>
                <div class="plan-name">{plan_label_es}</div>
                <div class="plan-sub">{precio_label}</div>
            </div>
            <div class="plan-price">
                <div class="plan-price-val">${p['setup']//100:,}</div>
                <div class="plan-price-note">USD · pago único</div>
            </div>
        </div>

        <!-- Loading state -->
        <div id="loading">
            <span class="spinner"></span>Cargando opciones de pago…
        </div>

        <!-- Payment form -->
        <form id="payment-form" style="display:none">

            <p class="section-label">Tu información</p>

            <div class="field">
                <label for="nombre">Nombre completo</label>
                <input type="text" id="nombre" placeholder="Juan García" required>
            </div>
            <div class="field">
                <label for="email">Email</label>
                <input type="email" id="email" placeholder="tu@email.com" required>
            </div>

            <div class="divider"></div>
            <p class="section-label">Información de pago</p>

            <div class="stripe-wrap" id="stripe-wrap">
                <div id="payment-element"></div>
            </div>

            <div id="error"></div>

            <button id="btn">Pagar ${p['setup']//100:,} ahora 🔒</button>

            <div class="trust">
                <span class="trust-item">🔒 Pago seguro con Stripe</span>
                <span class="trust-item">🛡️ Datos encriptados</span>
                <span class="trust-item">✅ Sin contratos</span>
            </div>
        </form>
    </div>

    <script>
    (function() {{
        const CLIENT_SECRET = '{client_secret}';
        const PAQUETE       = '{paquete}';
        const PK            = '{os.environ.get("STRIPE_PUBLIC_KEY", "")}';

        if (!CLIENT_SECRET || !PK) {{
            document.getElementById('loading').innerHTML =
                'Error de configuración. Contacta a <a href="mailto:contact@getdrivftllc.com">contact@getdrivftllc.com</a>';
            return;
        }}

        const stripe = Stripe(PK);

        const appearance = {{
            theme: 'stripe',
            variables: {{
                colorPrimary:    '#5B5BF6',
                colorBackground: '#ffffff',
                colorText:       '#0D0D0D',
                borderRadius:    '8px',
                fontFamily:      "'Plus Jakarta Sans', sans-serif",
                spacingUnit:     '4px',
            }},
            rules: {{
                '.Input': {{ border: 'none', boxShadow: 'none', padding: '0' }},
            }},
        }};

        const elements = stripe.elements({{ clientSecret: CLIENT_SECRET, appearance }});

        const paymentEl = elements.create('payment', {{
            fields: {{ billingDetails: {{ name: 'never', email: 'never' }} }},
            wallets: {{ applePay: 'auto', googlePay: 'auto' }},
        }});

        paymentEl.mount('#payment-element');

        paymentEl.on('focus',  () => document.getElementById('stripe-wrap').classList.add('focused'));
        paymentEl.on('blur',   () => document.getElementById('stripe-wrap').classList.remove('focused'));

        paymentEl.on('ready', () => {{
            document.getElementById('loading').style.display = 'none';
            document.getElementById('payment-form').style.display = 'block';
        }});

        document.getElementById('payment-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const btn    = document.getElementById('btn');
            const nombre = document.getElementById('nombre').value.trim();
            const email  = document.getElementById('email').value.trim();

            if (!nombre || !email) {{
                document.getElementById('error').textContent = 'Por favor completa nombre y email.';
                return;
            }}

            btn.disabled    = true;
            btn.textContent = 'Procesando…';
            document.getElementById('error').textContent = '';

            const returnUrl = window.location.origin
                + '/pago-exitoso?nombre=' + encodeURIComponent(nombre)
                + '&paquete=' + PAQUETE
                + '&email='   + encodeURIComponent(email);

            const {{ error }} = await stripe.confirmPayment({{
                elements,
                confirmParams: {{
                    return_url: returnUrl,
                    payment_method_data: {{
                        billing_details: {{ name: nombre, email: email }},
                    }},
                }},
            }});

            if (error) {{
                document.getElementById('error').textContent = error.message;
                btn.disabled    = false;
                btn.textContent = 'Reintentar';
            }}
        }});
    }})();
    </script>
</body>
</html>"""
    return html


@app.route("/contacto-lead", methods=["POST"])
def contacto_lead():
    try:
        datos  = request.json or {}
        nombre  = datos.get("nombre",   "—")
        email   = datos.get("email",    "—")
        telefono= datos.get("telefono", "—")
        negocio = datos.get("negocio",  "—")

        gmail_user = os.environ.get("GMAIL_USER")
        gmail_pass = os.environ.get("GMAIL_PASSWORD")
        if not gmail_user or not gmail_pass:
            print("[LEAD] GMAIL_USER/PASSWORD no configurados — prospecto no notificado")
            return jsonify({"ok": True})   # igual devuelve ok al cliente

        cuerpo = f"""🌱 NUEVO PROSPECTO — Basic Lead (Pay per Lead)

Nombre:   {nombre}
Email:    {email}
Teléfono: {telefono}
Negocio:  {negocio}

Plan solicitado: Basic Lead — $0 setup + $7/reservación
Fecha:    {datetime.now().strftime("%Y-%m-%d %H:%M")}

Responde en menos de 24 horas para cerrar este cliente.
"""
        msg = MIMEMultipart()
        msg["From"]    = gmail_user
        msg["To"]      = gmail_user
        msg["Subject"] = f"🌱 Nuevo prospecto Basic Lead: {negocio} ({nombre})"
        msg.attach(MIMEText(cuerpo, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(gmail_user, gmail_pass)
        servidor.send_message(msg)
        servidor.quit()

        print(f"[LEAD] Email enviado — {nombre} / {negocio} / {email}")
        return jsonify({"ok": True})

    except Exception as e:
        print(f"[LEAD] Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/crear-pago", methods=["POST"])
def crear_pago():
    try:
        datos = request.json
        paquete = datos.get("paquete", "basic")
        precios_setup = {"basic": 50000, "standard": 90000, "professional": 200000}

        intent = stripe.PaymentIntent.create(
            amount=precios_setup.get(paquete, 50000),
            currency="usd",
            automatic_payment_methods={"enabled": True},
            metadata={"paquete": paquete, "cliente": datos.get("nombre"), "email": datos.get("email")}
        )
        return jsonify({"client_secret": intent.client_secret})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/pago-exitoso")
def pago_exitoso():
    nombre = request.args.get("nombre", "Cliente")
    paquete = request.args.get("paquete", "basic")
    email = request.args.get("email", "")

    montos = {"basic": 500, "standard": 900, "professional": 2000}
    monto = montos.get(paquete, 500)
    numero_factura = datetime.now().strftime("%Y%m%d%H%M%S")

    if email:
        enviar_factura_email(nombre, email, paquete, monto, numero_factura)

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Pago Exitoso — Drivft LLC</title>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center}}
            .card{{background:white;border-radius:20px;padding:3rem;width:100%;max-width:480px;text-align:center;box-shadow:0 20px 60px rgba(0,0,0,0.2)}}
            .icon{{font-size:64px;margin-bottom:16px}}
            h1{{font-size:24px;color:#111;margin-bottom:8px}}
            p{{font-size:15px;color:#888;margin-bottom:24px}}
            .factura{{font-size:13px;color:#aaa;margin-bottom:20px}}
            a{{display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border-radius:8px;text-decoration:none;font-weight:500}}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon">🎉</div>
            <h1>Pago Exitoso!</h1>
            <p>Gracias {nombre}! Tu pago del paquete <strong>{paquete.title()}</strong> fue procesado exitosamente. Te contactaremos en menos de 24 horas para comenzar tu proyecto.</p>
            <p class="factura">Factura #{numero_factura}</p>
            <a href="/">Volver al inicio</a>
        </div>
    </body>
    </html>
    """
    return html


# ─── LOGIN / LOGOUT ──────────────────────────────────────
@app.route("/panel-login", methods=["GET", "POST"])
def panel_login():
    error = ""
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        clave   = request.form.get("clave", "")
        ok_user = os.environ.get("PANEL_USER",     "admin")
        ok_pass = os.environ.get("PANEL_PASSWORD", "drivft2026")
        if usuario == ok_user and clave == ok_pass:
            session["autenticado"] = True
            return redirect(url_for("panel"))
        error = "Usuario o contraseña incorrectos."

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Login — {NEGOCIO_NOMBRE}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);
          min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .card{{background:white;border-radius:20px;padding:2.5rem 2rem;width:100%;max-width:400px;
           box-shadow:0 20px 60px rgba(0,0,0,0.25);text-align:center}}
    .icon{{font-size:48px;margin-bottom:12px}}
    h1{{font-size:22px;font-weight:700;color:#1A1A2E;margin-bottom:4px}}
    .sub{{font-size:13px;color:#9A7D5A;margin-bottom:28px}}
    label{{font-size:13px;font-weight:500;color:#444;display:block;text-align:left;margin-bottom:5px}}
    input{{width:100%;padding:11px 14px;border:1.5px solid #E8DACC;border-radius:10px;
           font-size:14px;font-family:'Inter',sans-serif;margin-bottom:14px;outline:none}}
    input:focus{{border-color:#5C3D8F;box-shadow:0 0 0 3px rgba(92,61,143,0.1)}}
    button{{width:100%;padding:13px;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);
            color:white;border:none;border-radius:10px;font-size:15px;font-weight:600;
            cursor:pointer;font-family:'Inter',sans-serif}}
    button:hover{{opacity:0.9}}
    .error{{background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;border-radius:8px;
            padding:10px 14px;font-size:13px;margin-bottom:14px;text-align:left}}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">{NEGOCIO_EMOJI}</div>
    <h1>{NEGOCIO_NOMBRE}</h1>
    <p class="sub">Panel de administración</p>
    {"<div class='error'>⚠️ " + error + "</div>" if error else ""}
    <form method="POST">
      <label>Usuario</label>
      <input type="text" name="usuario" placeholder="admin" required autofocus>
      <label>Contraseña</label>
      <input type="password" name="clave" placeholder="••••••••" required>
      <button type="submit">Entrar al panel →</button>
    </form>
  </div>
</body>
</html>"""


@app.route("/panel-logout")
def panel_logout():
    session.clear()
    return redirect(url_for("panel_login"))


# ─── ADMIN MAESTRO (login propio, separado del /panel) ───
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = ""
    if request.method == "POST":
        usuario = request.form.get("usuario", "")
        clave   = request.form.get("clave", "")
        ok_user = os.environ.get("ADMIN_USER",     "drivft")
        ok_pass = os.environ.get("ADMIN_PASSWORD", "drivft-admin-2026")
        if usuario == ok_user and clave == ok_pass:
            session["admin_autenticado"] = True
            return redirect(url_for("admin"))
        error = "Credenciales incorrectas."

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin Login — Drivft LLC</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#3B1F6A,#5C3D8F,#7B5EA7);
          min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .card{{background:white;border-radius:20px;padding:2.5rem 2rem;width:100%;max-width:400px;
           box-shadow:0 24px 64px rgba(0,0,0,0.3);text-align:center}}
    .logo{{font-size:44px;margin-bottom:10px}}
    .badge{{display:inline-block;background:#EDE9FE;color:#5C3D8F;font-size:11px;
            font-weight:700;padding:4px 12px;border-radius:20px;margin-bottom:14px;letter-spacing:0.06em}}
    h1{{font-size:22px;font-weight:700;color:#1A1A2E;margin-bottom:3px}}
    .sub{{font-size:13px;color:#9A7D5A;margin-bottom:28px}}
    label{{font-size:13px;font-weight:600;color:#5C3D8F;display:block;text-align:left;margin-bottom:5px}}
    input{{width:100%;padding:11px 14px;border:1.5px solid #E8DACC;border-radius:10px;
           font-size:14px;font-family:'Inter',sans-serif;margin-bottom:14px;outline:none}}
    input:focus{{border-color:#5C3D8F;box-shadow:0 0 0 3px rgba(92,61,143,0.12)}}
    button{{width:100%;padding:13px;background:linear-gradient(135deg,#5C3D8F,#7B5EA7);
            color:white;border:none;border-radius:10px;font-size:15px;font-weight:700;
            cursor:pointer;font-family:'Inter',sans-serif;letter-spacing:0.02em}}
    button:hover{{opacity:0.9}}
    .error{{background:#FEF2F2;color:#DC2626;border:1px solid #FECACA;border-radius:8px;
            padding:10px 14px;font-size:13px;margin-bottom:14px;text-align:left}}
    .footer{{margin-top:20px;font-size:11px;color:#C4B8D8}}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🚀</div>
    <div class="badge">ADMIN MAESTRO</div>
    <h1>Drivft LLC</h1>
    <p class="sub">Acceso exclusivo para el equipo Drivft</p>
    {"<div class='error'>⚠️ " + error + "</div>" if error else ""}
    <form method="POST">
      <label>Usuario</label>
      <input type="text" name="usuario" placeholder="drivft" required autofocus>
      <label>Contraseña</label>
      <input type="password" name="clave" placeholder="••••••••" required>
      <button type="submit">Entrar al admin →</button>
    </form>
    <p class="footer">Variables de entorno: ADMIN_USER / ADMIN_PASSWORD</p>
  </div>
</body>
</html>"""


@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin")
def admin():
    if not _admin_ok():
        return redirect(url_for("admin_login"))

    clientes  = cargar_clientes()
    now       = datetime.now()
    mes_label = now.strftime("%B %Y").capitalize()

    # ── Stats globales ──────────────────────────────────────
    activos         = [c for c in clientes if c.get("status", "activo") == "activo"]
    total_mensual   = sum(c.get("mensualidad", 0) for c in activos)
    total_reservas  = sum(c.get("reservas_mes", 0) for c in activos)
    total_leads_amt = sum(
        c.get("reservas_mes", 0) * c.get("tarifa_por_reserva", 0) for c in activos
    )
    gran_total   = total_mensual + total_leads_amt
    n_inactivos  = len([c for c in clientes if c.get("status") == "inactivo"])
    n_prueba     = len([c for c in clientes if c.get("status") == "prueba"])

    # ── Cards de clientes ───────────────────────────────────
    PLAN_COLORS = {
        "basic":             ("#EDE9FE", "#5B21B6"),
        "standard":          ("#DBEAFE", "#1D4ED8"),
        "professional":      ("#D1FAE5", "#065F46"),
        "basic-lead":        ("#FEF9C3", "#854D0E"),
        "standard-lead":     ("#FED7AA", "#9A3412"),
        "professional-lead": ("#FCE7F3", "#9D174D"),
    }
    STATUS_COLORS = {"activo": ("#DCFCE7", "#166534"), "inactivo": ("#FEE2E2", "#991B1B"), "prueba": ("#FEF9C3", "#854D0E")}

    cards_html = ""
    for c in clientes:
        plan          = c.get("plan", "basic")
        status        = c.get("status", "activo")
        c_negocio     = c.get("negocio", "este cliente")
        c_id          = c.get("id", "")
        c_fecha       = c.get("fecha_inicio", "—")
        pb, pt = PLAN_COLORS.get(plan, ("#EDE9FE", "#5B21B6"))
        sb, st = STATUS_COLORS.get(status, ("#F3F4F6", "#374151"))
        mensual  = c.get("mensualidad", 0)
        tpr      = c.get("tarifa_por_reserva", 0)
        reservas = c.get("reservas_mes", 0)
        lead_amt = reservas * tpr
        subtotal = mensual + lead_amt
        notas    = c.get("notas", "") or ""
        notas_row = (
            f"<div class='row'><span class='row-lbl'>Notas</span>"
            f"<span class='row-val' style='font-size:11px;color:#9CA3AF;max-width:55%;text-align:right'>{notas}</span></div>"
        ) if notas else ""

        cards_html += f"""
<div class="cliente-card" data-status="{status}">
  <div class="card-top">
    <div>
      <div class="card-name">{c_negocio}</div>
      <div class="card-id">{c_id}</div>
    </div>
    <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
      <span class="pill" style="background:{pb};color:{pt}">{plan}</span>
      <span class="pill" style="background:{sb};color:{st}">{status}</span>
    </div>
  </div>
  <div class="card-body">
    <div class="row"><span class="row-lbl">Mensualidad</span><span class="row-val">${mensual:,}/mes</span></div>
    <div class="row"><span class="row-lbl">Tarifa por reserva</span><span class="row-val">${tpr}/reserva</span></div>
    <div class="row"><span class="row-lbl">Reservas del mes</span><span class="row-val">{reservas} rsv</span></div>
    <div class="row"><span class="row-lbl">Pay-per-lead</span><span class="row-val accent">${lead_amt:,}</span></div>
    <div class="divider"></div>
    <div class="row"><span class="row-lbl" style="font-weight:600">Total a cobrar</span><span class="row-val" style="font-size:18px;font-weight:700;color:#5B5BF6">${subtotal:,}</span></div>
    <div class="row"><span class="row-lbl">Inicio</span><span class="row-val" style="color:#9CA3AF">{c_fecha}</span></div>
    {notas_row}
  </div>
  <div class="card-foot">
    <form method="POST" action="/admin/eliminar-cliente" style="display:inline">
      <input type="hidden" name="id" value="{c_id}">
      <button type="submit" class="btn-delete" onclick="return confirm('Eliminar a {c_negocio}?')">
        🗑 Eliminar
      </button>
    </form>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin — Drivft LLC</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Plus Jakarta Sans',sans-serif;background:#FAFAF7;min-height:100vh;color:#0D0D0D}}

    /* ── Header ── */
    header{{border-bottom:1px solid rgba(13,13,13,0.08);background:#FAFAF7;position:sticky;top:0;z-index:10}}
    .hdr{{max-width:1200px;margin:0 auto;padding:0 32px;height:60px;display:flex;align-items:center;justify-content:space-between}}
    .hdr-left{{display:flex;align-items:center;gap:14px}}
    .logo{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:18px;color:#0D0D0D;letter-spacing:-0.02em}}
    .logo span{{color:#5B5BF6}}
    .hdr-tag{{font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:0.08em;text-transform:uppercase;padding:3px 10px;border:1px solid rgba(13,13,13,0.1);border-radius:999px}}
    .hdr-right{{display:flex;align-items:center;gap:20px}}
    .hdr-link{{font-size:13px;color:#6B7280;text-decoration:none;font-weight:500}}
    .hdr-link:hover{{color:#0D0D0D}}
    .hdr-logout{{font-size:13px;color:#6B7280;text-decoration:none;font-weight:500}}
    .hdr-logout:hover{{color:#EF4444}}

    /* ── Layout ── */
    .page{{max-width:1200px;margin:0 auto;padding:40px 32px}}

    /* ── Stats row ── */
    .stats-row{{display:flex;align-items:stretch;border:1px solid rgba(13,13,13,0.08);border-radius:16px;background:#fff;margin-bottom:48px;overflow:hidden}}
    .stat-item{{flex:1;padding:32px 28px;text-align:center}}
    .stat-item+.stat-item{{border-left:1px solid rgba(13,13,13,0.08)}}
    .stat-num{{font-family:'Space Grotesk',sans-serif;font-size:52px;font-weight:700;color:#0D0D0D;line-height:1;letter-spacing:-0.03em}}
    .stat-lbl{{font-size:11px;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.08em;margin-top:8px}}

    /* ── Section header ── */
    .sec-hdr{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}}
    .sec-title{{font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:600;color:#0D0D0D;letter-spacing:-0.01em}}
    .btn-add{{background:#5B5BF6;color:#fff;border:none;border-radius:8px;padding:9px 18px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif;letter-spacing:-0.01em}}
    .btn-add:hover{{background:#4A4AE8}}

    /* ── Filters ── */
    .filters{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:24px}}
    .flt{{padding:6px 14px;border-radius:999px;border:1px solid rgba(13,13,13,0.12);background:transparent;font-size:12px;font-weight:600;cursor:pointer;color:#6B7280;font-family:'Plus Jakarta Sans',sans-serif}}
    .flt.active{{background:#0D0D0D;color:#fff;border-color:#0D0D0D}}

    /* ── Cards grid ── */
    .cards-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px;margin-bottom:40px}}
    .cliente-card{{background:#fff;border:1px solid rgba(13,13,13,0.08);border-radius:16px;overflow:hidden;transition:box-shadow 0.15s}}
    .cliente-card:hover{{box-shadow:0 8px 32px rgba(13,13,13,0.08)}}
    .card-top{{padding:20px 20px 16px;display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1px solid rgba(13,13,13,0.06)}}
    .card-name{{font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:#0D0D0D;letter-spacing:-0.01em}}
    .card-id{{font-size:11px;color:#D1D5DB;margin-top:2px;font-family:monospace}}
    .pill{{font-size:11px;font-weight:600;padding:3px 10px;border-radius:999px;letter-spacing:0.02em}}
    .card-body{{padding:16px 20px;display:flex;flex-direction:column;gap:0}}
    .row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(13,13,13,0.05)}}
    .row:last-child{{border-bottom:none}}
    .row-lbl{{font-size:12px;color:#9CA3AF;font-weight:500}}
    .row-val{{font-size:13px;font-weight:600;color:#0D0D0D}}
    .accent{{color:#16A34A}}
    .divider{{height:1px;background:rgba(13,13,13,0.08);margin:8px 0}}
    .card-foot{{padding:12px 20px;background:#FAFAF7;border-top:1px solid rgba(13,13,13,0.06);display:flex;justify-content:flex-end}}
    .btn-delete{{background:transparent;border:none;color:#9CA3AF;font-size:12px;font-weight:500;cursor:pointer;padding:4px 8px;font-family:'Plus Jakarta Sans',sans-serif}}
    .btn-delete:hover{{color:#EF4444}}

    /* ── Add form ── */
    .form-wrap{{background:#fff;border:1px solid rgba(13,13,13,0.08);border-radius:16px;padding:28px;margin-bottom:28px;display:none}}
    .form-wrap.open{{display:block}}
    .form-title{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:600;color:#0D0D0D;margin-bottom:20px}}
    .form-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}}
    .fg label{{display:block;font-size:11px;font-weight:600;color:#9CA3AF;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px}}
    .fg input,.fg select,.fg textarea{{width:100%;padding:9px 12px;border:1px solid rgba(13,13,13,0.12);border-radius:8px;font-size:13px;font-family:'Plus Jakarta Sans',sans-serif;outline:none;background:#FAFAF7;color:#0D0D0D}}
    .fg input:focus,.fg select:focus,.fg textarea:focus{{border-color:#5B5BF6;background:#fff;box-shadow:0 0 0 3px rgba(91,91,246,0.08)}}
    .form-actions{{display:flex;gap:10px;margin-top:20px}}
    .btn-save{{background:#5B5BF6;color:#fff;border:none;border-radius:8px;padding:10px 20px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif}}
    .btn-save:hover{{background:#4A4AE8}}
    .btn-cancel{{background:transparent;border:1px solid rgba(13,13,13,0.12);color:#6B7280;border-radius:8px;padding:10px 16px;font-size:13px;font-weight:500;cursor:pointer;font-family:'Plus Jakarta Sans',sans-serif}}
    .btn-cancel:hover{{border-color:#0D0D0D;color:#0D0D0D}}

    /* ── Empty state ── */
    .empty{{text-align:center;padding:64px 24px;color:#9CA3AF}}
    .empty-icon{{font-size:48px;margin-bottom:12px}}
    .empty p{{font-size:14px}}

    @media(max-width:640px){{
      .page{{padding:24px 16px}}
      .hdr{{padding:0 16px}}
      .stats-row{{flex-direction:column}}
      .stat-item+.stat-item{{border-left:none;border-top:1px solid rgba(13,13,13,0.08)}}
      .stat-num{{font-size:40px}}
      .cards-grid{{grid-template-columns:1fr}}
    }}
  </style>
</head>
<body>

<header>
  <div class="hdr">
    <div class="hdr-left">
      <div class="logo">Driv<span>ft</span></div>
      <span class="hdr-tag">Panel Admin</span>
    </div>
    <div class="hdr-right">
      <a href="/panel" class="hdr-link">↗ Panel demo</a>
      <a href="/admin-logout" class="hdr-logout">Cerrar sesión</a>
    </div>
  </div>
</header>

<div class="page">

  <!-- Stats row -->
  <div class="stats-row">
    <div class="stat-item">
      <div class="stat-num">{len(activos)}</div>
      <div class="stat-lbl">Clientes activos</div>
    </div>
    <div class="stat-item">
      <div class="stat-num">${total_mensual:,}</div>
      <div class="stat-lbl">Ingreso mensual</div>
    </div>
    <div class="stat-item">
      <div class="stat-num">{total_reservas}</div>
      <div class="stat-lbl">Reservas del mes</div>
    </div>
    <div class="stat-item">
      <div class="stat-num">${total_leads_amt:,}</div>
      <div class="stat-lbl">Pay-per-lead</div>
    </div>
  </div>

  <!-- Section header -->
  <div class="sec-hdr">
    <div class="sec-title">Clientes — {mes_label}</div>
    <button class="btn-add" onclick="toggleForm()">+ Agregar cliente</button>
  </div>

  <!-- Filters -->
  <div class="filters">
    <button class="flt active" onclick="filtrar('todos',this)">Todos ({len(clientes)})</button>
    <button class="flt" onclick="filtrar('activo',this)">Activos ({len(activos)})</button>
    <button class="flt" onclick="filtrar('inactivo',this)">Inactivos ({n_inactivos})</button>
    <button class="flt" onclick="filtrar('prueba',this)">Prueba ({n_prueba})</button>
  </div>

  <!-- Add form -->
  <div class="form-wrap" id="form-nuevo">
    <div class="form-title">Nuevo cliente</div>
    <form method="POST" action="/admin/agregar-cliente">
      <div class="form-grid">
        <div class="fg"><label>ID único</label>
          <input type="text" name="id" placeholder="cliente-002" required></div>
        <div class="fg"><label>Nombre del negocio</label>
          <input type="text" name="negocio" placeholder="Salon Maria" required></div>
        <div class="fg"><label>Plan</label>
          <select name="plan">
            <option value="basic">basic</option>
            <option value="standard">standard</option>
            <option value="professional">professional</option>
            <option value="basic-lead">basic-lead</option>
            <option value="standard-lead">standard-lead</option>
            <option value="professional-lead">professional-lead</option>
          </select>
        </div>
        <div class="fg"><label>Mensualidad ($)</label>
          <input type="number" name="mensualidad" value="175" min="0"></div>
        <div class="fg"><label>Tarifa por reserva ($)</label>
          <input type="number" name="tarifa_por_reserva" value="8" min="0"></div>
        <div class="fg"><label>Reservas del mes</label>
          <input type="number" name="reservas_mes" value="0" min="0"></div>
        <div class="fg"><label>Fecha de inicio</label>
          <input type="date" name="fecha_inicio" value="{now.strftime('%Y-%m-%d')}"></div>
        <div class="fg"><label>Status</label>
          <select name="status">
            <option value="activo">activo</option>
            <option value="inactivo">inactivo</option>
            <option value="prueba">prueba</option>
          </select>
        </div>
        <div class="fg" style="grid-column:1/-1"><label>Notas internas</label>
          <textarea name="notas" rows="2" placeholder="Cualquier detalle relevante..."></textarea>
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" class="btn-save">Guardar cliente</button>
        <button type="button" class="btn-cancel" onclick="toggleForm()">Cancelar</button>
      </div>
    </form>
  </div>

  <!-- Client cards -->
  {"<div class='cards-grid' id='cards-grid'>" + cards_html + "</div>" if clientes else
   "<div class='empty'><div class='empty-icon'>🏢</div><p>No hay clientes aún.<br>Agrega el primero con el botón de arriba.</p></div>"}

</div>

<script>
  function toggleForm() {{
    const f = document.getElementById('form-nuevo');
    f.classList.toggle('open');
    if (f.classList.contains('open')) f.scrollIntoView({{behavior:'smooth',block:'start'}});
  }}
  function filtrar(status, btn) {{
    document.querySelectorAll('.flt').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.cliente-card').forEach(card => {{
      card.style.display = (status === 'todos' || card.dataset.status === status) ? '' : 'none';
    }});
  }}
</script>
</body>
</html>"""


@app.route("/admin/agregar-cliente", methods=["POST"])
def admin_agregar_cliente():
    if not _admin_ok():
        return redirect(url_for("admin_login"))
    clientes = cargar_clientes()
    nuevo = {
        "id":                request.form.get("id", "").strip(),
        "negocio":           request.form.get("negocio", "").strip(),
        "plan":              request.form.get("plan", "basic"),
        "tarifa_por_reserva":int(request.form.get("tarifa_por_reserva", 8)),
        "mensualidad":       int(request.form.get("mensualidad", 0)),
        "fecha_inicio":      request.form.get("fecha_inicio", ""),
        "reservas_mes":      int(request.form.get("reservas_mes", 0)),
        "status":            request.form.get("status", "activo"),
        "notas":             request.form.get("notas", "").strip(),
    }
    if nuevo["id"] and nuevo["negocio"]:
        clientes.append(nuevo)
        guardar_clientes(clientes)
    return redirect(url_for("admin"))


@app.route("/admin/eliminar-cliente", methods=["POST"])
def admin_eliminar_cliente():
    if not _admin_ok():
        return redirect(url_for("admin_login"))
    cliente_id = request.form.get("id", "")
    clientes   = cargar_clientes()
    clientes   = [c for c in clientes if c.get("id") != cliente_id]
    guardar_clientes(clientes)
    return redirect(url_for("admin"))


@app.route("/privacy-policy")
def privacy_policy():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Privacy Policy — Drivft LLC</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: #F9F7FF;
      color: #1A1A2E;
      line-height: 1.75;
    }
    header {
      background: linear-gradient(135deg, #5C3D8F, #7B5EA7);
      padding: 28px 24px;
      text-align: center;
      color: white;
    }
    header .logo { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; }
    header .logo span { opacity: 0.7; font-weight: 300; }
    header p { font-size: 13px; opacity: 0.8; margin-top: 4px; }
    .container {
      max-width: 740px;
      margin: 48px auto;
      padding: 0 24px 80px;
    }
    h1 { font-size: 28px; font-weight: 700; color: #5C3D8F; margin-bottom: 6px; }
    .updated { font-size: 13px; color: #9A7D5A; margin-bottom: 36px; }
    h2 {
      font-size: 16px; font-weight: 700; color: #5C3D8F;
      margin-top: 36px; margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 2px solid #E8E0FF;
    }
    p { font-size: 15px; color: #3A3A5C; margin-bottom: 14px; }
    ul { margin: 0 0 14px 20px; }
    ul li { font-size: 15px; color: #3A3A5C; margin-bottom: 6px; }
    .highlight {
      background: #EDE8FF;
      border-left: 4px solid #5C3D8F;
      border-radius: 0 8px 8px 0;
      padding: 14px 18px;
      margin: 20px 0;
      font-size: 14px;
      color: #3A1A6E;
    }
    a { color: #5C3D8F; text-decoration: none; }
    a:hover { text-decoration: underline; }
    footer {
      text-align: center;
      padding: 24px;
      font-size: 12px;
      color: #B0A0CC;
      border-top: 1px solid #E8E0FF;
    }
    footer a { color: #7B5EA7; }
  </style>
</head>
<body>

<header>
  <div class="logo">Drivft <span>LLC</span></div>
  <p>Digital Services &amp; Automation Agency</p>
</header>

<div class="container">
  <h1>Privacy Policy</h1>
  <p class="updated">Last updated: June 8, 2026</p>

  <p>Drivft LLC ("we," "us," or "our") operates digital reservation and appointment systems for local businesses. This Privacy Policy explains how we collect, use, and protect the personal information you provide when using our services.</p>

  <h2>1. Information We Collect</h2>
  <p>When you make a reservation or appointment through our platform, we collect the following information:</p>
  <ul>
    <li><strong>Full name</strong> — to identify your reservation</li>
    <li><strong>Email address</strong> — to send booking confirmations and reminders</li>
    <li><strong>Phone number</strong> — to send SMS appointment confirmations and reminders</li>
    <li><strong>Appointment details</strong> — date, time, and service requested</li>
  </ul>

  <h2>2. How We Use Your Information</h2>
  <p>Your information is used exclusively to provide and support the reservation service:</p>
  <ul>
    <li>Send booking confirmation messages via email and/or SMS</li>
    <li>Send appointment reminders before your scheduled time</li>
    <li>Allow the business to manage and fulfill your appointment</li>
    <li>Respond to customer service inquiries</li>
  </ul>

  <h2>3. SMS Messaging</h2>
  <div class="highlight">
    By providing your phone number, you consent to receive SMS text messages from the business regarding your appointment. Message frequency varies — typically 1–3 messages per booking (confirmation + reminder). Standard message and data rates may apply.
  </div>
  <p>To opt out of SMS messages at any time, reply <strong>STOP</strong> to any text message you receive. You will receive one final confirmation message and no further texts will be sent. To re-subscribe, reply <strong>START</strong>. For help, reply <strong>HELP</strong>.</p>

  <h2>4. We Do Not Sell Your Data</h2>
  <p>We do <strong>not</strong> sell, rent, trade, or share your personal information with third parties for marketing or advertising purposes. Your data is only used to operate the reservation service on behalf of the business you are booking with.</p>

  <h2>5. Data Sharing</h2>
  <p>We work with trusted service providers to deliver our services, including:</p>
  <ul>
    <li><strong>Twilio</strong> — for SMS delivery</li>
    <li><strong>Google</strong> — for email delivery and calendar services</li>
    <li><strong>Railway / Cloud Hosting</strong> — for secure server infrastructure</li>
  </ul>
  <p>These providers access only the minimum data needed to perform their function and are bound by their own privacy policies.</p>

  <h2>6. Data Retention</h2>
  <p>Reservation records are retained for up to 12 months to allow businesses to reference past appointments. You may request deletion of your data at any time by contacting us.</p>

  <h2>7. Security</h2>
  <p>We take reasonable technical and organizational measures to protect your personal information against unauthorized access, loss, or misuse. All data is transmitted over secure HTTPS connections.</p>

  <h2>8. Your Rights</h2>
  <p>You have the right to:</p>
  <ul>
    <li>Request access to the personal data we hold about you</li>
    <li>Request correction or deletion of your data</li>
    <li>Opt out of SMS communications at any time by replying <strong>STOP</strong></li>
  </ul>

  <h2>9. Contact Us</h2>
  <p>If you have questions about this Privacy Policy or wish to exercise your data rights, contact us at:</p>
  <p>
    <strong>Drivft LLC</strong><br>
    Email: <a href="mailto:contact@getdrivftllc.com">contact@getdrivftllc.com</a><br>
    Website: <a href="https://getdrivftllc.com">getdrivftllc.com</a>
  </p>

  <h2>10. Changes to This Policy</h2>
  <p>We may update this Privacy Policy from time to time. Changes will be posted on this page with an updated date. Continued use of the service after changes constitutes your acceptance of the revised policy.</p>
</div>

<footer>
  &copy; 2026 Drivft LLC &mdash; <a href="/terms">Terms of Service</a> &mdash; <a href="/privacy-policy">Privacy Policy</a>
</footer>

</body>
</html>"""
    return html


@app.route("/terms")
def terms():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Terms of Service — Drivft LLC</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: #F9F7FF;
      color: #1A1A2E;
      line-height: 1.75;
    }
    header {
      background: linear-gradient(135deg, #5C3D8F, #7B5EA7);
      padding: 28px 24px;
      text-align: center;
      color: white;
    }
    header .logo { font-size: 24px; font-weight: 700; letter-spacing: -0.02em; }
    header .logo span { opacity: 0.7; font-weight: 300; }
    header p { font-size: 13px; opacity: 0.8; margin-top: 4px; }
    .container {
      max-width: 740px;
      margin: 48px auto;
      padding: 0 24px 80px;
    }
    h1 { font-size: 28px; font-weight: 700; color: #5C3D8F; margin-bottom: 6px; }
    .updated { font-size: 13px; color: #9A7D5A; margin-bottom: 36px; }
    h2 {
      font-size: 16px; font-weight: 700; color: #5C3D8F;
      margin-top: 36px; margin-bottom: 10px;
      padding-bottom: 6px;
      border-bottom: 2px solid #E8E0FF;
    }
    p { font-size: 15px; color: #3A3A5C; margin-bottom: 14px; }
    ul { margin: 0 0 14px 20px; }
    ul li { font-size: 15px; color: #3A3A5C; margin-bottom: 6px; }
    .highlight {
      background: #EDE8FF;
      border-left: 4px solid #5C3D8F;
      border-radius: 0 8px 8px 0;
      padding: 14px 18px;
      margin: 20px 0;
      font-size: 14px;
      color: #3A1A6E;
    }
    .sms-box {
      background: white;
      border: 1.5px solid #D4C8F0;
      border-radius: 12px;
      padding: 20px 24px;
      margin: 24px 0;
    }
    .sms-box h3 { font-size: 14px; font-weight: 700; color: #5C3D8F; margin-bottom: 10px; }
    .sms-box p { font-size: 14px; margin-bottom: 8px; }
    .sms-box code {
      background: #EDE8FF; padding: 2px 8px;
      border-radius: 5px; font-weight: 600; color: #5C3D8F;
    }
    a { color: #5C3D8F; text-decoration: none; }
    a:hover { text-decoration: underline; }
    footer {
      text-align: center;
      padding: 24px;
      font-size: 12px;
      color: #B0A0CC;
      border-top: 1px solid #E8E0FF;
    }
    footer a { color: #7B5EA7; }
  </style>
</head>
<body>

<header>
  <div class="logo">Drivft <span>LLC</span></div>
  <p>Digital Services &amp; Automation Agency</p>
</header>

<div class="container">
  <h1>Terms of Service</h1>
  <p class="updated">Last updated: June 8, 2026</p>

  <p>These Terms of Service ("Terms") govern your use of the reservation and appointment scheduling system operated by Drivft LLC ("Drivft," "we," or "us") on behalf of local businesses. By using this service, you agree to these Terms.</p>

  <h2>1. Description of Service</h2>
  <p>Drivft LLC provides digital reservation and appointment management systems for local service businesses. Our platform allows customers to book appointments online, receive automated confirmation and reminder messages, and communicate with the business.</p>
  <p>The reservation system is operated by Drivft LLC as a technology service provider. The actual services (spa treatments, restaurant reservations, etc.) are rendered by the individual business, not by Drivft LLC.</p>

  <h2>2. SMS Text Messaging</h2>

  <div class="sms-box">
    <h3>📱 SMS Program Disclosure</h3>
    <p><strong>Program:</strong> Appointment confirmation and reminder notifications</p>
    <p><strong>Message frequency:</strong> 1–3 messages per appointment (confirmation + reminder)</p>
    <p><strong>Rates:</strong> Message and data rates may apply</p>
    <p><strong>To get help:</strong> Reply <code>HELP</code></p>
    <p><strong>To cancel:</strong> Reply <code>STOP</code> at any time</p>
  </div>

  <p>By providing your mobile phone number when booking an appointment, you consent to receive SMS text messages from the business via Drivft LLC's platform. These messages will include booking confirmations, appointment reminders, and any follow-up needed related to your appointment.</p>

  <h2>3. Opting Out of SMS</h2>
  <div class="highlight">
    To stop receiving SMS messages, reply <strong>STOP</strong> to any message. You will receive a one-time confirmation and will not receive further messages. To re-subscribe, reply <strong>START</strong>. For assistance, reply <strong>HELP</strong> or email us at <a href="mailto:contact@getdrivftllc.com">contact@getdrivftllc.com</a>.
  </div>

  <h2>4. Appointments and Cancellations</h2>
  <p>Appointment booking through our platform is subject to the individual business's availability and cancellation policy. Drivft LLC is not responsible for:</p>
  <ul>
    <li>Service quality or outcome provided by the business</li>
    <li>Cancellations or rescheduling initiated by the business</li>
    <li>No-show fees or cancellation charges set by the business</li>
  </ul>
  <p>Please contact the business directly for questions about their specific policies.</p>

  <h2>5. User Responsibilities</h2>
  <p>By using this service, you agree to:</p>
  <ul>
    <li>Provide accurate and complete information when booking</li>
    <li>Not use the platform for any fraudulent or unlawful purpose</li>
    <li>Not attempt to disrupt or overload our systems</li>
    <li>Respect the business's scheduling and cancellation policies</li>
  </ul>

  <h2>6. Limitation of Liability</h2>
  <p>Drivft LLC provides this platform "as is." We are not liable for any damages arising from use of the reservation system, including but not limited to missed appointments, technical outages, or SMS delivery failures caused by your carrier or network.</p>

  <h2>7. Privacy</h2>
  <p>Your use of this service is also governed by our <a href="/privacy-policy">Privacy Policy</a>, which explains how we collect and use your personal information.</p>

  <h2>8. Changes to Terms</h2>
  <p>We reserve the right to update these Terms at any time. Updated Terms will be posted on this page with a new effective date. Continued use of the service after changes constitutes acceptance.</p>

  <h2>9. Contact</h2>
  <p>
    <strong>Drivft LLC</strong><br>
    Email: <a href="mailto:contact@getdrivftllc.com">contact@getdrivftllc.com</a><br>
    Website: <a href="https://getdrivftllc.com">getdrivftllc.com</a>
  </p>
</div>

<footer>
  &copy; 2026 Drivft LLC &mdash; <a href="/terms">Terms of Service</a> &mdash; <a href="/privacy-policy">Privacy Policy</a>
</footer>

</body>
</html>"""
    return html


@app.route("/privacy")
def privacy():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Privacy Policy - Drivft LLC</title><style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#333}h1,h2{color:#5C3D8F}</style></head><body><h1>Privacy Policy</h1><p>Last updated: June 2026</p><h2>Data We Collect</h2><p>Drivft LLC collects name, phone number, and email address when clients schedule appointments at getdrivftllc.com.</p><h2>How We Use Your Data</h2><p>We use your information solely to send appointment confirmations and reminders via SMS and email. Not for marketing.</p><h2>SMS Messaging</h2><p>By providing your phone number and checking the consent box on our booking form, you agree to receive SMS appointment reminders from Drivft LLC. Message frequency varies. Message and data rates may apply. Reply STOP to unsubscribe. Reply HELP for help.</p><h2>No Third-Party Sharing</h2><p>We do not sell, share, or transfer your mobile phone number to third parties.</p><h2>Contact</h2><p>contact@getdrivftllc.com or (689) 299-3994.</p></body></html>"""


if __name__ == "__main__":
    # Programar el reporte mensual automatico (1ro de mes a las 8am)
    _programar_reporte_mensual()

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
