import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_modulo_bancos(ruta_archivo):
    """
    Procesa exclusivamente el Módulo BANCOS (BBVA y Mercado Pago)
    aplicando las reglas específicas de limpieza.
    """
    print(f"Cargando Módulo BANCOS desde: {ruta_archivo}...")
    xls = pd.ExcelFile(ruta_archivo)
    hojas_disponibles = xls.sheet_names

    resultados_bancos = {}

    nombre_archivo = getattr(ruta_archivo, 'name', str(ruta_archivo)).lower()

    # Función auxiliar para determinar el nombre del banco basado en hoja y archivo
    def identificar_banco(nombre_hoja, nombre_archivo_lower):
        hoja_upper = str(nombre_hoja).upper()
        # Bancos conocidos que queremos identificar automáticamente
        bancos_conocidos = ['SANTANDER', 'BANAMEX', 'HSBC', 'BANORTE', 'SCOTIABANK', 'INBURSA', 'NU']

        # 1. Si la hoja empieza con "BBVA_" o es solo números (históricamente BBVA)
        if hoja_upper.startswith('BBVA_') or str(nombre_hoja).isdigit():
            cuenta = str(nombre_hoja).replace('BBVA_', '')
            return f"BBVA_{cuenta}" if cuenta.isdigit() else f"BBVA_{hoja_upper}"

        # 2. Buscar en el nombre de la hoja
        for banco in bancos_conocidos:
            if banco in hoja_upper:
                return f"{banco}_{hoja_upper.replace(banco, '').strip(' _-')}"

        # 3. Buscar en el nombre del archivo
        for banco in bancos_conocidos:
            if banco.lower() in nombre_archivo_lower:
                # Si lo encontramos en el archivo, usamos el nombre del banco y el nombre de la hoja como identificador
                return f"{banco}_{hoja_upper}"

        # 4. Si el archivo es BBVA pero la hoja no es numérica
        if 'bbva' in nombre_archivo_lower:
             return f"BBVA_{hoja_upper}"

        # REGLA ESTRICTA SUGERIDA POR EL USUARIO:
        # Si la hoja empieza con "BANCO " o "BANCO_", la procesamos directamente.
        # Ej: "BANCO BANAMEX 1234" -> "BANAMEX_1234"
        if hoja_upper.startswith('BANCO '):
             partes = hoja_upper.replace('BANCO ', '').split(' ', 1)
             if len(partes) == 2:
                  return f"{partes[0]}_{partes[1]}"
             return f"OTROS_{hoja_upper.replace('BANCO ', '')}"

        if hoja_upper.startswith('BANCO_'):
             partes = hoja_upper.replace('BANCO_', '').split('_', 1)
             if len(partes) == 2:
                  return f"{partes[0]}_{partes[1]}"
             return f"OTROS_{hoja_upper.replace('BANCO_', '')}"

        # FALLBACK: En lugar de usar el nombre de archivo (que genera pestañas gigantes/feas),
        # lo marcamos como OTROS_NombreHoja si no coincide con los patrones esperados.
        return f"OTROS_{hoja_upper}"

    # ==========================================
    # 1. MERCADO PAGO (EST MP y MP) - Procesar primero por ser formato único
    # ==========================================
    # Guardamos qué hojas ya procesamos para no repetirlas
    hojas_procesadas = []

    # Si suben el archivo individual de MP, puede que las hojas no se llamen "EST MP" o "MP"
    hoja_est_mp = next((h for h in hojas_disponibles if 'EST MP' in h.upper() or ('ESTADO' in h.upper() and 'MP' in nombre_archivo)), None)
    if hoja_est_mp:
        print(f"Procesando Mercado Pago Estado de Cuenta ({hoja_est_mp})...")
        df_raw = pd.read_excel(xls, sheet_name=hoja_est_mp, header=None)
        fila_encabezado_est = -1
        for i, fila in df_raw.iterrows():
            if fila.astype(str).str.contains('RELEASE_DATE', case=False, na=False).any():
                fila_encabezado_est = i
                break

        if fila_encabezado_est != -1:
            df_est_mp = pd.read_excel(xls, sheet_name=hoja_est_mp, header=fila_encabezado_est)
            df_est_mp = df_est_mp.dropna(subset=['RELEASE_DATE'])

            # Map columns to standard
            cols_map_mp_est = {
                'RELEASE_DATE': 'FECHA',
                'REFERENCE_ID': 'REFERENCE',
                'TRANSACTION_NET_AMOUNT': 'MONTO', # Will be split to CARGO/ABONO later if needed
                'PARTIAL_BALANCE': 'SALDO'
            }

            # Map CONCEPTO based on available columns to avoid duplicates
            if 'TRANSACTION_TYPE' in df_est_mp.columns:
                cols_map_mp_est['TRANSACTION_TYPE'] = 'CONCEPTO'
            elif 'DESCRIPTION' in df_est_mp.columns:
                cols_map_mp_est['DESCRIPTION'] = 'CONCEPTO'

            # Fallbacks for variations
            for col in df_est_mp.columns:
                col_upper = str(col).upper()
                if 'DATE' in col_upper and 'RELEASE' not in col_upper and 'FECHA' not in cols_map_mp_est.values():
                    cols_map_mp_est[col] = 'FECHA'

            # Use dictionary renaming, resolving mapping carefully
            df_est_mp = df_est_mp.rename(columns=cols_map_mp_est)

            # Limpiar Fechas (para que Pandas entienda DD/MM/YYYY correctamente y no como MM/DD/YYYY)
            if 'FECHA' in df_est_mp.columns:
                # Mercado Pago suele mandar fechas como string. Forzamos formato día primero.
                df_est_mp['FECHA'] = pd.to_datetime(df_est_mp['FECHA'], dayfirst=True, errors='coerce')
                # Opcional: convertirlo a formato string estándar si así se espera en SQLite, o dejar como datetime.
                # Lo dejamos como datetime y SQLite/Pandas lo manejarán bien.

            # Limpiar Montos (Quitar comas si es texto, convertir a float)
            if 'MONTO' in df_est_mp.columns:
                # The user noted MONTO (TRANSACTION_NET_AMOUNT) might come as text with commas like '-115,000.00'
                if df_est_mp['MONTO'].dtype == object:
                    df_est_mp['MONTO'] = df_est_mp['MONTO'].astype(str).str.replace(',', '', regex=False)

                df_est_mp['MONTO'] = pd.to_numeric(df_est_mp['MONTO'], errors='coerce')
                df_est_mp['ABONO'] = df_est_mp['MONTO'].apply(lambda x: x if pd.notnull(x) and x > 0 else 0)
                df_est_mp['CARGO'] = df_est_mp['MONTO'].apply(lambda x: abs(x) if pd.notnull(x) and x < 0 else 0)

            # Limpiar Saldos (Mismo problema potencial de texto y comas)
            if 'SALDO' in df_est_mp.columns:
                if df_est_mp['SALDO'].dtype == object:
                    df_est_mp['SALDO'] = df_est_mp['SALDO'].astype(str).str.replace(',', '', regex=False)
                df_est_mp['SALDO'] = pd.to_numeric(df_est_mp['SALDO'], errors='coerce')

            for col_req in ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']:
                if col_req not in df_est_mp.columns:
                    df_est_mp[col_req] = None

            columnas_finales = ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']
            df_est_mp = df_est_mp[columnas_finales]

            resultados_bancos['MP_ESTADO_CUENTA'] = df_est_mp
            print(f"  ✅ EST MP limpio: {len(df_est_mp)} movimientos.")
            hojas_procesadas.append(hoja_est_mp)

    hoja_mp_detalle = next((h for h in hojas_disponibles if h.upper() == 'MP' or ('DETALLE' in h.upper() and 'MP' in nombre_archivo.upper())), None)
    if hoja_mp_detalle:
        print(f"Procesando Detalle Mercado Pago ({hoja_mp_detalle})...")
        df_raw = pd.read_excel(xls, sheet_name=hoja_mp_detalle, header=None)
        fila_encabezado_mp = -1
        for i, fila in df_raw.iterrows():
            # Buscar explícitamente los nombres COMPLETOS de las columnas de Mercado Pago
            # y asegurarse de que estamos en una fila de encabezados real (varias columnas)
            # Evitar caer en textos informativos (ej. "Trabajamos para brindarte más detalle sobre los cargos...")
            fila_str = fila.astype(str)
            if (fila_str.str.contains('Número de la operación', case=False, na=False).any() or \
               fila_str.str.contains('Operación relacionada', case=False, na=False).any() or \
               fila_str.str.contains('Número del movimiento', case=False, na=False).any() or \
               fila_str.str.contains('Número del cargo', case=False, na=False).any()) and \
               not fila_str.str.contains('Trabajamos para brindarte', case=False, na=False).any():
                fila_encabezado_mp = i
                break

        if fila_encabezado_mp != -1:
            df_mp = pd.read_excel(xls, sheet_name=hoja_mp_detalle, header=fila_encabezado_mp)

            # Limpiar nombres de columnas eliminando saltos de línea y espacios raros
            df_mp.columns = df_mp.columns.str.replace('\n', ' ').str.strip()

            # Opciones comunes para ID único de Mercado Pago en exportaciones:
            col_id = next((col for col in ['Número del cargo', 'Número de la operación', 'Número del movimiento', 'N° de factura fiscal'] if col in df_mp.columns), None)

            if col_id:
                antes = len(df_mp)
                df_mp = df_mp.drop_duplicates(subset=[col_id])
                df_mp = df_mp.dropna(subset=[col_id])
                despues = len(df_mp)
                print(f"  ✅ MP detalle limpio: Usando columna '{col_id}'. Eliminados {antes-despues} duplicados. Quedan {despues}.")
            else:
                 print(f"  ⚠️ No se encontró columna ID válida para quitar duplicados. Columnas son: {df_mp.columns.tolist()}")

            # Map columns to standard for MP DETALLE
            cols_map_mp_det = {
                'Fecha de creación': 'FECHA',
                'Detalle': 'CONCEPTO',
                'Monto (MXN)': 'MONTO',
            }

            # Map REFERENCE based on available columns to avoid duplicates
            if 'Operación relacionada' in df_mp.columns:
                cols_map_mp_det['Operación relacionada'] = 'REFERENCE'
            elif 'Número de la operación' in df_mp.columns:
                cols_map_mp_det['Número de la operación'] = 'REFERENCE'

            df_mp = df_mp.rename(columns=cols_map_mp_det)

            if 'MONTO' in df_mp.columns:
                df_mp['MONTO'] = pd.to_numeric(df_mp['MONTO'], errors='coerce')
                df_mp['ABONO'] = df_mp['MONTO'].apply(lambda x: x if pd.notnull(x) and x > 0 else 0)
                df_mp['CARGO'] = df_mp['MONTO'].apply(lambda x: abs(x) if pd.notnull(x) and x < 0 else 0)

            for col_req in ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']:
                if col_req not in df_mp.columns:
                    df_mp[col_req] = None

            columnas_finales = ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']
            df_mp = df_mp[columnas_finales]

            resultados_bancos['MP_DETALLE'] = df_mp
            hojas_procesadas.append(hoja_mp_detalle)
        else:
            print(f"  ⚠️ No se encontraron encabezados válidos en la hoja MP. Omitiendo.")

    # ==========================================
    # 2. PROCESAMIENTO DINÁMICO DE OTROS BANCOS (BBVA, SANTANDER, ETC)
    # ==========================================
    # Iterar sobre las hojas que no hayan sido procesadas aún como MP
    hojas_restantes = [h for h in hojas_disponibles if h not in hojas_procesadas]

    # Si es el archivo consolidado y no pudimos extraer hojas útiles, fallback
    if not hojas_restantes and not resultados_bancos:
        print("⚠️ No se encontraron hojas identificables. Intentando procesar la primera hoja.")
        if len(hojas_disponibles) > 0:
            hojas_restantes = [hojas_disponibles[0]]

    for hoja in hojas_restantes:
        print(f"Procesando posible cuenta bancaria en hoja: {hoja}...")
        try:
            df_raw = pd.read_excel(xls, sheet_name=hoja, header=None)
        except Exception as e:
            print(f"No se pudo leer la hoja {hoja}: {e}")
            continue

        # Buscar la fila que contiene palabras clave de encabezados de banco
        fila_encabezado = -1
        for i, fila in df_raw.iterrows():
            fila_str = fila.astype(str).str.lower()
            # Criterio: Debe tener algo parecido a Fecha/Día y algo como Cargo/Abono/Retiro/Depósito
            tiene_fecha = fila_str.str.contains(r'^día|^dia|^fecha', na=False).any()
            tiene_movimiento = fila_str.str.contains(r'cargo|abono|retiro|depósito|deposito', na=False).any()

            if tiene_fecha and tiene_movimiento:
                fila_encabezado = i
                break
            # Fallback simple (solo fecha/dia)
            elif fila_str.str.contains(r'^día|^dia', na=False).any():
                fila_encabezado = i
                break

        if fila_encabezado != -1:
            # Re-leer usando la fila encontrada como encabezado
            df_banco = pd.read_excel(xls, sheet_name=hoja, header=fila_encabezado)

            # Limpiar nombres de columnas y estandarizar
            cols_map = {}
            for col in df_banco.columns:
                col_str = str(col).strip().lower()
                if 'día' in col_str or 'dia' in col_str or 'fecha' in col_str:
                    cols_map[col] = 'FECHA'
                elif 'referencia' in col_str:
                    cols_map[col] = 'REFERENCE'
                elif 'concepto' in col_str or 'descripción' in col_str or 'descripcion' in col_str:
                    cols_map[col] = 'CONCEPTO'
                elif 'cargo' in col_str or 'retiro' in col_str:
                    cols_map[col] = 'CARGO'
                elif 'abono' in col_str or 'deposito' in col_str or 'depósito' in col_str:
                    cols_map[col] = 'ABONO'
                elif 'saldo' in col_str:
                    cols_map[col] = 'SALDO'

            df_banco = df_banco.rename(columns=cols_map)

            # Asegurar las 10 columnas obligatorias
            for col_req in ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']:
                if col_req not in df_banco.columns:
                    df_banco[col_req] = None

            # Dejar solo las columnas estandarizadas (y eliminar filas totalmente vacías)
            columnas_finales = ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']
            df_banco = df_banco.dropna(how='all', subset=['FECHA', 'CONCEPTO', 'CARGO', 'ABONO', 'SALDO'])
            df_banco = df_banco[columnas_finales]

            # Obtener el nombre de la cuenta usando la función auxiliar dinámica
            nombre_cuenta = identificar_banco(hoja, nombre_archivo)

            resultados_bancos[nombre_cuenta] = df_banco
            print(f"  ✅ Banco {nombre_cuenta} limpio: {len(df_banco)} movimientos.")
        else:
            print(f"  ⚠️ No se encontró una fila de encabezados válida en la hoja '{hoja}'. Omitiendo.")

    return resultados_bancos

if __name__ == '__main__':
    bancos_limpios = limpiar_modulo_bancos('CONCILIACION FEBRERO OK - copia.xlsm')
