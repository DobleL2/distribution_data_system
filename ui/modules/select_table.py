import pandas as pd
import requests
import streamlit as st
from modules.api_url import API_URL as API_BASE_URL

def select_table(table_name):
    response = requests.get(f"{API_BASE_URL}/select_dataset/", params={"dataset": table_name})
    return response.json()

def get_datasets():
    return requests.get(f"{API_BASE_URL}/datasets_names/").json()

def get_current_dataset():
    return requests.get(f"{API_BASE_URL}/current_dataset/").json()

def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:        
        tables = get_datasets()['results']
        tables = pd.DataFrame(tables)
        st.title("Seleccionar Tabla de Registros a utilizar")
        st.info("En el caso que se tenga varias bases subidas y se quiera trabajar con alguna en especifico seleccionarla",icon="ℹ️")
        current_dataset = get_current_dataset()
        if current_dataset:            
            st.subheader("Actual dataset seleccionado")
            st.write(f'Nombre: {current_dataset["dataset_name"]}')
            st.write(pd.DataFrame(current_dataset['results']).drop(columns=['id','status','assigned_to','assigned_at','processed_at']))
        else:
            st.warning("No se ha seleccionado un dataset todavía, seleccione alguno de los disponibles o suba uno.")

        if not tables.empty:
            st.subheader('Nuevo dataset con el que se desea trabajar')
            datasets_options = tables['dataset_name'].unique().tolist()
            datasets_options = [i for i in datasets_options if i!=current_dataset['dataset_name']]
            table_name_to_select = st.selectbox('Dataset a seleccionar',datasets_options)
            if datasets_options:
                if st.button("Cambiar a la tabla seleccionada"):
                    response = select_table(table_name_to_select)
                    st.rerun()
                    st.info(response)
        else:
            st.info('No hay tablas disponibles en este momento para seleccionar')
        