import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_modulo_ventas_v2(ruta_archivo):
    """
    Procesa exclusivamente el Módulo VENTAS con las reglas exactas del usuario.
    Si dice MERCADO PAGO, BBVA o SCOOTERZONE, va a su bloque.
    Cualquier OTRA palabra (Aliantextil, Lance, Físico) se considera EFECTIVO.
    Si está literalmente VACÍA, es SIN BANCO.
    """
    xls = pd.ExcelFile(ruta_archivo)
    hojas_disponibles = xls.sheet_names

    # Buscar la hoja de ventas o tomar la primera si es archivo individual
    hoja_ventas = next((h for h in hojas_disponibles if 'VENTA' in h.upper() or 'NOTA' in h.upper()), None)
    if not hoja_ventas and len(hojas_disponibles) > 0:
         hoja_ventas = hojas_disponibles[0]

    if not hoja_ventas:
         return {}

    df_ventas = pd.read_excel(xls, sheet_name=hoja_ventas)
    df_ventas.columns = df_ventas.columns.str.lower().str.strip()

    # Asegurar que la columna 'bancos_cobro' exista
    if 'bancos_cobro' not in df_ventas.columns:
         # Intentar buscar alguna columna similar
         col_alternativa = next((c for c in df_ventas.columns if 'banco' in c or 'cobro' in c or 'metodo' in c), None)
         if col_alternativa:
              df_ventas = df_ventas.rename(columns={col_alternativa: 'bancos_cobro'})
         else:
              df_ventas['bancos_cobro'] = 'SIN_ESPECIFICAR'

    # Rellenar vacíos con palabra clave
    df_ventas['bancos_cobro'] = df_ventas['bancos_cobro'].fillna('SIN_ESPECIFICAR')

    bloques_ventas = {}

    # 1. MERCADO PAGO
    mask_mp = df_ventas['bancos_cobro'].str.contains('MERCADO PAGO', case=False)
    bloques_ventas['VENTAS_MP'] = df_ventas[mask_mp].copy()

    # 2. BBVA
    mask_bbva = df_ventas['bancos_cobro'].str.contains('BBVA', case=False)
    bloques_ventas['VENTAS_BBVA'] = df_ventas[mask_bbva].copy()

    # 3. SCOOTERZONE
    mask_sz = df_ventas['bancos_cobro'].str.contains('SCOOTERZONE', case=False)
    bloques_ventas['VENTAS_SCOOTERZONE'] = df_ventas[mask_sz].copy()

    # 5. SIN BANCO (Solo si no tiene leyenda o si es la palabra clave que pusimos)
    mask_sin_banco = df_ventas['bancos_cobro'] == 'SIN_ESPECIFICAR'
    bloques_ventas['VENTAS_SIN_BANCO'] = df_ventas[mask_sin_banco].copy()

    # 4. EFECTIVO / FÍSICO
    # Todo lo que no sea SIN_ESPECIFICAR, y que no caiga en las máscaras anteriores (o que comparta)
    # Ejemplo: "Lance" no es MP, BBVA, SZ ni SIN_ESPECIFICAR -> va a EFECTIVO
    # Ejemplo: "Físico, BBVA" -> ya fue a BBVA, pero la parte "Físico" significa Efectivo.
    mask_efectivo = df_ventas['bancos_cobro'].str.contains('Físico', case=False) | \
                    (~(mask_mp | mask_bbva | mask_sz | mask_sin_banco))
    bloques_ventas['VENTAS_EFECTIVO'] = df_ventas[mask_efectivo].copy()

    return bloques_ventas

if __name__ == '__main__':
    ventas_separadas = limpiar_modulo_ventas_v2('CONCILIACION FEBRERO OK - copia.xlsm')
    print("\nResumen final del Módulo Ventas (Corregido):")
    for key, df in ventas_separadas.items():
        print(f"- {key}: {len(df)} registros")
        if len(df) > 0:
            print(f"  Ejemplos de cobro: {df['bancos_cobro'].unique()[:5].tolist()}")
        print("---")
