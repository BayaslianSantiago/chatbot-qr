import streamlit as st
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re

# Configuración de la página
st.set_page_config(page_title="Chatbot IA - Asistente Virtual", page_icon="🤖", layout="wide")

# Inicializar el modelo conversacional
@st.cache_resource
def load_conversation_model():
    """
    Carga un modelo conversacional preentrenado.
    Opciones disponibles:
    - 'facebook/blenderbot-400M-distill' (inglés, ligero)
    - 'google/flan-t5-base' (multilingüe, bueno para Q&A)
    - 'Helsinki-NLP/opus-mt-en-es' (traducción)
    """
    try:
        # Modelo conversacional ligero y efectivo
        model_name = "google/flan-t5-base"
        
        # Cargar tokenizer y modelo
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Crear pipeline
        generator = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
        
        return generator, tokenizer
    except Exception as e:
        st.error(f"Error al cargar el modelo: {e}")
        return None, None

generator, tokenizer = load_conversation_model()

# Función para procesar el archivo Excel
def procesar_excel(archivo):
    """Procesa el archivo Excel y extrae información de forma genérica."""
    try:
        df = pd.read_excel(archivo)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        st.sidebar.success(f"✅ Archivo cargado: {len(df)} filas")
        st.sidebar.write("Columnas detectadas:", list(df.columns))
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Función para crear contexto desde el Excel
def crear_contexto(df, col_pregunta, col_respuesta):
    """Crea un contexto de conocimiento desde el DataFrame."""
    if col_pregunta not in df.columns or col_respuesta not in df.columns:
        st.error("Las columnas seleccionadas no existen en el archivo")
        return None
    
    # Limpiar datos nulos
    df_limpio = df[[col_pregunta, col_respuesta]].dropna()
    
    # Crear base de conocimiento en formato texto
    conocimiento = []
    for _, row in df_limpio.iterrows():
        conocimiento.append({
            'pregunta': str(row[col_pregunta]).strip(),
            'respuesta': str(row[col_respuesta]).strip()
        })
    
    return conocimiento

# Función para buscar en la base de conocimiento
def buscar_en_base(pregunta, conocimiento):
    """Busca respuestas relevantes en la base de conocimiento."""
    pregunta_lower = pregunta.lower()
    resultados = []
    
    for item in conocimiento:
        pregunta_base = item['pregunta'].lower()
        
        # Buscar coincidencias de palabras clave
        palabras_pregunta = set(pregunta_lower.split())
        palabras_base = set(pregunta_base.split())
        
        # Calcular similitud simple por palabras comunes
        coincidencias = len(palabras_pregunta.intersection(palabras_base))
        
        if coincidencias > 0 or pregunta_lower in pregunta_base or pregunta_base in pregunta_lower:
            resultados.append({
                'pregunta': item['pregunta'],
                'respuesta': item['respuesta'],
                'score': coincidencias
            })
    
    # Ordenar por score
    resultados.sort(key=lambda x: x['score'], reverse=True)
    
    return resultados[:3]  # Top 3 resultados

# Función para generar respuesta con el modelo
def generar_respuesta(pregunta, contexto_relevante):
    """Genera una respuesta usando el modelo conversacional."""
    if not generator:
        return "El modelo no está disponible. Por favor, recarga la página."
    
    # Si hay contexto relevante, usarlo
    if contexto_relevante:
        # Construir prompt con contexto
        contexto_texto = "\n".join([f"P: {r['pregunta']}\nR: {r['respuesta']}" for r in contexto_relevante])
        
        prompt = f"""Basándote en la siguiente información, responde la pregunta del usuario de manera clara y concisa.

Información disponible:
{contexto_texto}

Pregunta del usuario: {pregunta}

Respuesta:"""
    else:
        # Pregunta directa sin contexto
        prompt = f"Responde esta pregunta de manera útil: {pregunta}"
    
    try:
        # Generar respuesta
        respuesta = generator(
            prompt,
            max_length=200,
            min_length=20,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            num_return_sequences=1
        )
        
        return respuesta[0]['generated_text'].strip()
    except Exception as e:
        return f"Error al generar respuesta: {e}"

# Título de la aplicación
st.title("🤖 Chatbot IA - Asistente Conversacional")
st.markdown("### Powered by FLAN-T5 - Modelo conversacional preentrenado")

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Información del modelo
with st.sidebar.expander("ℹ️ Sobre el modelo"):
    st.markdown("""
    **Modelo:** Google FLAN-T5 Base
    
    - ✅ Entrenado en conversaciones
    - ✅ Entiende contexto
    - ✅ Genera respuestas naturales
    - ✅ Multilingüe (incluye español)
    - ✅ Sin APIs externas
    """)

# Cargar archivo Excel
archivo_subido = st.sidebar.file_uploader(
    "Sube tu archivo Excel (.xlsx, .xls)",
    type=['xlsx', 'xls'],
    help="El archivo debe contener preguntas/temas y respuestas"
)

# Inicializar variables de sesión
if 'historial' not in st.session_state:
    st.session_state.historial = []

if 'conocimiento' not in st.session_state:
    st.session_state.conocimiento = None

