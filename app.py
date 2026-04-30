from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from notificaciones import mandar_email, mandar_whatsapp
import json, os
from datetime import datetime

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

# ─── RUTA 1: Formulario web ───────────────────────────────
@app.route("/reservar", methods=["POST"])
def reservar():
    datos = request.json
    datos["id"] = datetime.now().strftime("%Y%m%d%H%M%S")
    datos["estado"] = "confirmada"
    datos["creada"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    datos["canal"] = "web"

    reservaciones = cargar()
    reservaciones.append(datos)
    guardar(reservaciones)

    # Manda email si tiene email
    if datos.get("email"):
        mandar_email(
            datos["email"],
            datos["nombre"],
            datos["fecha"],
            datos["hora"],
            datos["servicio"]
        )

    # Manda WhatsApp si tiene teléfono
    if datos.get("telefono"):
        mandar_whatsapp(
            datos["telefono"],
            datos["nombre"],
            datos["fecha"],
            datos["hora"],
            datos["servicio"]
        )

    print(f"✅ Nueva reservación web: {datos['nombre']} - {datos['fecha']} {datos['hora']}")
    return jsonify({"ok": True})


# ─── RUTA 2: WhatsApp entrante (Twilio webhook) ───────────
@app.route("/whatsapp", methods=["POST"])
def whatsapp_entrante():
    mensaje = request.form.get("Body", "").strip().lower()
    numero = request.form.get("From", "").replace("whatsapp:+1", "")
    nombre = request.form.get("ProfileName", "Cliente")

    reservaciones = cargar()

    # Detecta si el mensaje tiene formato de reservación
    # Formato esperado: "reservar / Juan García / 2026-05-10 / 10:00 AM / Corte de cabello"
    if mensaje.startswith("reservar"):
        partes = mensaje.split("/")
        if len(partes) >= 5:
            nueva = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "nombre": partes[1].strip().title(),
                "email": "",
                "telefono": numero,
                "fecha": partes[2].strip(),
                "hora": partes[3].strip(),
                "servicio": partes[4].strip().title(),
                "estado": "confirmada",
                "creada": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "canal": "whatsapp"
            }
            reservaciones.append(nueva)
            guardar(reservaciones)

            respuesta = f"✅ Listo {nueva['nombre']}! Tu cita quedó para el {nueva['fecha']} a las {nueva['hora']}. ¡Te esperamos!"
        else:
            respuesta = (
                "Para reservar mándame este mensaje con tus datos:\n\n"
                "reservar / Tu nombre / Fecha (2026-05-10) / Hora (10:00 AM) / Servicio\n\n"
                "Ejemplo:\nreservar / María García / 2026-05-15 / 2:00 PM / Consulta general"
            )
    elif "hola" in mensaje or "info" in mensaje:
        respuesta = (
            "👋 Hola! Para hacer una reservación mándame:\n\n"
            "reservar / Tu nombre / Fecha / Hora / Servicio\n\n"
            "Ejemplo:\nreservar / Juan Pérez / 2026-05-15 / 10:00 AM / Corte de cabello"
        )
    else:
        respuesta = "Hola! Para reservar escribe: reservar / nombre / fecha / hora / servicio"

    # Twilio espera respuesta en XML
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{respuesta}</Message>
</Response>"""

    return xml, 200, {"Content-Type": "text/xml"}


# ─── RUTA 3: Panel del dueño ──────────────────────────────
@app.route("/panel")
def panel():
    reservaciones = cargar()
    hoy = datetime.now().strftime("%Y-%m-%d")
    hoy_lista = [r for r in reservaciones if r.get("fecha") == hoy]
    todas = sorted(reservaciones, key=lambda x: x.get("creada", ""), reverse=True)
    proximas = [r for r in reservaciones if r.get("fecha", "") >= hoy]
    web_count = len([r for r in reservaciones if r.get("canal") == "web"])
    wp_count = len([r for r in reservaciones if r.get("canal") == "whatsapp"])

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Panel de Reservaciones</title>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',sans-serif;background:#f0f2f5;min-height:100vh}}
    .topbar{{background:linear-gradient(135deg,#667eea,#764ba2);padding:20px 32px;display:flex;justify-content:space-between;align-items:center}}
    .topbar h1{{color:white;font-size:20px;font-weight:600}}
    .topbar span{{color:rgba(255,255,255,0.8);font-size:13px}}
    .container{{padding:28px 32px;max-width:1100px;margin:0 auto}}
    .stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:28px}}
    .stat{{background:white;border-radius:16px;padding:20px 24px;box-shadow:0 2px 8px rgba(0,0,0,0.06)}}
    .stat-icon{{font-size:28px;margin-bottom:8px}}
    .stat-val{{font-size:32px;font-weight:600;color:#111;line-height:1}}
    .stat-label{{font-size:13px;color:#888;margin-top:6px}}
    .stat-sub{{font-size:12px;color:#aaa;margin-top:3px}}
    .section-title{{font-size:15px;font-weight:600;color:#333;margin-bottom:14px;display:flex;align-items:center;gap:8px}}
    .card{{background:white;border-radius:16px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:24px}}
    .empty{{text-align:center;padding:32px;color:#bbb;font-size:14px}}
    table{{width:100%;border-collapse:collapse}}
    th{{text-align:left;font-size:12px;font-weight:600;color:#999;text-transform:uppercase;letter-spacing:0.05em;padding:0 16px 12px}}
    td{{padding:14px 16px;font-size:14px;color:#333;border-top:1px solid #f5f5f5}}
    tr:hover td{{background:#fafafa}}
    .badge{{font-size:11px;padding:4px 10px;border-radius:20px;font-weight:500;display:inline-block}}
    .badge-web{{background:#EEF2FF;color:#4F46E5}}
    .badge-wp{{background:#F0FDF4;color:#16A34A}}
    .badge-confirmed{{background:#F0FDF4;color:#16A34A}}
    .badge-pending{{background:#FEF9C3;color:#CA8A04}}
    .today-card{{background:linear-gradient(135deg,#667eea,#764ba2);border-radius:16px;padding:24px;margin-bottom:24px;color:white}}
    .today-card h2{{font-size:16px;font-weight:600;opacity:0.9;margin-bottom:16px}}
    .today-item{{background:rgba(255,255,255,0.15);border-radius:10px;padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center}}
    .today-item:last-child{{margin-bottom:0}}
    .today-name{{font-size:14px;font-weight:500}}
    .today-service{{font-size:12px;opacity:0.8;margin-top:2px}}
    .today-time{{font-size:15px;font-weight:600;background:rgba(255,255,255,0.2);padding:6px 12px;border-radius:8px}}
    .search-bar{{width:100%;padding:10px 16px;border:1.5px solid #e8e8e8;border-radius:10px;font-size:14px;outline:none;margin-bottom:16px;transition:border 0.2s}}
    .search-bar:focus{{border-color:#667eea}}
    .filters{{display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap}}
    .filter-btn{{padding:6px 14px;border-radius:20px;border:1.5px solid #e8e8e8;background:white;font-size:12px;cursor:pointer;transition:all 0.15s;color:#666}}
    .filter-btn.active{{background:#667eea;color:white;border-color:#667eea}}
    .cancel-btn{{font-size:11px;padding:4px 10px;border-radius:6px;border:1px solid #fca5a5;background:#fff;color:#ef4444;cursor:pointer}}
    .cancel-btn:hover{{background:#fef2f2}}
    .refresh{{font-size:12px;padding:8px 16px;border-radius:8px;border:1.5px solid #e8e8e8;background:white;cursor:pointer;color:#666;float:right}}
    .refresh:hover{{background:#f5f5f5}}
    @media(max-width:600px){{
      .container{{padding:16px}}
      .topbar{{padding:16px}}
      th,td{{padding:10px 8px}}
    }}
  </style>
</head>
<body>

<div class="topbar">
  <h1>📅 Panel de Reservaciones</h1>
  <span>Hoy: {datetime.now().strftime("%d/%m/%Y")}</span>
</div>

<div class="container">

  <!-- STATS -->
  <div class="stats">
    <div class="stat">
      <div class="stat-icon">📆</div>
      <div class="stat-val">{len(hoy_lista)}</div>
      <div class="stat-label">Citas hoy</div>
      <div class="stat-sub">{datetime.now().strftime("%A %d de %B")}</div>
    </div>
    <div class="stat">
      <div class="stat-icon">📋</div>
      <div class="stat-val">{len(todas)}</div>
      <div class="stat-label">Total reservaciones</div>
      <div class="stat-sub">Todas las citas</div>
    </div>
    <div class="stat">
      <div class="stat-icon">🌐</div>
      <div class="stat-val">{web_count}</div>
      <div class="stat-label">Via formulario web</div>
      <div class="stat-sub">{round(web_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
    <div class="stat">
      <div class="stat-icon">📱</div>
      <div class="stat-val">{wp_count}</div>
      <div class="stat-label">Via WhatsApp</div>
      <div class="stat-sub">{round(wp_count/len(todas)*100) if todas else 0}% del total</div>
    </div>
  </div>

  <!-- CITAS DE HOY -->
  <div class="today-card">
    <h2>⏰ Citas de hoy</h2>
    {"".join(f'''
    <div class="today-item">
      <div>
        <div class="today-name">{r.get("nombre","")}</div>
        <div class="today-service">{r.get("servicio","")}</div>
      </div>
      <div class="today-time">{r.get("hora","")}</div>
    </div>''' for r in sorted(hoy_lista, key=lambda x: x.get("hora",""))) if hoy_lista else '<div style="opacity:0.7;text-align:center;padding:16px">No hay citas para hoy</div>'}
  </div>

  <!-- TODAS LAS RESERVACIONES -->
  <div class="card">
    <button class="refresh" onclick="location.reload()">🔄 Actualizar</button>
    <div class="section-title">📋 Todas las reservaciones</div>

    <input class="search-bar" type="text" id="search" placeholder="🔍 Buscar por nombre, servicio, fecha..." onkeyup="filtrar()">

    <div class="filters">
      <button class="filter-btn active" onclick="setFiltro('todos', this)">Todos</button>
      <button class="filter-btn" onclick="setFiltro('hoy', this)">Hoy</button>
      <button class="filter-btn" onclick="setFiltro('web', this)">Web</button>
      <button class="filter-btn" onclick="setFiltro('whatsapp', this)">WhatsApp</button>
    </div>

    {"<table><tr><th>Nombre</th><th>Servicio</th><th>Fecha</th><th>Hora</th><th>Canal</th><th>Telefono</th><th>Estado</th></tr>" +
    "".join(f'''
    <tr class="fila" data-canal="{r.get("canal","web")}" data-fecha="{r.get("fecha","")}">
      <td><strong>{r.get("nombre","")}</strong><br><span style="font-size:12px;color:#999">{r.get("email","")}</span></td>
      <td>{r.get("servicio","")}</td>
      <td>{r.get("fecha","")}</td>
      <td><strong>{r.get("hora","")}</strong></td>
      <td><span class="badge {'badge-wp' if r.get('canal')=='whatsapp' else 'badge-web'}">{r.get("canal","web")}</span></td>
      <td>{r.get("telefono","—")}</td>
      <td><span class="badge badge-confirmed">Confirmada</span></td>
    </tr>''' for r in todas) +
    "</table>" if todas else '<div class="empty">📭 No hay reservaciones aún</div>'}
  </div>

</div>

<script>
  let filtroActual = 'todos';
  const hoy = '{hoy}';

  function filtrar() {{
    const texto = document.getElementById('search').value.toLowerCase();
    document.querySelectorAll('.fila').forEach(fila => {{
      const contenido = fila.textContent.toLowerCase();
      const canal = fila.dataset.canal;
      const fecha = fila.dataset.fecha;
      const matchTexto = contenido.includes(texto);
      const matchFiltro =
        filtroActual === 'todos' ? true :
        filtroActual === 'hoy' ? fecha === hoy :
        canal === filtroActual;
      fila.style.display = matchTexto && matchFiltro ? '' : 'none';
    }});
  }}

  function setFiltro(f, btn) {{
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


if __name__ == "__main__":
    print("🚀 Sistema de reservaciones corriendo...")
    print("📋 Panel del dueño: http://localhost:5000/panel")
    app.run(debug=True, port=5000)