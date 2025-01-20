import requests
import streamlit as st
import pandas as pd
from modules.api_url import API_URL as API_BASE_URL

def buscar_registro(dataset,id_name,id_busqueda):
    response = requests.get(f"{API_BASE_URL}/buscar_registro/", params={"dataset": dataset,"id_name":id_name,"id_busqueda":id_busqueda})
    return response.json()

def get_datasets():
    return requests.get(f"{API_BASE_URL}/datasets_names/").json()


def get_columns(dataset):
    return requests.get(f"{API_BASE_URL}/get_columns/",params={"dataset":dataset}).json()

def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:
        st.title("Busqueda de registros")
        tables = get_datasets()['results']
        tables = pd.DataFrame(tables)
        st.info("En el caso que se necesite buscar algun registro en específico, seleccionar la columna con el identificador único en la tabla cuando se subio y buscar en base a dicho registro único",icon="ℹ️")
        if not tables.empty:
            datasets_options = tables['dataset_name'].unique()
            dataset = st.selectbox('Table to select',datasets_options)
            if dataset:
                columnas_base =get_columns(dataset)['results']
                no_mostrar = {'id','status','assigned_to','assigned_at','processed_at'}
                columnas = [elemento for elemento in columnas_base if elemento not in no_mostrar]
                id_name = st.selectbox("Seleccionar identificador unico para busqueda:", options=columnas)
                id_busqueda = st.text_input("Ingrese el registro a buscar")

                if st.button("Buscar Registro"):
                    record = buscar_registro(dataset,id_name,id_busqueda)['results']
                    if len(record)>0:
                        record = record[0]
                        st.session_state['record_id'] = record['id']
                        datos_demograficos, datos_respuestas = dividir_datos(record)

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
                        st.warning('No existen registros con el identificador buscado')
        else:
            st.info('No hay tablas disponibles en este momento para mostrar')

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