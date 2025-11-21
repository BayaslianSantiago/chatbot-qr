import streamlit as st
import pandas as pd
from datetime import datetime
import time
import json
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Asistente Virtual",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== FUNCIONES DE CARGA DE CONFIGURACIÓN =====

@st.cache_data
def cargar_configuracion():
    """Carga la configuración desde config.json"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        st.error("⚠️ No se encontró config.json")
        return {
            'negocio': {
                'nombre': 'Mi Negocio',
                'emoji': '🏪',
                'tagline': 'Estamos aquí para ayudarte',
                'logo': None
            },
            'colores': {
                'primario': '#667eea',
                'secundario': '#764ba2',
                'fondo_usuario': '#667eea',
                'fondo_bot': '#f1f3f4'
            },
            'mensajes': {
                'bienvenida': '¡Hola! 👋 Bienvenido. Soy tu asistente virtual. ¿En qué puedo ayudarte?',
                'sugerencias': [
                    '📍 ¿Dónde están ubicados?',
                    '🕐 ¿Cuál es el horario?',
                    '💰 ¿Cuáles son los precios?',
                    '📞 ¿Cómo los contacto?'
                ]
            }
        }

@st.cache_data
def cargar_base_conocimiento():
    """Carga la base de conocimiento desde base_conocimiento.xlsx"""
    try:
        df = pd.read_excel('base_conocimiento.xlsx')
        return df
    except FileNotFoundError:
        st.warning("⚠️ No se encontró base_conocimiento.xlsx")
        return None
    except Exception as e:
        st.error(f"Error al cargar base de conocimiento: {e}")
        return None

@st.cache_data
def cargar_productos():
    """Carga el catálogo de productos desde productos.xlsx"""
    try:
        df = pd.read_excel('productos.xlsx')
        return df
    except FileNotFoundError:
        st.warning("⚠️ No se encontró productos.xlsx")
        return None
    except Exception as e:
        st.error(f"Error al cargar productos: {e}")
        return None

def cargar_logo():
    """Carga el logo desde la carpeta assets/"""
    logo_path = 'assets/logo.png'
    if os.path.exists(logo_path):
        return logo_path
    return None

# ===== CARGAR CONFIGURACIONES =====
config = cargar_configuracion()
base_conocimiento = cargar_base_conocimiento()
productos = cargar_productos()
logo_path = cargar_logo()

# Extraer configuraciones
negocio = config['negocio']
colores = config['colores']
mensajes_config = config['mensajes']

# CSS personalizado con colores dinámicos
st.markdown(f"""
<style>
    /* Ocultar elementos de Streamlit */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Fondo y estilo general */
    .stApp {{
        background: linear-gradient(135deg, {colores['primario']} 0%, {colores['secundario']} 100%);
    }}
    
    /* Container del chat */
    .chat-container {{
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 600px;
        margin: 20px auto;
    }}
    
    /* Header del negocio */
    .business-header {{
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, {colores['primario']} 0%, {colores['secundario']} 100%);
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }}
    
    .business-logo {{
        font-size: 50px;
        margin-bottom: 10px;
    }}
    
    .business-name {{
        font-size: 24px;
        font-weight: bold;
        margin: 0;
    }}
    
    .business-tagline {{
        font-size: 14px;
        opacity: 0.9;
        margin-top: 5px;
    }}
    
    /* Mensajes */
    .user-message {{
        background: {colores['fondo_usuario']};
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 10px 0;
        margin-left: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }}
    
    .bot-message {{
        background: {colores['fondo_bot']};
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 10px 0;
        margin-right: 20%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    
    .message-time {{
        font-size: 10px;
        opacity: 0.6;
        margin-top: 4px;
    }}
    
    /* Input personalizado */
    .stTextInput input {{
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        padding: 12px 20px;
    }}
    
    /* Botón enviar */
    .stButton button {{
        border-radius: 25px;
        background: {colores['primario']};
        color: white;
        border: none;
        padding: 10px 20px;
    }}
    
    /* Logo personalizado */
    .logo-container {{
        text-align: center;
        margin-bottom: 10px;
    }}
    
    .logo-container img {{
        max-width: 120px;
        max-height: 120px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
</style>
""", unsafe_allow_html=True)

# Inicializar sesión
if 'mensajes' not in st.session_state:
    st.session_state.mensajes = []
    st.session_state.primera_visita = True

# ==== INTERFAZ PRINCIPAL ====

# Header del negocio
if logo_path:
    st.markdown(f"""
    <div class="business-header">
        <div class="logo-container">
            <img src="data:image/png;base64,{get_image_base64(logo_path)}" alt="Logo">
        </div>
        <h1 class="business-name">{negocio['nombre']}</h1>
        <p class="business-tagline">{negocio['tagline']}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="business-header">
        <div class="business-logo">{negocio['emoji']}</div>
        <h1 class="business-name">{negocio['nombre']}</h1>
        <p class="business-tagline">{negocio['tagline']}</p>
    </div>
    """, unsafe_allow_html=True)

# Función para convertir imagen a base64
def get_image_base64(image_path):
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Mensaje de bienvenida automático
if st.session_state.primera_visita:
    st.session_state.mensajes.append({
        'tipo': 'bot',
        'contenido': mensajes_config['bienvenida'],
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

# Sugerencias rápidas
if len(st.session_state.mensajes) <= 1 and mensajes_config['sugerencias']:
    st.markdown("### 💡 Preguntas frecuentes:")
    
    col1, col2 = st.columns(2)
    
    for i, sugerencia in enumerate(mensajes_config['sugerencias']):
        col = col1 if i % 2 == 0 else col2
        with col:
            if st.button(sugerencia, key=f"sug_{i}", use_container_width=True):
                # Agregar como mensaje del usuario
                st.session_state.mensajes.append({
                    'tipo': 'usuario',
                    'contenido': sugerencia,
                    'hora': datetime.now().strftime("%H:%M")
                })
                
                # Buscar respuesta en base de conocimiento
                respuesta = procesar_consulta(sugerencia)
                
                st.session_state.mensajes.append({
                    'tipo': 'bot',
                    'contenido': respuesta,
                    'hora': datetime.now().strftime("%H:%M")
                })
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Función de búsqueda simple
def buscar_respuesta(pregunta, df):
    """Busca una respuesta en la base de conocimiento"""
    if df is None or df.empty:
        return "Disculpa, aún estoy aprendiendo. Por favor, intenta con otra pregunta o contacta directamente con el negocio."
    
    try:
        # Búsqueda simple en la primera columna
        pregunta_lower = pregunta.lower()
        
        for idx, row in df.iterrows():
            pregunta_base = str(row.iloc[0]).lower()
            
            # Buscar coincidencias
            if pregunta_lower in pregunta_base or pregunta_base in pregunta_lower:
                return str(row.iloc[1])
        
        # Si no encuentra coincidencia exacta, buscar palabras clave
        palabras_pregunta = set(pregunta_lower.split())
        
        for idx, row in df.iterrows():
            pregunta_base = str(row.iloc[0]).lower()
            palabras_base = set(pregunta_base.split())
            
            # Si hay al menos 2 palabras en común
            if len(palabras_pregunta.intersection(palabras_base)) >= 2:
                return str(row.iloc[1])
        
        return "No encontré información específica sobre eso. ¿Podrías reformular tu pregunta o elegir una de las opciones sugeridas?"
    
    except Exception as e:
        return f"Disculpa, ocurrió un error. Por favor intenta nuevamente."

def buscar_producto(pregunta, df_productos):
    """Busca información sobre productos"""
    if df_productos is None or df_productos.empty:
        return None
    
    try:
        pregunta_lower = pregunta.lower()
        
        # Buscar por nombre de producto
        for idx, row in df_productos.iterrows():
            nombre_producto = str(row.iloc[0]).lower()
            
            if nombre_producto in pregunta_lower or pregunta_lower in nombre_producto:
                # Construir respuesta con todas las características
                respuesta = f"**{row.iloc[0]}**\n\n"
                
                # Agregar todas las características disponibles
                for i in range(1, len(row)):
                    columna = df_productos.columns[i]
                    valor = row.iloc[i]
                    if pd.notna(valor):
                        respuesta += f"• **{columna}:** {valor}\n"
                
                return respuesta
        
        # Buscar por características específicas
        palabras_clave = ['precio', 'costo', 'cuanto', 'color', 'tamaño', 'peso', 'característica']
        
        for palabra in palabras_clave:
            if palabra in pregunta_lower:
                # Buscar productos que tengan esa característica
                resultados = []
                for idx, row in df_productos.iterrows():
                    nombre = str(row.iloc[0])
                    # Buscar en todas las columnas
                    for col in df_productos.columns:
                        if palabra in col.lower():
                            resultados.append(f"• **{nombre}**: {row[col]}")
                            break
                
                if resultados:
                    return "Encontré esta información:\n\n" + "\n".join(resultados[:5])
        
        return None
    
    except Exception as e:
        return None

def procesar_consulta(pregunta):
    """Procesa la consulta del usuario buscando en productos y conocimiento general"""
    
    # Primero intentar buscar en productos
    respuesta_producto = buscar_producto(pregunta, productos)
    
    if respuesta_producto:
        return respuesta_producto
    
    # Si no encuentra en productos, buscar en base de conocimiento general
    respuesta_general = buscar_respuesta(pregunta, base_conocimiento)
    
    return respuesta_general

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
    enviar = st.button("📤", use_container_width=True, type="primary")

# Procesar mensaje
if enviar and mensaje_usuario:
    # Agregar mensaje del usuario
    st.session_state.mensajes.append({
        'tipo': 'usuario',
        'contenido': mensaje_usuario,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    # Buscar respuesta
    with st.spinner("Escribiendo..."):
        time.sleep(0.5)  # Simular pensamiento
        respuesta_bot = procesar_consulta(mensaje_usuario)
    
    st.session_state.mensajes.append({
        'tipo': 'bot',
        'contenido': respuesta_bot,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    st.rerun()

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; opacity: 0.6; font-size: 12px;'>
    Powered by {negocio['nombre']} • Asistente Virtual IA
</div>
""", unsafe_allow_html=True)
