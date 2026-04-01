import re

with open("app.py", "r") as f:
    content = f.read()

# Lines 885-886:
# df_mostrar = df_mostrar.fillna("")
# df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")
old_cfdi = """            df_mostrar = df_mostrar.fillna("")
            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")"""
new_cfdi = """            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")"""

if old_cfdi in content:
    content = content.replace(old_cfdi, new_cfdi)
    print("Fixed CFDI fillna")

with open("app.py", "w") as f:
    f.write(content)
