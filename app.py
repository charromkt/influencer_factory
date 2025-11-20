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

# Inicialización de Session State
def init_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = [
            {"role": "assistant", "content": "Hola. Soy el Estratega Principal de Brand People. Vamos a encontrar tu ángulo único. Para empezar, cuéntame: ¿A qué te dedicas y cuál es tu objetivo principal en redes?"}
        ]
    if 'profile' not in st.session_state:
        st.session_state['profile'] = None
    if 'ideas' not in st.session_state:
        st.session_state['ideas'] = None
    if 'selected_idea' not in st.session_state:
        st.session_state['selected_idea'] = None
    if 'script' not in st.session_state:
        st.session_state['script'] = None
    if 'custom_questions' not in st.session_state:
        st.session_state['custom_questions'] = pd.DataFrame([
            {"Pregunta": "Pregunta personalizada 1..."}
        ])

init_session_state()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏭 Fábrica de Influencers")
    
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
    
    # Banco de Preguntas
    st.subheader("Banco de Preguntas 📝")
    st.markdown("**Preguntas Base (Obligatorias):**")
    for q in DEFAULT_QUESTIONS:
        st.caption(f"• {q}")
        
    use_custom = st.toggle("Añadir preguntas personalizadas")
    if use_custom:
        st.session_state['custom_questions'] = st.data_editor(
            st.session_state['custom_questions'],
            num_rows="dynamic",
            hide_index=True,
            key="questions_editor"
        )

# --- LAYOUT PRINCIPAL (2 COLUMNAS) ---
col_tools, col_chat = st.columns([1, 1])

