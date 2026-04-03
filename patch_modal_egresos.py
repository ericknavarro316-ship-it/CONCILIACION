import re

with open('app.py', 'r') as f:
    content = f.read()

search = """# Interceptar query params para abrir modal
if "expediente" in st.query_params:
    id_venta_target = st.query_params["expediente"]
    # Limpiar el query param para que al cerrar el modal no se vuelva a abrir al refrescar
    st.query_params.clear()
    abrir_expediente(id_venta_target)"""

replace = """@st.dialog("📁 Expediente de Egreso", width="large")
def abrir_expediente_egresos(uuid_raw):
    import os
    import subprocess
    import platform
    import pandas as pd
    import re

    # Sanitizar UUID para evitar Path Traversal vulnerabilities
    uuid_str = str(uuid_raw).strip().upper()
    if not uuid_str:
        st.error("UUID inválido.")
        return

    def open_local_path(path):
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            st.error(f"No se pudo abrir: {e}")

    # Determinar la ruta base de la carpeta
    ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str) # Fallback
    tablas_todas = get_all_tables()
    tablas_egresos = [t for t in tablas_todas if t.startswith("CFDI_E_") or t == "PAGOS_E"]

    for tb in tablas_egresos:
        df_tb = get_df_from_sql(tb)
        if 'UUID' in df_tb.columns and not df_tb.empty:
            fila_match = df_tb[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str]
            if not fila_match.empty:
                # Determinar TIPO_COMPROBANTE
                tipo_comprobante = "OTROS"
                if "PUE" in tb.upper(): tipo_comprobante = "PUE"
                elif "PPD" in tb.upper(): tipo_comprobante = "PPD"
                elif "PAGOS" in tb.upper(): tipo_comprobante = "PAGOS"

                # Determinar MES
                col_fecha = 'Fecha Pago' if 'PAGOS' in tb.upper() else 'Fecha Emisión'
                mes_folder = "GENERAL"
                if col_fecha in fila_match.columns:
                    fecha_val = fila_match.iloc[0][col_fecha]
                    try:
                        dt_fecha = pd.to_datetime(fecha_val, errors='coerce')
                        if pd.notna(dt_fecha):
                            mes_folder = dt_fecha.strftime("%Y_%m")
                    except: pass

                ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", mes_folder, tipo_comprobante, uuid_str)
                break

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.write(f"Gestionando documentos para Factura/Egreso: **{uuid_str}**")
    with col_h2:
        if os.path.exists(ruta_base):
            if st.button("📂 Abrir Carpeta", help="Abre la carpeta física en Windows/Mac."):
                open_local_path(ruta_base)

    # Buscar si existe en la base de datos de expedientes (Usamos UUID en la columna ID_VENTA temporalmente/genéricamente)
    df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
    if df_exp.empty:
        df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

    archivos_egreso = df_exp[df_exp['ID_VENTA'].astype(str).str.upper() == uuid_str] if not df_exp.empty else pd.DataFrame()

    # Mostrar archivos existentes
    if not archivos_egreso.empty:
        st.subheader("Documentos Guardados")
        for idx, row in archivos_egreso.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                if st.button("Abrir", key=f"abrir_e_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")
    else:
        st.info("Aún no hay documentos para este Egreso. Sube los archivos arrastrándolos aquí abajo.")

    st.divider()
    st.subheader("Subir Nuevos Archivos")
    uploaded_files = st.file_uploader("Arrastra aquí PDF, XML, PNG, JPG...", accept_multiple_files=True, key=f"uploader_e_{uuid_str}")

    if uploaded_files and st.button("💾 Guardar Archivos"):
        from database_sqlite import update_table_from_df
        os.makedirs(ruta_base, exist_ok=True)
        nuevos_registros = []
        for uf in uploaded_files:
            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', uf.name)
            ruta_destino = os.path.join(ruta_base, safe_name)
            with open(ruta_destino, "wb") as f:
                f.write(uf.getbuffer())
            nuevos_registros.append({
                "ID_VENTA": uuid_str,  # Reusamos columna para guardar el UUID
                "NOMBRE_ARCHIVO": safe_name,
                "TIPO_DOCUMENTO": safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO',
                "RUTA_LOCAL": ruta_destino
            })
        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)
            if df_exp.empty: df_exp = df_nuevos
            else: df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)
            save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
            st.success("Archivos guardados correctamente.")
            import time
            time.sleep(1)
            st.rerun()

# Interceptar query params para abrir modal
if "expediente" in st.query_params:
    id_venta_target = st.query_params["expediente"]
    st.query_params.clear()
    abrir_expediente(id_venta_target)
elif "expediente_egreso" in st.query_params:
    uuid_target = st.query_params["expediente_egreso"]
    st.query_params.clear()
    abrir_expediente_egresos(uuid_target)"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
