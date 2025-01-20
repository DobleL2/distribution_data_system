import pandas as pd
import requests
import streamlit as st
from modules.api_url import API_URL as API_BASE_URL

def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:
        def delete_table(table_name):
            response = requests.delete(f"{API_BASE_URL}/delete_table/", params={"table_name": table_name})
            return response.json()

        def get_datasets():
            return requests.get(f"{API_BASE_URL}/datasets_names/").json()
        
        tables = get_datasets()['results']
        tables = pd.DataFrame(tables)
        st.title("Borrar tablas")
        st.info("En el caso que se necesite borrar alguna de las tablas ingresadas",icon="ℹ️")
        st.warning("NOTA: Una vez eliminada la información no podrá recuperarse",icon="ℹ️")
        if not tables.empty:
            datasets_options = tables['dataset_name'].unique()
            table_name_to_delete = st.selectbox('Table to Delete',datasets_options)
            if st.button("Delete Table"):
                response = delete_table(table_name_to_delete)
                st.info(response)
                st.rerun()
        else:
            st.info('No hay tablas disponibles en este momento para eliminar')
        

        

        

