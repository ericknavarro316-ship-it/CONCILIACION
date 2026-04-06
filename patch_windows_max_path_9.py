with open('app.py', 'r') as f:
    content = f.read()

helper_code = """
def safe_path(ruta_relativa):
    import os
    ruta_absoluta = os.path.abspath(ruta_relativa)
    if os.name == 'nt':
        prefijo = "\\\\\\\\?\\\\"
        if not ruta_absoluta.startswith(prefijo):
            return prefijo + ruta_absoluta
    return ruta_absoluta

def safe_parse_dates(serie):
"""

content = content.replace("def safe_parse_dates(serie):", helper_code.strip())

content = content.replace('os.makedirs(ruta_base, exist_ok=True)', 'os.makedirs(safe_path(ruta_base), exist_ok=True)')
content = content.replace('with open(ruta_destino, "wb") as f:', 'with open(safe_path(ruta_destino), "wb") as f:')

with open('app.py', 'w') as f:
    f.write(content)
