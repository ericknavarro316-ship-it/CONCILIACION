import re

with open('app.py', 'r') as f:
    content = f.read()

# Add a helper function at the top of the file
search = """def safe_parse_dates(serie):"""

replace = """def safe_path(ruta_relativa):
    import os
    ruta_absoluta = os.path.abspath(ruta_relativa)
    if os.name == 'nt':
        if not ruta_absoluta.startswith(r"\\\\?\\"):
            return r"\\\\?\\" + ruta_absoluta
    return ruta_absoluta

def safe_parse_dates(serie):"""

# Let's replace only once to be safe
content = content.replace(search, replace, 1)

# Now we process all the specific lines individually using simple string replacements
search_list = [
    (r'os.makedirs(ruta_base, exist_ok=True)', r'os.makedirs(safe_path(ruta_base), exist_ok=True)'),
    (r'with open(ruta_destino, "wb") as f:', r'with open(safe_path(ruta_destino), "wb") as f:')
]

for s, r in search_list:
    content = content.replace(s, r)

with open('app.py', 'w') as f:
    f.write(content)
