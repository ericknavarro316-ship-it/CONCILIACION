import streamlit as st
import pandas as pd
import io

def preparar_datos_crudos(file_upload):
    """
    Módulo P00: Limpieza y separación de hojas crudas.
    Recibe el archivo subido, extrae Notas de Venta, Bancos y separa CFDI I en PUE y PPD.
    """
    xls = pd.ExcelFile(file_upload)
    hojas_disponibles = xls.sheet_names

    datos = {}

    # 1. Extraer y limpiar Ventas (NOTA DE VENTA)
    if 'NOTA DE VENTA' in hojas_disponibles:
        df_ventas = pd.read_excel(xls, sheet_name='NOTA DE VENTA')
        # Limpiar columnas
        df_ventas.columns = df_ventas.columns.str.lower().str.strip()
        datos['VENTAS'] = df_ventas
    else:
        st.error("❌ El archivo crudo no tiene la hoja 'NOTA DE VENTA'.")
        return None

    # 2. Extraer y separar CFDI I
    if 'CFDI I' in hojas_disponibles:
        # Los reportes del SAT suelen tener el encabezado en la fila 3 (index 2)
        try:
            df_cfdi_i = pd.read_excel(xls, sheet_name='CFDI I', header=2)
            df_cfdi_i.columns = df_cfdi_i.columns.str.strip()

            # Identificar Método de Pago
            col_metodo = next((col for col in ['Método de Pago', 'Metodo de Pago'] if col in df_cfdi_i.columns), None)

            if col_metodo:
                df_pue = df_cfdi_i[df_cfdi_i[col_metodo].astype(str).str.contains('PUE', na=False, case=False)].copy()
                df_ppd = df_cfdi_i[df_cfdi_i[col_metodo].astype(str).str.contains('PPD', na=False, case=False)].copy()

                # Limpiar columnas para que coincidan con la lógica de I00
                df_pue.columns = df_pue.columns.str.lower().str.strip()
                df_ppd.columns = df_ppd.columns.str.lower().str.strip()

                datos['CFDI_I_PUE'] = df_pue
                datos['CFDI_I_PPD'] = df_ppd
            else:
                st.warning("⚠️ No se encontró la columna 'Método de Pago' en 'CFDI I'. No se pudo separar PUE/PPD.")
                return None
        except Exception as e:
            st.error(f"Error procesando 'CFDI I': {e}")
            return None
    else:
        st.error("❌ El archivo crudo no tiene la hoja 'CFDI I'.")
        return None

    return datos


