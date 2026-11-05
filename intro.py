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

# Estilos CSS con diseño lúdico y contraste absoluto para legibilidad
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
        client_id = f"NomNomApp_{int(time.time())}"
        client = paho.Client(client_id)
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        mensaje = json.dumps(payload_dict)
        info = client.publish(topic_comunicacion, mensaje)
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

# --- BARRA LATERAL CON LA ILUSTRACIÓN foto1.png ---
with st.sidebar:
    try:
        imagen_foto1 = Image.open("foto1.png")
        st.image(imagen_foto1, use_column_width=True)
    except Exception:
        st.write("🐾 Menú de Control")
        
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
                st.success(f"¡Ración {tipo_porcion} enviada al comedero correctamente!")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    with col_btn2:
        if st.button("🔒 Cerrar Compuerta"):
            resultado = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar"})
            if resultado is True:
                st.warning("Comando de cierre enviado con éxito (Indicador rojo en Wokwi).")
            else:
                st.error(f"Error de conexión MQTT: {resultado}")

    st.markdown('</div>', unsafe_allow_html=True)

    # Módulo de Asistente de Voz corregido y optimizado para abrir permisos de micrófono de forma nativa
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Asistente por Voz Inteligente")
    st.markdown("Habla con tu app para activar el dispensador. Di claramente uno de los siguientes comandos:")
    
    st.markdown("""
        <div style="background-color: #FFF9F5; padding: 12px; border-radius: 10px; border-left: 5px solid #E76F51; margin-bottom: 15px;">
            <b>📌 Comandos permitidos:</b><br>
            • <i>"Porción pequeña"</i><br>
            • <i>"Porción mediana"</i><br>
            • <i>"Porción grande"</i><br>
            • <i>"Cerrar compuerta"</i>
        </div>
    """, unsafe_allow_html=True)

    # Componente de voz mejorado utilizando permisos directos de la API del navegador
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
        <p id="voice-status" style="color: #2D2D2D; margin-top: 15px; font-size: 15px; font-weight: 700; min-height: 30px;"></p>
    </div>

    <script>
        const vBtn = document.getElementById('voice-btn');
        const vStatus = document.getElementById('voice-status');

        vBtn.onclick = async function() {
            try {
                // Solicitar explícitamente acceso al micrófono al navegador antes de iniciar el reconocimiento
                await navigator.mediaDevices.getUserMedia({ audio: true });
            } catch (err) {
                vStatus.innerText = "⚠️ Permiso de micrófono denegado o no disponible.";
                return;
            }

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                vStatus.innerText = "Tu navegador no soporta voz. Usa Google Chrome.";
                return;
            }

            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'es-ES';

            recognition.onstart = function() {
                vStatus.innerText = "🎧 Escuchando... Di tu comando.";
                vBtn.style.backgroundColor = "#E76F51";
                vBtn.innerText = "🔴 Escuchando...";
            };

            recognition.onresult = function(event) {
                let interimTranscript = '';
                let finalTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        interimTranscript += event.results[i][0].transcript;
                    }
                }

                if (interimTranscript !== '') {
                    vStatus.innerText = "💬 Escuchando: " + interimTranscript;
                }
                
                if (finalTranscript !== '') {
                    vStatus.innerText = "✅ Detectado: \"" + finalTranscript + "\"";
                    
                    // Publicar directamente por MQTT desde el contexto seguro de red o mandar el valor a Streamlit
                    const cleanedText = finalTranscript.trim().toLowerCase();
                    
                    // Enviar orden mediante fetch o postMessage
                    window.parent.postMessage({
                        type: 'streamlit:setComponentValue',
                        value: cleanedText
                    }, '*');
                }
            };

            recognition.onerror = function(event) {
                vStatus.innerText = "⚠️ Error: " + event.error;
                resetVButton();
            };

            recognition.onend = function() {
                resetVButton();
            };

            try {
                recognition.start();
            } catch(e) {
                vStatus.innerText = "⚠️ Vuelve a presionar el botón.";
                resetVButton();
            }
        };

        function resetVButton() {
            vBtn.style.backgroundColor = '#2A9D8F';
            vBtn.innerText = "🎙️ Presionar para Hablar";
        }
    </script>
    """

    # Renderizar el componente de voz
    resultado_voz = components.html(voz_html, height=150)

    # Caja de texto manual con legibilidad optimizada y oscura
    comando_voz = st.text_input("O escribe tu comando de forma manual (ej. cerrar compuerta):", key="txt_voz")
    
    # Procesamiento unificado de voz (si Streamlit recibe el input) o texto manual
    comando_a_procesar = comando_voz
    
    if comando_a_procesar:
        cmd_lower = comando_a_procesar.strip().lower()
        st.info(f"Procesando comando: **{comando_a_procesar}**")
        
        # Verificar si el usuario indicó cerrar la compuerta
        if "cerrar" in cmd_lower:
            res = enviar_mqtt({"dispositivo": "dispensador", "accion": "cerrar"})
            if res is True:
                st.warning("🔒 ¡Compuerta cerrada! Indicador cambiado a luz roja en Wokwi.")
            else:
                st.error(f"Error de conexión MQTT: {res}")
        else:
            # Si es porción pequeña, mediana o grande
            res = enviar_mqtt({"dispositivo": "voz", "Act1": cmd_lower})
            if res is True:
                st.success("📡 ¡Instrucción transmitida al dispositivo con éxito!")
            else:
                st.error(f"Error al enviar por MQTT: {res}")

    st.markdown('</div>', unsafe_allow_html=True)

# =========================================================================
# MÓDULO 2: CÁMARA Y MONITOREO HOGAREÑO CON foto2.png
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

            # Lógica basada estrictamente en la Clase 1
            if indice_clase == 1 or "clase 1" in clase_detectada.lower() or "lleno" in clase_detectada.lower() or "comida" in clase_detectada.lower():
                st.success("🟢 Aún hay comida en comedero")
            else:
                st.warning("🔴 Ya se acabó")
                
            st.caption(f"Detalle técnico de IA: Detectado [{clase_detectada}] con {confianza:.1f}% de certeza")

    st.markdown('</div>', unsafe_allow_html=True)

try:
    os.mkdir("temp")
except:
    pass
