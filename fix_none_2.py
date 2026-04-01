import re

with open("app.py", "r") as f:
    content = f.read()

old_format_dict = """                # Create format dict for money columns
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        format_dict[c] = "${:,.2f}"

                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'ABONO'), subset=['ABONO'] if 'ABONO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'Valor del cargo'), subset=['Valor del cargo'] if 'Valor del cargo' in cols_to_style else [])
                                           .format(format_dict, na_rep=""),
                             use_container_width=True, hide_index=True, column_config=cc_format)"""

new_format_dict = """                # Create format dict for money columns using a lambda for safer formatting and coercion to numeric
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        # Ensure string representations of empty are actual nans
                        df_mostrar[c] = pd.to_numeric(df_mostrar[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
                        format_dict[c] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""

                # Reemplazar explicitly in the dataframe just in case
                df_mostrar = df_mostrar.replace("None", "").fillna("")

                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'ABONO'), subset=['ABONO'] if 'ABONO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'Valor del cargo'), subset=['Valor del cargo'] if 'Valor del cargo' in cols_to_style else [])
                                           .format(format_dict, na_rep=""),
                             use_container_width=True, hide_index=True, column_config=cc_format)"""

if old_format_dict in content:
    content = content.replace(old_format_dict, new_format_dict)
    print("Fixed format dict logic")

with open("app.py", "w") as f:
    f.write(content)
