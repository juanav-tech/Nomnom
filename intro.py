import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps
import numpy as np
import time
import json
import paho.mqtt.client as paho

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

# Estilos CSS con diseño lúdico, amigable, sin sombra en el título y contraste optimizado
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
        text-shadow: none; /* Sin sombra detrás del NOMNOM */
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

    .stAlert p, .stAlert span, div[data-baseweb="notification"] div {
        color: #0F172A !important;
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
    </style>
""", unsafe_allow_html=True)

# Configuración del broker MQTT
broker = "broker.mqttdashboard.com"
port = 1883
topic_comunicacion = "voicejuana"

def enviar_mqtt(payload_dict):
    try:
        client = paho.Client("NomNomStreamlitApp")
        client.connect(broker, port)
        mensaje = json.dumps(payload_dict)
        client.publish(topic_comunicacion, mensaje)
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

# --- BARRA LATERAL CON LA ILUSTRACIÓN foto1.png ---
with st.sidebar:
    try:
        imagen_foto1 = Image.open("foto1.png")
        st.image(imagen_foto1, use_column_width=True)
    except Exception:
        st.write("🐾 [foto1.png no encontrada]")
        
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
            tamano = "pequena" if "Pequeña" in tipo_porcion else ("grande" if "Grande" in tipo_porcion else "mediana")
            resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "servir", "porcion": tamano})
            if resultado is True:
                st.success(f"¡Ración {tipo_porcion} enviada al comedero!")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    with col_btn2:
        if st.button("🔒 Cerrar Compuerta"):
            resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar"})
            if resultado is True:
                st.warning("Comando de cierre enviado con éxito.")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Módulo de Asistente de Voz con opciones claras
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Asistente por Voz Inteligente")
    st.markdown("Habla con tu app para activar el dispensador. Debes decir exactamente uno de los siguientes comandos:")
    
    st.markdown("""
        <div style="background-color: #FFF9F5; padding: 12px; border-radius: 10px; border-left: 5px solid #E76F51; margin-bottom: 15px;">
            <b>📌 Comandos permitidos:</b><br>
            • <i>"Porción pequeña"</i><br>
            • <i>"Porción mediana"</i><br>
            • <i>"Porción grande"</i>
        </div>
    """, unsafe_allow_html=True)

    voz_html = """
    <div style="text-align: center; padding: 10px;">
        <button id="voice-btn" style="
            background-color: #2A9D8F; 
            color: white; 
            border: 2px solid #2D2D2D; 
            padding: 12px 24px; 
            border-radius: 12px; 
            font-weight: 800; 
            font-size: 16px; 
            cursor: pointer;
            box-shadow: 3px 3px 0px #2D2D2D;">
            🎙️ Presionar para Hablar
        </button>
        <p id="voice-status" style="color: #2D2D2D; margin-top: 15px; font-size: 15px; font-weight: 700;"></p>
    </div>

    <script>
        const vBtn = document.getElementById('voice-btn');
        const vStatus = document.getElementById('voice-status');

        vBtn.onclick = function() {
            if (!('webkitSpeechRecognition' in window)) {
                vStatus.innerText = "Tu navegador no soporta voz. Usa Google Chrome.";
                return;
            }

            const recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'es-ES';

            recognition.onstart = function() {
                vStatus.innerText = "🎧 Escuchando tu instrucción...";
                vBtn.style.backgroundColor = "#E76F51";
                vBtn.innerText = "🔴 Escuchando...";
            };

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                vStatus.innerText = "💬 Transcripción: \\"" + speechResult + "\\"";
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: speechResult}, '*');
            };

            recognition.onerror = function(event) {
                vStatus.innerText = "⚠️ Error de reconocimiento: " + event.error;
                resetVButton();
            };

            recognition.onend = function() {
                resetVButton();
            };

            recognition.start();
        };

        function resetVButton() {
            vBtn.style.backgroundColor = '#2A9D8F';
            vBtn.innerText = "🎙️ Presionar para Hablar";
        }
    </script>
    """

    components.html(voz_html, height=140)

    comando_voz = st.text_input("O ingresa tu comando de texto manual:", key="txt_voz")
    if comando_voz:
        st.info(f"Procesando comando: **{comando_voz}**")
        res = enviar_mqtt({"dispositivo": "voz", "Act1": comando_voz.strip()})
        if res is True:
            st.success("📡 ¡Instrucción transmitida al dispositivo con éxito!")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# MÓDULO 2: CÁMARA Y MONITOREO DEL HOGAR (KERAS) CON LA ILUSTRACIÓN foto2.png
# =========================================================================
elif pestana == "👁️ Cámara y Monitoreo Hogareño":
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📹 Monitoreo en Directo desde Casa")
    
    # Mostramos la ilustración foto2.png en esta sección de monitoreo
    try:
        imagen_foto2 = Image.open("foto2.png")
        st.image(imagen_foto2, use_column_width=True)
    except Exception:
        st.write("[ foto2.png no encontrada ]")

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

            if indice_clase == 0 or "comida" in clase_detectada.lower() or "lleno" in clase_detectada.lower():
                st.success("🟢 Hay comida")
            else:
                st.warning("🔴 No hay comida")
                
            st.caption(f"Detalle técnico de IA: {clase_detectada} ({confianza:.1f}% de certeza)")

    st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
