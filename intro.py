import os
import html
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import time
import json
import paho.mqtt.client as paho

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Importación segura de OpenAI para Whisper
try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False

# Importación segura de TensorFlow y Keras (guardando el error real)
TF_ERROR = None
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    from tensorflow.keras.layers import DepthwiseConv2D
    TF_DISPONIBLE = True
except Exception as e:
    TF_DISPONIBLE = False
    TF_ERROR = f"No se pudo importar TensorFlow: {e}"

# Configuración de página con la identidad NomNom
st.set_page_config(
    page_title="NomNom | Dispensador Inteligente",
    page_icon="🐾",
    layout="centered"
)

# =========================================================================
# ESTILOS (alto contraste en todos los textos y alertas)
# =========================================================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    html, body, .stApp {
        background-color: #FAF5EE;
        font-family: 'Montserrat', sans-serif;
    }

    /* Textos generales siempre oscuros */
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp label, .stApp li,
    .stMarkdown p, [data-testid="stMarkdownContainer"] p {
        color: #1E293B;
    }
    .stApp h2, .stApp h3 { font-weight: 800; }
    [data-testid="stCaptionContainer"] p { color: #475569 !important; font-weight: 600; }

    /* ---------- Encabezado ---------- */
    .main-header {
        background: linear-gradient(135deg, #FFF1E6 0%, #FDE2E4 100%);
        padding: 22px 20px;
        border-radius: 22px;
        border: 3px dashed #E07A5F;
        margin: 8px 0 22px 0;
        box-shadow: 0 6px 20px rgba(224, 122, 95, 0.15);
        text-align: center;
    }
    .main-header h1 {
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 3px;
        color: #C2410C !important;
        font-size: 38px;
        margin: 0 0 6px 0;
        padding: 0;
    }
    .main-header p {
        color: #3B3F5C !important;
        font-weight: 700;
        font-size: 16px;
        margin: 0;
    }

    /* ---------- Tarjetas (st.container con borde) ---------- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 3px solid #F4A261 !important;
        border-radius: 20px !important;
        padding: 14px 18px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }

    /* ---------- Pestañas ---------- */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #FFF1E6;
        border-radius: 12px 12px 0 0;
        padding: 10px 18px;
    }
    .stTabs [data-baseweb="tab"] p {
        color: #3B3F5C !important;
        font-weight: 800;
    }
    .stTabs [aria-selected="true"] { background-color: #E76F51; }
    .stTabs [aria-selected="true"] p { color: #FFFFFF !important; }

    /* ---------- Barra lateral ---------- */
    [data-testid="stSidebar"] { background-color: #FFF1E6; }
    [data-testid="stSidebar"] h3 { color: #1E293B; }

    /* ---------- Campos de entrada ---------- */
    .stTextInput input {
        color: #1E293B !important;
        background-color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 2px solid #F4A261 !important;
        border-radius: 8px;
    }
    .stTextInput input::placeholder { color: #64748B !important; }
    .stTextInput label p { color: #1E293B !important; font-weight: 700 !important; }

    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 2px solid #F4A261 !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="select"] * { color: #1E293B !important; font-weight: 700; }
    div[data-baseweb="popover"] ul { background-color: #FFFFFF !important; }
    div[data-baseweb="popover"] li, div[data-baseweb="popover"] li * {
        color: #1E293B !important;
    }

    /* ---------- Alertas propias (contraste garantizado) ---------- */
    .alerta {
        padding: 14px 18px;
        border-radius: 14px;
        border: 2px solid;
        font-weight: 700;
        font-size: 15px;
        line-height: 1.45;
        margin: 12px 0 6px 0;
    }
    .alerta-success { background: #D8F3DC; color: #123D2A !important; border-color: #2D6A4F; }
    .alerta-warning { background: #FFE8CC; color: #4A2300 !important; border-color: #D9822B; }
    .alerta-error   { background: #FFD9D9; color: #5E0B0B !important; border-color: #C1121F; }
    .alerta-info    { background: #DCEBFF; color: #0B2A4A !important; border-color: #1D4E89; }

    /* ---------- Chips de estado ---------- */
    .chips { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
    .chip {
        flex: 1 1 180px;
        background: #FFFFFF;
        border: 2px solid #F4A261;
        border-radius: 16px;
        padding: 10px 14px;
        text-align: center;
    }
    .chip .chip-t { color: #475569 !important; font-size: 12px; font-weight: 800;
                    text-transform: uppercase; letter-spacing: 1px; }
    .chip .chip-v { color: #1E293B !important; font-size: 18px; font-weight: 800; }

    /* ---------- Botones ---------- */
    .stButton>button {
        background-color: #E76F51;
        border-radius: 12px;
        font-weight: 800;
        border: 2px solid #2D2D2D;
        width: 100%;
        padding: 12px;
        box-shadow: 3px 3px 0px #2D2D2D;
        transition: 0.2s;
    }
    .stButton>button, .stButton>button * { color: #FFFFFF !important; }
    .stButton>button:hover { background-color: #F4A261; transform: translateY(-2px); }
    .stButton>button:hover, .stButton>button:hover * { color: #2D2D2D !important; }

    /* ---------- Audio y cámara ---------- */
    [data-testid="stAudioInput"], [data-testid="stCameraInput"] {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        border: 2px solid #F4A261 !important;
        padding: 12px !important;
    }
    [data-testid="stAudioInput"] *, [data-testid="stCameraInput"] label p {
        color: #1E293B !important;
    }

    .comandos-box {
        background-color: #FFF4EC;
        padding: 14px 16px;
        border-radius: 12px;
        border-left: 6px solid #E76F51;
        margin: 8px 0 16px 0;
        color: #1E293B;
        font-weight: 600;
        line-height: 1.7;
    }
    </style>
""", unsafe_allow_html=True)


# =========================================================================
# UTILIDADES
# =========================================================================
def alerta(tipo, texto):
    """Mensaje con colores de alto contraste. `texto` puede incluir <b>."""
    iconos = {"success": "✅", "warning": "🔒", "error": "⚠️", "info": "💬"}
    st.markdown(
        f'<div class="alerta alerta-{tipo}">{iconos.get(tipo, "")} {texto}</div>',
        unsafe_allow_html=True
    )


def encontrar_imagen(nombre):
    """Busca la imagen por nombre (sin importar mayúsculas) en la carpeta del
    script, en la carpeta de trabajo y en sus subcarpetas."""
    for carpeta in (BASE_DIR, os.getcwd(), os.path.dirname(BASE_DIR)):
        ruta = os.path.join(carpeta, nombre)
        if os.path.isfile(ruta):
            return ruta

    ignorar = {"node_modules", "venv", "env", "__pycache__"}
    for raiz in dict.fromkeys([BASE_DIR, os.getcwd()]):
        for carpeta, subdirs, archivos in os.walk(raiz):
            subdirs[:] = [d for d in subdirs if not d.startswith(".") and d not in ignorar]
            for a in archivos:
                if a.lower() == nombre.lower():
                    return os.path.join(carpeta, a)
    return None


def mostrar_imagen(nombre):
    """Muestra la imagen sin importar la versión de Streamlit. Devuelve True si se mostró."""
    ruta = encontrar_imagen(nombre)
    if ruta is None:
        return False
    try:
        img = Image.open(ruta)
        try:
            st.image(img, use_container_width=True)
        except TypeError:
            st.image(img, use_column_width=True)
        return True
    except Exception:
        return False


# Configuración MQTT
broker = "broker.mqttdashboard.com"
port = 1883
mqtt_topic = "voicejuana"


def crear_cliente_mqtt():
    """Cliente MQTT compatible con paho-mqtt 1.x y 2.x."""
    nombre = f"NomNomClient_{int(time.time())}"
    try:
        return paho.Client(paho.CallbackAPIVersion.VERSION1, nombre)  # paho 2.x
    except AttributeError:
        return paho.Client(nombre)  # paho 1.x


def enviar_mqtt(payload_dict):
    try:
        client = crear_cliente_mqtt()
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        mensaje = json.dumps(payload_dict)
        info = client.publish(mqtt_topic, mensaje)
        info.wait_for_publish(timeout=3)
        time.sleep(0.5)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        return str(e)


def despachar(payload, tipo_ok, texto_ok, estado, ultimo):
    """Envía por MQTT y devuelve (tipo, texto) para mostrar el resultado."""
    res = enviar_mqtt(payload)
    if res is True:
        st.session_state.estado = estado
        st.session_state.ultimo = ultimo
        return tipo_ok, texto_ok
    return "error", f"Error de conexión MQTT: {html.escape(str(res))}"


# Cargar el modelo Keras con caché (devuelve el error real si falla)
@st.cache_resource
def cargar_modelo_teachable():
    if not TF_DISPONIBLE:
        return None, None, TF_ERROR

    ruta_modelo = os.path.join(BASE_DIR, "keras_model.h5")
    ruta_labels = os.path.join(BASE_DIR, "labels.txt")

    if not os.path.exists(ruta_modelo):
        return None, None, f"No existe keras_model.h5. Archivos en la carpeta: {os.listdir(BASE_DIR)}"
    if not os.path.exists(ruta_labels):
        return None, None, f"No existe labels.txt. Archivos en la carpeta: {os.listdir(BASE_DIR)}"

    # Parche para el argumento 'groups' que incluye Teachable Machine
    class CompatDepthwiseConv2D(DepthwiseConv2D):
        def __init__(self, *args, **kwargs):
            kwargs.pop("groups", None)
            super().__init__(*args, **kwargs)

    try:
        model = load_model(
            ruta_modelo,
            compile=False,
            custom_objects={"DepthwiseConv2D": CompatDepthwiseConv2D},
        )
        with open(ruta_labels, "r", encoding="utf-8") as f:
            class_names = [line.strip() for line in f.readlines()]
        return model, class_names, None
    except Exception as e:
        return None, None, f"Error al leer el modelo: {e}"


# Estado de la sesión
if "estado" not in st.session_state:
    st.session_state.estado = "Cerrada"
if "ultimo" not in st.session_state:
    st.session_state.ultimo = "—"

# =========================================================================
# ENCABEZADO
# =========================================================================
col_a, col_img_main, col_c = st.columns([1, 2, 1])
with col_img_main:
    if not mostrar_imagen("coca.png"):
        st.caption("[ Imagen coca.png no encontrada ]")

st.markdown("""
    <div class="main-header">
        <h1>🐾 NomNom</h1>
        <p>Tu dispensador inteligente y amigable para consentir a tu peludo</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================================
# BARRA LATERAL: ILUSTRACIÓN foto1.png Y API KEY
# =========================================================================
with st.sidebar:
    if not mostrar_imagen("foto1.png"):
        st.write("🐾 Menú de Control")

    st.markdown("### 🔑 Configuración de IA")
    api_key_input = st.text_input(
        "OpenAI API Key:",
        type="password",
        placeholder="sk-...",
        key="main_api_key_input"
    )
    if api_key_input:
        os.environ['OPENAI_API_KEY'] = api_key_input

    faltantes = [n for n in ("coca.png", "foto1.png", "foto2.png") if encontrar_imagen(n) is None]
    if faltantes:
        with st.expander("🔧 Imágenes no encontradas"):
            st.write("Faltan:", ", ".join(faltantes))
            st.write("Archivos en la carpeta de la app:")
            st.code("\n".join(sorted(os.listdir(BASE_DIR))))

tab_panel, tab_camara = st.tabs(["🏠 Panel de Control e IoT", "👁️ Cámara y Monitoreo"])

# =========================================================================
# MÓDULO 1: CONTROL MANUAL Y ASISTENTE DE VOZ
# =========================================================================
with tab_panel:

    chips_slot = st.empty()  # se llena al final, con el estado ya actualizado

    # ---------- Panel de alimentación ----------
    resultado_panel = None
    with st.container(border=True):
        st.subheader("🍽️ Panel de Alimentación Rápida")
        st.markdown("Selecciona el tamaño de la ración y envía la orden al instante.")

        tipo_porcion = st.selectbox(
            "📏 Tamaño de la ración:",
            ["Porción Pequeña (50g)", "Porción Mediana (100g)", "Porción Grande (200g)"]
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Servir Comida"):
                if "Pequeña" in tipo_porcion:
                    tamano, angulo_val = "pequena", 45
                elif "Grande" in tipo_porcion:
                    tamano, angulo_val = "grande", 180
                else:
                    tamano, angulo_val = "mediana", 90

                resultado_panel = despachar(
                    {"dispositivo": "dispensador", "accion": "servir", "porcion": tamano,
                     "angulo": angulo_val, "status": "GREEN"},
                    "success",
                    f"¡Ración <b>{html.escape(tipo_porcion)}</b> enviada al comedero correctamente!",
                    f"Abierta ({tamano})", f"Servir {tamano}"
                )

        with col_btn2:
            if st.button("🔒 Cerrar Compuerta"):
                resultado_panel = despachar(
                    {"dispositivo": "dispensador", "accion": "cerrar", "angulo": 0, "status": "RED"},
                    "warning",
                    "Comando de cierre enviado con éxito. <b>Indicador rojo</b> activado en Wokwi.",
                    "Cerrada", "Cerrar compuerta"
                )

        if resultado_panel:
            alerta(*resultado_panel)

    # ---------- Asistente de voz ----------
    resultado_voz = None
    with st.container(border=True):
        st.subheader("🎙️ Asistente por Voz Inteligente")
        st.markdown("Graba tu voz diciendo **exactamente uno** de los comandos permitidos:")

        st.markdown("""
            <div class="comandos-box">
                📌 <b>Comandos permitidos:</b><br>
                • <i>"Porción pequeña"</i><br>
                • <i>"Porción mediana"</i><br>
                • <i>"Porción grande"</i><br>
                • <i>"Cerrar compuerta"</i>
            </div>
        """, unsafe_allow_html=True)

        audio_file = st.audio_input("Grabar instrucción de voz", key="mic_recorder")

        captured_text = None
        mensajes_voz = []

        if audio_file:
            if api_key_input and HAS_OPENAI:
                with st.spinner("Procesando audio con Whisper AI..."):
                    try:
                        client_ai = OpenAI(api_key=api_key_input)
                        transcript = client_ai.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="es"
                        )
                        captured_text = transcript.text.strip()
                        mensajes_voz.append(("info", f"🗣️ Lo que la IA escuchó: <b>\"{html.escape(captured_text)}\"</b>"))
                    except Exception as e:
                        mensajes_voz.append(("error", f"Error procesando el audio: {html.escape(str(e))}"))
            else:
                mensajes_voz.append(("warning", "Ingresa tu OpenAI API Key en la barra lateral para procesar el audio con Whisper."))

        # Opción manual complementaria
        comando_voz = st.text_input(
            "O ingresa tu comando de forma manual:",
            key="txt_voz",
            placeholder="Ej: porción pequeña, cerrar compuerta..."
        )
        if comando_voz:
            captured_text = comando_voz

        for m in mensajes_voz:
            alerta(*m)

        # Validación estricta con ángulos y LED independientes
        if captured_text:
            cmd_lower = captured_text.strip().lower()
            alerta("info", f"Procesando comando: <b>{html.escape(captured_text)}</b>")

            if "cerrar" in cmd_lower:
                resultado_voz = despachar(
                    {"dispositivo": "dispensador", "accion": "cerrar", "angulo": 0, "status": "RED"},
                    "warning", "¡Compuerta cerrada! Indicador cambiado a <b>luz roja</b> en Wokwi.",
                    "Cerrada", "Voz: cerrar compuerta"
                )
            elif "pequeña" in cmd_lower or "pequena" in cmd_lower:
                resultado_voz = despachar(
                    {"dispositivo": "dispensador", "accion": "servir", "porcion": "pequena",
                     "angulo": 45, "status": "GREEN"},
                    "success", "¡Comando detectado! <b>Porción pequeña</b> enviada al dispositivo.",
                    "Abierta (pequena)", "Voz: porción pequeña"
                )
            elif "grande" in cmd_lower:
                resultado_voz = despachar(
                    {"dispositivo": "dispensador", "accion": "servir", "porcion": "grande",
                     "angulo": 180, "status": "GREEN"},
                    "success", "¡Comando detectado! <b>Porción grande</b> enviada al dispositivo.",
                    "Abierta (grande)", "Voz: porción grande"
                )
            elif "mediana" in cmd_lower:
                resultado_voz = despachar(
                    {"dispositivo": "dispensador", "accion": "servir", "porcion": "mediana",
                     "angulo": 90, "status": "GREEN"},
                    "success", "¡Comando detectado! <b>Porción mediana</b> enviada al dispositivo.",
                    "Abierta (mediana)", "Voz: porción mediana"
                )
            else:
                resultado_voz = (
                    "error",
                    "Comando no reconocido. Solo se permite: <b>'Porción pequeña'</b>, "
                    "<b>'Porción mediana'</b>, <b>'Porción grande'</b> o <b>'Cerrar compuerta'</b>."
                )

            alerta(*resultado_voz)

    # Chips de estado (ya con el estado actualizado)
    chips_slot.markdown(f"""
        <div class="chips">
            <div class="chip"><div class="chip-t">Compuerta</div>
                <div class="chip-v">{html.escape(st.session_state.estado)}</div></div>
            <div class="chip"><div class="chip-t">Último comando</div>
                <div class="chip-v">{html.escape(st.session_state.ultimo)}</div></div>
        </div>
    """, unsafe_allow_html=True)

# =========================================================================
# MÓDULO 2: CÁMARA Y MONITOREO HOGAREÑO CON foto2.png
# =========================================================================
with tab_camara:

    with st.container(border=True):
        st.subheader("📹 Monitoreo en Directo desde Casa")

        mostrar_imagen("foto2.png")

        st.markdown("Observa la comida de tu mascota a través de la cámara del hogar.")

        modelo, clases, error_modelo = cargar_modelo_teachable()

        if modelo is None:
            alerta("error", "No se pudo cargar el modelo de Teachable Machine.")
            st.code(error_modelo)  # Aquí verás la causa exacta

        # La cámara se muestra siempre, aunque el modelo falle
        captura_camara = st.camera_input("Vista del plato en casa")

        if captura_camara is not None and modelo is not None:
            image = Image.open(captura_camara).convert("RGB")

            size = (224, 224)
            image_resized = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
            image_array = np.asarray(image_resized)

            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            data[0] = normalized_image_array

            prediccion = modelo.predict(data)
            indice_clase = int(np.argmax(prediccion[0]))
            clase_detectada = clases[indice_clase]
            confianza = float(prediccion[0][indice_clase]) * 100

            st.divider()
            st.markdown("### 🔍 Análisis del Comedero")

            if (indice_clase == 1 or "clase 1" in clase_detectada.lower()
                    or "lleno" in clase_detectada.lower() or "comida" in clase_detectada.lower()):
                alerta("success", "🟢 <b>Aún hay comida en el comedero</b>")
            else:
                alerta("warning", "🔴 <b>No se detectó comida en el comedero</b>")

            st.caption(f"Detalle técnico de IA: Detectado [{clase_detectada}] con {confianza:.1f}% de certeza")

os.makedirs("temp", exist_ok=True)
