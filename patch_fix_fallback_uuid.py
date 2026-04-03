import re

with open('app.py', 'r') as f:
    content = f.read()

search = """                        # Determinar ruta destino
                        ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str)"""

replace = """                        # Si uuid_str sigue nulo, tenemos que inicializarlo antes de usar path.join
                        if not uuid_str:
                            uuid_str_temp = "DESCONOCIDO"
                        else:
                            uuid_str_temp = uuid_str

                        # Determinar ruta destino inicial
                        ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", "MANUAL", uuid_str_temp)"""

content = content.replace(search, replace)

search_uuid_zip = """                            zip_name_raw = file_name.replace('.zip', '').split('/')[-1]
                            match_global = re.search(r'[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}', zip_name_raw)"""
replace_uuid_zip = """                            # Si no se pudo obtener del PDF, y fue extraido de un ZIP, verificamos si la carpeta o el ZIP padre tiene nombre de UUID
                            zip_name_raw = file_path_in_zip.split('/')[0] if '/' in file_path_in_zip else file_name.replace('.zip', '')
                            match_global = re.search(r'[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}', zip_name_raw)"""
content = content.replace(search_uuid_zip, replace_uuid_zip)


with open('app.py', 'w') as f:
    f.write(content)
