import streamlit as st
import pandas as pd
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="Asistente Virtual",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para look profesional
st.markdown("""
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fondo y estilo general */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container del chat */
    .chat-container {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 600px;
        margin: 20px auto;
    }
    
    /* Header del negocio */
    .business-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    
    .business-logo {
        font-size: 50px;
        margin-bottom: 10px;
    }
    
    .business-name {
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }
    
    .business-tagline {
        font-size: 14px;
        opacity: 0.9;
        margin-top: 5px;
    }
    
    /* Mensajes */
    .user-message {
        background: #667eea;
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0;
        margin-left: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background: #f1f3f4;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px 0;
        margin-right: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .message-time {
        font-size: 10px;
        opacity: 0.6;
        margin-top: 4px;
    }
    
    /* Botones de sugerencias */
    .suggestion-btn {
        background: white;
        border: 2px solid #667eea;
        color: #667eea;
        padding: 10px 20px;
        border-radius: 20px;
        margin: 5px;
        cursor: pointer;
        display: inline-block;
        font-size: 14px;
    }
    
    /* Input personalizado */
    .stTextInput input {
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        padding: 12px 20px;
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-block;
        padding: 10px;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        background-color: #667eea;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
</style>
""", unsafe_allow_html=True)

# Inicializar sesión
if 'mensajes' not in st.session_state:
    st.session_state.mensajes = []
    st.session_state.primera_visita = True

if 'info_negocio' not in st.session_state:
    st.session_state.info_negocio = {
        'nombre': 'Mi Negocio',
        'emoji': '🏪',
        'tagline': 'Estamos aquí para ayudarte',
        'activo': False
    }

# Sidebar para configuración del negocio (admin)
with st.sidebar:
    st.title("⚙️ Panel de Administración")
    st.markdown("---")
    
    st.subheader("Información del Negocio")
    
    nombre_negocio = st.text_input(
        "Nombre del negocio:",
        value=st.session_state.info_negocio['nombre'],
        placeholder="Ej: Restaurante El Buen Sabor"
    )
    
    emoji_negocio = st.text_input(
        "Emoji/Ícono:",
        value=st.session_state.info_negocio['emoji'],
        placeholder="🍕 🏪 ☕ 💼"
    )
    
    tagline = st.text_input(
        "Mensaje de bienvenida:",
        value=st.session_state.info_negocio['tagline'],
        placeholder="Tu satisfacción es nuestra prioridad"
    )
    
    if st.button("💾 Guardar Configuración"):
        st.session_state.info_negocio = {
            'nombre': nombre_negocio,
            'emoji': emoji_negocio,
            'tagline': tagline,
            'activo': True
        }
        st.success("✅ Configuración guardada!")
    
    st.markdown("---")
    st.subheader("📊 Base de Conocimiento")
    
    archivo_subido = st.file_uploader(
        "Subir Excel con información:",
        type=['xlsx', 'xls'],
        help="Formato: Pregunta | Respuesta"
    )
    
    if archivo_subido:
        try:
            df = pd.read_excel(archivo_subido)
            st.success(f"✅ {len(df)} entradas cargadas")
            
            # Guardar en sesión
            if 'base_conocimiento' not in st.session_state:
                st.session_state.base_conocimiento = df
            
            with st.expander("Ver datos"):
                st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    if st.button("🔄 Reiniciar Chat"):
        st.session_state.mensajes = []
        st.session_state.primera_visita = True
        st.rerun()
    
    st.markdown("---")
    st.caption("💡 Vista de cliente: Colapsa este panel")

# ==== INTERFAZ PRINCIPAL (Lo que ve el cliente) ====

# Header del negocio
info = st.session_state.info_negocio

st.markdown(f"""
<div class="business-header">
    <div class="business-logo">{info['emoji']}</div>
    <h1 class="business-name">{info['nombre']}</h1>
    <p class="business-tagline">{info['tagline']}</p>
</div>
""", unsafe_allow_html=True)

# Mensaje de bienvenida automático
if st.session_state.primera_visita:
    st.session_state.mensajes.append({
        'tipo': 'bot',
        'contenido': f"¡Hola! 👋 Bienvenido a {info['nombre']}. Soy tu asistente virtual y estoy aquí para ayudarte. ¿En qué puedo asistirte hoy?",
        'hora': datetime.now().strftime("%H:%M")
    })
    st.session_state.primera_visita = False

# Área de mensajes
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)

# Mostrar mensajes
for msg in st.session_state.mensajes:
    if msg['tipo'] == 'usuario':
        st.markdown(f"""
        <div class="user-message">
            {msg['contenido']}
            <div class="message-time">{msg['hora']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="bot-message">
            {msg['contenido']}
            <div class="message-time">{msg['hora']}</div>
        </div>
        """, unsafe_allow_html=True)

# Sugerencias rápidas (opcional)
if len(st.session_state.mensajes) <= 1:
    st.markdown("### 💡 Preguntas frecuentes:")
    
    col1, col2 = st.columns(2)
    
    sugerencias = [
        "📍 ¿Dónde están ubicados?",
        "🕐 ¿Cuál es el horario?",
        "💰 ¿Cuáles son los precios?",
        "📞 ¿Cómo los contacto?"
    ]
    
    for i, sugerencia in enumerate(sugerencias):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(sugerencia, key=f"sug_{i}", use_container_width=True):
                # Agregar como mensaje del usuario
                st.session_state.mensajes.append({
                    'tipo': 'usuario',
                    'contenido': sugerencia,
                    'hora': datetime.now().strftime("%H:%M")
                })
                
                # Respuesta automática (aquí irá la IA después)
                respuesta = f"Gracias por tu pregunta sobre: {sugerencia}. Pronto conectaré esta respuesta con nuestra base de datos."
                
                st.session_state.mensajes.append({
                    'tipo': 'bot',
                    'contenido': respuesta,
                    'hora': datetime.now().strftime("%H:%M")
                })
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Input del usuario
st.markdown("---")

col1, col2 = st.columns([5, 1])

with col1:
    mensaje_usuario = st.text_input(
        "Escribe tu mensaje...",
        placeholder="Escribe tu pregunta aquí...",
        label_visibility="collapsed",
        key="input_mensaje"
    )

with col2:
    enviar = st.button("Enviar", use_container_width=True, type="primary")

# Procesar mensaje
if enviar and mensaje_usuario:
    # Agregar mensaje del usuario
    st.session_state.mensajes.append({
        'tipo': 'usuario',
        'contenido': mensaje_usuario,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    # Simular "escribiendo..." (después aquí irá la IA)
    with st.spinner("Escribiendo..."):
        time.sleep(1)
        
        # Respuesta placeholder (aquí conectarás la IA)
        respuesta_bot = "Gracias por tu mensaje. Estoy en desarrollo y pronto podré responderte con información precisa sobre nuestro negocio. 🤖"
        
        # Si hay base de conocimiento, intentar buscar
        if 'base_conocimiento' in st.session_state:
            df = st.session_state.base_conocimiento
            # Búsqueda simple (mejorarás esto con IA)
            resultados = df[df.iloc[:, 0].str.contains(mensaje_usuario, case=False, na=False)]
            
            if not resultados.empty:
                respuesta_bot = resultados.iloc[0, 1]  # Primera respuesta encontrada
    
    st.session_state.mensajes.append({
        'tipo': 'bot',
        'contenido': respuesta_bot,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; opacity: 0.6; font-size: 12px;'>
    Powered by Asistente Virtual IA • Desarrollado para tu negocio
</div>
""", unsafe_allow_html=True)
