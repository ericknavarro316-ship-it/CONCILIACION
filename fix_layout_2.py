import re

with open("app.py", "r") as f:
    content = f.read()

# Fix the st.columns([8, 2]) in Ventas and Ventas Resumen as well

old_btn_resumen = """                    col_vbtn1, col_vbtn2 = st.columns([8, 2])
                    with col_vbtn1:"""

new_btn_resumen = """                    col_vbtn1, col_vbtn2 = st.columns(2)
                    with col_vbtn1:"""

if old_btn_resumen in content:
    content = content.replace(old_btn_resumen, new_btn_resumen)
    print("Fixed btn_resumen")

old_btn_ventas = """                    col_vbtn3, col_vbtn4 = st.columns([8, 2])
                    with col_vbtn3:"""

new_btn_ventas = """                    col_vbtn3, col_vbtn4 = st.columns(2)
                    with col_vbtn3:"""

if old_btn_ventas in content:
    content = content.replace(old_btn_ventas, new_btn_ventas)
    print("Fixed btn_ventas")

with open("app.py", "w") as f:
    f.write(content)
