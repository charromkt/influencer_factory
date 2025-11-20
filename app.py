import streamlit as st
from openai import OpenAI
import json
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Fábrica de Influencers - Brand People", page_icon="🏭", layout="wide")

# CSS para maximizar espacio
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Constantes
DEFAULT_QUESTIONS = [
    "Su nicho específico",
    "Su Jerga (palabras técnicas que validan autoridad)",
    "Sus 'Enemigos' (opiniones polémicas o mitos que odia)",
    "Sus Anécdotas personales"
]

import uuid

# Inicialización de Session State (Estructura Refactorizada)
def init_session_state():
    if 'data' not in st.session_state:
        st.session_state['data'] = {
            "current_profile_id": None,
            "profiles": {} 
        }
    
    # Migración de datos antiguos (si existen) a la nueva estructura
    if 'profile' in st.session_state and st.session_state['profile'] and not st.session_state['data']['profiles']:
        # Crear un perfil default con los datos viejos
        default_id = str(uuid.uuid4())
        st.session_state['data']['profiles'][default_id] = {
            "name": st.session_state['profile'].get('nombre', 'Perfil Default'),
            "dna": st.session_state['profile'],
            "chat_history": st.session_state.get('chat_history', []),
            "topics": {}
        }
        st.session_state['data']['current_profile_id'] = default_id
        
        # Limpiar estado antiguo para evitar confusión
        for key in ['profile', 'chat_history', 'ideas', 'selected_idea', 'script']:
            if key in st.session_state:
                del st.session_state[key]

init_session_state()

# Helper para obtener el perfil actual
def get_current_profile():
    pid = st.session_state['data']['current_profile_id']
    if pid and pid in st.session_state['data']['profiles']:
        return st.session_state['data']['profiles'][pid]
    return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏭 Fábrica de Influencers")
    
    # --- GESTIÓN DE PERFILES ---
    st.header("👥 Perfiles")
    
    # Selector de Perfil
    profiles = st.session_state['data']['profiles']
    profile_options = {pid: p['name'] for pid, p in profiles.items()}
    
    selected_pid = st.selectbox(
        "Seleccionar Perfil:",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
        index=list(profile_options.keys()).index(st.session_state['data']['current_profile_id']) if st.session_state['data']['current_profile_id'] in profile_options else None,
        key="profile_selector"
    )
    
    if selected_pid != st.session_state['data']['current_profile_id']:
        st.session_state['data']['current_profile_id'] = selected_pid
        st.rerun()

    # Crear Nuevo Perfil
    with st.expander("➕ Nuevo Perfil"):
        new_profile_name = st.text_input("Nombre del Nuevo Perfil")
        if st.button("Crear Perfil"):
            if new_profile_name:
                new_id = str(uuid.uuid4())
                st.session_state['data']['profiles'][new_id] = {
                    "name": new_profile_name,
                    "dna": None,
                    "chat_history": [{"role": "assistant", "content": "Hola. Soy el Estratega Principal. Vamos a definir este nuevo perfil."}],
                    "topics": {}
                }
                st.session_state['data']['current_profile_id'] = new_id
                st.success(f"Perfil '{new_profile_name}' creado.")
                st.rerun()
            else:
                st.warning("Escribe un nombre.")

    # Guardar/Cargar Datos
    with st.expander("💾 Base de Datos (JSON)"):
        # Descargar
        json_str = json.dumps(st.session_state['data'], indent=2)
        st.download_button(
            label="Descargar Todo",
            data=json_str,
            file_name="influencer_factory_data.json",
            mime="application/json"
        )
        
        # Cargar
        uploaded_file = st.file_uploader("Cargar Archivo", type=['json'])
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state['data'] = data
                st.success("Datos cargados correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al cargar: {e}")

    st.divider()
    
    # Navegación Principal
    st.header("Navegación")
    stage = st.radio(
        "Ir a la etapa:",
        ["1. El Perfilador 🕵️", "2. El Estratega 🧠", "3. El Guionista ✍️"]
    )
    
    st.divider()
    
    # Configuración API
    st.subheader("Configuración")
    api_key = st.text_input("OpenAI API Key", type="password")
    
    client = None
    if not api_key:
        st.warning("⚠️ Ingresa tu API Key.")
    else:
        try:
            client = OpenAI(api_key=api_key)
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.divider()

    # Banco de Preguntas (Global o por Perfil? Por ahora Global)
    st.subheader("Banco de Preguntas 📝")
    st.markdown("**Preguntas Base (Obligatorias):**")
    for q in DEFAULT_QUESTIONS:
        st.caption(f"• {q}")
        
    # (Opcional: Podríamos mover custom_questions dentro del perfil, pero por simplicidad lo dejamos global o lo migramos luego)


# --- LAYOUT PRINCIPAL (2 COLUMNAS) ---
col_tools, col_chat = st.columns([1, 1])

