import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Global summary table formatting
old_resumen_global = """                cc_resumen_global = {
                    "Total Abonos": st.column_config.NumberColumn("Total Abonos", format="$%.2f"),
                    "Total Cargos": st.column_config.NumberColumn("Total Cargos", format="$%.2f"),
                    "Último Saldo": st.column_config.NumberColumn("Último Saldo", format="$%.2f")
                }
                st.dataframe(df_resumen, use_container_width=True, hide_index=True, column_config=cc_resumen_global)"""

new_resumen_global = """                cc_resumen_global = {
                    "Total Abonos": st.column_config.NumberColumn("Total Abonos"),
                    "Total Cargos": st.column_config.NumberColumn("Total Cargos"),
                    "Último Saldo": st.column_config.NumberColumn("Último Saldo")
                }

                # Format to strings with commas and dollar signs using Pandas Styler
                st.dataframe(df_resumen.style.format({
                    "Total Abonos": "${:,.2f}",
                    "Total Cargos": "${:,.2f}",
                    "Último Saldo": "${:,.2f}"
                }, na_rep=""), use_container_width=True, hide_index=True, column_config=cc_resumen_global)"""

if old_resumen_global in content:
    content = content.replace(old_resumen_global, new_resumen_global)
    print("Fixed global summary table formatting")

# 2. Detail bank tables
old_bancos_table = """                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'ABONO'), subset=['ABONO'] if 'ABONO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'Valor del cargo'), subset=['Valor del cargo'] if 'Valor del cargo' in cols_to_style else [])
                                           .format(na_rep=""),
                             use_container_width=True, hide_index=True, column_config=cc_format)"""

new_bancos_table = """                # Create format dict for money columns
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        format_dict[c] = "${:,.2f}"

                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'ABONO'), subset=['ABONO'] if 'ABONO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'Valor del cargo'), subset=['Valor del cargo'] if 'Valor del cargo' in cols_to_style else [])
                                           .format(format_dict, na_rep=""),
                             use_container_width=True, hide_index=True, column_config=cc_format)"""

if old_bancos_table in content:
    content = content.replace(old_bancos_table, new_bancos_table)
    print("Fixed bank detail table formatting")

# 3. Ventas resumen table
old_ventas_resumen_table = """                    # Column Config
                    cols_dinero_formateadas = ['Total (antes descuento)', 'Efectivo', 'Tarjeta Crédito', 'Transferencia', 'Total Real']
                    cc_resumen = {}
                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            cc_resumen[col] = st.column_config.NumberColumn(col, format="$%.2f")

                    st.divider()"""

new_ventas_resumen_table = """                    # Column Config
                    cols_dinero_formateadas = ['Total (antes descuento)', 'Efectivo', 'Tarjeta Crédito', 'Transferencia', 'Total Real']
                    cc_resumen = {}
                    format_dict_resumen = {}
                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            cc_resumen[col] = st.column_config.NumberColumn(col)
                            format_dict_resumen[col] = "${:,.2f}"

                    st.divider()"""

if old_ventas_resumen_table in content:
    content = content.replace(old_ventas_resumen_table, new_ventas_resumen_table)
    print("Fixed ventas resumen table formatting logic")

old_ventas_resumen_render = """                    st.dataframe(df_vista_final_resumen, use_container_width=True, hide_index=True, column_config=cc_resumen)"""

new_ventas_resumen_render = """                    st.dataframe(df_vista_final_resumen.style.format(format_dict_resumen, na_rep=""), use_container_width=True, hide_index=True, column_config=cc_resumen)"""

if old_ventas_resumen_render in content:
    content = content.replace(old_ventas_resumen_render, new_ventas_resumen_render)
    print("Fixed ventas resumen render")


# 4. Ventas notas table
old_ventas_notas_table = """                    cc_v = {}
                    if 'PRECIO UNITARIO' in df_v_vista.columns:
                        cc_v['PRECIO UNITARIO'] = st.column_config.NumberColumn('PRECIO UNITARIO', format="$%.2f")

                    # Export & Delete UI para Ventas"""

new_ventas_notas_table = """                    cc_v = {}
                    format_dict_v = {}
                    if 'PRECIO UNITARIO' in df_v_vista.columns:
                        cc_v['PRECIO UNITARIO'] = st.column_config.NumberColumn('PRECIO UNITARIO')
                        format_dict_v['PRECIO UNITARIO'] = "${:,.2f}"

                    # Export & Delete UI para Ventas"""

if old_ventas_notas_table in content:
    content = content.replace(old_ventas_notas_table, new_ventas_notas_table)
    print("Fixed ventas notas table formatting logic")

old_ventas_notas_render = """                    # Mostrar tabla
                    st.dataframe(df_v_vista, use_container_width=True, hide_index=True, column_config=cc_v)"""

new_ventas_notas_render = """                    # Mostrar tabla
                    st.dataframe(df_v_vista.style.format(format_dict_v, na_rep=""), use_container_width=True, hide_index=True, column_config=cc_v)"""

if old_ventas_notas_render in content:
    content = content.replace(old_ventas_notas_render, new_ventas_notas_render)
    print("Fixed ventas notas render")


# Also replace format="$%.2f" with format=None for cc_format in bancos
old_cc_format = """                        cc_format[col_moneda] = st.column_config.NumberColumn(col_moneda, format="$%.2f")"""
new_cc_format = """                        cc_format[col_moneda] = st.column_config.NumberColumn(col_moneda)"""
if old_cc_format in content:
    content = content.replace(old_cc_format, new_cc_format)
    print("Fixed cc_format")


with open("app.py", "w") as f:
    f.write(content)
