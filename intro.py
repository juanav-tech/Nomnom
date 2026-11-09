import os
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import time
import json
import paho.mqtt.client as paho

# Importación segura de OpenAI para Whisper
try:
    from openai import OpenAI
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False

# Importación segura de TensorFlow y Keras
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TF_DISPONIBLE = True
except Exception:
    TF_DISPONIBLE = False

# Configuración de página con la identidad NomNom
st.set_page_config(
    page_title="NomNom | Dispensador Inteligente",
    page_icon="🐾",
    layout="centered"
)

# Estilos CSS con diseño lúdico y contraste corregido en las alertas
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;800&display=swap');

    .stApp {
        background-color: #FAF5EE;
        color: #2D2D2D;
        font-family: 'Montserrat', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #FFF1E6 0%, #FDE2E4 100%);
        padding: 25px;
        border-radius: 20px;
        border: 3px dashed #E07A5F;
        margin-bottom: 25px;
        box-shadow: 0 6px 20px rgba(224, 122, 95, 0.15);
        text-align: center;
    }

    .main-header h1 {
        font-family: 'Montserrat', sans-serif;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #DDA15E;
        font-size: 38px;
        text-shadow: none;
    }

    .main-header p {
        color: #4A4E69 !important;
        font-weight: 700;
        font-size: 16px;
    }

    .card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 20px;
        border: 3px solid #F4A261;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
    }

    .card h3 {
        color: #1E293B !important;
        font-weight: 800;
    }
    
    .card p, .card label, .stMarkdown, span {
        color: #334155 !important;
        font-weight: 600;
    }

    /* Estilo para asegurar legibilidad en el campo de texto manual */
    .stTextInput input {
        color: #1E293B !important;
        background-color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 2px solid #F4A261 !important;
        border-radius: 8px;
    }

    .stTextInput label p {
        color: #1E293B !important;
        font-weight: 700 !important;
    }

    /* Corrección de alto contraste para las cajas de éxito, advertencia y error */
    div.stAlert {
        background-color: #FFFDF9 !important;
        border: 2px solid #F4A261 !important;
        border-radius: 12px !important;
    }

    .stAlert p, .stAlert span, div[data-baseweb="notification"] div {
        color: #1E293B !important;
        font-weight: 700 !important;
    }

    .stButton>button {
        background-color: #E76F51;
        color: white !important;
        border-radius: 12px;
        font-weight: 800;
        border: 2px solid #2D2D2D;
        width: 100%;
        padding: 12px;
        box-shadow: 3px 3px 0px #2D2D2D;
        transition: 0.2s;
    }

    .stButton>button:hover {
        background-color: #F4A261;
        color: #2D2D2D !important;
        transform: translateY(-2px);
    }

    /* Grabador de audio nativo */
    [data-testid="stAudioInput"] {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        border: 2px solid #F4A261 !important;
        padding: 12px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Configuración MQTT con tu tópico 'voicejuana'
broker = "broker.mqttdashboard.com"
port = 1883
mqtt_topic = "voicejuana"

def enviar_mqtt(payload_dict):
    try:
        client = paho.Client(f"NomNomClient_{int(time.time())}")
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        mensaje = json.dumps(payload_dict)
        info = client.publish(mqtt_topic, mensaje)
        info.wait_for_publish(timeout=3)
        client.loop_stop()
        client.disconnect()
        return True
    except Exception as e:
        return str(e)

# Cargar el modelo Keras con caché
@st.cache_resource
def cargar_modelo_teachable():
    if not TF_DISPONIBLE:
        return None, None
    try:
        model = load_model('keras_model.h5', compile=False)
        with open('labels.txt', 'r', encoding='utf-8') as f:
            class_names = [line.strip() for line in f.readlines()]
        return model, class_names
    except Exception as e:
        return None, None

# --- LAYOUT SUPERIOR: IMAGEN PRINCIPAL (coca.png) ---
col_img1, col_img_main, col_img3 = st.columns([1, 2, 1])

with col_img_main:
    try:
        imagen_coca = Image.open("coca.png")
        st.image(imagen_coca, use_column_width=True)
    except Exception:
        st.markdown("<div style='text-align: center; color: #E76F51; font-weight: bold;'>[ Imagen coca.png no encontrada ]</div>", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🐾 NOMNOM</h1>
        <p>Tu dispensador inteligente y amigable para consentir a tu peludo</p>
    </div>
""", unsafe_allow_html=True)

# --- BARRA LATERAL CON LA ILUSTRACIÓN foto1.png Y CAMPO PARA LA API KEY ---
with st.sidebar:
    try:
        imagen_foto1 = Image.open("foto1.png")
        st.image(imagen_foto1, use_column_width=True)
    except Exception:
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

    pestana = st.radio("🎛️ Opciones", ["🏠 Panel de Control e IoT", "👁️ Cámara y Monitoreo Hogareño"])

# =========================================================================
# MÓDULO 1: CONTROL MANUAL Y ASISTENTE DE VOZ
# =========================================================================
if pestana == "🏠 Panel de Control e IoT":
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🍽️ Panel de Alimentación Rápida")
    st.markdown("Selecciona el tamaño de la porción que deseas dispensar y envía la orden al instante.")

    tipo_porcion = st.selectbox(
        "📏 Tamaño de la ración:",
        ["Porción Pequeña (50g)", "Porción Mediana (100g)", "Porción Grande (200g)"]
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Servir Comida"):
            if "Pequeña" in tipo_porcion:
                tamano = "pequena"
                angulo_motor = 45
            elif "Grande" in tipo_porcion:
                tamano = "grande"
                angulo_motor = 180
            else:
                tamano = "mediana"
                angulo_motor = 90

            resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "servir", "porcion": tamano, "angulo": angulo_motor, "status": "GREEN"})
            if resultado is True:
                st.success(f"¡Ración {tipo_porcion} enviada al comedero correctamente!")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    with col_btn2:
        if st.button("🔒 Cerrar Compuerta"):
            resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar", "angulo": 0, "status": "RED"})
            if resultado is True:
                st.warning("Comando de cierre enviado con éxito (Indicador rojo en Wokwi).")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Asistente de voz conectado con la API Key ingresada en el menú lateral
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Asistente por Voz Inteligente")
    st.markdown("Graba tu voz diciendo **exactamente uno de los siguientes comandos permitidos**:")
    
    st.markdown("""
        <div style="background-color: #FFF9F5; padding: 14px; border-radius: 10px; border-left: 5px solid #E76F51; margin-bottom: 15px;">
            <b>📌 Comandos permitidos para abrir o cerrar:</b><br>
            • <i>"Porción pequeña"</i><br>
            • <i>"Porción mediana"</i><br>
            • <i>"Porción grande"</i><br>
            • <i>"Cerrar compuerta"</i>
        </div>
    """, unsafe_allow_html=True)

    audio_file = st.audio_input("Grabar instrucción de voz", key="mic_recorder")

    captured_text = None

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
                    st.info(f"🗣️ *Lo que la IA escuchó:* \"{captured_text}\"")
                except Exception as e:
                    st.error(f"Error procesando el audio: {e}")
        else:
            st.warning("⚠️ Por favor ingresa tu OpenAI API Key en la barra lateral para procesar el audio con Whisper.")

    # Opción manual complementaria
    comando_voz = st.text_input("O ingresa tu comando de forma manual:", key="txt_voz", placeholder="Ej: porción pequeña, cerrar compuerta...")
    if comando_voz:
        captured_text = comando_voz

    # Filtrado y validación estricta de los 4 comandos permitidos con sus respectivos ángulos internos y cambio de color del bombillo
    if captured_text:
        cmd_lower = captured_text.strip().lower()
        st.info(f"Procesando comando: **{captured_text}**")
        
        es_porcion_pequena = "pequeña" in cmd_lower or "pequena" in cmd_lower
        es_porcion_mediana = "mediana" in cmd_lower
        es_porcion_grande = "grande" in cmd_lower
        es_cerrar = "cerrar" in cmd_lower

        if es_cerrar:
            res = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar", "angulo": 0, "status": "RED"})
            if res is True:
                st.warning("🔒 ¡Compuerta cerrada! Indicador cambiado a luz roja en Wokwi.")
            else:
                st.error(f"Error de conexión MQTT: {res}")
                
        elif es_porcion_pequena or es_porcion_mediana or es_porcion_grande:
            if es_porcion_pequena:
                porcion_str = "pequena"
                angulo_motor = 45
            elif es_porcion_grande:
                porcion_str = "grande"
                angulo_motor = 180
            else:
                porcion_str = "mediana"
                angulo_motor = 90

            res = enviar_mqtt({"dispositivo": "dispensador", "accion": "servir", "porcion": porcion_str, "angulo": angulo_motor, "status": "GREEN"})
            if res is True:
                st.success(f"📡 ¡Comando detectado! Ración enviada al dispositivo con éxito.")
            else:
                st.error(f"Error al enviar por MQTT: {res}")
        else:
            st.error("⚠️ Comando no reconocido. Solo se permite: 'Porción pequeña', 'Porción mediana', 'Porción grande' o 'Cerrar compuerta'.")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# MÓDULO 2: CÁMARA Y MONITOREO HOGAREÑO CON foto2.png (CLASE 1)
# =========================================================================
elif pestana == "👁️ Cámara y Monitoreo Hogareño":
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📹 Monitoreo en Directo desde Casa")
    
    try:
        imagen_foto2 = Image.open("foto2.png")
        st.image(imagen_foto2, use_column_width=True)
    except Exception:
        pass

    st.markdown("Aquí puedes observar la comida de tu mascota en tiempo real a través de la cámara del hogar.")

    modelo, clases = cargar_modelo_teachable()

    if modelo is None:
        st.error("⚠️ No se pudieron cargar los archivos `keras_model.h5` o `labels.txt` en el repositorio.")
    else:
        captura_camara = st.camera_input("Vista del plato en casa")

        if captura_camara is not None:
            image = Image.open(captura_camara).convert("RGB")
            
            size = (224, 224)
            image_resized = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
            image_array = np.asarray(image_resized)
            
            normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            data[0] = normalized_image_array

            prediccion = modelo.predict(data)
            indice_clase = np.argmax(prediccion[0])
            clase_detectada = clases[indice_clase]
            confianza = float(prediccion[0][indice_clase]) * 100

            st.divider()
            st.markdown("### 🔍 Análisis del Comedero:")

            if indice_clase == 1 or "clase 1" in clase_detectada.lower() or "lleno" in clase_detectada.lower() or "comida" in clase_detectada.lower():
                st.success("🟢 Aún hay comida en comedero")
            else:
                st.warning("🔴 no se detectó comida en el comedero")
                
            st.caption(f"Detalle técnico de IA: Detectado [{clase_detectada}] con {confianza:.1f}% de certeza")

    st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
