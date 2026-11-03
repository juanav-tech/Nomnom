import os
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
import time
import paho.mqtt.client as paho
import json

# Configuración de página con diseño estético
st.set_page_config(
    page_title="Control de Puerta por Voz - Smart Home",
    page_icon="🚪",
    layout="centered"
)

# Estilos CSS personalizados
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
        border-left: 6px solid #38BDF8;
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
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

def on_publish(client, userdata, result):                     
    print("el dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("ClienteJuana")
client1.on_message = on_message

# Encabezado estético
st.markdown("""
    <div class="main-header">
        <h1 style="color: #FFFFFF; margin: 0; font-size: 26px;">🚪 Control de Puerta por Voz</h1>
        <p style="color: #94A3B8; margin: 5px 0 0 0;">Interfaz Multimodal conectada con Wokwi vía MQTT</p>
    </div>
""", unsafe_allow_html=True)

# Imagen centrada
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        image = Image.open('voice_ctrl.jpg')
        st.image(image, use_column_width=True)
    except Exception:
        pass

# Tarjeta principal para la interacción de voz
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("🎙️ Asistente de Acceso")
st.write("Di un comando como **'cerrar puerta'** para enviar la orden al simulador.")

# Componente HTML/JS nativo para reconocimiento de voz sin dependencias de Bokeh
speech_html = """
<div style="text-align: center;">
    <button id="record-btn" style="
        background-color: #38BDF8; 
        color: #0F172A; 
        border: none; 
        padding: 12px 24px; 
        border-radius: 8px; 
        font-weight: bold; 
        font-size: 16px; 
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
        🎙️ Hablar para Cerrar Puerta
    </button>
    <p id="status" style="color: #94A3B8; margin-top: 10px; font-size: 14px;"></p>
</div>

<script>
    const btn = document.getElementById('record-btn');
    const statusText = document.getElementById('status');

    btn.onclick = function() {
        if (!('webkitSpeechRecognition' in window)) {
            statusText.innerText = "Tu navegador no soporta reconocimiento de voz. Usa Google Chrome.";
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'es-ES';

        recognition.onstart = function() {
            statusText.innerText = "Escuchando... Habla ahora.";
            btn.style.backgroundColor = "#F43F5E";
            btn.innerText = "🔴 Escuchando...";
        };

        recognition.onresult = function(event) {
            const speechResult = event.results[0][0].transcript;
            statusText.innerText = "Comando: " + speechResult;
            
            // Envía el texto reconocido de vuelta a Streamlit mediante un parámetro de URL/Query o interacción
            const streamlitDoc = window.parent.document;
            const textInput = streamlitDoc.querySelectorAll('input[type=text]');
            
            // Creamos un evento personalizado o comunicamos el valor
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: speechResult}, '*');
        };

        recognition.onerror = function(event) {
            statusText.innerText = "Error en el reconocimiento: " + event.error;
            resetButton();
        };

        recognition.onend = function() {
            resetButton();
        };

        recognition.start();
    };

    function resetButton() {
        btn.style.backgroundColor = "#38BDF8";
        btn.innerText = "🎙️ Hablar para Cerrar Puerta";
    }
</script>
"""

# Renderizamos el componente de voz limpio
components.html(speech_html, height=120)

# Nota: Para mantener total compatibilidad con tu lógica actual basada en el input de texto de Streamlit o botones de control directo, 
# puedes respaldarlo con un campo de texto interactivo auxiliar si deseas capturar comandos escritos o de respaldo:
spoken_text = st.text_input("O escribe tu comando manual aquí:", key="comando_manual")

if spoken_text:
    st.success(f"Comando procesado: **{spoken_text}**")
    try:
        client1.on_publish = on_publish                                     
        client1.connect(broker, port)  
        message = json.dumps({"Act1": spoken_text.strip()})
        ret = client1.publish("voicejuana", message)
        st.info("📡 ¡Comando enviado al simulador Wokwi con éxito!")
    except Exception as e:
        st.error(f"Error al conectar con el broker MQTT: {e}")

st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
