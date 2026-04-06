import re

with open('app.py', 'r') as f:
    content = f.read()

search = """                                    # Actualizar columna PDF en la tabla correspondiente
                                    safe_name_tmp = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    if 'PDF' not in df_tb.columns:
                                        df_tb['PDF'] = ""
                                    # Si es el XML no reemplazamos el PDF si ya existe, a menos que queramos guardar ambos,
                                    # pero si es PDF damos prioridad
                                    current_pdf = df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'].values[0]
                                    if pd.isna(current_pdf) or current_pdf == "" or safe_name_tmp.lower().endswith('.pdf'):
                                        df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'] = safe_name_tmp
                                        update_table_from_df(df_tb, tb)

                                    break"""

replace = """                                    # Actualizar columna PDF en la tabla correspondiente
                                    safe_name_tmp = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    if 'PDF' not in df_tb.columns:
                                        df_tb['PDF'] = ""
                                    # Si es el XML no reemplazamos el PDF si ya existe, a menos que queramos guardar ambos,
                                    # pero si es PDF damos prioridad
                                    try:
                                        current_pdf = df_tb.loc[df_tb[col_uuid].astype(str).str.strip().str.upper() == uuid_str, 'PDF'].values[0]
                                        if pd.isna(current_pdf) or current_pdf == "" or safe_name_tmp.lower().endswith('.pdf'):
                                            df_tb.loc[df_tb[col_uuid].astype(str).str.strip().str.upper() == uuid_str, 'PDF'] = safe_name_tmp
                                            update_table_from_df(df_tb, tb)
                                    except Exception as e:
                                        pass

                                    break"""
content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
