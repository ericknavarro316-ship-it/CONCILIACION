import re

with open('app.py', 'r') as f:
    content = f.read()

search = """# 4. HELPER DE FILTROS GLOBALES (OPTIMIZADO CON SQL-FIRST)"""

replace = """# 4. FUNCIONES PARA EXTRACCION Y VINCULACION DE UUID (CFDI <-> VENTAS)
def extraer_uuid_de_archivo(ruta_archivo):
    import re
    import os
    uuid_pattern = r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'

    ext = os.path.splitext(ruta_archivo)[1].lower()

    try:
        if ext == '.xml':
            with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(uuid_pattern, content)
                if match:
                    return match.group(0).upper()
        elif ext == '.pdf':
            import pdfplumber
            with pdfplumber.open(ruta_archivo) as pdf:
                # Revisar las primeras páginas donde suele estar el UUID
                for page in pdf.pages[:2]:
                    text = page.extract_text()
                    if text:
                        match = re.search(uuid_pattern, text)
                        if match:
                            return match.group(0).upper()
    except Exception as e:
        print(f"Error extrayendo UUID de {ruta_archivo}: {e}")
        pass

    return None

def vincular_cfdi_y_venta(id_venta, ruta_archivo, nombre_archivo):
    uuid_extraido = extraer_uuid_de_archivo(ruta_archivo)
    if not uuid_extraido:
        return False

    vinculado = False

    # 1. Actualizar tablas CFDI_I
    tablas_todas = get_all_tables()
    tablas_cfdi = [t for t in tablas_todas if t.startswith("CFDI_I_")]

    for tb_cfdi in tablas_cfdi:
        df_cfdi = get_df_from_sql(tb_cfdi)
        if not df_cfdi.empty and 'UUID' in df_cfdi.columns:
            # Encontrar la fila con ese UUID (ignorando case y espacios)
            mask_uuid = df_cfdi['UUID'].astype(str).str.strip().str.upper() == uuid_extraido
            if mask_uuid.any():
                # Actualizamos las columnas ID VENTA y PDF
                if 'ID VENTA' not in df_cfdi.columns:
                    df_cfdi['ID VENTA'] = ""
                if 'PDF' not in df_cfdi.columns:
                    df_cfdi['PDF'] = ""

                df_cfdi.loc[mask_uuid, 'ID VENTA'] = id_venta
                df_cfdi.loc[mask_uuid, 'PDF'] = nombre_archivo
                update_table_from_df(df_cfdi, tb_cfdi)
                vinculado = True

    # 2. Actualizar tablas de VENTAS
    if vinculado:
        tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]
        for tb_venta in tablas_ventas:
            df_venta = get_df_from_sql(tb_venta)
            col_id = 'id_venta' if 'id_venta' in df_venta.columns else 'ID VENTA' if 'ID VENTA' in df_venta.columns else None

            if col_id and not df_venta.empty:
                mask_venta = df_venta[col_id].astype(str).str.strip() == str(id_venta)
                if mask_venta.any():
                    if 'UUID' not in df_venta.columns:
                        df_venta['UUID'] = ""
                    df_venta.loc[mask_venta, 'UUID'] = uuid_extraido
                    update_table_from_df(df_venta, tb_venta)

    return vinculado

# 5. HELPER DE FILTROS GLOBALES (OPTIMIZADO CON SQL-FIRST)"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
