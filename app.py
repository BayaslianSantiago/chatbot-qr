import streamlit as st
import pandas as pd
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import io

# Configuración de la página
st.set_page_config(page_title="Chatbot IA - Asistente Virtual", page_icon="🤖", layout="wide")

# Inicializar el modelo de embeddings (se carga una sola vez)
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# Función para procesar el archivo Excel
def procesar_excel(archivo):
    """
    Procesa el archivo Excel y extrae información de forma genérica.
    Asume que tiene columnas con preguntas/temas y respuestas/información.
    """
    try:
        df = pd.read_excel(archivo)
        
        # Mostrar las columnas disponibles
        st.sidebar.success(f"✅ Archivo cargado: {len(df)} filas")
        st.sidebar.write("Columnas detectadas:", list(df.columns))
        
        return df
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        return None

# Función para crear la base de conocimiento
def crear_base_conocimiento(df, col_pregunta, col_respuesta):
    """
    Crea una base de conocimiento combinando preguntas y respuestas.
    """
    if col_pregunta not in df.columns or col_respuesta not in df.columns:
        st.error("Las columnas seleccionadas no existen en el archivo")
        return None, None
    
    # Limpiar datos nulos
    df_limpio = df[[col_pregunta, col_respuesta]].dropna()
    
    # Crear textos combinados para mejor contexto
    textos = []
    for _, row in df_limpio.iterrows():
        texto_combinado = f"Pregunta: {row[col_pregunta]} Respuesta: {row[col_respuesta]}"
        textos.append(texto_combinado)
    
    # Generar embeddings
    embeddings = model.encode(textos)
    
    return textos, embeddings, df_limpio

# Función para buscar la mejor respuesta
def buscar_respuesta(pregunta_usuario, textos, embeddings, df_limpio, col_respuesta, top_k=3):
    """
    Busca las respuestas más relevantes usando similitud coseno.
    """
    # Generar embedding de la pregunta del usuario
    pregunta_embedding = model.encode([pregunta_usuario])
    
    # Calcular similitudes
    similitudes = cosine_similarity(pregunta_embedding, embeddings)[0]
    
    # Obtener los índices de las top_k respuestas más similares
    indices_top = np.argsort(similitudes)[-top_k:][::-1]
    
    # Verificar que hay suficiente similitud (umbral mínimo)
    if similitudes[indices_top[0]] < 0.3:
        return "Lo siento, no encontré información relevante sobre tu consulta. ¿Podrías reformular tu pregunta?", 0.0
    
    # Construir respuesta combinando las mejores coincidencias
    respuestas = []
    for idx in indices_top:
        if similitudes[idx] > 0.3:  # Solo incluir respuestas relevantes
            respuestas.append(df_limpio.iloc[idx][col_respuesta])
    
    # Si hay múltiples respuestas similares, combinarlas
    if len(respuestas) > 1:
        respuesta_final = "Encontré esta información relevante:\n\n" + "\n\n".join([f"• {resp}" for resp in respuestas[:2]])
    else:
        respuesta_final = respuestas[0]
    
    return respuesta_final, similitudes[indices_top[0]]

# Título de la aplicación
st.title("🤖 Chatbot IA - Asistente Virtual")
st.markdown("### Carga tu archivo Excel y conversa con tus datos")

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Cargar archivo Excel
archivo_subido = st.sidebar.file_uploader(
    "Sube tu archivo Excel (.xlsx, .xls)",
    type=['xlsx', 'xls'],
    help="El archivo debe contener columnas con preguntas/temas y respuestas"
)

# Inicializar variables de sesión
if 'historial' not in st.session_state:
    st.session_state.historial = []

if 'base_conocimiento' not in st.session_state:
    st.session_state.base_conocimiento = None

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
        if st.sidebar.button("🚀 Procesar y Activar Chatbot"):
            with st.spinner("Procesando datos y generando embeddings..."):
                textos, embeddings, df_limpio = crear_base_conocimiento(df, col_pregunta, col_respuesta)
                
                if textos is not None:
                    st.session_state.base_conocimiento = {
                        'textos': textos,
                        'embeddings': embeddings,
                        'df': df_limpio,
                        'col_respuesta': col_respuesta
                    }
                    st.sidebar.success("✅ ¡Chatbot activado y listo!")
                    st.balloons()

# Mostrar preview de datos
if archivo_subido is not None and df is not None:
    with st.expander("📊 Vista previa de los datos"):
        st.dataframe(df.head(10))

# Área de chat
st.markdown("---")

# Verificar si el chatbot está activo
if st.session_state.base_conocimiento is not None:
    st.success("✅ Chatbot activo - ¡Haz tu pregunta!")
    
    # Formulario de chat
    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        with col1:
            pregunta = st.text_input(
                "Tu pregunta:",
                placeholder="Escribe tu consulta aquí...",
                label_visibility="collapsed"
            )
        
        with col2:
            submit = st.form_submit_button("Enviar", use_container_width=True)
    
    # Procesar pregunta
    if submit and pregunta:
        # Agregar pregunta al historial
        st.session_state.historial.append({"role": "user", "content": pregunta})
        
        # Buscar respuesta
        base = st.session_state.base_conocimiento
        respuesta, confianza = buscar_respuesta(
            pregunta,
            base['textos'],
            base['embeddings'],
            base['df'],
            base['col_respuesta']
        )
        
        # Agregar respuesta al historial
        st.session_state.historial.append({
            "role": "assistant",
            "content": respuesta,
            "confianza": confianza
        })
    
    # Mostrar historial de chat
    st.markdown("### 💬 Conversación")
    for mensaje in st.session_state.historial:
        if mensaje["role"] == "user":
            with st.chat_message("user"):
                st.write(mensaje["content"])
        else:
            with st.chat_message("assistant"):
                st.write(mensaje["content"])
                if "confianza" in mensaje:
                    st.caption(f"Confianza: {mensaje['confianza']:.2%}")
    
    # Botón para limpiar historial
    if st.button("🗑️ Limpiar conversación"):
        st.session_state.historial = []
        st.rerun()

else:
    st.info("👆 Sube un archivo Excel y configura el chatbot para comenzar")
    
    # Mostrar instrucciones
    with st.expander("📖 ¿Cómo usar este chatbot?"):
        st.markdown("""
        **Pasos para usar el chatbot:**
        
        1. **Sube tu archivo Excel** desde el panel lateral
        2. **Selecciona las columnas** que contienen:
           - Preguntas o temas (puede ser: FAQ, Productos, Servicios, etc.)
           - Respuestas o información relacionada
        3. **Haz clic en "Procesar y Activar Chatbot"**
        4. **¡Listo!** Ya puedes hacer preguntas
        
        **Formato recomendado del Excel:**
        - **Columna A**: Pregunta, Tema, Producto, etc.
        - **Columna B**: Respuesta, Descripción, Información, etc.
        
        **Ejemplos de uso:**
        - Base de conocimientos FAQ
        - Catálogo de productos
        - Información de servicios
        - Políticas de empresa
        - Guías técnicas
        """)

# Footer
st.markdown("---")
st.caption("🤖 Chatbot IA con Sentence Transformers | Sin APIs externas")
