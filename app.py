import streamlit as st
import pandas as pd
from datetime import datetime
import time
import json
import os
from pathlib import Path
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# Configuración de la página
st.set_page_config(
    page_title="Asistente Virtual",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== CARGAR MODELO DE IA =====

@st.cache_resource
def cargar_modelo_ia():
    """Carga un modelo conversacional ligero para generar respuestas"""
    try:
        # Usar modelo ligero y eficiente
        model_name = "microsoft/DialoGPT-medium"
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        return tokenizer, model
    except Exception as e:
        st.error(f"Error al cargar modelo IA: {e}")
        return None, None

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
            },
            'ia': {
                'habilitada': True,
                'modo': 'hibrido'
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
tokenizer, modelo_ia = cargar_modelo_ia()

# Extraer configuraciones
negocio = config['negocio']
colores = config['colores']
mensajes_config = config['mensajes']
ia_config = config.get('ia', {'habilitada': True, 'modo': 'hibrido'})

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

# ===== FUNCIONES DE IA Y BÚSQUEDA =====

def crear_contexto_negocio():
    """Crea un contexto resumido del negocio con toda la información disponible"""
    contexto = f"Información sobre {negocio['nombre']}:\n\n"
    
    # Agregar información general
    if base_conocimiento is not None and not base_conocimiento.empty:
        contexto += "Información general:\n"
        for idx, row in base_conocimiento.head(10).iterrows():
            contexto += f"- {row.iloc[0]}: {row.iloc[1]}\n"
        contexto += "\n"
    
    # Agregar productos
    if productos is not None and not productos.empty:
        contexto += "Productos disponibles:\n"
        for idx, row in productos.head(10).iterrows():
            contexto += f"- {row.iloc[0]}"
            if len(row) > 1 and pd.notna(row.iloc[1]):
                contexto += f" (Precio: {row.iloc[1]})"
            contexto += "\n"
    
    return contexto

def buscar_en_base_datos(pregunta):
    """Busca información relevante en las bases de datos"""
    info_relevante = []
    pregunta_lower = pregunta.lower()
    
    # Buscar en base de conocimiento
    if base_conocimiento is not None:
        for idx, row in base_conocimiento.iterrows():
            pregunta_base = str(row.iloc[0]).lower()
            if any(palabra in pregunta_base for palabra in pregunta_lower.split()):
                info_relevante.append(f"• {row.iloc[0]}: {row.iloc[1]}")
    
    # Buscar en productos
    if productos is not None:
        for idx, row in productos.iterrows():
            nombre_producto = str(row.iloc[0]).lower()
            if nombre_producto in pregunta_lower or any(palabra in nombre_producto for palabra in pregunta_lower.split()):
                producto_info = f"• {row.iloc[0]}"
                if len(row) > 1:
                    producto_info += f" - Precio: {row.iloc[1]}"
                if len(row) > 2:
                    producto_info += f" - {df.columns[2]}: {row.iloc[2]}"
                info_relevante.append(producto_info)
    
    return info_relevante[:5]  # Máximo 5 resultados relevantes

def generar_respuesta_ia(pregunta, info_relevante, historial_reciente):
    """Genera una respuesta usando el modelo de IA con contexto"""
    
    if not ia_config['habilitada'] or tokenizer is None or modelo_ia is None:
        # Si IA no está disponible, usar respuesta directa
        if info_relevante:
            return "\n".join(info_relevante)
        return "Lo siento, no encontré información específica sobre eso. ¿Puedes ser más específico?"
    
    try:
        # Construir prompt con contexto
        contexto = crear_contexto_negocio()
        
        if info_relevante:
            contexto += "\nInformación relevante para esta pregunta:\n"
            contexto += "\n".join(info_relevante)
        
        # Prompt estructurado
        prompt = f"""Como asistente virtual de {negocio['nombre']}, responde de manera amigable y útil.

{contexto}

Usuario: {pregunta}
Asistente:"""
        
        # Generar respuesta con el modelo
        inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        # Generar con parámetros controlados
        outputs = modelo_ia.generate(
            inputs,
            max_length=inputs.shape[1] + 100,
            min_length=inputs.shape[1] + 20,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3
        )
        
        respuesta = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extraer solo la respuesta del asistente
        if "Asistente:" in respuesta:
            respuesta = respuesta.split("Asistente:")[-1].strip()
        
        # Si la respuesta es muy corta o genérica, complementar con info relevante
        if len(respuesta) < 30 and info_relevante:
            respuesta = "Te comparto esta información:\n\n" + "\n".join(info_relevante)
        
        return respuesta
        
    except Exception as e:
        # Fallback a respuesta directa
        if info_relevante:
            return "Encontré esta información que puede ayudarte:\n\n" + "\n".join(info_relevante)
        return "Disculpa, tuve un problema al procesar tu pregunta. ¿Podrías reformularla?"

def procesar_consulta(pregunta, historial):
    """Procesa la consulta del usuario con IA"""
    
    # Buscar información relevante en las bases de datos
    info_relevante = buscar_en_base_datos(pregunta)
    
    # Obtener historial reciente (últimos 3 mensajes)
    historial_reciente = historial[-6:] if len(historial) > 6 else historial
    
    # Generar respuesta con IA
    respuesta = generar_respuesta_ia(pregunta, info_relevante, historial_reciente)
    
    return respuesta

# Función para convertir imagen a base64
def get_image_base64(image_path):
    import base64
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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
                
                # Procesar con IA
                respuesta = procesar_consulta(sugerencia, st.session_state.mensajes)
                
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
    enviar = st.button("📤", use_container_width=True, type="primary")

# Procesar mensaje
if enviar and mensaje_usuario:
    # Agregar mensaje del usuario
    st.session_state.mensajes.append({
        'tipo': 'usuario',
        'contenido': mensaje_usuario,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    # Generar respuesta con IA
    with st.spinner("Pensando..."):
        respuesta_bot = procesar_consulta(mensaje_usuario, st.session_state.mensajes)
    
    st.session_state.mensajes.append({
        'tipo': 'bot',
        'contenido': respuesta_bot,
        'hora': datetime.now().strftime("%H:%M")
    })
    
    st.rerun()

# Footer
st.markdown("---")
if ia_config['habilitada']:
    st.markdown(f"""
    <div style='text-align: center; opacity: 0.6; font-size: 12px;'>
        🤖 Powered by {negocio['nombre']} • Asistente con IA
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='text-align: center; opacity: 0.6; font-size: 12px;'>
        Powered by {negocio['nombre']} • Asistente Virtual
    </div>
    """, unsafe_allow_html=True)