def conciliar_ventas_vs_cfdi(datos):
    """
    Módulo I00: Lógica de conciliación.
    Toma los DataFrames ya limpios y separados (Ventas, PUE, PPD) y los cruza.
    """
    df_ventas = datos['VENTAS']
    df_pue = datos['CFDI_I_PUE']
    df_ppd = datos['CFDI_I_PPD']

    # Columnas clave en Ventas
    col_uuid_ventas = 'uuid' if 'uuid' in df_ventas.columns else None
    posibles_nombres_monto = ['precio_real', 'total', 'importe', 'monto']
    col_monto_ventas = next((col for col in posibles_nombres_monto if col in df_ventas.columns), None)

    if not col_uuid_ventas or not col_monto_ventas:
        st.error(f"No se encontraron columnas clave (UUID o Monto/Precio Real) en Ventas. Columnas: {df_ventas.columns.tolist()}")
        return None

    df_ventas['estado_conciliacion'] = 'PENDIENTE'
    df_ventas['origen_conciliacion'] = ''

    resumen = {"PUE (UUID)": 0, "PPD (UUID)": 0, "PUE (Monto)": 0}

    # PASO 1: CONCILIAR POR UUID (PUE)
    if 'uuid' in df_pue.columns:
        uuids_pue = df_pue['uuid'].dropna().unique()
        mask_pue = df_ventas[col_uuid_ventas].isin(uuids_pue) & (df_ventas['estado_conciliacion'] == 'PENDIENTE')
        df_ventas.loc[mask_pue, 'estado_conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_pue, 'origen_conciliacion'] = 'CFDI PUE (UUID)'
        resumen["PUE (UUID)"] = int(mask_pue.sum())

    # PASO 2: CONCILIAR POR UUID (PPD)
    if 'uuid' in df_ppd.columns:
        uuids_ppd = df_ppd['uuid'].dropna().unique()
        mask_ppd = df_ventas[col_uuid_ventas].isin(uuids_ppd) & (df_ventas['estado_conciliacion'] == 'PENDIENTE')
        df_ventas.loc[mask_ppd, 'estado_conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_ppd, 'origen_conciliacion'] = 'CFDI PPD (UUID)'
        resumen["PPD (UUID)"] = int(mask_ppd.sum())

    # PASO 3: CONCILIAR POR MONTO (PUE)
    col_monto_pue = next((col for col in ['total', 'importe'] if col in df_pue.columns), None)
    if col_monto_pue:
        montos_pue = df_pue[col_monto_pue].dropna().unique()
        mask_monto = df_ventas[col_monto_ventas].isin(montos_pue) & (df_ventas['estado_conciliacion'] == 'PENDIENTE')
        df_ventas.loc[mask_monto, 'estado_conciliacion'] = 'REVISIÓN MONTO'
        df_ventas.loc[mask_monto, 'origen_conciliacion'] = 'CFDI PUE (Monto)'
        resumen["PUE (Monto)"] = int(mask_monto.sum())

    # Crear Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_ventas.to_excel(writer, sheet_name='VENTAS_PROCESADAS', index=False)
        df_pue.to_excel(writer, sheet_name='CFDI_I_PUE', index=False)
        df_ppd.to_excel(writer, sheet_name='CFDI_I_PPD', index=False)
        pd.DataFrame(list(resumen.items()), columns=['Criterio', 'Cantidad Conciliada']).to_excel(writer, sheet_name='RESUMEN', index=False)

    return output.getvalue(), resumen

# ==========================================================
# INTERFAZ GRÁFICA (FRONTEND) CON STREAMLIT
# ==========================================================
st.set_page_config(page_title="App de Conciliación Completa", page_icon="💰", layout="wide")

st.title("💰 Sistema de Conciliación: Extracción y Limpieza (P00) + Conciliación (I00)")
st.markdown("""
Sube tu archivo de Excel **crudo** (con las hojas **NOTA DE VENTA** y **CFDI I**).
La aplicación se encargará de separar automáticamente los CFDI en PUE y PPD, limpiar los datos y hacer el cruce.
""")

uploaded_file = st.file_uploader("Sube tu archivo crudo de Excel (.xlsx o .xlsm)", type=["xlsx", "xlsm"])

if uploaded_file is not None:
    st.info("Archivo cargado. Haz clic en ejecutar.")

    if st.button("🚀 Extraer, Limpiar y Conciliar", type="primary"):
        with st.spinner("1. Extrayendo y limpiando (Módulo P00)..."):
            datos_limpios = preparar_datos_crudos(uploaded_file)

        if datos_limpios is not None:
            with st.spinner("2. Cruzando información (Módulo I00)..."):
                resultado = conciliar_ventas_vs_cfdi(datos_limpios)

            if resultado is not None:
                excel_bytes, resumen = resultado
                st.success("¡Conciliación completada con éxito!")

                st.subheader("📊 Resumen del Cruce (Ventas vs CFDI)")
                col1, col2, col3 = st.columns(3)
                col1.metric("Conciliados UUID (PUE)", resumen["PUE (UUID)"])
                col2.metric("Conciliados UUID (PPD)", resumen["PPD (UUID)"])
                col3.metric("Revisión Monto (PUE)", resumen["PUE (Monto)"])

                st.markdown("---")
                st.markdown("### Descarga tu archivo procesado:")
                st.download_button(
                    label="📥 Descargar Excel Listo",
                    data=excel_bytes,
                    file_name="CONCILIACION_COMPLETA_RESULTADO.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
