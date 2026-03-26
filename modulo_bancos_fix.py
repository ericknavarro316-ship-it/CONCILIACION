import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_mp(xls):
    print("Procesando Detalle Mercado Pago (MP)...")
    df_raw = pd.read_excel(xls, sheet_name='MP', header=None)
    fila_encabezado_mp = -1
    for i, fila in df_raw.iterrows():
        # Busca el nombre exacto del encabezado de MercadoPago (como en el archivo test)
        if fila.astype(str).str.contains('Número de la operación', case=False, na=False).any() or \
           fila.astype(str).str.contains('Operación relacionada', case=False, na=False).any() or \
           fila.astype(str).str.contains('Número del movimiento', case=False, na=False).any():
            fila_encabezado_mp = i
            break

    if fila_encabezado_mp != -1:
        df_mp = pd.read_excel(xls, sheet_name='MP', header=fila_encabezado_mp)

        # Opciones comunes para ID único de Mercado Pago en exportaciones:
        col_id = next((col for col in ['Número del cargo', 'Número de la operación', 'Número del movimiento', 'N° de factura fiscal'] if col in df_mp.columns), None)

        if col_id:
            antes = len(df_mp)
            df_mp = df_mp.drop_duplicates(subset=[col_id])
            df_mp = df_mp.dropna(subset=[col_id])
            despues = len(df_mp)
            print(f"  ✅ MP detalle limpio: Usando columna '{col_id}'. Eliminados {antes-despues} duplicados/vacíos. Quedan {despues}.")
        else:
            print(f"  ⚠️ No se encontró columna ID válida para quitar duplicados. Columnas son: {df_mp.columns.tolist()}")

if __name__ == '__main__':
    xls = pd.ExcelFile('CONCILIACION FEBRERO OK - copia.xlsm')
    limpiar_mp(xls)
