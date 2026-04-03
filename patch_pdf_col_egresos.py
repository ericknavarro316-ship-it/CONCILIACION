import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update process_egreso_file (bulk upload logic)
search_process = """                                    ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", mes_folder, tipo_comprobante, uuid_str)
                                    break

                        os.makedirs(ruta_base, exist_ok=True)
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)"""

replace_process = """                                    ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", mes_folder, tipo_comprobante, uuid_str)

                                    # Actualizar columna PDF en la tabla correspondiente
                                    safe_name_tmp = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    if 'PDF' not in df_tb.columns:
                                        df_tb['PDF'] = ""
                                    # Si es el XML no reemplazamos el PDF si ya existe, a menos que queramos guardar ambos,
                                    # pero si es PDF damos prioridad
                                    current_pdf = df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'].values[0]
                                    if pd.isna(current_pdf) or current_pdf == "" or safe_name_tmp.lower().endswith('.pdf'):
                                        df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'] = safe_name_tmp
                                        update_table_from_df(df_tb, tb)

                                    break

                        os.makedirs(ruta_base, exist_ok=True)
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)"""

content = content.replace(search_process, replace_process)

# 2. Update abrir_expediente_egresos (manual upload logic)
search_modal = """        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)"""

replace_modal = """        if nuevos_registros:
            # Actualizar la columna PDF en la tabla correspondiente si suben un PDF
            for tb in tablas_egresos:
                df_tb = get_df_from_sql(tb)
                if 'UUID' in df_tb.columns and not df_tb.empty:
                    mask = df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str
                    if mask.any():
                        # Buscar si se subió algún PDF para asignarlo al campo
                        pdf_name = next((r["NOMBRE_ARCHIVO"] for r in nuevos_registros if r["TIPO_DOCUMENTO"] == "PDF"), None)
                        if not pdf_name:
                            # Si no hay PDF, tomamos el primer archivo como referencia (ej XML)
                            pdf_name = nuevos_registros[0]["NOMBRE_ARCHIVO"]

                        if 'PDF' not in df_tb.columns:
                            df_tb['PDF'] = ""

                        df_tb.loc[mask, 'PDF'] = pdf_name
                        update_table_from_df(df_tb, tb)
                        break

            df_nuevos = pd.DataFrame(nuevos_registros)"""

content = content.replace(search_modal, replace_modal)

with open('app.py', 'w') as f:
    f.write(content)
