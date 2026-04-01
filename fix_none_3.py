import re

with open("app.py", "r") as f:
    content = f.read()

# Fix Ventas Resumen
old_vr = """                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            cc_resumen[col] = st.column_config.NumberColumn(col)
                            format_dict_resumen[col] = "${:,.2f}" """

new_vr = """                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            # Convertir strings "None" o NaNs y asegurar formato numérico real
                            df_vista_final_resumen[col] = pd.to_numeric(df_vista_final_resumen[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
                            cc_resumen[col] = st.column_config.NumberColumn(col)
                            format_dict_resumen[col] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""

                    df_vista_final_resumen = df_vista_final_resumen.replace("None", "").fillna("")
"""

if old_vr in content:
    content = content.replace(old_vr, new_vr)
    print("Fixed ventas resumen")

# Fix Ventas Notas
old_vn = """                    cc_v = {}
                    format_dict_v = {}
                    if 'PRECIO UNITARIO' in df_v_vista.columns:
                        cc_v['PRECIO UNITARIO'] = st.column_config.NumberColumn('PRECIO UNITARIO')
                        format_dict_v['PRECIO UNITARIO'] = "${:,.2f}"

                    # Export & Delete UI para Ventas"""

new_vn = """                    cc_v = {}
                    format_dict_v = {}
                    if 'PRECIO UNITARIO' in df_v_vista.columns:
                        df_v_vista['PRECIO UNITARIO'] = pd.to_numeric(df_v_vista['PRECIO UNITARIO'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
                        cc_v['PRECIO UNITARIO'] = st.column_config.NumberColumn('PRECIO UNITARIO')
                        format_dict_v['PRECIO UNITARIO'] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""

                    df_v_vista = df_v_vista.replace("None", "").fillna("")

                    # Export & Delete UI para Ventas"""

if old_vn in content:
    content = content.replace(old_vn, new_vn)
    print("Fixed ventas notas")

with open("app.py", "w") as f:
    f.write(content)
