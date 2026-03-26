import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_modulo_cfdi(ruta_archivo):
    """
    Procesa exclusivamente el Módulo CFDI.
    Toma los reportes del SAT (Ingresos y Egresos), salta encabezados basura,
    y separa por PUE y PPD. Las hojas de PAGOS se pasan tal cual.
    """
    print(f"Cargando Módulo CFDI desde: {ruta_archivo}...")
    xls = pd.ExcelFile(ruta_archivo)
    hojas_disponibles = xls.sheet_names

    resultados_cfdi = {}

    # Función auxiliar para procesar CFDI (I o E)
    def procesar_cfdi(nombre_hoja, prefijo):
        if nombre_hoja in hojas_disponibles:
            print(f"Procesando {nombre_hoja}...")
            # Los reportes del SAT suelen tener el encabezado en la fila 3 (índice 2)
            try:
                df = pd.read_excel(xls, sheet_name=nombre_hoja, header=2)
                # Limpiar nombres de columnas (espacios extras)
                df.columns = df.columns.astype(str).str.strip()

                # Buscar la columna de Método de Pago
                col_metodo = next((col for col in ['Método de Pago', 'Metodo de Pago'] if col in df.columns), None)

                if col_metodo:
                    # Crear PUE
                    df_pue = df[df[col_metodo].astype(str).str.contains('PUE', case=False, na=False)].copy()
                    # Crear PPD
                    df_ppd = df[df[col_metodo].astype(str).str.contains('PPD', case=False, na=False)].copy()

                    resultados_cfdi[f"{prefijo}_PUE"] = df_pue
                    resultados_cfdi[f"{prefijo}_PPD"] = df_ppd

                    print(f"  ✅ {nombre_hoja} separado en: {len(df_pue)} PUE y {len(df_ppd)} PPD.")
                else:
                    print(f"  ⚠️ No se encontró la columna '{col_metodo}' en {nombre_hoja}. Se guarda completo.")
                    resultados_cfdi[prefijo] = df
            except Exception as e:
                print(f"  ❌ Error procesando {nombre_hoja}: {e}")
        else:
            print(f"  ⚠️ La hoja {nombre_hoja} no existe en el archivo.")

    # Función auxiliar para procesar PAGOS
    def procesar_pagos(nombre_hoja, clave):
        if nombre_hoja in hojas_disponibles:
            print(f"Procesando {nombre_hoja} (Sin limpieza adicional)...")
            try:
                # Ocasionalmente los pagos también traen basura del SAT en fila 3, probamos si header=2 aplica
                # Revisemos primero si la fila 0 tiene algo o es el header real.
                df_test = pd.read_excel(xls, sheet_name=nombre_hoja, nrows=3, header=None)
                if df_test.iloc[2].astype(str).str.contains('UUID|Folio', case=False, na=False).any():
                     df = pd.read_excel(xls, sheet_name=nombre_hoja, header=2)
                else:
                     df = pd.read_excel(xls, sheet_name=nombre_hoja) # Header normal

                df.columns = df.columns.astype(str).str.strip()
                resultados_cfdi[clave] = df
                print(f"  ✅ {nombre_hoja} cargado: {len(df)} registros.")
            except Exception as e:
                print(f"  ❌ Error procesando {nombre_hoja}: {e}")
        else:
            print(f"  ⚠️ La hoja {nombre_hoja} no existe en el archivo.")

    # Identificar hojas si se suben individualmente o con nombres ligeramente distintos
    hoja_cfdi_i = next((h for h in hojas_disponibles if 'CFDI I' in h.upper() or ('INGRESO' in h.upper() and 'CFDI' in h.upper())), None)
    hoja_cfdi_e = next((h for h in hojas_disponibles if 'CFDI E' in h.upper() or ('EGRESO' in h.upper() and 'CFDI' in h.upper())), None)
    hoja_pagos_i = next((h for h in hojas_disponibles if 'PAGOS I' in h.upper() or ('PAGO' in h.upper() and 'I' in h.upper())), None)
    hoja_pagos_e = next((h for h in hojas_disponibles if 'PAGOS E' in h.upper() or ('PAGO' in h.upper() and 'E' in h.upper())), None)

    # Fallback para archivos individuales de 1 hoja (si no es pago, asumimos CFDI I por defecto)
    if len(hojas_disponibles) == 1 and not (hoja_cfdi_i or hoja_cfdi_e or hoja_pagos_i or hoja_pagos_e):
         if 'PAGO' in hojas_disponibles[0].upper():
              hoja_pagos_e = hojas_disponibles[0] # Asumimos Pagos E por seguridad
         else:
              hoja_cfdi_i = hojas_disponibles[0] # Asumimos Ingresos por seguridad

    # Ejecutar procesamiento
    if hoja_cfdi_i: procesar_cfdi(hoja_cfdi_i, 'CFDI_I')
    if hoja_cfdi_e: procesar_cfdi(hoja_cfdi_e, 'CFDI_E')
    if hoja_pagos_i: procesar_pagos(hoja_pagos_i, 'PAGOS_I')
    if hoja_pagos_e: procesar_pagos(hoja_pagos_e, 'PAGOS_E')

    return resultados_cfdi

if __name__ == '__main__':
    cfdi_limpios = limpiar_modulo_cfdi('CONCILIACION FEBRERO OK - copia.xlsm')
    print("\nResumen final del Módulo CFDI:")
    for key, df in cfdi_limpios.items():
        print(f"- {key}: {len(df)} registros")
