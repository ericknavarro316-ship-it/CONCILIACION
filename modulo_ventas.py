import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_modulo_ventas(ruta_archivo):
    """
    Procesa exclusivamente el Módulo VENTAS.
    Carga la hoja 'NOTA DE VENTA' y separa las filas en diferentes bloques
    (BBVA, MERCADO PAGO, SCOOTERZONE, EFECTIVO, SIN BANCO) según 'bancos_cobro'.
    """
    print(f"Cargando Módulo VENTAS desde: {ruta_archivo}...")
    xls = pd.ExcelFile(ruta_archivo)

    if 'NOTA DE VENTA' not in xls.sheet_names:
        print("❌ No se encontró la hoja 'NOTA DE VENTA'.")
        return {}

    df_ventas = pd.read_excel(xls, sheet_name='NOTA DE VENTA')

    # Estandarizar columnas a minúsculas
    df_ventas.columns = df_ventas.columns.str.lower().str.strip()

    # Asegurarnos de que existe la columna bancos_cobro
    if 'bancos_cobro' not in df_ventas.columns:
        print("❌ No se encontró la columna 'bancos_cobro'. Imposible separar por bloques.")
        return {'VENTAS_TOTALES': df_ventas}

    # Rellenar vacíos con un texto base para evitar errores al buscar
    df_ventas['bancos_cobro'] = df_ventas['bancos_cobro'].fillna('SIN_ESPECIFICAR')

    # Crear un diccionario para almacenar los bloques
    bloques_ventas = {}

    print("Separando ventas por bloque de cobro...")

    # 1. MERCADO PAGO (Si contiene 'MERCADO PAGO')
    mask_mp = df_ventas['bancos_cobro'].str.contains('MERCADO PAGO', case=False)
    bloques_ventas['VENTAS_MP'] = df_ventas[mask_mp].copy()

    # 2. BBVA (Si contiene 'BBVA')
    mask_bbva = df_ventas['bancos_cobro'].str.contains('BBVA', case=False)
    bloques_ventas['VENTAS_BBVA'] = df_ventas[mask_bbva].copy()

    # 3. SCOOTERZONE (Si contiene 'SCOOTERZONE')
    mask_sz = df_ventas['bancos_cobro'].str.contains('SCOOTERZONE', case=False)
    bloques_ventas['VENTAS_SCOOTERZONE'] = df_ventas[mask_sz].copy()

    # 4. Físico / Efectivo (Si contiene 'Físico')
    mask_fisico = df_ventas['bancos_cobro'].str.contains('Físico', case=False)
    bloques_ventas['VENTAS_FISICO'] = df_ventas[mask_fisico].copy()

    # 5. SIN BANCO (Los que dicen SIN_ESPECIFICAR o métodos raros que no encajan en los 4 principales)
    # Por ejemplo, Aliantextil o Lance, si no están mapeados a bancos
    mask_sin_banco = ~(mask_mp | mask_bbva | mask_sz | mask_fisico)
    bloques_ventas['VENTAS_SIN_BANCO'] = df_ventas[mask_sin_banco].copy()

    # OJO: Si una venta dice "Físico, BBVA", se copiará en AMBOS bloques.
    # Esto es común en sistemas de punto de venta (Split Payment).
    # La conciliación matemática (Análisis) deberá tener esto en cuenta.

    return bloques_ventas

if __name__ == '__main__':
    ventas_separadas = limpiar_modulo_ventas('CONCILIACION FEBRERO OK - copia.xlsm')
    print("\nResumen final del Módulo Ventas:")
    for key, df in ventas_separadas.items():
        print(f"- {key}: {len(df)} registros")
        if len(df) > 0:
            # Mostrar los métodos reales que cayeron en este bloque para verificar
            print(f"  Ejemplos de cobro: {df['bancos_cobro'].unique()[:3].tolist()}")
        print("---")
