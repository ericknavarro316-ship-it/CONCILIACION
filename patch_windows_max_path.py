with open('app.py', 'r') as f:
    content = f.read()

# Add a helper function at the top of the file
search = """def safe_parse_dates(serie):"""

replace = """def safe_path(ruta_relativa):
    import os
    ruta_absoluta = os.path.abspath(ruta_relativa)
    if os.name == 'nt' and not ruta_absoluta.startswith('\\\\?\\'):
        return '\\\\?\\' + ruta_absoluta
    return ruta_absoluta

def safe_parse_dates(serie):"""

content = content.replace(search, replace)

# 1. Update in Ventas modal
search_ventas = """            with open(ruta_destino, "wb") as f:
                f.write(uf.getbuffer())"""

replace_ventas = """            os.makedirs(safe_path(ruta_base), exist_ok=True)
            with open(safe_path(ruta_destino), "wb") as f:
                f.write(uf.getbuffer())"""
content = content.replace(search_ventas, replace_ventas)

search_ventas_dir = """        os.makedirs(ruta_base, exist_ok=True)"""
replace_ventas_dir = """        os.makedirs(safe_path(ruta_base), exist_ok=True)"""
content = content.replace(search_ventas_dir, replace_ventas_dir)

# 2. Update in Egresos modal
search_egresos = """            with open(ruta_destino, "wb") as f:
                f.write(uf.getbuffer())"""

replace_egresos = """            os.makedirs(safe_path(ruta_base), exist_ok=True)
            with open(safe_path(ruta_destino), "wb") as f:
                f.write(uf.getbuffer())"""
content = content.replace(search_egresos, replace_egresos)

search_egresos_dir = """        os.makedirs(ruta_base, exist_ok=True)"""
replace_egresos_dir = """        os.makedirs(safe_path(ruta_base), exist_ok=True)"""
content = content.replace(search_egresos_dir, replace_egresos_dir)

# 3. Update in process_egreso_file (Bulk Egresos)
search_process = """                        os.makedirs(ruta_base, exist_ok=True)
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                        ruta_destino = os.path.join(ruta_base, safe_name)

                        file_buffer.seek(0)
                        with open(ruta_destino, "wb") as f:
                            f.write(file_buffer.read())"""

replace_process = """                        os.makedirs(safe_path(ruta_base), exist_ok=True)
                        safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                        ruta_destino = os.path.join(ruta_base, safe_name)

                        file_buffer.seek(0)
                        with open(safe_path(ruta_destino), "wb") as f:
                            f.write(file_buffer.read())"""
content = content.replace(search_process, replace_process)

# 4. Update in Bulk Ventas (ZIP)
search_ventas_zip = """                                    # Guardar archivo
                                    os.makedirs(ruta_base, exist_ok=True)
                                    file_name = path_parts[-1]
                                    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    ruta_destino = os.path.join(ruta_base, safe_name)

                                    with open(ruta_destino, "wb") as f:
                                        f.write(z.read(file_info.filename))"""

replace_ventas_zip = """                                    # Guardar archivo
                                    os.makedirs(safe_path(ruta_base), exist_ok=True)
                                    file_name = path_parts[-1]
                                    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    ruta_destino = os.path.join(ruta_base, safe_name)

                                    with open(safe_path(ruta_destino), "wb") as f:
                                        f.write(z.read(file_info.filename))"""
content = content.replace(search_ventas_zip, replace_ventas_zip)

# 5. Update in Bulk Ventas (PDF)
search_ventas_pdf = """                            # 3. Guardar archivo
                            os.makedirs(ruta_base, exist_ok=True)
                            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', pdf_file.name)
                            ruta_destino = os.path.join(ruta_base, safe_name)

                            with open(ruta_destino, "wb") as f:
                                f.write(pdf_file.getbuffer())"""

replace_ventas_pdf = """                            # 3. Guardar archivo
                            os.makedirs(safe_path(ruta_base), exist_ok=True)
                            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', pdf_file.name)
                            ruta_destino = os.path.join(ruta_base, safe_name)

                            with open(safe_path(ruta_destino), "wb") as f:
                                f.write(pdf_file.getbuffer())"""
content = content.replace(search_ventas_pdf, replace_ventas_pdf)


with open('app.py', 'w') as f:
    f.write(content)