# --- COLUMNA DERECHA: CHAT PERSISTENTE ---
with col_chat:
    # Contenedor de chat con altura fija (550px)
    chat_container = st.container(height=550)
    with chat_container:
        for message in st.session_state['chat_history']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input del chat (siempre visible abajo)
    if prompt := st.chat_input("Tu respuesta..."):
        if not client:
            st.error("Por favor configura tu API Key en el menú lateral.")
        else:
            # Agregar usuario al historial
            st.session_state['chat_history'].append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Preparar preguntas (Base + Custom)
            final_questions = DEFAULT_QUESTIONS.copy()
            if use_custom:
                custom_list = st.session_state['custom_questions']["Pregunta"].tolist()
                custom_list = [q for q in custom_list if q and str(q).strip()]
                final_questions.extend(custom_list)
            
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
            
            messages = [{"role": "system", "content": system_prompt}] + st.session_state['chat_history']
            
            with st.spinner("El Estratega está pensando..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=messages
                    )
                    bot_reply = response.choices[0].message.content
                    
                    st.session_state['chat_history'].append({"role": "assistant", "content": bot_reply})
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
        # --- VISTA 1: EL PERFILADOR ---
        if stage == "1. El Perfilador 🕵️":
            st.subheader("🕵️ Perfilado")
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
                                st.session_state['chat_history'].append({"role": "user", "content": f"[AUDIO]: {text}"})
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

            st.write("") # Espacio mínimo
            
            # Generar Perfil
            if st.button("✅ Finalizar y Generar Perfil", type="primary", use_container_width=True):
                if not client:
                    st.error("Falta API Key.")
                elif len(st.session_state['chat_history']) < 3:
                    st.warning("Conversación muy corta.")
                else:
                    with st.spinner("Analizando..."):
                        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state['chat_history']])
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
                            st.session_state['profile'] = json.loads(json_text)
                            st.success("¡Perfil Generado!")
                        except Exception as e:
                            st.error(f"Error: {e}")

            # Visualizador de Perfil
            if st.session_state['profile']:
                with st.expander("Ver ADN de Marca", expanded=True):
                    st.json(st.session_state['profile'])

        # --- VISTA 2: EL ESTRATEGA ---
        elif stage == "2. El Estratega 🧠":
            st.subheader("🧠 Estrategia")
            
            if not st.session_state['profile']:
                st.warning("⚠️ Completa la Fase 1.")
            else:
                st.caption("Perfil: " + st.session_state['profile'].get('nombre', 'Desconocido'))
                
                if st.button("Generar Ideas (Brand People)", type="primary", use_container_width=True):
                    if not client:
                        st.error("Falta API Key.")
                    else:
                        with st.spinner("Pensando..."):
                            profile_str = json.dumps(st.session_state['profile'])
                            ideas_prompt = f"""
                            Actúa como Director Creativo de Brand People. Usando el perfil JSON, genera 10 ideas de video basadas ESTRICTAMENTE en los 5 Pilares de la Agencia:
                            1. EDUCACIÓN RÁPIDA (How-To)
                            2. CURIOSIDAD (Did you know?)
                            3. POLÉMICA/RANKING
                            4. LIFESTYLE/VLOG
                            5. GAMIFICACIÓN
                            
                            Perfil: {profile_str}
                            
                            Output esperado: JSON con clave 'ideas' (lista de objetos {{'titulo', 'pilar', 'gancho_visual'}}).
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
                                st.session_state['ideas'] = data.get('ideas', []) if isinstance(data, dict) else data
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                # Botón para generar MÁS ideas (append)
                if st.session_state['ideas'] and st.button("🔄 Generar 5 Ideas Más"):
                    if not client:
                        st.error("Falta API Key.")
                    else:
                        with st.spinner("Pensando más ideas..."):
                            profile_str = json.dumps(st.session_state['profile'])
                            # Prompt simplificado para añadir más
                            more_ideas_prompt = f"""
                            Genera 5 ideas ADICIONALES de video para este perfil.
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
                                st.session_state['ideas'].extend(new_ideas)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                
                # Sección para agregar idea personalizada
                with st.expander("➕ Agregar Idea Personalizada"):
                    with st.form("custom_idea_form"):
                        custom_title = st.text_input("Título de la Idea")
                        custom_hook = st.text_input("Gancho Visual (Opcional)")
                        custom_pilar = st.selectbox("Pilar", ["EDUCACIÓN", "CURIOSIDAD", "POLÉMICA", "LIFESTYLE", "GAMIFICACIÓN", "OTRO"])
                        
                        if st.form_submit_button("Agregar Idea"):
                            if custom_title:
                                new_custom_idea = {
                                    "titulo": custom_title,
                                    "pilar": custom_pilar,
                                    "gancho_visual": custom_hook if custom_hook else "N/A"
                                }
                                if st.session_state['ideas'] is None:
                                    st.session_state['ideas'] = []
                                st.session_state['ideas'].append(new_custom_idea)
                                st.success("Idea agregada.")
                                st.rerun()
                            else:
                                st.warning("El título es obligatorio.")

                if st.session_state['ideas']:
                    st.write("---")
                    options = [f"[{idea['pilar']}] {idea['titulo']}" for idea in st.session_state['ideas']]
                    selection = st.radio("Selecciona una idea:", options)
                    
                    index = options.index(selection)
                    st.session_state['selected_idea'] = st.session_state['ideas'][index]
                    
                    st.info(f"**Gancho:** {st.session_state['selected_idea']['gancho_visual']}")

        # --- VISTA 3: EL GUIONISTA ---
        elif stage == "3. El Guionista ✍️":
            st.subheader("✍️ Guionización")
            
            if not st.session_state['selected_idea']:
                st.warning("⚠️ Selecciona una idea en Fase 2.")
            else:
                st.caption(f"Idea: {st.session_state['selected_idea']['titulo']}")
                
                # Configuración Avanzada del Guionista (Editable)
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
                            profile_str = json.dumps(st.session_state['profile'])
                            idea_str = json.dumps(st.session_state['selected_idea'])
                            
                            # Usar el prompt del área de texto si existe, sino el default
                            final_script_prompt = script_instructions.replace("{profile_str}", profile_str).replace("{idea_str}", idea_str)
                            
                            try:
                                response = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "Eres un guionista experto."},
                                        {"role": "user", "content": final_script_prompt}
                                    ]
                                )
                                st.session_state['script'] = response.choices[0].message.content
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

                if st.session_state['script']:
                    st.text_area("Teleprompter:", value=st.session_state['script'], height=300)
