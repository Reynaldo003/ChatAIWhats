import os
import time
import requests
import sett
from openai import OpenAI
import json
from datetime import datetime

def obtener_Mensaje_whatsapp(message):
    if 'type' not in message:
        return 'mensaje no reconocido'

    typeMessage = message['type']
    if typeMessage == 'text':
        text = message['text']['body']
    elif typeMessage == 'button':
        text = message['button']['text']
    elif typeMessage == 'interactive' and message['interactive']['type'] == 'list_reply':
        text = message['interactive']['list_reply']['title']
    elif typeMessage == 'interactive' and message['interactive']['type'] == 'button_reply':
        text = message['interactive']['button_reply']['title']
    else:
        text = 'mensaje no procesado'
    return text

def enviar_Mensaje_whatsapp(data):
    try:
        whatsapp_token = sett.whatsapp_token
        whatsapp_url = sett.whatsapp_url
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + whatsapp_token
        }
        print("se envia ", data)
        response = requests.post(whatsapp_url, headers=headers, data=data)
        if response.status_code == 200:
            return 'mensaje enviado', 200
        else:
            return 'error al enviar mensaje', response.status_code
    except Exception as e:
        return e, 403

def text_Message(number, text, footer):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "text",
        "text": {"body": text},
        "footer": {"text": footer},
    })
    return data

def buttonReply_Message(number, options, body, footer, sedd, messageId):
    buttons = []
    for i, option in enumerate(options):
        buttons.append({
            "type": "reply",
            "reply": {"id": sedd + "_btn_" + str(i+1), "title": option}
        })

    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {"buttons": buttons}
        }
    })
    return data

def listReply_Message(number, options, body, footer, sedd, messageId):
    rows = []
    for i, option in enumerate(options):
        rows.append({"id": sedd + "_row_" + str(i+1), "title": option, "description": ""})

    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "footer": {"text": footer},
            "action": {
                "button": "Ver Opciones",
                "sections": [{"title": "Secciones", "rows": rows}]
            }
        }
    })
    return data

def document_Message(number, url, caption, filename):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "document",
        "document": {"link": url, "caption": caption, "filename": filename}
    })
    return data

def sticker_Message(number, sticker_id):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "sticker",
        "sticker": {"id": sticker_id}
    })
    return data

def get_media_id(media_name, media_type):
    media_id = ""
    if media_type == "sticker":
        media_id = sett.stickers.get(media_name, None)
    elif media_type == "image":
        media_id = sett.images.get(media_name, None)
    elif media_type == "video":
        media_id = sett.videos.get(media_name, None)
    elif media_type == "audio":
        media_id = sett.audio.get(media_name, None)
    return media_id

def replyReaction_Message(number, messageId, emoji):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "type": "reaction",
        "reaction": {"message_id": messageId, "emoji": emoji}
    })
    return data

def replyText_Message(number, messageId, text):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number,
        "context": {"message_id": messageId},
        "type": "text",
        "text": {"body": text}
    })
    return data

def markRead_Message(messageId):
    data = json.dumps({
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": messageId
    })
    return data


DATA_FILE = os.path.join(os.path.dirname(__file__), "prospectos.json")
PROSPECTOS = {}
CURRENT_NUMBER = None

PLANTILLA_PROSPECTO = {
    "nombre": "",
    "presupuesto": "",
    "urgencia": "",
    "categoria_interes": "",
    "enganche": "",
    "auto_a_cuenta": "",
    "auto_objetivo": "",
    "fecha_cita": "",
    "prueba_manejo": "",
    "fecha_prueba": "",
    "pago": "",
    "fecha_hora_actual": ""
}

def _load_data():
    global PROSPECTOS
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                PROSPECTOS = json.load(f)
        else:
            PROSPECTOS = {}
    except Exception:
        PROSPECTOS = {}

