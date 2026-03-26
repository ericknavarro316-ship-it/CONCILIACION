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

    # ==========================================
    # 1. BBVA (Hojas numéricas)
    # ==========================================
    hojas_numericas = [h for h in hojas_disponibles if h.isdigit()]

    for hoja in hojas_numericas:
        print(f"Procesando cuenta BBVA: {hoja}...")
        df_raw = pd.read_excel(xls, sheet_name=hoja, header=None)

        # Buscar la fila que contiene la palabra "Día" o "Dia"
        fila_encabezado = -1
        for i, fila in df_raw.iterrows():
            if fila.astype(str).str.contains(r'^Día|^Dia', case=False, na=False).any():
                fila_encabezado = i
                break

        if fila_encabezado != -1:
            # Re-leer usando la fila encontrada como encabezado
            df_banco = pd.read_excel(xls, sheet_name=hoja, header=fila_encabezado)

            # Limpiar nombres de columnas y estandarizar
            cols_map = {}
            for col in df_banco.columns:
                col_str = str(col).strip().lower()
                if 'día' in col_str or 'dia' in col_str:
                    cols_map[col] = 'FECHA'
                elif 'concepto' in col_str or 'referencia' in col_str:
                    cols_map[col] = 'DESCRIPCION'
                elif 'cargo' in col_str:
                    cols_map[col] = 'CARGO'
                elif 'abono' in col_str:
                    cols_map[col] = 'ABONO'
                elif 'saldo' in col_str:
                    cols_map[col] = 'SALDO'

            df_banco = df_banco.rename(columns=cols_map)

            # Dejar solo las columnas estandarizadas (y eliminar filas totalmente vacías)
            columnas_finales = [c for c in ['FECHA', 'DESCRIPCION', 'CARGO', 'ABONO', 'SALDO'] if c in df_banco.columns]
            df_banco = df_banco[columnas_finales].dropna(how='all')

            resultados_bancos[f"BBVA_{hoja}"] = df_banco
            print(f"  ✅ BBVA {hoja} limpio: {len(df_banco)} movimientos.")
        else:
            print(f"  ⚠️ No se encontró la fila 'Día' en la hoja {hoja}. Omitiendo.")

    # ==========================================
    # 2. MERCADO PAGO (EST MP y MP)
    # ==========================================
    if 'EST MP' in hojas_disponibles:
        print("Procesando Mercado Pago (EST MP)...")
        df_raw = pd.read_excel(xls, sheet_name='EST MP', header=None)
        fila_encabezado_est = -1
        for i, fila in df_raw.iterrows():
            if fila.astype(str).str.contains('RELEASE_DATE', case=False, na=False).any():
                fila_encabezado_est = i
                break

        if fila_encabezado_est != -1:
            df_est_mp = pd.read_excel(xls, sheet_name='EST MP', header=fila_encabezado_est)
            df_est_mp = df_est_mp.dropna(subset=['RELEASE_DATE'])
            resultados_bancos['MP_ESTADO_CUENTA'] = df_est_mp
            print(f"  ✅ EST MP limpio: {len(df_est_mp)} movimientos.")

    if 'MP' in hojas_disponibles:
        print("Procesando Detalle Mercado Pago (MP)...")
        df_raw = pd.read_excel(xls, sheet_name='MP', header=None)
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
            df_mp = pd.read_excel(xls, sheet_name='MP', header=fila_encabezado_mp)

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
                resultados_bancos['MP_DETALLE'] = df_mp
            else:
                 print(f"  ⚠️ No se encontró columna ID válida para quitar duplicados. Columnas son: {df_mp.columns.tolist()}")
                 # Guardar de todos modos
                 resultados_bancos['MP_DETALLE'] = df_mp
        else:
            print(f"  ⚠️ No se encontraron encabezados válidos en la hoja MP. Omitiendo.")

    return resultados_bancos

if __name__ == '__main__':
    bancos_limpios = limpiar_modulo_bancos('CONCILIACION FEBRERO OK - copia.xlsm')
