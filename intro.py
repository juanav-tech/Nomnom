import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import time
import json
import paho.mqtt.client as paho

# Configuración de página con la identidad NomNom
st.set_page_config(
    page_title="NomNom | Dispensador Inteligente",
    page_icon="🐾",
    layout="centered"
)

# Estilos CSS con la línea gráfica artesanal y contraste optimizado
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

    .stApp {
        background-color: #FDFBF7;
        color: #2D2D2D;
        font-family: 'Montserrat', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #FFF1E6 0%, #FDE2E4 100%);
        padding: 25px;
        border-radius: 16px;
        border: 2px dashed #E07A5F;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(224, 122, 95, 0.1);
        text-align: center;
    }

    .main-header h1 {
        font-family: 'Arial Black', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #DDA15E;
    }

    .main-header p {
        color: #4A4E69 !important;
        font-weight: 700;
    }

    .card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 16px;
        border: 2px solid #F4A261;
        margin-bottom: 20px;
        box-shadow: 0 6px 16px rgba(0,0,0,0.05);
    }

    .card h3, .card p, .card label, .stMarkdown {
        color: #2D2D2D !important;
    }

    .stAlert p, .stAlert span, div[data-baseweb="notification"] div {
        color: #1F2937 !important;
        font-weight: 700 !important;
    }

    .stButton>button {
        background-color: #E76F51;
        color: white;
        border-radius: 10px;
        font-weight: bold;
        border: 2px solid #2D2D2D;
        width: 100%;
        padding: 12px;
        box-shadow: 2px 2px 0px #2D2D2D;
    }

    .stButton>button:hover {
        background-color: #F4A261;
        color: #2D2D2D;
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

# --- CONFIGURACIÓN DE RECEPCIÓN MQTT EN TIEMPO REAL DESDE WOKWI ---
if "respuesta_wokwi" not in st.session_state:
    st.session_state.respuesta_wokwi = "Esperando señal del simulador..."

def al_recibir_mensaje(client, userdata, message):
    st.session_state.respuesta_wokwi = message.payload.decode("utf-8")

@st.cache_resource
def iniciar_receptor():
    try:
        client_sub = paho.Client("StreamlitListenerNomNom")
        client_sub.on_message = al_recibir_mensaje
        client_sub.connect(broker, port)
        client_sub.subscribe(topic_comunicacion)
        client_sub.loop_start()
        return client_sub
    except:
        return None

iniciar_receptor()

# --- ENCABEZADO Y ESPACIO PARA ILUSTRACIÓN ---
col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
with col_img2:
    try:
        st.image("ilustracion_principal.png", use_column_width=True)
    except Exception:
        st.markdown("<div style='text-align: center; color: #E76F51; font-style: italic; font-weight: bold;'>[ Espacio para ilustración estilo boceto / NomNom ]</div>", unsafe_allow_html=True)

st.markdown("""
    <div class="main-header">
        <h1>🐾 NOMNOM</h1>
        <p>Dispensador Inteligente de Alimentos para Mascotas</p>
    </div>
""", unsafe_allow_html=True)

# Menú de navegación
pestana = st.sidebar.radio("🎛️ Navegación", ["🏠 Panel de Control e IoT", "👁️ Cámara y Monitoreo"])

# =========================================================================
# MÓDULO 1: CONTROL MANUAL Y VOZ (MQTT & WOKWI)
# =========================================================================
if pestana == "🏠 Panel de Control e IoT":
    
    # Tarjeta de Estado en Tiempo Real desde Wokwi
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📡 Estado en Tiempo Real desde Wokwi")
    st.info(f"**Respuesta del ESP32:** {st.session_state.respuesta_wokwi}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🍽️ Panel de Alimentación Rápida")
    st.write("Selecciona la porción exacta para tu mascota y envíala al dispositivo IoT[cite: 7, 10].")

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

    # Módulo de Reconocimiento de Voz
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Asistente por Voz")
    st.write("Habla con tu app para activar el dispensador de forma remota:")

    voz_html = """
    <div style="text-align: center; padding: 10px;">
        <button id="voice-btn" style="
            background-color: #2A9D8F; 
            color: white; 
            border: 2px solid #2D2D2D; 
            padding: 12px 24px; 
            border-radius: 10px; 
            font-weight: bold; 
            font-size: 16px; 
            cursor: pointer;
            box-shadow: 2px 2px 0px #2D2D2D;">
            🎙️ Presionar para Hablar
        </button>
        <p id="voice-status" style="color: #2D2D2D; margin-top: 10px; font-size: 14px; font-weight: 600;"></p>
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
                vStatus.innerText = "Escuchando instrucción...";
                vBtn.style.backgroundColor = "#E76F51";
                vBtn.innerText = "🔴 Escuchando...";
            };

            recognition.onresult = function(event) {
                const speechResult = event.results[0][0].transcript;
                vStatus.innerText = "Comando reconocido: " + speechResult;
                window.parent.postMessage({type: 'streamlit:setComponentValue', value: speechResult}, '*');
            };

            recognition.onerror = function(event) {
                vStatus.innerText = "Error: " + event.error;
                resetVButton();
            };

            recognition.onend = function() {
                resetVButton();
            };

            recognition.start();
        };

        function resetVButton() {
            vBtn.style.backgroundColor = #2A9D8F;
            vBtn.innerText = "🎙️ Presionar para Hablar";
        }
    </script>
    """

    components.html(voz_html, height=130)

    comando_voz = st.text_input("O escribe tu instrucción manual:", key="txt_voz")
    if comando_voz:
        st.info(f"Procesando: **{comando_voz}**")
        res = enviar_mqtt({"dispositivo": "voz", "Act1": comando_voz.strip()})
        if res is True:
            st.success("📡 ¡Instrucción transmitida a Wokwi exitosamente!")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# MÓDULO 2: CÁMARA Y MONITOREO DEL PLATO
# =========================================================================
elif pestana == "👁️ Cámara y Monitoreo":
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📸 Monitoreo del Plato de la Mascota")
    st.write("Toma una fotografía actual para verificar visualmente si tu mascota ya comió[cite: 7, 10].")

    foto_plato = st.camera_input("Toma una foto del comedero")

    if foto_plato is not None:
        st.success("✨ Imagen capturada correctamente y lista para supervisión.")
        st.info("💡 Consejo: Puedes usar esta vista para comprobar el estado físico del plato en casa estés donde estés[cite: 7, 10].")

    st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
