import streamlit as st
import requests
import json
from docx import Document
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Diccionario de Problemas Económicos", page_icon="📚", layout="wide")

# Function to set the background color
def set_background_color(color):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Function to create the information column
def crear_columna_info():
    st.markdown("""
    ### Sobre esta aplicación

    Esta aplicación es un Diccionario de Problemas Económicos. Permite a los usuarios obtener respuestas a problemas económicos según la interpretación de diversas corrientes económicas.

    ### Cómo usar la aplicación:

    1. Elija un problema económico de la lista predefinida o proponga su propio problema.
    2. Seleccione una o más corrientes económicas.
    3. Haga clic en "Obtener respuesta" para generar las respuestas.
    4. Lea las respuestas y fuentes proporcionadas.
    5. Si lo desea, descargue un documento DOCX con toda la información.

    ### Autor y actualización:
    **Moris Polanco**, 26 ag 2024

    ### Cómo citar esta aplicación (formato APA):
    Polanco, M. (2024). *Diccionario de Problemas Económicos* [Aplicación web]. https://dicproblemas.streamlit.app

    ---
    **Nota:** Esta aplicación utiliza inteligencia artificial para generar respuestas basadas en información disponible en línea. Siempre verifique la información con fuentes académicas para un análisis más profundo.
    """)

# Titles and Main Column
st.title("Diccionario de Problemas Económicos")

# Set background color to light yellow
set_background_color("#FFF9C4")  # Light yellow color code

col1, col2 = st.columns([1, 2])

with col1:
    crear_columna_info()

with col2:
    TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
    SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

    # 101 economic problems in question form
    problemas_economicos = sorted([
        # ... the same list of problems ...
    ])

    # Economic schools of thought
    escuelas_economicas = [
        # ... the same list of schools ...
    ]

    def buscar_informacion(query, escuela):
        url = "https://google.serper.dev/search"
        payload = json.dumps({
            "q": f"{query} {escuela} economía"
        })
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()

    def generar_respuesta(problema, escuela, contexto):
        url = "https://api.together.xyz/inference"
        payload = json.dumps({
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "prompt": f"Contexto: {contexto}\n\nProblema: {problema}\nEscuela: {escuela}\n\nProporciona una respuesta al problema económico '{problema}' según la interpretación del {escuela}. La respuesta debe ser concisa pero informativa, similar a una entrada de diccionario. Si es posible, incluye una referencia a una obra o figura específica de {escuela} que trate este concepto.\n\nRespuesta:",
            "max_tokens": 2048,
            "temperature": 0,
            "top_p": 0.7,
            "top_k": 50,
            "repetition_penalty": 0,
            "stop": ["Problema:"]
        })
        headers = {
            'Authorization': f'Bearer {TOGETHER_API_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        return response.json()['output']['choices'][0]['text'].strip()

    def create_docx(problema, respuestas, fuentes):
        doc = Document()
        doc.add_heading('Diccionario de Problemas Económicos', 0)

        doc.add_heading('Problema', level=1)
        doc.add_paragraph(problema)

        for escuela, respuesta in respuestas.items():
            doc.add_heading(f'Respuesta según la corriente {escuela}', level=2)
            doc.add_paragraph(respuesta)

        doc.add_heading('Fuentes', level=1)
        for fuente in fuentes[:10]:  # Limit to ten sources
            doc.add_paragraph(fuente, style='List Bullet')

        doc.add_paragraph('\nNota: Este documento fue generado por un asistente de IA. Verifica la información con fuentes académicas para un análisis más profundo.')

        doc.add_paragraph('\nPolanco, M. (2024). Diccionario de Problemas Económicos [Aplicación web]. https://dicproblemas.streamlit.app')

        return doc

    st.write("**Elige un problema económico de la lista o propón tu propio problema**:")

    opcion = st.radio("", ["Elegir de la lista", "Proponer mi propio problema"])

    if opcion == "Elegir de la lista":
        problema = st.selectbox("Selecciona un problema:", problemas_economicos)
    else:
        problema = st.text_input("Ingresa tu propio problema económico:")

    st.write("Selecciona una o más corrientes económicas (máximo 5):")
    escuelas_seleccionadas = st.multiselect("Corrientes Económicas", escuelas_economicas)

    if len(escuelas_seleccionadas) > 5:
        st.warning("Has seleccionado más de 5 corrientes. Por favor, selecciona un máximo de 5.")
    else:
        if st.button("Obtener respuesta"):
            if problema and escuelas_seleccionadas:
                with st.spinner("Buscando información y generando respuestas..."):
                    respuestas, todas_fuentes = {}, []

                    for escuela in escuelas_seleccionadas:
                        # Buscar información relevante
                        resultados_busqueda = buscar_informacion(problema, escuela)
                        contexto = "\n".join([item["snippet"] for item in resultados_busqueda.get("organic", [])])
                        fuentes = [item["link"] for item in resultados_busqueda.get("organic", [])]

                        # Generar respuesta
                        respuesta = generar_respuesta(problema, escuela, contexto)

                        respuestas[escuela] = respuesta
                        todas_fuentes.extend(fuentes)

                    # Mostrar las respuestas
                    st.subheader(f"Respuestas para el problema: {problema}")
                    for escuela, respuesta in respuestas.items():
                        st.markdown(f"**{escuela}:** {respuesta}")

                    # Botón para descargar el documento
                    doc = create_docx(problema, respuestas, todas_fuentes)
                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)
                    st.download_button(
                        label="Descargar respuesta en DOCX",
                        data=buffer,
                        file_name=f"Respuesta_{problema.replace(' ', '_')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            else:
                st.warning("Por favor, selecciona un problema y al menos una corriente.")
