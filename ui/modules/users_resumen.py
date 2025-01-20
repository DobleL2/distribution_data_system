import io
import pandas as pd
import requests
import streamlit as st
from modules.api_url import API_URL as API_BASE_URL

def run():
    if "auth_token" not in st.session_state or not st.session_state["auth_token"]:
        st.error("Debe iniciar sesión para tener acceso a esta pagina.")
        st.stop()
    else:
        def get_users_resumen(table_name):
            response = requests.get(f"{API_BASE_URL}/resumen_production/", params={"dataset": table_name})
            return response.json()

        def get_datasets():
            return requests.get(f"{API_BASE_URL}/datasets_names/").json()
        
        tables = get_datasets()['results']
        tables = pd.DataFrame(tables)
        st.title("Resumen de registros procesados por los usuarios en la aplicación")
        st.info("En el caso que se tenga varias bases subidas y se quiera trabajar con alguna en especifico seleccionarla",icon="ℹ️")
        if not tables.empty:
            datasets_options = tables['dataset_name'].unique()
            table_name_to_select = st.selectbox('Table to select',datasets_options)
            if st.button("Select Table"):
                response = get_users_resumen(table_name_to_select)
                df_resume = pd.DataFrame(response['results'])
                st.write(df_resume)
                # Crear el botón de descarga
                st.download_button(
                    label="Descargar registros procesados por usuarios en Excel",
                    data=resumen_data(df_resume),
                    file_name="production.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info('No hay tablas disponibles en este momento para eliminar')
        
        
def resumen_data(df):
    # Guardar el DataFrame en un buffer de bytes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    output.seek(0)
    
    return output