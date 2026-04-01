import re

with open("app.py", "r") as f:
    content = f.read()

# Replace the formatting logic for Ventas Resumen again just in case it wasn't caught
old_vr = """                    # Column Config
                    cols_dinero_formateadas = ['Total (antes descuento)', 'Efectivo', 'Tarjeta Crédito', 'Transferencia', 'Total Real']
                    cc_resumen = {}
                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            cc_resumen[col] = st.column_config.NumberColumn(col, format="$%.2f")"""

new_vr = """                    # Column Config
                    cols_dinero_formateadas = ['Total (antes descuento)', 'Efectivo', 'Tarjeta Crédito', 'Transferencia', 'Total Real']
                    cc_resumen = {}
                    format_dict_resumen = {}
                    for col in cols_dinero_formateadas:
                        if col in df_vista_final_resumen.columns:
                            cc_resumen[col] = st.column_config.NumberColumn(col)
                            format_dict_resumen[col] = "${:,.2f}" """

if old_vr in content:
    content = content.replace(old_vr, new_vr)
    print("Fixed ventas resumen")

with open("app.py", "w") as f:
    f.write(content)
