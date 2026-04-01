import re

with open("app.py", "r") as f:
    content = f.read()

# Fix the st.columns logic that I removed manually

old_export_delete_code = """
            col_btn1, col_btn2 = st.columns([8, 2])
            with col_btn1:
                from io import BytesIO

                # Función para generar excel de descarga
                def to_excel(df_to_export):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_to_export.to_excel(writer, index=False, sheet_name='Export')
                    return output.getvalue()

                st.download_button(
                    label="📥 Exportar a Excel",
                    data=to_excel(df_filtrado),
                    file_name=f"{cuenta_sel}_Exportado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"export_{key_prefix}"
                )

            with col_btn2:
                if st.button("🗑️ Eliminar Tabla", key=f"del_{key_prefix}", type="secondary", help="Borra definitivamente esta cuenta/tabla de la base de datos."):
                    st.session_state[f"confirm_del_{key_prefix}"] = True

                if st.session_state.get(f"confirm_del_{key_prefix}", False):
                    st.warning("¿Estás seguro?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("✅ Sí, borrar", key=f"yes_{key_prefix}", type="primary"):
                        if drop_table_from_sql(cuenta_sel):
                            st.success(f"Tabla {cuenta_sel} eliminada.")
                            st.session_state[f"confirm_del_{key_prefix}"] = False
                            import time
                            time.sleep(1.5)
                            st.rerun()
                    if c_no.button("❌ No", key=f"no_{key_prefix}"):
                        st.session_state[f"confirm_del_{key_prefix}"] = False
                        st.rerun()
"""

old_edit_btn_code = """
            # Botón para activar/desactivar modo edición
            col_edit1, col_edit2 = st.columns([8, 2])
            with col_edit2:
                if st.button("✏️ Editar Manualmente", key=f"btn_edit_{key_prefix}", help="Activa el modo de edición de celdas."):
                    st.session_state[f"edit_{key_prefix}"] = not st.session_state[f"edit_{key_prefix}"]
"""

# Those have been removed already, let's verify if there are any remaining `st.columns([8, 2])`
if "st.columns([8, 2])" in content:
    print("Found more st.columns([8, 2])!")
else:
    print("None found!")
