import json
import pandas as pd
import requests
import streamlit as st
from modules.api_url import API_URL as API_BASE_URL


def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:
        def add_table(data, table_name):
            url = f"{API_BASE_URL}/add_table/"
            payload = {
                "data": data,
                "table_name": table_name
            }
            response = requests.post(url, json=payload)
            return response.json()

        st.title("Cargar datos que se desean procesar")
        st.info("En esta sección se sube el archivo que se desee procesar y repartir entre los usuarios.",icon="ℹ️")

        uploaded_file = st.file_uploader("Upload your file (CSV/XLSX)", type=["csv", "xlsx"])

        if uploaded_file:
            table_name = st.text_input("Table Name")
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)  
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)  
            else:
                st.error('Unsupported file format. Please upload a CSV or Excel file.')
                df = None
            if not df.empty:
                df = df.fillna('')
                verificar_columna(df,'ID','ID_TABLE')
                verificar_columna(df,'id','ID_TABLE')
                verificar_columna(df,'STATUS','STATUS_TABLE')
                verificar_columna(df,'status','STATUS_TABLE')
                st.write("Uploaded Data:", df)
                df_dict = df.to_dict(orient="list")
                if table_name:
                    if st.button("Create Table"):
                        response = add_table(df_dict, 'dataset_'+table_name.strip().replace(" ","_"))
                        st.info(response["message"])

def verificar_columna(df,columna_a_verificar,nuevo_nombre):
    # Verificar si la columna existe y cambiarle el nombre
    if columna_a_verificar in df.columns:
        df.rename(columns={columna_a_verificar: nuevo_nombre}, inplace=True)