import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Remove col_btn1, col_btn2 and their contents (Export and Delete buttons).
btn_block_start = """            col_btn1, col_btn2 = st.columns([8, 2])
            with col_btn1:"""

btn_block_end = """                        st.session_state[f"confirm_del_{key_prefix}"] = False
                        st.rerun()"""

start_idx = content.find(btn_block_start)
end_idx = content.find(btn_block_end, start_idx) + len(btn_block_end)

if start_idx != -1 and end_idx != -1:
    btn_block = content[start_idx:end_idx]
    content = content.replace(btn_block, "")
    print("Removed btn_block")

# 2. Remove col_edit1, col_edit2 and their contents
edit_block_start = """            col_edit1, col_edit2 = st.columns([8, 2])
            with col_edit2:"""

edit_block_end = """                if st.button("✏️ Editar Manualmente", key=f"btn_edit_{key_prefix}", help="Activa el modo de edición de celdas."):
                    st.session_state[f"edit_{key_prefix}"] = not st.session_state[f"edit_{key_prefix}"]"""

start_idx2 = content.find(edit_block_start)
end_idx2 = content.find(edit_block_end, start_idx2) + len(edit_block_end)

if start_idx2 != -1 and end_idx2 != -1:
    edit_block = content[start_idx2:end_idx2]
    content = content.replace(edit_block, "")
    print("Removed edit_block")

# 3. Insert the new buttons BELOW the table render logic
# Table render logic ends around:
table_render_end = """                st.dataframe(df_mostrar.style.map(lambda v: style_bancos(v, 'CARGO'), subset=['CARGO'] if 'CARGO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'ABONO'), subset=['ABONO'] if 'ABONO' in cols_to_style else [])
                                           .map(lambda v: style_bancos(v, 'Valor del cargo'), subset=['Valor del cargo'] if 'Valor del cargo' in cols_to_style else [])
                                           .format(na_rep=""),
                             use_container_width=True, hide_index=True, column_config=cc_format)"""

new_buttons_block = """

            st.divider()
            # Botones de Acción Múltiple
            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                from io import BytesIO
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
                    key=f"export_{key_prefix}",
                    use_container_width=True
                )

            with col_act2:
                btn_text = "❌ Cancelar Edición" if st.session_state.get(f"edit_{key_prefix}") else "✏️ Editar Manualmente"
                if st.button(btn_text, key=f"btn_edit_{key_prefix}", help="Activa el modo de edición de celdas.", use_container_width=True):
                    st.session_state[f"edit_{key_prefix}"] = not st.session_state.get(f"edit_{key_prefix}", False)
                    st.rerun()

            with col_act3:
                if st.button("🗑️ Eliminar Tabla", key=f"del_{key_prefix}", type="secondary", help="Borra definitivamente esta cuenta/tabla de la base de datos.", use_container_width=True):
                    st.session_state[f"confirm_del_{key_prefix}"] = True

                if st.session_state.get(f"confirm_del_{key_prefix}", False):
                    st.warning("¿Estás seguro?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("✅ Sí", key=f"yes_{key_prefix}", type="primary"):
                        if drop_table_from_sql(cuenta_sel):
                            st.success(f"Tabla {cuenta_sel} eliminada.")
                            st.session_state[f"confirm_del_{key_prefix}"] = False
                            import time
                            time.sleep(1.5)
                            st.rerun()
                    if c_no.button("❌ No", key=f"no_{key_prefix}"):
                        st.session_state[f"confirm_del_{key_prefix}"] = False
                        st.rerun()"""

if table_render_end in content:
    content = content.replace(table_render_end, table_render_end + new_buttons_block)
    print("Inserted new buttons block")

with open("app.py", "w") as f:
    f.write(content)
