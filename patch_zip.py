import re

with open('app.py', 'r') as f:
    content = f.read()

# Update the file uploader section
search = """        archivo_ventas_csv = st.file_uploader("📂 Cargar Reporte de Series (CSV con ;)", type=['csv'], accept_multiple_files=True, key="ventas_csv", help="Archivo CSV que contiene ID Venta, Producto y Número de Serie.")
        archivo_ventas_pdf = st.file_uploader("📂 Cargar Notas de Ventas en lote (PDF)", type=['pdf'], accept_multiple_files=True, key="ventas_pdf", help="Se extraerá el Folio y se guardará en su respectivo expediente de venta automáticamente.")"""

replace = """        archivo_ventas_csv = st.file_uploader("📂 Cargar Reporte de Series (CSV con ;)", type=['csv'], accept_multiple_files=True, key="ventas_csv", help="Archivo CSV que contiene ID Venta, Producto y Número de Serie.")
        archivo_ventas_pdf = st.file_uploader("📂 Cargar Notas de Ventas en lote (PDF)", type=['pdf'], accept_multiple_files=True, key="ventas_pdf", help="Se extraerá el Folio y se guardará en su respectivo expediente de venta automáticamente.")
        archivo_ventas_zip = st.file_uploader("📂 Cargar Expedientes (ZIP)", type=['zip'], accept_multiple_files=True, key="ventas_zip", help="Sube archivos ZIP donde el nombre de la carpeta o archivo contenga el ID VENTA (ej. carpeta 28336/).")"""

content = content.replace(search, replace)

# Add ZIP processing logic
search2 = """            if archivo_ventas_pdf:"""

replace2 = """            if archivo_ventas_zip:
                import zipfile

                df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                if df_exp.empty:
                    df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

                tablas_todas = get_all_tables()
                tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]

                nuevos_registros_expediente = []

                for zip_file in archivo_ventas_zip:
                    with st.spinner(f"Procesando ZIP: {zip_file.name}..."):
                        try:
                            with zipfile.ZipFile(zip_file) as z:
                                for file_info in z.infolist():
                                    if file_info.is_dir():
                                        continue

                                    # Extraer ID Venta a partir del directorio superior, o del nombre del ZIP si esta en la raiz
                                    path_parts = file_info.filename.split('/')
                                    if len(path_parts) > 1:
                                        # Buscar la carpeta mas profunda que parezca un ID (numerica)
                                        # O simplemente tomar la carpeta contenedora directa
                                        id_venta_raw = path_parts[-2]
                                    else:
                                        id_venta_raw = zip_file.name.replace('.zip', '')

                                    # Extraer el numero de la cadena
                                    num_match = re.search(r'\d+', id_venta_raw)
                                    if num_match:
                                        id_venta = num_match.group(0)
                                    else:
                                        id_venta = id_venta_raw

                                    id_venta_saneado = re.sub(r'[^a-zA-Z0-9_\-]', '', str(id_venta))
                                    if not id_venta_saneado:
                                        continue

                                    # Buscar ruta de expediente
                                    ruta_base = os.path.join("EXPEDIENTES", "MANUAL", id_venta_saneado)
                                    for tb in tablas_ventas:
                                        df_tb = get_df_from_sql(tb)
                                        col_id = 'id_venta' if 'id_venta' in df_tb.columns else 'ID VENTA' if 'ID VENTA' in df_tb.columns else None
                                        col_fecha = 'fecha' if 'fecha' in df_tb.columns else 'FECHA' if 'FECHA' in df_tb.columns else None

                                        if col_id and col_fecha and not df_tb.empty:
                                            fila_match = df_tb[df_tb[col_id].astype(str).str.strip() == id_venta_saneado]
                                            if not fila_match.empty:
                                                banco_folder = tb.replace('VENTAS_', '')
                                                fecha_val = fila_match.iloc[0][col_fecha]
                                                mes_folder = "GENERAL"
                                                try:
                                                    dt_fecha = pd.to_datetime(fecha_val, errors='coerce')
                                                    if pd.notna(dt_fecha):
                                                        mes_folder = dt_fecha.strftime("%Y_%m")
                                                except: pass
                                                ruta_base = os.path.join("EXPEDIENTES", "VENTAS", mes_folder, banco_folder, id_venta_saneado)
                                                break

                                    # Guardar archivo
                                    os.makedirs(ruta_base, exist_ok=True)
                                    file_name = path_parts[-1]
                                    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    ruta_destino = os.path.join(ruta_base, safe_name)

                                    with open(ruta_destino, "wb") as f:
                                        f.write(z.read(file_info.filename))

                                    tipo_doc = safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO'

                                    nuevos_registros_expediente.append({
                                        "ID_VENTA": id_venta_saneado,
                                        "NOMBRE_ARCHIVO": safe_name,
                                        "TIPO_DOCUMENTO": tipo_doc,
                                        "RUTA_LOCAL": ruta_destino
                                    })

                        except Exception as e:
                            st.error(f"Error procesando ZIP {zip_file.name}: {e}")

                if nuevos_registros_expediente:
                    df_nuevos = pd.DataFrame(nuevos_registros_expediente)
                    if df_exp.empty:
                        df_exp = df_nuevos
                    else:
                        df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)

                    save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
                    procesados_ventas = True
                    st.success(f"✅ Se guardaron {len(nuevos_registros_expediente)} archivos extraídos de ZIP en sus respectivos expedientes.")

            if archivo_ventas_pdf:"""

content = content.replace(search2, replace2)

with open('app.py', 'w') as f:
    f.write(content)
