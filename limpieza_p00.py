import pandas as pd
import numpy as np

def limpiar_y_preparar_datos(ruta_archivo_crudo):
    """
    Simula el módulo P00 de las macros de Excel.
    Toma el archivo crudo, extrae las hojas, limpia los encabezados
    y separa los CFDI en PUE y PPD.
    """
    print(f"Cargando archivo crudo: {ruta_archivo_crudo}")

    # 1. Cargar el Excel
    xls = pd.ExcelFile(ruta_archivo_crudo)
    hojas_disponibles = xls.sheet_names

    resultados = {}

    # 2. Procesar NOTA DE VENTA (Ventas crudas) -> VENTAS_BBVA (Ejemplo simplificado)
    if 'NOTA DE VENTA' in hojas_disponibles:
        df_ventas = pd.read_excel(xls, sheet_name='NOTA DE VENTA')
        # Para el prototipo, asumimos que NOTA DE VENTA es la base de las ventas.
        # Aquí se aplicaría la lógica para dividir en BBVA, MP, ScooterZone, etc.
        # Filtrar o agrupar según corresponda. Aquí solo la renombramos por ahora.
        resultados['VENTAS'] = df_ventas
        print(f"✅ Ventas cargadas: {len(df_ventas)} registros.")

    # 3. Procesar CFDI I (Ingresos) -> Separar en PUE y PPD
    if 'CFDI I' in hojas_disponibles:
        # Los encabezados reales en el Excel del SAT a menudo están en la fila 3 (índice 2)
        df_cfdi_i = pd.read_excel(xls, sheet_name='CFDI I', header=2)

        # Limpiar nombres de columnas
        df_cfdi_i.columns = df_cfdi_i.columns.str.strip()

        # Identificar la columna del Método de Pago
        col_metodo = 'Método de Pago' if 'Método de Pago' in df_cfdi_i.columns else 'Metodo de Pago'

        if col_metodo in df_cfdi_i.columns:
            # Filtrar por PUE
            df_pue = df_cfdi_i[df_cfdi_i[col_metodo].astype(str).str.contains('PUE', na=False, case=False)].copy()
            # Filtrar por PPD
            df_ppd = df_cfdi_i[df_cfdi_i[col_metodo].astype(str).str.contains('PPD', na=False, case=False)].copy()

            resultados['CFDI_I_PUE'] = df_pue
            resultados['CFDI_I_PPD'] = df_ppd

            print(f"✅ CFDI I separado: {len(df_pue)} PUE, {len(df_ppd)} PPD.")
        else:
            print(f"⚠️ No se encontró la columna '{col_metodo}' en CFDI I.")

    # 4. Procesar hojas bancarias (hojas numéricas)
    hojas_bancarias = [h for h in hojas_disponibles if h.isdigit()]
    bancos_dict = {}
    for h in hojas_bancarias:
        df_banco = pd.read_excel(xls, sheet_name=h)
        # Limpiar encabezados si es necesario
        bancos_dict[h] = df_banco
        print(f"✅ Banco {h} cargado: {len(df_banco)} registros.")

    resultados['BANCOS'] = bancos_dict

    return resultados

if __name__ == '__main__':
    # Prueba local
    datos = limpiar_y_preparar_datos('CONCILIACION FEBRERO OK - copia.xlsm')