current_profile = get_current_profile()

# --- COLUMNA DERECHA: CHAT PERSISTENTE ---
with col_chat:
    # Contenedor de chat con altura fija (550px)
    chat_container = st.container(height=550)
    with chat_container:
        if current_profile:
            for message in current_profile['chat_history']:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        else:
            st.info("Crea o selecciona un perfil para comenzar.")

    # Input del chat (siempre visible abajo)
    if prompt := st.chat_input("Tu respuesta..."):
        if not client:
            st.error("Por favor configura tu API Key en el menú lateral.")
        elif not current_profile:
            st.error("Primero crea un perfil en el menú lateral.")
        else:
            # Agregar usuario al historial
            current_profile['chat_history'].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Preparar preguntas (Base + Custom)
            # (Nota: custom_questions sigue siendo global por ahora, se podría migrar a perfil si se desea)
            final_questions = DEFAULT_QUESTIONS.copy()
            if 'custom_questions' in st.session_state: # Check simple
                 # Lógica simplificada para custom questions global
                 pass 
            
            # Reconstruir questions_str (simplificado para no romper lógica anterior)
            questions_str = "\n".join([f"- {q}" for q in final_questions])

            # Llamada a OpenAI
            system_prompt = f"""Eres el Estratega Principal de la agencia 'Brand People'. Tu misión es construir el perfil de un nuevo talento mediante una entrevista conversacional.
         
         BASE DE CONOCIMIENTO (ARQUETIPOS DE ÉXITO):
         1. El Técnico/Analista (Estilo 'Chapu'/'Fer Pérez'): Datos duros, mecánica, sim-racing, costos reales.
         2. El Insider/Aventurero (Estilo 'Char'): Detrás de cámaras, logística, experiencias exclusivas, enfoque femenino en nichos masculinos.
         3. El Gen Z/Lifestyle (Estilo 'Julian'/'Mateo'): Aspiracional, retos, humor, cultura pop, karts, vlogs rápidos.
         
         TU TAREA:
         Entrevista al usuario para encajarlo en uno de estos arquetipos o crear uno nuevo.
         
         DEBES CUBRIR ESTAS PREGUNTAS CLAVE (una a una, no todas juntas):
         {questions_str}
         
         OBJETIVO FINAL: No generes el perfil aún, solo entrevista paso a paso.
            """
            
            messages = [{"role": "system", "content": system_prompt}] + current_profile['chat_history']
            
            with st.spinner("El Estratega está pensando..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages
                    )
                    bot_reply = response.choices[0].message.content
                    
                    current_profile['chat_history'].append({"role": "assistant", "content": bot_reply})
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(bot_reply)
                except Exception as e:
                    st.error(f"Error de API: {e}")

