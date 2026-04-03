import re

with open('app.py', 'r') as f:
    content = f.read()

search = """            st.dataframe(df_mostrar, use_container_width=True, hide_index=True, column_config=cc_cfdi)"""

replace = """            # Agregar Link para abrir Expediente de Egreso basado en el UUID
            if tipo_cfdi == "EGRESOS" and 'UUID' in df_mostrar.columns:
                df_mostrar['LINK_EXPEDIENTE'] = df_mostrar['UUID'].apply(
                    lambda x: f"/?expediente_egreso={x}" if pd.notnull(x) and str(x).strip() != "" else None
                )
                cc_cfdi['UUID'] = st.column_config.LinkColumn(
                    "UUID (Expediente)",
                    display_text=r"/\?expediente_egreso=(.*)"
                )
                df_mostrar['UUID'] = df_mostrar['LINK_EXPEDIENTE']
                df_mostrar = df_mostrar.drop(columns=['LINK_EXPEDIENTE'])

            st.dataframe(df_mostrar, use_container_width=True, hide_index=True, column_config=cc_cfdi)"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
