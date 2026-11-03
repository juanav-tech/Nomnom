import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
import paho.mqtt.client as paho
import json
import paho.mqtt.client as mqtt

# Configuración global de la página
st.set_page_config(
    page_title="Smart Home & AI Hub - Juana",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS globales compartidos
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

# Menú de navegación principal en la barra lateral
with st.sidebar:
    st.title("🎛️ Centro de Control")
    seleccion_app = st.radio(
        "Selecciona el Módulo:",
        ["🎙️ Control por Voz (Wokwi)", "📡 Lector de Sensores MQTT", "👁️ Visión por Computador"]
    )
    st.markdown("---")
    st.caption("Entorno: Streamlit & Wokwi IoT Bridge")

# =========================================================
# MÓDULO 1: CONTROL POR VOZ (CONECTADO A WOKWI)
# =========================================================
if seleccion_app == "🎙️ Control por Voz (Wokwi)":
    
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
    client1 = paho.Client("ClienteJuanaVoz")
    client1.on_message = on_message

    st.markdown("""
        <div class="main-header">
            <h1 style="color: #FFFFFF; margin: 0; font-size: 26px;">🚪 Control de Puerta por Voz</h1>
            <p style="color: #94A3B8; margin: 5px 0 0 0;">Interfaz Multimodal conectada con Wokwi vía MQTT</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            image = Image.open('voice_ctrl.jpg')
            st.image(image, use_column_width=True)
        except Exception:
            pass

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎙️ Asistente de Acceso")
    st.write("Di un comando como **'cerrar puerta'** para enviar la orden al simulador Wokwi.")

    stt_button = Button(label="🎙️ Hablar para Controlar", width=280)

    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
     
        recognition.onresult = function (e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    value += e.results[i][0].transcript;
                }
            }
            if ( value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
        recognition.start();
        """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen_voice",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0)

    if result:
        if "GET_TEXT" in result:
            spoken_text = result.get("GET_TEXT")
            st.success(f"Comando reconocido: **{spoken_text}**")
            
            client1.on_publish = on_publish                                     
            client1.connect(broker, port)  
            message = json.dumps({"Act1": spoken_text.strip()})
            # Importante: El tópico debe coincidir con el que escucha tu ESP32 en Wokwi
            ret = client1.publish("voicejuana", message)

    st.markdown('</div>', unsafe_allow_html=True)

    try:
        os.mkdir("temp")
    except:
        pass

# =========================================================
# MÓDULO 2: LECTOR DE SENSORES MQTT
# =========================================================
elif seleccion_app == "📡 Lector de Sensores MQTT":
    
    if 'sensor_data' not in st.session_state:
        st.session_state.sensor_data = None

    def get_mqtt_message(broker, port, topic, client_id):
        message_received = {"received": False, "payload": None}
        
        def on_message(client, userdata, message):
            try:
                payload = json.loads(message.payload.decode())
                message_received["payload"] = payload
                message_received["received"] = True
            except:
                message_received["payload"] = message.payload.decode()
                message_received["received"] = True
        
        try:
            client = mqtt.Client(client_id=client_id)
            client.on_message = on_message
            client.connect(broker, port, 60)
            client.subscribe(topic)
            client.loop_start()
            
            timeout = time.time() + 5
            while not message_received["received"] and time.time() < timeout:
                time.sleep(0.1)
            
            client.loop_stop()
            client.disconnect()
            
            return message_received["payload"]
        except Exception as e:
            return {"error": str(e)}

    with st.sidebar:
        st.subheader('⚙️ Configuración MQTT Wokwi')
        broker_sens = st.text_input('Broker MQTT', value='broker.mqttdashboard.com')
        port_sens = st.number_input('Puerto', value=1883, min_value=1, max_value=65535)
        topic_sens = st.text_input('Tópico', value='Sensor/THP2')
        client_id_sens = st.text_input('ID del Cliente', value='streamlit_sensor_client')

    st.title('📡 Lector de Sensor MQTT (Wokwi Telemetría)')
    st.write("Monitorea los datos enviados por tus sensores simulados en tiempo real.")
    st.divider()

    if st.button('🔄 Obtener Datos del Sensor', use_container_width=True):
        with st.spinner('Conectando al broker y esperando datos...'):
            st.session_state.sensor_data = get_mqtt_message(broker_sens, int(port_sens), topic_sens, client_id_sens)

    if st.session_state.sensor_data:
        st.divider()
        st.subheader('📊 Datos Recibidos')
        data = st.session_state.sensor_data
        
        if isinstance(data, dict) and 'error' in data:
            st.error(f"❌ Error de conexión: {data['error']}")
        else:
            st.success('✅ Datos recibidos correctamente desde Wokwi')
            if isinstance(data, dict):
                cols = st.columns(len(data))
                for i, (key, value) in enumerate(data.items()):
                    with cols[i]:
                        st.metric(label=key, value=value)
                with st.expander('Ver JSON completo'):
                    st.json(data)
            else:
                st.code(data)

# =========================================================
# MÓDULO 3: VISIÓN POR COMPUTADOR
# =========================================================
elif seleccion_app == "👁️ Visión por Computador":
    st.title("👁️ Módulo de Visión por Computador")
    st.write("Selecciona la herramienta analítica que deseas utilizar:")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        with st.container(border=True):
            st.subheader("🧠 Teachable Machine")
            st.write("Clasificación de imágenes con modelos personalizados.")
            st.info("Configurado mediante las librerías de TensorFlow/Keras.")
    with col_v2:
        with st.container(border=True):
            st.subheader("🔍 YOLO Object Detection")
            st.write("Detección y localización de objetos en tiempo real.")
            st.info("Configurado mediante Ultralytics YOLOv5.")