# --- COLUMNA IZQUIERDA: HERRAMIENTAS POR ETAPA ---
with col_tools:
    
    # Wrapper con altura fija (550px) para scroll independiente
    tools_container = st.container(height=550)
    
    with tools_container:
        if not current_profile:
            st.warning("👈 Crea un perfil nuevo en la barra lateral para comenzar.")
        else:
            # --- VISTA 1: EL PERFILADOR ---
            if stage == "1. El Perfilador 🕵️":
                st.subheader(f"🕵️ Perfilado: {current_profile['name']}")
                st.info("Responde al chat para construir tu perfil.")
                
                # Audio Input (Compacto)
                with st.expander("🎙️ Cargar Audio (Opcional)"):
                    audio_file = st.file_uploader("Archivo de audio", type=['mp3', 'wav', 'm4a'])
                    if audio_file and st.button("Transcribir"):
                        if not client:
                            st.error("Falta API Key.")
                        else:
                            with st.spinner("Transcribiendo..."):
                                try:
                                    transcription = client.audio.transcriptions.create(
                                        model="whisper-1", 
                                        file=audio_file
                                    )
                                    text = transcription.text
                                    st.success("¡Listo!")
                                    current_profile['chat_history'].append({"role": "user", "content": f"[AUDIO]: {text}"})
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                st.write("") # Espacio mínimo
                
                # Generar Perfil
                if st.button("✅ Finalizar y Generar Perfil", type="primary", use_container_width=True):
                    if not client:
                        st.error("Falta API Key.")
                    elif len(current_profile['chat_history']) < 3:
                        st.warning("Conversación muy corta.")
                    else:
                        with st.spinner("Analizando..."):
                            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in current_profile['chat_history']])
                            extraction_prompt = f"""
                            Analiza la siguiente entrevista y extrae el perfil del talento.
                            Conversación:
                            {history_text}
                            
                            Devuelve SOLO un JSON válido con estas claves exactas: 
                            'nombre', 'arquetipo', 'tono', 'jerga_tecnica', 'opiniones_polemicas', 'temas_pasion'.
                            """
                            
                            try:
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "Eres un asistente experto en extracción de datos JSON."},
                                        {"role": "user", "content": extraction_prompt}
                                    ],
                                    response_format={"type": "json_object"}
                                )
                                json_text = response.choices[0].message.content
                                current_profile['dna'] = json.loads(json_text)
                                st.success("¡Perfil Generado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                # Visualizador de Perfil
                if current_profile['dna']:
                    with st.expander("Ver ADN de Marca", expanded=True):
                        st.json(current_profile['dna'])
        # --- VISTA 2: EL ESTRATEGA ---
        elif stage == "2. El Estratega 🧠":
            st.subheader("🧠 Estrategia")
            
            if not current_profile['dna']:
                st.warning("⚠️ Completa la Fase 1 (Perfilado) primero.")
            else:
                st.caption("Perfil: " + current_profile['name'])
                
                # --- GESTIÓN DE TEMAS ---
                st.markdown("### 📂 Temas / Campañas")
                
                # Ensure 'topics' key exists in current_profile
                if 'topics' not in current_profile:
                    current_profile['topics'] = {}

                # Crear Nuevo Tema
                with st.expander("➕ Nuevo Tema", expanded=not bool(current_profile['topics'])):
                    new_topic_name = st.text_input("Nombre del Tema (ej: Black Friday, Educativo, Lanzamiento)")
                    if st.button("Crear Tema"):
                        if new_topic_name:
                            topic_id = str(uuid.uuid4())
                            current_profile['topics'][topic_id] = {
                                "name": new_topic_name,
                                "ideas": []
                            }
                            st.success(f"Tema '{new_topic_name}' creado.")
                            st.rerun()
                
                # Seleccionar Tema Activo
                if not current_profile['topics']:
                    st.info("Crea un tema para empezar a generar ideas.")
                else:
                    topic_options = {tid: t['name'] for tid, t in current_profile['topics'].items()}
                    selected_topic_id = st.selectbox(
                        "Seleccionar Tema Activo:",
                        options=list(topic_options.keys()),
                        format_func=lambda x: topic_options[x]
                    )
                    
                    current_topic = current_profile['topics'][selected_topic_id]
                    
                    st.divider()
                    st.subheader(f"💡 Ideas para: {current_topic['name']}")
                    
                    # Generar Ideas (Si está vacío)
                    if not current_topic['ideas']:
                        if st.button(f"Generar Ideas para {current_topic['name']}", type="primary", use_container_width=True):
                            if not client:
                                st.error("Falta API Key.")
                            else:
                                with st.spinner("Pensando..."):
                                    profile_str = json.dumps(current_profile['dna'])
                                    ideas_prompt = f"""
                                    Actúa como Director Creativo. Usando el perfil JSON, genera 10 ideas de video para el tema '{current_topic['name']}'.
                                    Basadas en los 5 Pilares: EDUCACIÓN, CURIOSIDAD, POLÉMICA, LIFESTYLE, GAMIFICACIÓN.
                                    
                                    Perfil: {profile_str}
                                    
                                    Output esperado: JSON con clave 'ideas' (lista de objetos {{'id': 'uuid', 'titulo', 'pilar', 'gancho_visual', 'script': null}}).
                                    """
                                    
                                    try:
                                        response = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "Eres un experto en marketing viral. Devuelve JSON."},
                                                {"role": "user", "content": ideas_prompt}
                                            ],
                                            response_format={"type": "json_object"}
                                        )
                                        data = json.loads(response.choices[0].message.content)
                                        new_ideas = data.get('ideas', []) if isinstance(data, dict) else data
                                        
                                        # Asegurar ID y script null
                                        for idea in new_ideas:
                                            idea['id'] = str(uuid.uuid4())
                                            if 'script' not in idea: idea['script'] = None
                                            
                                        current_topic['ideas'] = new_ideas
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                    # Mostrar Ideas Existentes
                    else:
                        # Botón para generar MÁS ideas
                        if st.button("🔄 Generar 5 Ideas Más"):
                            if not client:
                                st.error("Falta API Key.")
                            else:
                                with st.spinner("Pensando más ideas..."):
                                    profile_str = json.dumps(current_profile['dna'])
                                    more_ideas_prompt = f"""
                                    Genera 5 ideas ADICIONALES de video para el tema '{current_topic['name']}' y este perfil.
                                    Perfil: {profile_str}
                                    Output: JSON con clave 'ideas' (lista de objetos {{'titulo', 'pilar', 'gancho_visual'}}).
                                    """
                                    try:
                                        response = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "Eres un experto en marketing viral. Devuelve JSON."},
                                                {"role": "user", "content": more_ideas_prompt}
                                            ],
                                            response_format={"type": "json_object"}
                                        )
                                        data = json.loads(response.choices[0].message.content)
                                        new_ideas = data.get('ideas', []) if isinstance(data, dict) else data
                                        for idea in new_ideas:
                                            idea['id'] = str(uuid.uuid4())
                                            idea['script'] = None
                                        current_topic['ideas'].extend(new_ideas)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        # Agregar Idea Personalizada
                        with st.expander("➕ Agregar Idea Personalizada"):
                            with st.form("custom_idea_form"):
                                custom_title = st.text_input("Título de la Idea")
                                custom_hook = st.text_input("Gancho Visual (Opcional)")
                                custom_pilar = st.selectbox("Pilar", ["EDUCACIÓN", "CURIOSIDAD", "POLÉMICA", "LIFESTYLE", "GAMIFICACIÓN", "OTRO"])
                                
                                if st.form_submit_button("Agregar Idea"):
                                    if custom_title:
                                        new_custom_idea = {
                                            "id": str(uuid.uuid4()),
                                            "titulo": custom_title,
                                            "pilar": custom_pilar,
                                            "gancho_visual": custom_hook if custom_hook else "N/A",
                                            "script": None
                                        }
                                        current_topic['ideas'].append(new_custom_idea)
                                        st.success("Idea agregada.")
                                        st.rerun()
                                    else:
                                        st.warning("El título es obligatorio.")

                        st.write("---")
                        for idea in current_topic['ideas']:
                            with st.expander(f"[{idea['pilar']}] {idea['titulo']}"):
                                st.write(f"**Gancho:** {idea['gancho_visual']}")
                                if idea.get('script'):
                                    st.success("✅ Guión listo")

        # --- VISTA 3: EL GUIONISTA ---
        elif stage == "3. El Guionista ✍️":
            st.subheader("✍️ Guionización")
            
            if not current_profile['topics']:
                st.warning("⚠️ Primero crea Temas e Ideas en la Fase 2.")
            else:
                # Selector de Tema
                topic_options = {tid: t['name'] for tid, t in current_profile['topics'].items()}
                selected_topic_id = st.selectbox(
                    "Seleccionar Tema:",
                    options=list(topic_options.keys()),
                    format_func=lambda x: topic_options[x],
                    key="script_topic_selector"
                )
                current_topic = current_profile['topics'][selected_topic_id]
                
                if not current_topic['ideas']:
                    st.warning("Este tema no tiene ideas aún.")
                else:
                    # Selector de Idea
                    idea_options = {idea['id']: idea['titulo'] for idea in current_topic['ideas']}
                    selected_idea_id = st.selectbox(
                        "Seleccionar Idea:",
                        options=list(idea_options.keys()),
                        format_func=lambda x: idea_options[x],
                        key="script_idea_selector"
                    )
                    
                    # Encontrar objeto idea seleccionado
                    selected_idea = next((i for i in current_topic['ideas'] if i['id'] == selected_idea_id), None)
                    
                    if selected_idea:
                        st.caption(f"Gancho: {selected_idea['gancho_visual']}")
                        
                        # Configuración Avanzada (Prompt Editable)
                        with st.expander("⚙️ Configuración Avanzada del Guionista", expanded=False):
                            default_script_prompt = """Eres el Guionista Senior de Brand People. Escribe el guión para la idea seleccionada.
                 
LA FÓRMULA MATEMÁTICA DEL GUIÓN (NO TE DESVÍES):
1. EL GANCHO (0-3 seg): Prohibido saludar. Inicia con Afirmación Polémica, Lista o Reto.
2. EL CUERPO (4-50 seg): Velocidad alta. Frases cortas. Jerga técnica explicada rápido.
3. EL CTA (Final): Llamado a la acción específico.

Perfil: {profile_str}
Idea: {idea_str}

Formato: Texto plano, líneas dobles."""
                            
                            script_instructions = st.text_area(
                                "Instrucciones para el Guionista (Prompt):", 
                                value=default_script_prompt,
                                height=300,
                                help="Puedes editar estas instrucciones. Mantén {profile_str} y {idea_str} donde quieras que se inserten los datos."
                            )
                        
                        if st.button("Escribir Guión", type="primary", use_container_width=True):
                            if not client:
                                st.error("Falta API Key.")
                            else:
                                with st.spinner("Escribiendo..."):
                                    profile_str = json.dumps(current_profile['dna'])
                                    idea_str = json.dumps(selected_idea)
                                    
                                    final_script_prompt = script_instructions.replace("{profile_str}", profile_str).replace("{idea_str}", idea_str)
                                    
                                    try:
                                        response = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "Eres un guionista experto."},
                                                {"role": "user", "content": final_script_prompt}
                                            ]
                                        )
                                        selected_idea['script'] = response.choices[0].message.content
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        
                        if selected_idea.get('script'):
                            st.text_area("Teleprompter:", value=selected_idea['script'], height=300)
