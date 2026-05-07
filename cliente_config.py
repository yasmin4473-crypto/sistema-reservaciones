NEGOCIO_NOMBRE    = "Drivft LLC"
NEGOCIO_SLOGAN    = "Digital Services & Automation"
NEGOCIO_EMOJI     = "🚀"
NEGOCIO_TELEFONO  = "+1 (555) 000-0000"
NEGOCIO_EMAIL     = "contact@getdrivftllc.com"
NEGOCIO_DIRECCION = "Miami, Florida, USA"
NEGOCIO_WHATSAPP  = "18336841568"

COLOR_PRIMARIO     = "#5C3D8F"
COLOR_SECUNDARIO   = "#7B5EA7"
COLOR_FONDO_INICIO = "#667eea"
COLOR_FONDO_FIN    = "#764ba2"

SERVICIOS = [
    "Sistema de Reservaciones",
    "Pagina Web Profesional",
    "Bot de WhatsApp",
    "Chatbot con IA",
]

SERVICIOS_EMOJIS = ["📅", "🌐", "📱", "🤖"]

SERVICIOS_DESCRIPCIONES = [
    "Sistema completo de reservaciones online 24/7.",
    "Pagina web profesional hasta 5 paginas.",
    "Bot de WhatsApp para reservaciones automaticas.",
    "Chatbot con IA para atender clientes automaticamente.",
]

HORAS_DISPONIBLES = [
    "9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM",
]

SOBRE_NOSOTROS_TITULO = "Sobre Drivft LLC"
SOBRE_NOSOTROS_TEXTO  = "Somos una agencia de servicios digitales especializada en automatizacion para negocios latinos en USA."

STATS = [
    ("24/7", "Disponibilidad"),
    ("100%", "Automatizado"),
    ("30min", "Setup por cliente"),
]

FOTO_HERO     = ""
FOTO_NOSOTROS = ""
FOTOS_GALERIA = []

GOOGLE_MAPS_EMBED = ""

EMAIL_FROM      = "reservaciones@getdrivftllc.com"
EMAIL_FROM_NAME = "Drivft LLC Reservaciones"
# Chatbot
FAQ = [
    {
        "keywords_es": ["precio", "precios", "costo", "cuanto", "cuánto", "vale", "cobra"],
        "keywords_en": ["price", "prices", "cost", "how much", "charge", "fee"],
        "respuesta_es": f"Nuestros paquetes empiezan en $500 de setup. Basic $500, Standard $900, Professional $2,000. Escríbenos a {NEGOCIO_EMAIL} para más detalles.",
        "respuesta_en": f"Our packages start at $500 setup. Basic $500, Standard $900, Professional $2,000. Email us at {NEGOCIO_EMAIL} for details.",
    },
    {
        "keywords_es": ["horario", "hora", "horas", "cuando", "cuándo", "disponible", "atienden"],
        "keywords_en": ["hours", "schedule", "when", "available", "open", "time"],
        "respuesta_es": "Estamos disponibles de lunes a viernes de 9am a 6pm (EST). Respondemos WhatsApp y email en menos de 24 horas.",
        "respuesta_en": "We are available Monday to Friday 9am to 6pm (EST). We respond to WhatsApp and email within 24 hours.",
    },
    {
        "keywords_es": ["ubicacion", "ubicación", "donde", "dónde", "direccion", "dirección", "oficina"],
        "keywords_en": ["location", "where", "address", "office", "based"],
        "respuesta_es": f"Estamos ubicados en {NEGOCIO_DIRECCION}. Trabajamos de forma remota con negocios en todo USA.",
        "respuesta_en": f"We are based in {NEGOCIO_DIRECCION}. We work remotely with businesses across the USA.",
    },
    {
        "keywords_es": ["servicio", "servicios", "ofrecen", "hacen", "incluye", "que tienen"],
        "keywords_en": ["service", "services", "offer", "include", "what do you do"],
        "respuesta_es": f"Ofrecemos: {', '.join(SERVICIOS)}. Todo integrado en un solo sistema para tu negocio.",
        "respuesta_en": f"We offer: {', '.join(SERVICIOS)}. All integrated in one system for your business.",
    },
    {
        "keywords_es": ["reservar", "reservacion", "reservación", "cita", "agendar", "como reservo"],
        "keywords_en": ["book", "booking", "reservation", "appointment", "schedule", "how to book"],
        "respuesta_es": "Puedes reservar usando el formulario en esta pagina, por WhatsApp o escribiéndonos al email.",
        "respuesta_en": "You can book using the form on this page, via WhatsApp, or by emailing us.",
    },
    {
        "keywords_es": ["telefono", "teléfono", "llamar", "contacto", "contactar", "whatsapp"],
        "keywords_en": ["phone", "call", "contact", "whatsapp", "reach"],
        "respuesta_es": f"Puedes contactarnos al {NEGOCIO_TELEFONO} o por WhatsApp al +{NEGOCIO_WHATSAPP}. También en {NEGOCIO_EMAIL}.",
        "respuesta_en": f"You can reach us at {NEGOCIO_TELEFONO} or WhatsApp +{NEGOCIO_WHATSAPP}. Also at {NEGOCIO_EMAIL}.",
    },
]

CHATBOT_BIENVENIDA_ES = f"Hola! Soy el asistente de {NEGOCIO_NOMBRE}. Como puedo ayudarte?"
CHATBOT_BIENVENIDA_EN = f"Hi! I'm the {NEGOCIO_NOMBRE} assistant. How can I help you?"
CHATBOT_NO_ENTIENDO_ES = "No entendi tu pregunta. Puedes preguntarme sobre: precios, horarios, servicios, ubicacion o como reservar."
CHATBOT_NO_ENTIENDO_EN = "I didn't understand. You can ask me about: prices, hours, services, location or how to book."