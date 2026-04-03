import re

with open('app.py', 'r') as f:
    content = f.read()

search = """        # Top-level filter for INGRESOS vs EGRESOS
        tipo_cfdi = st.radio("Selecciona Categoría:", ["INGRESOS", "EGRESOS"], horizontal=True)
        st.divider()"""

replace = """        # Top-level filter for INGRESOS vs EGRESOS
        tipo_cfdi = st.radio("Selecciona Categoría:", ["INGRESOS", "EGRESOS"], horizontal=True)
        st.divider()

        # Upload files into Expedientes for EGRESOS
        if tipo_cfdi == "EGRESOS":
            with st.expander("📥 Cargar Expedientes de Egresos (PDF / ZIP)", expanded=False):
                st.markdown("Sube múltiples PDFs o un archivo ZIP. El sistema extraerá el UUID del PDF o del nombre de la carpeta en el ZIP para vincularlo a su respectiva factura.")

                archivo_egresos_pdf = st.file_uploader("📂 Cargar Facturas (PDF)", type=['pdf'], accept_multiple_files=True, key="egresos_pdf")
                archivo_egresos_zip = st.file_uploader("📂 Cargar Expedientes Completos (ZIP)", type=['zip'], accept_multiple_files=True, key="egresos_zip")

                if st.button("Procesar Archivos de Egresos", type="primary"):
                    import os
                    import zipfile
                    import shutil

                    df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                    if df_exp.empty:
                        df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

                    tablas_egresos = [t for t in tablas_todas if t.startswith("CFDI_E_") or t == "PAGOS_E"]
                    nuevos_registros_expediente = []

                    def process_egreso_file(file_name, file_buffer, is_zip_content=False, file_path_in_zip=""):
                        uuid_str = None

                        # Si viene de ZIP, intentar extraer UUID del folder padre primero
                        if is_zip_content and '/' in file_path_in_zip:
                            parts = file_path_in_zip.split('/')
                            # Asumimos que el penultimo puede ser el UUID
                            potential_uuid = parts[-2]
                            if re.match(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$', potential_uuid):
                                uuid_str = potential_uuid.upper()

                        # Si no hay UUID aún y es PDF, escanear el PDF
                        if not uuid_str and file_name.lower().endswith('.pdf'):
                            import pdfplumber
                            try:
                                with pdfplumber.open(file_buffer) as pdf:
                                    for page in pdf.pages[:2]:
                                        text = page.extract_text()
                                        if text:
                                            match = re.search(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}', text)
                                            if match:
                                                uuid_str = match.group(0).upper()
                                                break
                            except Exception as e:
                                pass

                        if not uuid_str:
                            return None

                        # Determinar ruta destino
                        ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str)
                        for tb in tablas_egresos:
                            df_tb = get_df_from_sql(tb)
                            if 'UUID' in df_tb.columns and not df_tb.empty:
                                fila_match = df_tb[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str]
                                if not fila_match.empty:
                                    tipo_comprobante = "OTROS"
                                    if "PUE" in tb.upper(): tipo_comprobante = "PUE"
                                    elif "PPD" in tb.upper(): tipo_comprobante = "PPD"
                                    elif "PAGOS" in tb.upper(): tipo_comprobante = "PAGOS"

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

                        os.makedirs(ruta_base, exist_ok=True)
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                        ruta_destino = os.path.join(ruta_base, safe_name)

                        file_buffer.seek(0)
                        with open(ruta_destino, "wb") as f:
                            f.write(file_buffer.read())

                        tipo_doc = safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO'

                        return {
                            "ID_VENTA": uuid_str,
                            "NOMBRE_ARCHIVO": safe_name,
                            "TIPO_DOCUMENTO": tipo_doc,
                            "RUTA_LOCAL": ruta_destino
                        }

                    # Procesar PDFs
                    if archivo_egresos_pdf:
                        for pdf_file in archivo_egresos_pdf:
                            with st.spinner(f"Procesando {pdf_file.name}..."):
                                rec = process_egreso_file(pdf_file.name, pdf_file)
                                if rec:
                                    nuevos_registros_expediente.append(rec)

                    # Procesar ZIPs
                    if archivo_egresos_zip:
                        from io import BytesIO
                        for zip_file in archivo_egresos_zip:
                            with st.spinner(f"Extrayendo ZIP {zip_file.name}..."):
                                try:
                                    with zipfile.ZipFile(zip_file) as z:
                                        for file_info in z.infolist():
                                            if file_info.is_dir(): continue
                                            with z.open(file_info) as f:
                                                file_buffer = BytesIO(f.read())
                                                file_name = file_info.filename.split('/')[-1]
                                                rec = process_egreso_file(file_name, file_buffer, is_zip_content=True, file_path_in_zip=file_info.filename)
                                                if rec:
                                                    nuevos_registros_expediente.append(rec)
                                except Exception as e:
                                    st.error(f"Error procesando ZIP: {e}")

                    if nuevos_registros_expediente:
                        df_nuevos = pd.DataFrame(nuevos_registros_expediente)
                        if df_exp.empty: df_exp = df_nuevos
                        else: df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)
                        save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
                        st.success(f"✅ Se guardaron {len(nuevos_registros_expediente)} archivos en Expedientes de Egresos.")
                        import time
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.warning("⚠️ No se identificaron archivos con UUIDs válidos o no se subió nada.")
            st.divider()"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
