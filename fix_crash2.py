import re

with open("app.py", "r") as f:
    content = f.read()

# Wait, let's verify if there are any other fillna("") for these dataframes.
# At lines 614:
# df_mostrar = df_mostrar.fillna("")
# df_mostrar = df_mostrar.replace("None", "")

old_initial_fillna = """            # Reemplazar explícitamente "None" y nulls con cadena vacía para limpiar la UI
            df_mostrar = df_mostrar.fillna("")
            df_mostrar = df_mostrar.replace("None", "")"""

new_initial_fillna = """            # Reemplazar explícitamente "None" para limpiar la UI. NO usar fillna("") en numéricos
            df_mostrar = df_mostrar.replace("None", "")"""

if old_initial_fillna in content:
    content = content.replace(old_initial_fillna, new_initial_fillna)
    print("Fixed initial fillna")


old_initial_vr = """                    # Limpieza visual
                    df_resumen = df_resumen.fillna("")
                    df_resumen = df_resumen.replace("None", "").replace("NaT", "")"""

new_initial_vr = """                    # Limpieza visual
                    df_resumen = df_resumen.replace("None", "").replace("NaT", "")"""

if old_initial_vr in content:
    content = content.replace(old_initial_vr, new_initial_vr)
    print("Fixed initial vr")


old_initial_vn = """                    df_v_vista = df_v_vista.fillna("")
                    df_v_vista = df_v_vista.replace("None", "").replace("NaT", "")"""

new_initial_vn = """                    df_v_vista = df_v_vista.replace("None", "").replace("NaT", "")"""

if old_initial_vn in content:
    content = content.replace(old_initial_vn, new_initial_vn)
    print("Fixed initial vn")

with open("app.py", "w") as f:
    f.write(content)
