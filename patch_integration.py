import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Integrar en modal abrir_expediente
search_modal = """            nuevos_registros.append({
                "ID_VENTA": id_venta,
                "NOMBRE_ARCHIVO": safe_name,
                "TIPO_DOCUMENTO": safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO',
                "RUTA_LOCAL": ruta_destino
            })"""

replace_modal = """            nuevos_registros.append({
                "ID_VENTA": id_venta,
                "NOMBRE_ARCHIVO": safe_name,
                "TIPO_DOCUMENTO": safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO',
                "RUTA_LOCAL": ruta_destino
            })

            # Intentar vincular UUID con CFDI
            vincular_cfdi_y_venta(id_venta, ruta_destino, safe_name)"""

content = content.replace(search_modal, replace_modal)

# 2. Integrar en carga por PDF
search_pdf = """                            nuevos_registros_expediente.append({
                                "ID_VENTA": id_venta_saneado,
                                "NOMBRE_ARCHIVO": safe_name,
                                "TIPO_DOCUMENTO": "PDF",
                                "RUTA_LOCAL": ruta_destino
                            })"""

replace_pdf = """                            nuevos_registros_expediente.append({
                                "ID_VENTA": id_venta_saneado,
                                "NOMBRE_ARCHIVO": safe_name,
                                "TIPO_DOCUMENTO": "PDF",
                                "RUTA_LOCAL": ruta_destino
                            })

                            # Intentar vincular UUID con CFDI
                            vincular_cfdi_y_venta(id_venta_saneado, ruta_destino, safe_name)"""

content = content.replace(search_pdf, replace_pdf)

# 3. Integrar en carga por ZIP
search_zip = """                                    nuevos_registros_expediente.append({
                                        "ID_VENTA": id_venta_saneado,
                                        "NOMBRE_ARCHIVO": safe_name,
                                        "TIPO_DOCUMENTO": tipo_doc,
                                        "RUTA_LOCAL": ruta_destino
                                    })"""

replace_zip = """                                    nuevos_registros_expediente.append({
                                        "ID_VENTA": id_venta_saneado,
                                        "NOMBRE_ARCHIVO": safe_name,
                                        "TIPO_DOCUMENTO": tipo_doc,
                                        "RUTA_LOCAL": ruta_destino
                                    })

                                    # Intentar vincular UUID con CFDI
                                    vincular_cfdi_y_venta(id_venta_saneado, ruta_destino, safe_name)"""

content = content.replace(search_zip, replace_zip)

with open('app.py', 'w') as f:
    f.write(content)
