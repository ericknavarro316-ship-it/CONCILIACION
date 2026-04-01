import re

with open("app.py", "r") as f:
    content = f.read()

# Remove the fillna("") that is causing pd.notnull("") to return True and crashing the lambda.

old_banco = """                # Reemplazar explicitly in the dataframe just in case
                df_mostrar = df_mostrar.replace("None", "").fillna("")

                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])"""

new_banco = """                # Reemplazar explicitly in the dataframe just in case
                # We do NOT fillna("") here because the formatting lambda needs pd.notnull(x) to correctly identify NaNs.
                df_mostrar = df_mostrar.replace("None", "")

                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])"""

if old_banco in content:
    content = content.replace(old_banco, new_banco)
    print("Fixed banco")

old_ventas_resumen = """                    df_vista_final_resumen = df_vista_final_resumen.replace("None", "").fillna("")"""
new_ventas_resumen = """                    df_vista_final_resumen = df_vista_final_resumen.replace("None", "")"""

if old_ventas_resumen in content:
    content = content.replace(old_ventas_resumen, new_ventas_resumen)
    print("Fixed ventas resumen")

old_ventas_notas = """                    df_v_vista = df_v_vista.replace("None", "").fillna("")

                    # Export & Delete UI para Ventas"""

new_ventas_notas = """                    df_v_vista = df_v_vista.replace("None", "")

                    # Export & Delete UI para Ventas"""

if old_ventas_notas in content:
    content = content.replace(old_ventas_notas, new_ventas_notas)
    print("Fixed ventas notas")

with open("app.py", "w") as f:
    f.write(content)
