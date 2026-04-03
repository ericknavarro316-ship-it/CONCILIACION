import os
import re
import traceback

def test():
    file_name = "SECFD_20260205_121935_OK.pdf"
    uuid_str = "7EC63824-1234-48CB-9BA3-DF7ED0C6C3AC"
    mes_folder = "2026_02"
    tipo_comprobante = "PUE"

    ruta_base = os.path.join("EXPEDIENTES", "EGRESOS", mes_folder, tipo_comprobante, uuid_str)

    # Simulating what happens in app.py when `break` occurs and then we execute os.makedirs
    os.makedirs(ruta_base, exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
    ruta_destino = os.path.join(ruta_base, safe_name)

    with open(ruta_destino, "wb") as f:
        f.write(b"")

try:
    test()
except Exception as e:
    traceback.print_exc()
