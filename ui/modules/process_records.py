import requests
import streamlit as st
from modules.api_url import API_URL as API_BASE_URL

def get_record(user_id):
    response = requests.get(f"{API_BASE_URL}/get_record/", params={"user_id": user_id})
    return response.json()

def mark_as_processed(record_id, user_id):
    response = requests.post(
        f"{API_BASE_URL}/mark_as_processed/",
        json={"record_id": int(record_id), "user_id": str(user_id)}
    )
    return response.json()


def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:
        st.title("Process Record")
        st.header("Get Record for Processing")

        user_id = st.session_state['id']

        if st.button("Obtener Registro"):
            if st.session_state['record_id'] != None:
                mark_as_processed(int(st.session_state['record_id']), str(user_id))
            record = get_record(user_id)
            if record and 'data' in record:
                st.session_state['record_id'] = record['record_id']
                datos_demograficos, datos_respuestas = dividir_datos(record['data'])

                # Mostrar datos demográficos en 3 columnas
                st.subheader("Datos Demográficos")
                columnas_demo = st.columns(3)
                for i, (clave, valor) in enumerate(datos_demograficos.items()):
                    with columnas_demo[i % 3]:
                        html_content = f"""
                        <span style='font-size:18px; font-weight:bold; color:orange'>{clave}:</span>
                        <span style='font-size:16px;'>{valor}</span>
                        """
                        st.markdown(html_content, unsafe_allow_html=True)

                st.divider()  # Línea divisoria

                # Mostrar datos de respuestas en 5 columnas
                st.subheader("Datos de Respuestas")
                columnas_resp = st.columns(5)
                for i, (clave, valor) in enumerate(datos_respuestas.items()):
                    with columnas_resp[i % 5]:
                        html_content = f"""
                        <span style='font-size:18px; font-weight:bold; color:skyblue'>{clave}:</span>
                        <span style='font-size:16px;'>{valor}</span>
                        """
                        st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.error("No hay registros disponibles.")
        if st.session_state['record_id'] != None:
            if st.button('Finalizar Sesion'):
                mark_as_processed(int(st.session_state['record_id']), str(user_id))
                st.session_state["auth_token"] = None
                st.rerun()

import re

# Función para dividir los datos en demográficos y respuestas
def dividir_datos(datos):
    datos_demograficos = {}
    datos_respuestas = {}
    for clave, valor in datos.items():
        if re.match(r'^P', clave):  # Claves que comienzan con 'P'
            datos_respuestas[clave] = valor
        else:
            datos_demograficos[clave] = valor
    return datos_demograficos, datos_respuestas