def _save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(PROSPECTOS, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Cargar al importar
_load_data()

def _ensure_user(number: str):
    if number not in PROSPECTOS:
        PROSPECTOS[number] = PLANTILLA_PROSPECTO.copy()

# --- REEMPLAZA las funciones single-user por estas multiusuario ---
def get_info_prospecto():
    """Devuelve la info del usuario actual (CURRENT_NUMBER)."""
    if not CURRENT_NUMBER:
        return PLANTILLA_PROSPECTO.copy()
    _ensure_user(CURRENT_NUMBER)
    return PROSPECTOS[CURRENT_NUMBER]

def update_info_prospecto(**fields):
    """Actualiza la info del usuario actual y persiste en disco."""
    if not CURRENT_NUMBER:
        return PLANTILLA_PROSPECTO.copy()
    _ensure_user(CURRENT_NUMBER)
    for k, v in fields.items():
        if k in PLANTILLA_PROSPECTO:
            PROSPECTOS[CURRENT_NUMBER][k] = v
    PROSPECTOS[CURRENT_NUMBER]["fecha_hora_actual"] = datetime.now().isoformat()
    _save_data()
    return PROSPECTOS[CURRENT_NUMBER]


def replace_start(s):
    number = s[3:]
    if s.startswith("521"):
        return "52" + number
    else:
        return s


def gpt(text, number, messageId, name):
    try:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        client = OpenAI(api_key=OPENAI_API_KEY)
        global CURRENT_NUMBER
        CURRENT_NUMBER = replace_start(number)
        _ensure_user(CURRENT_NUMBER)
        tools = [
            {
                "type": "function",
                "name": "get_modelos_disponibles",
                "description": "Obtiene los modelos de autos disponibles en R&R Córdoba.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "categoria": {
                            # puede ser string o lista de strings
                            "oneOf": [
                                {"type": "string", "description": "SUV, Compactos, Camionetas"},
                                {"type": "array", "items": {"type": "string"}}
                            ],
                            "description": "Categoría(s) del auto"
                        }
                    },
                    "required": []
                }
            },
            {
                "type": "function",
                "name": "get_info_prospecto",
                "description": "Obtiene la información actual del prospecto.",
                "parameters": {"type": "object", "properties": {}}
            },
            {
                "type": "function",
                "name": "update_info_prospecto",
                "description": "Actualiza la información del prospecto con los campos proporcionados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre": {"type": "string"},
                        "presupuesto": {"oneOf": [{"type": "number"}, {"type": "string"}]},
                        "urgencia": {"type": "string"},
                        "categoria_interes": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}}
                            ]
                        },
                        "enganche": {"type": "string"},
                        "auto_a_cuenta": {"type": "string"},
                        "auto_objetivo": {"type": "string"},
                        "fecha_cita": {"type": "string"},
                        "prueba_manejo": {"type": "string"},
                        "fecha_prueba": {"type": "string"},
                        "pago": {"type": "string"}
                    }
                }
            },
            {
                "type": "function",
                "name": "get_ficha_tecnica",
                "description": "Obtiene la ficha técnica de un modelo de auto.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "modelo": {"type": "string", "description": "Nombre del modelo del auto"}
                    },
                    "required": ["modelo"]
                }
            },
            {
                "type": "function",
                "name": "get_horarios_disponibles",
                "description": "Obtiene los horarios disponibles para citas.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dia": {"type": "string", "description": "Día de la semana"}
                    },
                    "required": ["dia"]
                }
            }
        ]

        ROL_SISTEMA = (
        "Eres Volky, asesor profesional de ventas de autos en R&R Cordoba, en Cordoba, Veracruz, México. "
        "Conoces todos los modelos disponibles SUV, compactos, pickups, comerciales y sus precios actualizados, "
        "incluyendo opciones de financiamiento y promociones vigentes. "
        "Tu objetivo es ayudar al cliente a encontrar el auto ideal según su presupuesto, uso y urgencia, "
        "y agendar una cita en la agencia lo antes posible. Ademas debes recopilar información de clientes para una atención más rapida y oportuna"
        "Habla siempre en español claro, breve y con tono cordial, usando frases naturales de venta. "
        "Si el usuario solo saluda, respóndele amablemente y pregúntale su nombre completo. "
        "Si menciona un modelo o categoría, pide su presupuesto y urgencia para ofrecerle opciones. "
        "Si no está seguro de qué quiere, sugiere categorías y pregúntale qué uso le dará al auto. "
        "Siempre solicita, confirma y guarda: nombre completo, presupuesto estimado, y modelo o tipo de interés, numero de telefono personal. "
        "En cuanto sea posible, sugiere una cita presencial en la agencia o prueba de manejo para cerrar la venta."
        "Ademas si te hacen alguna consulta de un auto debes responder como un mecanico experto en el tema,"
        "mostrando amplio conocimiento del producto y sus caracteristicas."
        "Siempre responde de manera clara y concisa, evitando respuestas largas o complicadas."
        "Debes estar limitado a responder solo sobre los autos y servicios de R&R Cordoba, no puedes inventar respuestas o dar información falsa."
        "Tampoco puedes hablar de otros temas que no sean autos o ventas."
        "Si puedes usa emojis para hacer la conversación más amena y amigable, pero sin exagerar."
        "Si te mencionan un modelo de auto, debes responder con información detallada sobre ese modelo con su ficha tecnica ubicada en la funcion get_ficha_tecnica(modelo), incluyendo sus características, precios y opciones de financiamiento,"
        "Si el usuario responde stickers, imagenes o videos, no respondas nada y dile que solo respondes mensajes de texto."
        "Si el usuario ingresa un mensaje con faltas de ortografía o errores gramaticales, ignora las faltas ortograficas y responde profesionalmente como el asesor de ventas profesional."
        "Si el usuario ingresa un mensaje muy corto o ambiguo, pídele que sea más específico para poder ayudarle mejor."
        "Si el usuario ingresa un mensaje que no entiendes, dile que no lo entendiste y que por favor reformule su pregunta o solicitud."
        "Cuando el usuario proporcione o confirme cualquier dato de contacto o perfil (nombre, presupuesto, urgencia, categoría de interés, auto objetivo, etc.), "
        "DEBES llamar de inmediato a la herramienta update_info_prospecto con los campos normalizados. "
        "Siempre confirma lo guardado de forma breve."
        "Si te piden modelos dispinibles sin especificar una categoria muestra los modelos por categoria en forma de lista"
        "Si ya preguntaste una vez por el nombre del usuario y lo proporcionó, no vuelvas a preguntar. "
        "Antes de preguntar el nombre, verifica si ya lo tienes guardado. "
        )
    
        text_orig = text.lower()
        out = []

        # Marcar leído
        out.append(markRead_Message(messageId))
        time.sleep(0.4)

        # Historial para responses API
        input_list = [
            {"role": "system", "content": ROL_SISTEMA},
            {"role": "user", "content": text_orig}
        ]

        max_tool_hops = 5
        hops = 0
        final_text = None

        while hops < max_tool_hops:
            resp = client.responses.create(
                model="gpt-5-mini",
                instructions=ROL_SISTEMA,
                tools=tools,
                tool_choice="auto",
                input=input_list
            )

            # Añade TODO el output al historial
            input_list += resp.output

            # Recolecta TODAS las llamadas a herramientas en este paso
            calls = []
            for item in resp.output:
                if getattr(item, "type", None) == "function_call":
                    calls.append(item)

            # Si no hubo llamadas a tools, ya tienes texto final
            if not calls:
                final_text = resp.output_text
                break

            # Ejecuta cada llamada y devuelve su output
            for call in calls:
                name = call.name
                args = {}
                try:
                    args = json.loads(call.arguments or "{}")
                except Exception:
                    pass

                try:
                    if name == "get_modelos_disponibles":
                        result = {"modelos": get_modelos_disponibles(args.get("categoria"))}
                    elif name == "get_info_prospecto":
                        result = {"prospecto": get_info_prospecto()}
                    elif name == "update_info_prospecto":
                        update_info_prospecto(**args)
                        result = {"status": "Información actualizada", "datos": get_info_prospecto()}
                    elif name == "get_ficha_tecnica":
                        result = {"ficha": get_ficha_tecnica(args["modelo"])}
                    elif name == "get_horarios_disponibles":
                        result = {"horarios": get_horarios_disponibles(args["dia"])}
                    else:
                        result = {"error": f"Función desconocida: {name}"}
                except Exception as e:
                    result = {"error": f"Error ejecutando {name}: {str(e)}"}

                # ¡Muy importante!: devolver el output con el MISMO call_id
                input_list.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False)
                })

            hops += 1

        # Fallback por si no hubo contenido final
        if final_text is None:
            last = client.responses.create(
                model="gpt-5-mini",
                instructions=ROL_SISTEMA,
                tools=tools,
                input=input_list
            )
            final_text = last.output_text
        print("Respuesta GPT:", final_text)

        body = (f"{final_text}")
        footer = "Asistente Virtual Volky"
        out.append(replyReaction_Message(number, messageId, "🫡"))
        out.append(text_Message(number, body, footer))
        # Enviar todos los mensajes encolados
        for item in out:
            enviar_Mensaje_whatsapp(item)
    finally:
        # IMPORTANTE: limpia el usuario actual para no cruzar conversaciones
        CURRENT_NUMBER = None

