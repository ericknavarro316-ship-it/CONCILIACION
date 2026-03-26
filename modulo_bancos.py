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
            # Encontrar columna 'Día', 'Concepto', 'Cargo', 'Abono', 'Saldo'
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
        # En el archivo original, el encabezado verdadero está en la fila 4 (índice 3)
        # Buscar "RELEASE_DATE" para asegurar
        df_raw = pd.read_excel(xls, sheet_name='EST MP', header=None)
        fila_encabezado_est = -1
        for i, fila in df_raw.iterrows():
            if fila.astype(str).str.contains('RELEASE_DATE', case=False, na=False).any():
                fila_encabezado_est = i
                break

        if fila_encabezado_est != -1:
            df_est_mp = pd.read_excel(xls, sheet_name='EST MP', header=fila_encabezado_est)
            df_est_mp = df_est_mp.dropna(subset=['RELEASE_DATE']) # Quitar basura del final
            resultados_bancos['MP_ESTADO_CUENTA'] = df_est_mp
            print(f"  ✅ EST MP limpio: {len(df_est_mp)} movimientos.")

    if 'MP' in hojas_disponibles:
        print("Procesando Detalle Mercado Pago (MP)...")
        # Buscar "Número del cargo" o "Fecha del cargo" (Aprox fila 8 / índice 7)
        df_raw = pd.read_excel(xls, sheet_name='MP', header=None)
        fila_encabezado_mp = -1
        for i, fila in df_raw.iterrows():
            if fila.astype(str).str.contains('cargo', case=False, na=False).any() or \
               fila.astype(str).str.contains('operación', case=False, na=False).any():
                fila_encabezado_mp = i
                break

        if fila_encabezado_mp != -1:
            df_mp = pd.read_excel(xls, sheet_name='MP', header=fila_encabezado_mp)
            # Regla MP: Quitar duplicados. Identificador suele ser 'Número del cargo' o 'Número del movimiento'
            if 'Número del cargo' in df_mp.columns:
                antes = len(df_mp)
                df_mp = df_mp.drop_duplicates(subset=['Número del cargo'])
                df_mp = df_mp.dropna(subset=['Número del cargo'])
                despues = len(df_mp)
                print(f"  ✅ MP detalle limpio: Eliminados {antes-despues} duplicados/vacíos. Quedan {despues}.")
                resultados_bancos['MP_DETALLE'] = df_mp
            else:
                 print(f"  ⚠️ No se encontró 'Número del cargo' para quitar duplicados.")

    return resultados_bancos

if __name__ == '__main__':
    bancos_limpios = limpiar_modulo_bancos('CONCILIACION FEBRERO OK - copia.xlsm')
    print("\nResumen final del Módulo Bancos:")
    for key, df in bancos_limpios.items():
        print(f"- {key}: {len(df)} registros")
        print(df.head(2))
        print("---")
