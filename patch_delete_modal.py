import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update abrir_expediente
search_ventas = """        for idx, row in archivos_venta.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                # Botón Funcional
                if st.button("Abrir", key=f"abrir_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")"""

replace_ventas = """        for idx, row in archivos_venta.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                # Botón Funcional
                if st.button("Abrir", key=f"abrir_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")
            with col3:
                # Botón Eliminar
                if st.button("🗑️ Eliminar", key=f"del_{idx}", help="Elimina el archivo físicamente y del registro."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        try:
                            os.remove(row['RUTA_LOCAL'])
                        except Exception as e:
                            st.error(f"Error borrando archivo: {e}")
                    # Eliminar de la base de datos
                    df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                    if not df_exp.empty:
                        # Filtrar usando el índice original o ruta local para ser precisos
                        df_exp = df_exp[df_exp['RUTA_LOCAL'] != row['RUTA_LOCAL']]
                        from database_sqlite import update_table_from_df
                        # We use save_df_to_sql here, but wait, if we drop a row, it's better to rewrite the whole table.
                        import sqlite3
                        try:
                            conn = sqlite3.connect("conciliacion_data.db")
                            df_exp.to_sql("EXPEDIENTES_ARCHIVOS", conn, if_exists="replace", index=False)
                            conn.close()
                            st.rerun()
                        except Exception as e:
                            pass"""

content = content.replace(search_ventas, replace_ventas)

# 2. Update abrir_expediente_egresos
search_egresos = """        for idx, row in archivos_egreso.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                if st.button("Abrir", key=f"abrir_e_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")"""

replace_egresos = """        for idx, row in archivos_egreso.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                if st.button("Abrir", key=f"abrir_e_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")
            with col3:
                if st.button("🗑️ Eliminar", key=f"del_e_{idx}", help="Elimina el archivo físicamente y del registro."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        try:
                            os.remove(row['RUTA_LOCAL'])
                        except Exception as e:
                            st.error(f"Error borrando archivo: {e}")
                    # Eliminar de la base de datos
                    df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                    if not df_exp.empty:
                        df_exp = df_exp[df_exp['RUTA_LOCAL'] != row['RUTA_LOCAL']]
                        import sqlite3
                        try:
                            conn = sqlite3.connect("conciliacion_data.db")
                            df_exp.to_sql("EXPEDIENTES_ARCHIVOS", conn, if_exists="replace", index=False)
                            conn.close()
                            st.rerun()
                        except Exception as e:
                            pass"""

content = content.replace(search_egresos, replace_egresos)

with open('app.py', 'w') as f:
    f.write(content)
