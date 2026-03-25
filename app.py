import streamlit as st
import pandas as pd
import io

def conciliar_ventas_vs_cfdi(file_upload):
    """
    Función que recibe un archivo en memoria (subido vía Streamlit),
    lee las hojas necesarias, realiza el cruce y devuelve un nuevo archivo en memoria.
    """
    # Cargar los datos desde el archivo subido
    try:
        # read_excel soporta objetos de archivo (bytes) en Pandas
        xls = pd.ExcelFile(file_upload)

        hojas_necesarias = ["VENTAS_BBVA", "CFDI_I_PUE", "CFDI_I_PPD"]
        hojas_faltantes = [h for h in hojas_necesarias if h not in xls.sheet_names]

        if hojas_faltantes:
            st.error(f"El archivo no contiene las siguientes hojas requeridas: {', '.join(hojas_faltantes)}")
            return None

        df_ventas = pd.read_excel(xls, sheet_name="VENTAS_BBVA")
        df_pue = pd.read_excel(xls, sheet_name="CFDI_I_PUE")
        df_ppd = pd.read_excel(xls, sheet_name="CFDI_I_PPD")

    except Exception as e:
        st.error(f"Error al leer el archivo de Excel: {e}")
        return None

    # Normalizar columnas (todo a minúsculas, sin espacios al inicio/final)
    df_ventas.columns = df_ventas.columns.str.lower().str.strip()
    df_pue.columns = df_pue.columns.str.lower().str.strip()
    df_ppd.columns = df_ppd.columns.str.lower().str.strip()

    # Identificar nombres de columnas clave (Manejo de variaciones)
    col_uuid_ventas = 'uuid' if 'uuid' in df_ventas.columns else None

    # Manejo dinámico para la columna de monto
    posibles_nombres_monto = ['total', 'importe', 'monto', 'cargo']
    col_monto_ventas = next((col for col in posibles_nombres_monto if col in df_ventas.columns), None)

    if not col_uuid_ventas or not col_monto_ventas:
        st.error(f"No se encontraron columnas de 'UUID' o de 'Monto/Total' en VENTAS_BBVA. Columnas actuales: {df_ventas.columns.tolist()}")
        return None

    # Añadir columnas de resultado
    df_ventas['Estado_Conciliacion'] = 'PENDIENTE'
    df_ventas['Origen_Conciliacion'] = ''

    # Variables para resumen
    resumen = {"PUE (UUID)": 0, "PPD (UUID)": 0, "PUE (Monto)": 0}

    # ==========================================
    # PASO 1: CONCILIAR POR UUID EXACTO (PUE)
    # ==========================================
    if 'uuid' in df_pue.columns:
        uuids_pue = df_pue['uuid'].dropna().unique()
        mask_pue = df_ventas[col_uuid_ventas].isin(uuids_pue) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        df_ventas.loc[mask_pue, 'Estado_Conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_pue, 'Origen_Conciliacion'] = 'CFDI PUE (UUID)'
        resumen["PUE (UUID)"] = int(mask_pue.sum())

    # ==========================================
    # PASO 2: CONCILIAR POR UUID EXACTO (PPD)
    # ==========================================
    if 'uuid' in df_ppd.columns:
        uuids_ppd = df_ppd['uuid'].dropna().unique()
        mask_ppd = df_ventas[col_uuid_ventas].isin(uuids_ppd) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        df_ventas.loc[mask_ppd, 'Estado_Conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_ppd, 'Origen_Conciliacion'] = 'CFDI PPD (UUID)'
        resumen["PPD (UUID)"] = int(mask_ppd.sum())

    # ==========================================
    # PASO 3: CONCILIAR POR MONTO (Si no hubo UUID en PUE)
    # ==========================================
    col_monto_pue = next((col for col in posibles_nombres_monto if col in df_pue.columns), None)

    if col_monto_pue:
        montos_pue = df_pue[col_monto_pue].dropna().unique()
        mask_monto = df_ventas[col_monto_ventas].isin(montos_pue) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        df_ventas.loc[mask_monto, 'Estado_Conciliacion'] = 'REVISIÓN MONTO'
        df_ventas.loc[mask_monto, 'Origen_Conciliacion'] = 'CFDI PUE (Monto Similar)'
        resumen["PUE (Monto)"] = int(mask_monto.sum())

    # Preparar el archivo de salida en memoria (BytesIO)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_ventas.to_excel(writer, sheet_name='VENTAS_PROCESADAS', index=False)
        # Puedes añadir los CFDI originales o hojas de resumen aquí
        df_pue.to_excel(writer, sheet_name='CFDI_I_PUE', index=False)
        df_ppd.to_excel(writer, sheet_name='CFDI_I_PPD', index=False)

        # Opcional: Crear una hoja de resumen
        pd.DataFrame(list(resumen.items()), columns=['Método', 'Cantidad Conciliada']).to_excel(writer, sheet_name='RESUMEN', index=False)

    return output.getvalue(), resumen


# ==========================================================
# INTERFAZ GRÁFICA (FRONTEND) CON STREAMLIT
# ==========================================================

st.set_page_config(page_title="App de Conciliación", page_icon="💰", layout="wide")

st.title("💰 Sistema de Conciliación Automática")
st.markdown("""
Esta aplicación reemplaza las macros de Excel.
Sube tu archivo con las hojas **VENTAS_BBVA**, **CFDI_I_PUE** y **CFDI_I_PPD** y la app procesará todo en segundos.
""")

# 1. Componente para subir archivos
uploaded_file = st.file_uploader("Sube tu archivo de Excel (.xlsx o .xlsm)", type=["xlsx", "xlsm"])

if uploaded_file is not None:
    st.info("Archivo cargado exitosamente. Haz clic en el botón para iniciar.")

    # 2. Botón de ejecución
    if st.button("🚀 Ejecutar Conciliación (BBVA vs CFDI)", type="primary"):
        with st.spinner("Procesando miles de registros. Por favor espera..."):

            # Llamamos a nuestra función de Pandas
            resultado = conciliar_ventas_vs_cfdi(uploaded_file)

            if resultado is not None:
                excel_bytes, resumen = resultado

                st.success("¡Conciliación completada con éxito en segundos!")

                # Mostrar resumen rápido en pantalla
                st.subheader("📊 Resumen del Proceso")
                col1, col2, col3 = st.columns(3)
                col1.metric("Conciliados UUID (PUE)", resumen["PUE (UUID)"])
                col2.metric("Conciliados UUID (PPD)", resumen["PPD (UUID)"])
                col3.metric("Revisión Monto (PUE)", resumen["PUE (Monto)"])

                st.markdown("---")
                st.markdown("### Descarga tu archivo procesado:")

                # 3. Botón de descarga
                st.download_button(
                    label="📥 Descargar Excel Conciliado",
                    data=excel_bytes,
                    file_name="CONCILIACION_RESULTADO_FINAL.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
