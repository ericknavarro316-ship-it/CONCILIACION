import re

with open('app.py', 'r') as f:
    content = f.read()

search = """                        for tb in tablas_egresos:
                            df_tb = get_df_from_sql(tb)
                            if 'UUID' in df_tb.columns and not df_tb.empty:
                                fila_match = df_tb[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str]"""

replace = """                        for tb in tablas_egresos:
                            df_tb = get_df_from_sql(tb)

                            # Normalizar la busqueda de la columna UUID en caso de que venga con espacios o diferentes casings
                            col_uuid = next((c for c in df_tb.columns if c.strip().upper() == 'UUID'), None)

                            if col_uuid and not df_tb.empty:
                                fila_match = df_tb[df_tb[col_uuid].astype(str).str.strip().str.upper() == uuid_str]"""

content = content.replace(search, replace)

search_update = """                                    # Si es el XML no reemplazamos el PDF si ya existe, a menos que queramos guardar ambos,
                                    # pero si es PDF damos prioridad
                                    current_pdf = df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'].values[0]
                                    if pd.isna(current_pdf) or current_pdf == "" or safe_name_tmp.lower().endswith('.pdf'):
                                        df_tb.loc[df_tb['UUID'].astype(str).str.strip().str.upper() == uuid_str, 'PDF'] = safe_name_tmp
                                        update_table_from_df(df_tb, tb)"""

replace_update = """                                    # Si es el XML no reemplazamos el PDF si ya existe, a menos que queramos guardar ambos,
                                    # pero si es PDF damos prioridad
                                    current_pdf = df_tb.loc[df_tb[col_uuid].astype(str).str.strip().str.upper() == uuid_str, 'PDF'].values[0]
                                    if pd.isna(current_pdf) or current_pdf == "" or safe_name_tmp.lower().endswith('.pdf'):
                                        df_tb.loc[df_tb[col_uuid].astype(str).str.strip().str.upper() == uuid_str, 'PDF'] = safe_name_tmp
                                        update_table_from_df(df_tb, tb)"""
content = content.replace(search_update, replace_update)

with open('app.py', 'w') as f:
    f.write(content)
