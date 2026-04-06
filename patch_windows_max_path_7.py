with open('app.py', 'r') as f:
    content = f.read()

prefix = r"\\?\".replace('"', '')

replace = f"""def safe_path(ruta_relativa):
    import os
    ruta_absoluta = os.path.abspath(ruta_relativa)
    if os.name == 'nt' and not ruta_absoluta.startswith(r"\\\\?\\"):
        return r"\\\\?\\" + ruta_absoluta
    return ruta_absoluta

def safe_parse_dates(serie):"""

# Let's bypass the `\?\` parsing bug in python's `re` module or bash heredocs completely
content = content.replace("def safe_parse_dates(serie):", "def safe_path(ruta_relativa):\n    import os\n    ruta_absoluta = os.path.abspath(ruta_relativa)\n    if os.name == 'nt':\n        if not ruta_absoluta.startswith('\\\\'*2 + '?' + '\\\\'):\n            return '\\\\'*2 + '?' + '\\\\' + ruta_absoluta\n    return ruta_absoluta\n\ndef safe_parse_dates(serie):", 1)

content = content.replace('os.makedirs(ruta_base, exist_ok=True)', 'os.makedirs(safe_path(ruta_base), exist_ok=True)')
content = content.replace('with open(ruta_destino, "wb") as f:', 'with open(safe_path(ruta_destino), "wb") as f:')

with open('app.py', 'w') as f:
    f.write(content)
