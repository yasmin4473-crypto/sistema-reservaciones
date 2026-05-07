from flask import Flask, request, jsonify
from flask_cors import CORS
from notificaciones import mandar_email, mandar_whatsapp
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
)
import json, os
from datetime import datetime
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
        [f'{paquete.title()} Package - Setup Fee\n{p["desc"]}', f'${monto:,.2f}'],
        [f'Monthly maintenance (starting next month)', f'${p["mensual"]}/mo'],
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

ARCHIVO = "reservaciones.json"


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
    }

    for marcador, valor in reemplazos.items():
        html = html.replace(marcador, valor)

    return html


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

    return html


@app.route("/web")
def web():
    return _render_web()


@app.route("/landing")
def landing():
    with open("landing.html", "r", encoding="utf-8") as f:
        return f.read()


@app.route("/demo")
def demo():
    return _render_index()


@app.route("/")
def inicio():
    from flask import redirect
    return redirect("/landing")


# ─── RUTA 1: Formulario web ───────────────────────────────
@app.route("/reservar", methods=["POST"])
def reservar():
    datos = request.json
    datos["id"]     = datetime.now().strftime("%Y%m%d%H%M%S")
    datos["estado"] = "confirmada"
    datos["creada"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    datos["canal"]  = "web"

    reservaciones = cargar()
    reservaciones.append(datos)
    guardar(reservaciones)

    if datos.get("email"):
        mandar_email(datos["email"], datos["nombre"], datos["fecha"], datos["hora"], datos["servicio"])

    if datos.get("telefono"):
        mandar_whatsapp(datos["telefono"], datos["nombre"], datos["fecha"], datos["hora"], datos["servicio"])

    print(f"✅ Nueva reservación: {datos['nombre']} — {datos['fecha']} {datos['hora']}")
    return jsonify({"ok": True})


# ─── RUTA 2: WhatsApp entrante (Twilio webhook) ───────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp_entrante():
    mensaje = request.form.get("Body", "").strip().lower()
    numero  = request.form.get("From", "").replace("whatsapp:+1", "")

    reservaciones = cargar()

    if mensaje.startswith("reservar"):
        partes = mensaje.split("/")
        if len(partes) >= 5:
            nueva = {
                "id":       datetime.now().strftime("%Y%m%d%H%M%S"),
                "nombre":   partes[1].strip().title(),
                "email":    "",
                "telefono": numero,
                "fecha":    partes[2].strip(),
                "hora":     partes[3].strip(),
                "servicio": partes[4].strip().title(),
                "estado":   "confirmada",
                "creada":   datetime.now().strftime("%Y-%m-%d %H:%M"),
                "canal":    "whatsapp"
            }
            reservaciones.append(nueva)
            guardar(reservaciones)
            respuesta = (
                f"{NEGOCIO_EMOJI} *{NEGOCIO_NOMBRE}*\n\n"
                f"¡Listo {nueva['nombre']}! Tu mesa quedó para el {nueva['fecha']} a las {nueva['hora']}.\n"
                f"Pedido: {nueva['servicio']}\n\n¡Te esperamos!"
            )
        else:
            servicios_lista = "\n".join(f"• {s}" for s in SERVICIOS)
            respuesta = (
                f"Para reservar envíame:\n\n"
                f"reservar / Tu nombre / Fecha (2026-05-20) / Hora (1:00 PM) / Plato\n\n"
                f"Nuestros platos:\n{servicios_lista}"
            )
    elif any(w in mensaje for w in ["hola", "info", "menu", "menú", "precio"]):
        servicios_lista = "\n".join(f"• {s}" for s in SERVICIOS)
        respuesta = (
            f"{NEGOCIO_EMOJI} ¡Bienvenido a *{NEGOCIO_NOMBRE}*!\n\n"
            f"{NEGOCIO_SLOGAN}\n\n"
            f"Nuestro menú:\n{servicios_lista}\n\n"
            f"Para reservar:\nreservar / nombre / fecha / hora / plato"
        )
    else:
        respuesta = (
            f"{NEGOCIO_EMOJI} ¡Hola! Escribe *hola* para ver el menú "
            f"o reserva con:\nreservar / nombre / fecha / hora / plato"
        )

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""
    return xml, 200, {"Content-Type": "text/xml"}


# ─── RUTA 3: Panel del dueño ──────────────────────────────
@app.route("/panel")
def panel():
    reservaciones = cargar()
    hoy       = datetime.now().strftime("%Y-%m-%d")
    hoy_lista = [r for r in reservaciones if r.get("fecha") == hoy]
    todas     = sorted(reservaciones, key=lambda x: x.get("creada", ""), reverse=True)
    web_count = len([r for r in reservaciones if r.get("canal") == "web"])
    wp_count  = len([r for r in reservaciones if r.get("canal") == "whatsapp"])

    c1 = COLOR_PRIMARIO
    c2 = COLOR_SECUNDARIO

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NEGOCIO_NOMBRE} — Panel</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Inter',sans-serif;background:#FDF8F2;min-height:100vh}}
    .topbar{{background:linear-gradient(135deg,{c1},{c2});padding:20px 32px;display:flex;justify-content:space-between;align-items:center}}
    .topbar-left{{display:flex;align-items:center;gap:12px}}
    .topbar h1{{color:white;font-size:20px;font-weight:700}}
    .topbar span{{color:rgba(255,255,255,0.85);font-size:13px}}
    .container{{padding:28px 32px;max-width:1100px;margin:0 auto}}
    .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-bottom:28px}}
    .stat{{background:white;border-radius:16px;padding:20px 24px;box-shadow:0 2px 12px rgba(139,38,53,0.07);border-top:3px solid {c2}}}
    .stat-icon{{font-size:26px;margin-bottom:8px}}
    .stat-val{{font-size:32px;font-weight:700;color:{c1};line-height:1}}
    .stat-label{{font-size:13px;color:#9A7D5A;margin-top:6px}}
    .stat-sub{{font-size:12px;color:#C0A888;margin-top:3px}}
    .section-title{{font-size:14px;font-weight:600;color:#3A1A0A;margin-bottom:14px}}
    .card{{background:white;border-radius:16px;padding:24px;box-shadow:0 2px 12px rgba(139,38,53,0.07);margin-bottom:24px}}
    .empty{{text-align:center;padding:32px;color:#C0A888;font-size:14px}}
    table{{width:100%;border-collapse:collapse}}
    th{{text-align:left;font-size:11px;font-weight:700;color:#9A7D5A;text-transform:uppercase;letter-spacing:0.06em;padding:0 16px 12px}}
    td{{padding:14px 16px;font-size:14px;color:#3A1A0A;border-top:1px solid #FDF0E4}}
    tr:hover td{{background:#FDFAF6}}
    .badge{{font-size:11px;padding:4px 10px;border-radius:20px;font-weight:600;display:inline-block}}
    .badge-web{{background:#FFF0E8;color:{c1}}}
    .badge-wp{{background:#F0FDF4;color:#16A34A}}
    .badge-confirmed{{background:#FFF0E8;color:{c1}}}
    .today-card{{background:linear-gradient(135deg,{c1},{c2});border-radius:16px;padding:24px;margin-bottom:24px;color:white}}
    .today-card h2{{font-size:15px;font-weight:600;opacity:0.9;margin-bottom:16px}}
    .today-item{{background:rgba(255,255,255,0.15);border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}}
    .today-name{{font-size:14px;font-weight:600}}
    .today-service{{font-size:12px;opacity:0.8;margin-top:2px}}
    .today-time{{font-size:15px;font-weight:700;background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:8px;white-space:nowrap}}
    .search-bar{{width:100%;padding:10px 16px;border:1.5px solid #E8DACC;border-radius:10px;font-size:14px;outline:none;margin-bottom:16px;transition:border 0.2s;font-family:'Inter',sans-serif}}
    .search-bar:focus{{border-color:{c1};box-shadow:0 0 0 3px rgba(139,38,53,0.08)}}
    .filters{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
    .filter-btn{{padding:6px 14px;border-radius:20px;border:1.5px solid #E8DACC;background:white;font-size:12px;cursor:pointer;transition:all 0.15s;color:#9A7D5A;font-family:'Inter',sans-serif}}
    .filter-btn.active{{background:{c1};color:white;border-color:{c1}}}
    .refresh{{font-size:12px;padding:8px 16px;border-radius:8px;border:1.5px solid #E8DACC;background:white;cursor:pointer;color:#9A7D5A;float:right;font-family:'Inter',sans-serif}}
    .refresh:hover{{background:#FDF8F2}}
    @media(max-width:600px){{.container{{padding:16px}}.topbar{{padding:16px}}th,td{{padding:10px 8px}}}}
  </style>
</head>
<body>

<div class="topbar">
  <div class="topbar-left">
    <span style="font-size:28px">{NEGOCIO_EMOJI}</span>
    <h1>{NEGOCIO_NOMBRE}</h1>
  </div>
  <span>Hoy: {datetime.now().strftime("%d/%m/%Y")}</span>
</div>

<div class="container">

  <div class="stats">
    <div class="stat">
      <div class="stat-icon">📆</div>
      <div class="stat-val">{len(hoy_lista)}</div>
      <div class="stat-label">Reservas hoy</div>
      <div class="stat-sub">{datetime.now().strftime("%A %d de %B")}</div>
    </div>
    <div class="stat">
      <div class="stat-icon">📋</div>
      <div class="stat-val">{len(todas)}</div>
      <div class="stat-label">Total reservaciones</div>
      <div class="stat-sub">Todas las mesas</div>
    </div>
    <div class="stat">
      <div class="stat-icon">🌐</div>
      <div class="stat-val">{web_count}</div>
      <div class="stat-label">Vía formulario web</div>
      <div class="stat-sub">{round(web_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
    <div class="stat">
      <div class="stat-icon">📱</div>
      <div class="stat-val">{wp_count}</div>
      <div class="stat-label">Vía WhatsApp</div>
      <div class="stat-sub">{round(wp_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
  </div>

  <div class="today-card">
    <h2>⏰ Reservas de hoy</h2>
    {"".join(f'''
    <div class="today-item">
      <div>
        <div class="today-name">{r.get("nombre","")}</div>
        <div class="today-service">{r.get("servicio","")}</div>
      </div>
      <div class="today-time">{r.get("hora","")}</div>
    </div>''' for r in sorted(hoy_lista, key=lambda x: x.get("hora",""))) if hoy_lista else '<div style="opacity:0.7;text-align:center;padding:16px">No hay reservas para hoy</div>'}
  </div>

  <div class="card">
    <button class="refresh" onclick="location.reload()">🔄 Actualizar</button>
    <div class="section-title">📋 Todas las reservaciones</div>

    <input class="search-bar" type="text" id="search" placeholder="🔍 Buscar por nombre, plato, fecha..." onkeyup="filtrar()">

    <div class="filters">
      <button class="filter-btn active" onclick="setFiltro('todos',this)">Todos</button>
      <button class="filter-btn" onclick="setFiltro('hoy',this)">Hoy</button>
      <button class="filter-btn" onclick="setFiltro('web',this)">Web</button>
      <button class="filter-btn" onclick="setFiltro('whatsapp',this)">WhatsApp</button>
    </div>

    {"<table><tr><th>Nombre</th><th>Pedido</th><th>Fecha</th><th>Hora</th><th>Canal</th><th>Teléfono</th><th>Estado</th></tr>" +
    "".join(f'''
    <tr class="fila" data-canal="{r.get("canal","web")}" data-fecha="{r.get("fecha","")}">
      <td><strong>{r.get("nombre","")}</strong><br><span style="font-size:12px;color:#C0A888">{r.get("email","")}</span></td>
      <td>{r.get("servicio","")}</td>
      <td>{r.get("fecha","")}</td>
      <td><strong>{r.get("hora","")}</strong></td>
      <td><span class="badge {'badge-wp' if r.get('canal')=='whatsapp' else 'badge-web'}">{r.get("canal","web")}</span></td>
      <td>{r.get("telefono","—")}</td>
      <td><span class="badge badge-confirmed">Confirmada</span></td>
    </tr>''' for r in todas) +
    "</table>" if todas else f'<div class="empty">{NEGOCIO_EMOJI} No hay reservaciones aún</div>'}
  </div>

</div>

<script>
  let filtroActual = 'todos';
  const hoy = '{hoy}';
  function filtrar() {{
    const texto = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.fila').forEach(fila => {{
      const match = fila.textContent.toLowerCase().includes(texto);
      const matchFiltro =
        filtroActual==='todos'  ? true :
        filtroActual==='hoy'    ? fila.dataset.fecha===hoy :
        fila.dataset.canal===filtroActual;
      fila.style.display = match && matchFiltro ? '' : 'none';
    }});
  }}
  function setFiltro(f,btn) {{
    filtroActual = f;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    filtrar();
  }}
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
1. Always reply in the same language the user writes in.
2. Be concise — 2 to 3 sentences maximum.
3. If asked about booking or reservations, share the link: /demo
4. If you don't know something, say to contact us at {NEGOCIO_EMAIL}.
5. Never make up information not listed above.
"""

@app.route("/chat", methods=["POST"])
def chat():
    data    = request.json or {}
    mensaje = data.get("mensaje", "").strip()

    # ── DEBUG ────────────────────────────────────────────
    key = _OPENROUTER_API_KEY
    print(f"[CHAT] mensaje='{mensaje}'")
    print(f"[CHAT] OPENROUTER_API_KEY={'SET ('+key[:8]+'...)' if key else 'NO CONFIGURADA'}")
    # ─────────────────────────────────────────────────────

    if not mensaje:
        print("[CHAT] mensaje vacío → bienvenida")
        return jsonify({"respuesta": CHATBOT_BIENVENIDA_ES, "idioma": "es"})

    if not _OPENROUTER_API_KEY:
        print("[CHAT] API key ausente → fallback")
        return jsonify({"respuesta": "El chatbot no está configurado aún. Escríbenos a " + NEGOCIO_EMAIL, "idioma": "es"})

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
            return jsonify({"respuesta": respuesta, "idioma": "auto"})

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
            return jsonify({"respuesta": entrada[f"respuesta_{idioma}"], "idioma": idioma})

    no_entiendo = CHATBOT_NO_ENTIENDO_EN if idioma == "en" else CHATBOT_NO_ENTIENDO_ES
    return jsonify({"respuesta": no_entiendo, "idioma": idioma})


# ─── PAGOS CON STRIPE ────────────────────────────────────
@app.route("/pagar", methods=["GET"])
def pagar():
    paquete = request.args.get("paquete", "basic")
    precios = {
        "basic":        {"setup": 50000, "mensual": 17500, "nombre": "Basic Package"},
        "standard":     {"setup": 90000, "mensual": 27500, "nombre": "Standard Package"},
        "professional": {"setup": 200000, "mensual": 35000, "nombre": "Professional Package"},
    }
    p = precios.get(paquete, precios["basic"])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Pago — Drivft LLC</title>
        <script src="https://js.stripe.com/v3/"></script>
        <style>
            *{{margin:0;padding:0;box-sizing:border-box}}
            body{{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
            .card{{background:white;border-radius:20px;padding:2rem;width:100%;max-width:480px;box-shadow:0 20px 60px rgba(0,0,0,0.2)}}
            h1{{font-size:22px;color:#111;margin-bottom:4px}}
            .sub{{font-size:14px;color:#888;margin-bottom:24px}}
            .precio{{background:#f5f5f5;border-radius:12px;padding:16px;margin-bottom:20px}}
            .precio-val{{font-size:32px;font-weight:600;color:#5C3D8F}}
            .precio-label{{font-size:13px;color:#888;margin-top:4px}}
            label{{font-size:13px;font-weight:500;color:#444;display:block;margin-bottom:5px}}
            input{{width:100%;padding:10px 14px;border:1.5px solid #e8e8e8;border-radius:8px;font-size:14px;margin-bottom:16px;outline:none}}
            input:focus{{border-color:#5C3D8F}}
            #card-element{{padding:12px 14px;border:1.5px solid #e8e8e8;border-radius:8px;margin-bottom:16px}}
            button{{width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer}}
            button:disabled{{opacity:0.6}}
            #error{{color:#ef4444;font-size:13px;margin-bottom:12px}}
            .badge{{display:inline-block;background:#E1F5EE;color:#085041;font-size:12px;padding:4px 10px;border-radius:20px;margin-bottom:16px}}
        </style>
    </head>
    <body>
        <div class="card">
            <div class="badge">🔒 Pago seguro con Stripe</div>
            <h1>Drivft LLC</h1>
            <p class="sub">{p['nombre']}</p>
            <div class="precio">
                <div class="precio-val">${p['setup']//100:,}</div>
                <div class="precio-label">Setup fee unico + ${p['mensual']//100}/mes despues</div>
            </div>
            <label>Nombre completo</label>
            <input type="text" id="nombre" placeholder="Juan Garcia" required>
            <label>Email</label>
            <input type="email" id="email" placeholder="tu@email.com" required>
            <label>Tarjeta de credito</label>
            <div id="card-element"></div>
            <div id="error"></div>
            <button id="btn">Pagar ${p['setup']//100:,} ahora</button>
        </div>
        <script>
            const stripe = Stripe('{os.environ.get("STRIPE_PUBLIC_KEY")}');
            const elements = stripe.elements();
            const card = elements.create('card', {{style: {{base: {{fontSize: '16px', color: '#424770'}}}}}});
            card.mount('#card-element');
            
            document.getElementById('btn').addEventListener('click', async () => {{
                const btn = document.getElementById('btn');
                btn.disabled = true;
                btn.textContent = 'Procesando...';
                
                const nombre = document.getElementById('nombre').value;
                const email = document.getElementById('email').value;
                
                const res = await fetch('/crear-pago', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{paquete: '{paquete}', nombre, email}})
                }});
                const data = await res.json();
                
                if (data.error) {{
                    document.getElementById('error').textContent = data.error;
                    btn.disabled = false;
                    btn.textContent = 'Reintentar';
                    return;
                }}
                
                const result = await stripe.confirmCardPayment(data.client_secret, {{
                    payment_method: {{card, billing_details: {{name: nombre, email: email}}}}
                }});
                
                if (result.error) {{
                    document.getElementById('error').textContent = result.error.message;
                    btn.disabled = false;
                    btn.textContent = 'Reintentar';
                }} else {{
                    window.location.href = '/pago-exitoso?nombre=' + nombre + '&paquete={paquete}&email=' + encodeURIComponent(email);
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html


@app.route("/crear-pago", methods=["POST"])
def crear_pago():
    try:
        datos = request.json
        paquete = datos.get("paquete", "basic")
        precios_setup = {"basic": 50000, "standard": 90000, "professional": 200000}
        
        intent = stripe.PaymentIntent.create(
            amount=precios_setup.get(paquete, 50000),
            currency="usd",
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
            <p>Gracias {nombre}! Tu pago del paquete <strong>{paquete.title()}</strong> fue procesado. Te contactaremos en menos de 24 horas para comenzar tu proyecto.</p>
            {"<p class='factura'>📧 Tu factura fue enviada a <strong>" + email + "</strong></p>" if email else ""}
            <p class="factura">Factura #{numero_factura}</p>
            <a href="/">Volver al inicio</a>
        </div>
    </body>
    </html>
    """
    return html
if __name__ == "__main__":
    print(f"{NEGOCIO_EMOJI} {NEGOCIO_NOMBRE} — Sistema corriendo...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
