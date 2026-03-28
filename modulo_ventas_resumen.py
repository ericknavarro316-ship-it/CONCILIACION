import pandas as pd
import warnings
import io

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_reporte_ventas_csv(archivo_csv):
    """
    Procesa el archivo 'reporte_ventas.csv'.
    El problema de este archivo es que exporta con ';' como separador de columnas.
    Los montos monetarios contienen '$' y comas ',' de miles.
    Excel al abrirlo erróneamente con ',' divide las celdas en varias columnas.
    Esta función usa pandas con sep=';' para ignorar la coma y leer correctamente la tabla.
    """
    print(f"Cargando Reporte de Ventas (CSV)...")

    # Intentamos leerlo con el separador ;
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si es un archivo tipo buffer (como en Streamlit), regresamos al inicio
        if hasattr(archivo_csv, 'seek'):
            archivo_csv.seek(0)
        df = pd.read_csv(archivo_csv, sep=';', encoding='latin1')

    # Limpiamos los nombres de las columnas
    df.columns = df.columns.str.lower().str.strip()

    # Limpiar columnas de moneda (tienen $ y comas de miles)
    columnas_moneda = [
        'total (antes descuento)', 'efectivo', 'tarjeta crédito',
        'tarjeta débito', 'transferencia', 'deposito', 'total real'
    ]

    for col in columnas_moneda:
        if col in df.columns:
            # Reemplazar $, comas y convertir a float
            df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            # Manejar posibles espacios en blanco extra
            df[col] = df[col].str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Asegurarnos de que el ID Venta y fechas estén bien
    if 'id venta' in df.columns:
        df['id venta'] = df['id venta'].astype(str).str.replace(r'\.0$', '', regex=True)

    if 'fecha venta' in df.columns:
        df['fecha venta'] = pd.to_datetime(df['fecha venta'], errors='coerce')

    # Agruparlo en un diccionario para la BD
    return {'VENTAS_RESUMEN': df}

if __name__ == '__main__':
    # Datos de prueba simulando el archivo del usuario
    csv_data = '''ID Venta;"Fecha Venta";"Total (antes descuento)";Estado;"Forma pago";Efectivo;"Tarjeta Crédito";"Tarjeta Débito";Transferencia;Deposito;Cliente;"Tipo cliente";Vendedor;Sucursal;"Total Real"
28122;"2026-03-27 13:28:24";$6,999.00;activa;efectivo;$7,000.00;$0.00;$0.00;$0.00;$0.00;"Maria Lorena Aceves Hernandez";Distribuidor;"ROCIO VIRIDIANA RODRIGUEZ CASTAÑON";"SUC OBREGON";$7,000.00
28121;"2026-03-27 13:07:54";$13,999.00;activa;tarjeta_credito;$0.00;$13,999.00;$0.00;$0.00;$0.00;$0.00;"JENIFER CUITACO HERNANDEZ";cliente;"JESSICA GIOVANNA RODRIGUEZ CONTRERAS";"SUC VALLARTA";$13,999.00
28120;"2026-03-27 12:57:06";$1,000.00;activa;efectivo;$1,000.00;$0.00;$0.00;$0.00;$0.00;"JUAN MAYA SIMON";cliente;"JUAN ALBERTO MARTELL GARCIA";"ALMACEN COLON";$1,000.00'''

    import io
    df_res = limpiar_reporte_ventas_csv(io.StringIO(csv_data))
    print("Resumen de ventas:")
    print(df_res['VENTAS_RESUMEN'].head())
    print("\nTipos de datos:")
    print(df_res['VENTAS_RESUMEN'].dtypes)
