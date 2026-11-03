import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import time
import json
import paho.mqtt.client as paho

# Configuración de página con diseño estético de NomNom
st.set_page_config(
    page_title="NomNom | Dispensador Inteligente",
    page_icon="🐾",
    layout="centered"
)

# Estilos CSS personalizados alineados con la identidad visual del proyecto
st.markdown("""
    <style>
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
    }
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px;
        border-radius: 14px;
        border-left: 6px solid #F97316;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        text-align: center;
    }
    .card {
        background-color: #1E293B;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 15px;
    }
    .stButton>button {
        background-color: #F97316;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        width: 100%;
        padding: 10px;
    }
    .stButton>button:hover {
        background-color: #EA580C;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Configuración del broker MQTT
broker = "broker.mqttdashboard.com"
port = 1883
topic = "voicejuana"

def enviar_mqtt(payload_dict):
    try:
        client = paho.Client("NomNomStreamlitApp")
        client.connect(broker, port)
        mensaje = json.dumps(payload_dict)
        client.publish(topic, mensaje)
        client.disconnect()
        return True
    except Exception as e:
        return str(e)

# Encabezado principal de NomNom
st.markdown("""
    <div class="main-header">
        <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">🐾 NomNom - Dispensador Inteligente</h1>
        <p style="color: #94A3B8; margin: 5px 0 0 0;">Alimenta y cuida a tus mascotas a distancia vía MQTT y Wokwi</p>
    </div>
""", unsafe_allow_html=True)

# Tarjeta de Control por Voz y Botones Manuales
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🎙️ Panel de Control Multimodal")
st.write("Selecciona una porción o utiliza el reconocimiento de voz para activar el dispensador en casa[cite: 7, 10].")

# Opciones de porciones orientadas al negocio de la app
tipo_porcion = st.selectbox(
    "📏 Elige el tamaño de la porción:",
    ["Porción Pequeña (50g)", "Porción Mediana (100g)", "Porción Grande (200g)"]
)

col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Servir porción ahora"):
        tamano = "pequena" if "Pequeña" in tipo_porcion else ("grande" if "Grande" in tipo_porcion else "mediana")
        resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "servir", "porcion": tamano})
        if resultado is True:
            st.success(f"¡Orden enviada con éxito! Ración: {tipo_porcion}")
        else:
            st.error(f"Error de conexión MQTT: {resultado}")

with col2:
    if st.button("🔒 Cerrar Compuerta"):
        resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar"})
        if resultado is True:
            st.warning("Comando de cierre enviado al dispensador físico.")
        else:
            st.error(f"Error de conexión MQTT: {resultado}")

st.markdown('</div>', unsafe_allow_html=True)

# Módulo de Reconocimiento de Voz Nativo por Navegador (Sin errores de importación JS)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🗣️ Asistente por Voz integrado")
st.write("Di comandos como **'servir comida'** o **'porción grande'** directamente desde tu micrófono:")

语音_html = """
<div style="text-align: center; padding: 10px;">
    <button id="voice-btn" style="
        background-color: #38BDF8; 
        color: #0F172A; 
        border: none; 
        padding: 12px 24px; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 16px; 
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
        🎙️ Presionar para Hablar
    </button>
    <p id="voice-status" style="color: #94A3B8; margin-top: 10px; font-size: 14px;"></p>
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
            vStatus.innerText = "Escuchando instrucción para la mascota...";
            vBtn.style.backgroundColor = "#F43F5E";
            vBtn.innerText = "🔴 Escuchando...";
        };

        recognition.onresult = function(event) {
            const speechResult = event.results[0][0].transcript;
            vStatus.innerText = "Comando reconodido: " + speechResult;
            
            // Comunica el resultado a Streamlit
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
        vBtn.style.backgroundColor = "#38BDF8";
        vBtn.innerText = "🎙️ Presionar para Hablar";
    }
</script>
"""

components.html(语音_html, height=130)

# Campo de respaldo por texto manual sincronizado con MQTT
comando_voz = st.text_input("O ingresa tu comando de voz en texto:", key="txt_voz")
if comando_voz:
    st.info(f"Procesando instrucción: **{comando_voz}**")
    res = enviar_mqtt({"dispositivo": "voz", "Act1": comando_voz.strip()})
    if res is True:
        st.success("📡 ¡Comando de voz transmitido a Wokwi exitosamente!")

st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
