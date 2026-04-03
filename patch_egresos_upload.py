import re

with open('app.py', 'r') as f:
    content = f.read()

search = """        # Upload files into Expedientes for EGRESOS
        if tipo_cfdi == "EGRESOS":
            with st.expander("📥 Cargar Expedientes de Egresos (PDF / ZIP)", expanded=False):"""

replace = """        # Upload files into Expedientes for EGRESOS
        if tipo_cfdi == "EGRESOS":
            st.info("💡 **Tip:** Para cargar y guardar comprobantes, abre este menú desplegable:")
            with st.expander("📥 CARGAR EXPEDIENTES DE EGRESOS (PDF / ZIP)", expanded=False):"""

content = content.replace(search, replace)

search_fallback = """                        # Determinar ruta destino
                        ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str)
                        for tb in tablas_egresos:"""

replace_fallback = """                        # Determinar ruta destino
                        ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str)

                        # Si no encontramos el UUID, busquemos el nombre del ZIP como posible UUID en el fallback global
                        if is_zip_content and not uuid_str:
                            zip_name_raw = file_name.replace('.zip', '').split('/')[-1]
                            match_global = re.search(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}', zip_name_raw)
                            if match_global:
                                uuid_str = match_global.group(0).upper()
                                ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str)

                        if not uuid_str:
                            # Ultimo recurso: Guardar en una carpeta genérica llamada DESCONOCIDOS si no detectamos nada,
                            # al menos no perdemos el archivo si el cliente subió algo
                            ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "DESCONOCIDOS")
                            uuid_str = "DESCONOCIDO"

                        for tb in tablas_egresos:"""

content = content.replace(search_fallback, replace_fallback)

with open('app.py', 'w') as f:
    f.write(content)