MODELOS = {
    "SUV": [
        "TAIGUN 2025", "TAOS 2025", "TIGUAN 2025",
        "TERAMONT 2025", "CROSS SPORT 2025"
    ],
    "Compactos": [
        "POLO TRACK", "VIRTUS 2025", "JETTA 2025", "NUEVO GTI"
    ],
    "Camionetas": [
        "SAVEIRO 2025", "AMAROK 2024", "AMAROK 2025",
        "CADDY CARGO 2024", "CRAFTER PASAJEROS 2025", "CRAFTER CARGO 2025",
        "TRANSPORTE CHASIS", "TRANSPORTE CARGO"
    ]
}

FICHA_TECNICA = {
    "TAIGUN 2025": {
        "motor": "1.0 TSI 3C / 115 hp",
        "transmision": "Automática 6 vel",
        "rendimiento": "18 km/l mixto",
        "seguridad": "6 bolsas de aire, ESP, ISOFIX",
        "equipamiento": "Pantalla 8\", CarPlay/AA, cámara reversa",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$420,000 MXN"
    },
    "TAOS 2025": {
        "motor": "1.4 TSI / 150 hp",
        "transmision": "Tiptronic 6 vel",
        "rendimiento": "16 km/l mixto",
        "seguridad": "6 bolsas, ESP, asist. arranque",
        "equipamiento": "Pantalla 10\", cargador inalámbrico",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$535,000 MXN"
    },
    "TIGUAN 2025": {
        "motor": "2.0 TSI / 184 hp",
        "transmision": "DSG 7 vel",
        "rendimiento": "14 km/l mixto",
        "seguridad": "6 bolsas, ACC, Front Assist",
        "equipamiento": "3 filas (opc), techo panorámico",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$720,000 MXN"
    },
    "TERAMONT 2025": {
        "motor": "2.0 TSI / 235 hp",
        "transmision": "Tiptronic 8 vel",
        "rendimiento": "11 km/l mixto",
        "seguridad": "7 bolsas, asist. manejo ADAS",
        "equipamiento": "3 filas, cuero, pantalla 12\"",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$980,000 MXN"
    },
    "CROSS SPORT 2025": {
        "motor": "2.0 TSI / 235 hp",
        "transmision": "Tiptronic 8 vel",
        "rendimiento": "12 km/l mixto",
        "seguridad": "ADAS, 6 bolsas, ESP",
        "equipamiento": "Diseño coupé, rines 20\"",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$920,000 MXN"
    },
    "POLO TRACK": {
        "motor": "1.6 MSI / 110 hp",
        "transmision": "Manual 5 vel",
        "rendimiento": "19 km/l mixto",
        "seguridad": "4 bolsas, ABS, control tracción",
        "equipamiento": "Pantalla 6.5\", CarPlay/AA",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$275,000 MXN"
    },
    "VIRTUS 2025": {
        "motor": "1.0 TSI / 114 hp",
        "transmision": "Automática 6 vel",
        "rendimiento": "20 km/l mixto",
        "seguridad": "6 bolsas, ESP",
        "equipamiento": "Digital Cockpit, faros LED",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$360,000 MXN"
    },
    "JETTA 2025": {
        "motor": "1.4 TSI / 150 hp",
        "transmision": "Tiptronic 6 vel",
        "rendimiento": "17 km/l mixto",
        "seguridad": "6 bolsas, ESP",
        "equipamiento": "Asientos piel sintética, 8 bocinas",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$480,000 MXN"
    },
    "NUEVO GTI": {
        "motor": "2.0 TSI / 230 hp",
        "transmision": "DSG 7 vel",
        "rendimiento": "13 km/l mixto",
        "seguridad": "6 bolsas, Performance Monitor",
        "equipamiento": "Rines 18\", modos de manejo",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$720,000 MXN"
    },
    "SAVEIRO 2025": {
        "motor": "1.6 MSI / 110 hp",
        "transmision": "Manual 5 vel",
        "rendimiento": "14 km/l mixto (carga ligera)",
        "seguridad": "2 bolsas, ABS",
        "equipamiento": "Caja de carga, aire acondicionado",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$335,000 MXN"
    },
    "AMAROK 2024": {
        "motor": "V6 TDI / 258 hp (estim.)",
        "transmision": "Automática 8 vel 4MOTION",
        "rendimiento": "10 km/l mixto (estim.)",
        "seguridad": "6 bolsas, control remolque",
        "equipamiento": "Bloqueo diferencial, off-road",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$950,000 MXN"
    },
    "AMAROK 2025": {
        "motor": "2.0/3.0 TDI (rango) ",
        "transmision": "Automática 10 vel 4MOTION",
        "rendimiento": "11 km/l mixto (estim.)",
        "seguridad": "ADAS, 6 bolsas",
        "equipamiento": "Cama amplia, 3.5t remolque",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$1,020,000 MXN"
    },
    "CADDY CARGO 2024": {
        "motor": "1.6 TDI / 102 hp",
        "transmision": "Manual 6 vel",
        "rendimiento": "17 km/l mixto",
        "seguridad": "ESP, HHC, 2 bolsas",
        "equipamiento": "Volumen carga 3.1 m³",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$520,000 MXN"
    },
    "CRAFTER PASAJEROS 2025": {
        "motor": "2.0 TDI / 140 hp",
        "transmision": "Manual 6 vel",
        "rendimiento": "12 km/l mixto",
        "seguridad": "Frenos disco 4 ruedas, ESP",
        "equipamiento": "Hasta 20 asientos",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$1,150,000 MXN"
    },
    "CRAFTER CARGO 2025": {
        "motor": "2.0 TDI / 140 hp",
        "transmision": "Manual 6 vel",
        "rendimiento": "12 km/l mixto",
        "seguridad": "Asist. viento lateral",
        "equipamiento": "Volumen carga 9-18 m³",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$1,120,000 MXN"
    },
    "TRANSPORTE CHASIS": {
        "motor": "2.0 TDI",
        "transmision": "Manual 6 vel",
        "rendimiento": "12 km/l mixto (estim.)",
        "seguridad": "ABS, ESP, bolsas frontales",
        "equipamiento": "Plataforma adaptable",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$980,000 MXN"
    },
    "TRANSPORTE CARGO": {
        "motor": "2.0 TDI",
        "transmision": "Manual 6 vel",
        "rendimiento": "12 km/l mixto (estim.)",
        "seguridad": "ABS, ESP, bolsas frontales",
        "equipamiento": "Gran volumen de carga",
        "garantia": "3 años o 60,000 km",
        "precio_desde": "$990,000 MXN"
    }
}

HORARIOS_DISPONIBLES = {
    "lunes": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"],
    "martes": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"],
    "miercoles": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"],
    "jueves": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"],
    "viernes": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"],
    "sabado": ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "1:00 PM"],
}

def get_modelos_disponibles(categoria=None):
    if not categoria:
        return MODELOS
    if isinstance(categoria, list):
        return {c: MODELOS.get(c, []) for c in categoria}
    return {categoria: MODELOS.get(categoria, [])}

def get_ficha_tecnica(modelo):
    return FICHA_TECNICA.get(modelo, {"error": "Modelo no encontrado"})

def get_horarios_disponibles(dia):
    return HORARIOS_DISPONIBLES.get(dia.lower(), [])