# Procesar archivo si se cargó
if archivo_subido is not None:
    df = procesar_excel(archivo_subido)
    
    if df is not None:
        # Seleccionar columnas
        st.sidebar.subheader("Selecciona las columnas:")
        
        columnas = list(df.columns)
        
        col_pregunta = st.sidebar.selectbox(
            "Columna de Preguntas/Temas:",
            columnas,
            index=0,
            help="Columna que contiene las preguntas o temas"
        )
        
        col_respuesta = st.sidebar.selectbox(
            "Columna de Respuestas/Información:",
            columnas,
            index=1 if len(columnas) > 1 else 0,
            help="Columna que contiene las respuestas o información"
        )
        
        # Botón para procesar
        if st.sidebar.button("🚀 Activar Chatbot"):
            with st.spinner("Procesando base de conocimiento..."):
                conocimiento = crear_contexto(df, col_pregunta, col_respuesta)
                
                if conocimiento:
                    st.session_state.conocimiento = conocimiento
                    st.sidebar.success(f"✅ ¡Chatbot activado con {len(conocimiento)} entradas!")
                    st.balloons()

# Configuraciones adicionales
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Parámetros")

usar_contexto = st.sidebar.checkbox(
    "Usar base de conocimiento",
    value=True,
    help="Si está activado, el chatbot buscará primero en tu Excel"
)

modo_conversacion = st.sidebar.radio(
    "Modo de respuesta:",
    ["Con contexto (recomendado)", "Solo modelo IA", "Híbrido"],
    help="Híbrido combina búsqueda en Excel + generación IA"
)

# Mostrar preview de datos
if archivo_subido is not None and df is not None:
    with st.expander("📊 Vista previa de los datos"):
        st.dataframe(df.head(10))
        st.info(f"Total de registros: {len(df)}")

# Área de chat
st.markdown("---")

# Verificar si el modelo está cargado
if generator is not None:
    st.success("✅ Modelo conversacional cargado - ¡Hazme una pregunta!")
    
    # Formulario de chat
    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        with col1:
            pregunta = st.text_input(
                "Tu pregunta:",
                placeholder="¿En qué puedo ayudarte hoy?",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("Enviar", use_container_width=True)
    
    # Procesar pregunta
    if submit and pregunta:
        # Agregar pregunta al historial
        st.session_state.historial.append({"role": "user", "content": pregunta})
        
        with st.spinner("Pensando..."):
            # Buscar en base de conocimiento si existe
            contexto_relevante = []
            if usar_contexto and st.session_state.conocimiento:
                contexto_relevante = buscar_en_base(pregunta, st.session_state.conocimiento)
            
            # Generar respuesta según el modo
            if modo_conversacion == "Con contexto (recomendado)" and contexto_relevante:
                # Respuesta directa del Excel si hay coincidencia exacta
                respuesta = contexto_relevante[0]['respuesta']
                tipo_respuesta = "📚 Base de conocimiento"
            elif modo_conversacion == "Solo modelo IA":
                # Solo usar el modelo
                respuesta = generar_respuesta(pregunta, [])
                tipo_respuesta = "🤖 Generado por IA"
            else:
                # Modo híbrido: combinar contexto + modelo
                respuesta = generar_respuesta(pregunta, contexto_relevante)
                tipo_respuesta = "🔄 Híbrido (Contexto + IA)"
            
            # Agregar respuesta al historial
            st.session_state.historial.append({
                "role": "assistant",
                "content": respuesta,
                "tipo": tipo_respuesta,
                "contexto": len(contexto_relevante) > 0
            })
    
    # Mostrar historial de chat
    st.markdown("### 💬 Conversación")
    
    if not st.session_state.historial:
        st.info("👋 ¡Hola! Soy tu asistente virtual. Hazme cualquier pregunta.")
    
    for mensaje in st.session_state.historial:
        if mensaje["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(mensaje["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(mensaje["content"])
                st.caption(mensaje.get("tipo", ""))
    
    # Botones de control
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🗑️ Limpiar chat"):
            st.session_state.historial = []
            st.rerun()

else:
    st.error("❌ Error al cargar el modelo conversacional. Verifica las dependencias.")

# Instrucciones
with st.expander("📖 ¿Cómo funciona este chatbot?"):
    st.markdown("""
    ### 🎯 **Modos de operación:**
    
    1. **Con contexto (recomendado):**
       - Busca primero en tu base de datos Excel
       - Responde directamente si encuentra coincidencias
       - Rápido y preciso para info específica
    
    2. **Solo modelo IA:**
       - Usa únicamente el modelo FLAN-T5
       - Genera respuestas conversacionales
       - Ideal para preguntas generales
    
    3. **Híbrido:**
       - Combina búsqueda en Excel + generación IA
       - El modelo reformula y enriquece las respuestas del Excel
       - Balance perfecto entre precisión y naturalidad
    
    ### 📋 **Formato Excel recomendado:**
    
    | Pregunta | Respuesta |
    |----------|-----------|
    | ¿Cuál es el horario? | Lunes a viernes 9-18h |
    | ¿Dónde están ubicados? | Av. Principal 123 |
    
    ### 💡 **Ventajas:**
    - ✅ Modelo conversacional preentrenado (FLAN-T5)
    - ✅ Sin APIs externas ni costos adicionales
    - ✅ Funciona offline después de la primera carga
    - ✅ Genera respuestas naturales y contextuales
    """)

# Footer
st.markdown("---")
st.caption("🤖 Chatbot con Google FLAN-T5 | Modelo conversacional preentrenado | Sin APIs externas")
