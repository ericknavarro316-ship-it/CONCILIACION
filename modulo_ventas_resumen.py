import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

def limpiar_reporte_series_csv(archivo_csv):
    """
    Procesa el archivo CSV de Series (reemplazando el antiguo reporte de resumen).
    Este archivo contiene el mapeo entre ID Venta, Producto y su Número de Serie específico.
    Usa sep=';' para ignorar comas de datos y leer correctamente la tabla.
    """
    print(f"Cargando Reporte de Series (CSV)...")

    # Intentamos leerlo con el separador ;
    try:
        df = pd.read_csv(archivo_csv, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # Si es un archivo tipo buffer (como en Streamlit), regresamos al inicio
        if hasattr(archivo_csv, 'seek'):
            archivo_csv.seek(0)
        df = pd.read_csv(archivo_csv, sep=';', encoding='latin1')

    # Limpiamos los nombres de las columnas para hacer un merge más fácil después
    df.columns = df.columns.str.lower().str.strip()

    # Asegurarnos de que el ID Venta esté limpio (sin decimales .0)
    if 'id venta' in df.columns:
        df['id venta'] = df['id venta'].astype(str).str.replace(r'\.0$', '', regex=True)

    # Renombramos columnas clave a nombres estándar para facilitar el cruce
    renames = {
        'id venta': 'ID VENTA',
        'producto': 'PRODUCTO',
        'número de serie': 'NUMERO DE SERIE',
        'numero de serie': 'NUMERO DE SERIE'
    }

    # Aplicar renombres que existan
    df = df.rename(columns={k: v for k, v in renames.items() if k in df.columns})

    # Agruparlo en un diccionario para la BD
    return {'VENTAS_SERIES': df}

if __name__ == '__main__':
    # Datos de prueba proporcionados por el usuario
    csv_data = '''Id serie;"Número de Serie";Producto;"Codigo producto";Estatus;"Número de Factura";"Fecha Venta";"ID Venta";Sucursal;"Fecha Registro Serie";"Fecha creacion"
51044;HG5KTCC15R1016626;"V4 NARANJA";1bb9d710;inactivo;;"2026-02-20 12:32:00";26951;"EKAR OLIMPICO";2026-02-20;"2026-02-20 12:32:00"
51038;HWM258BK05W000112;"BK05 BLANCO";b5b49b0e;inactivo;;"2026-02-19 15:26:01";26926;"SUC JUAREZ";2026-02-19;"2026-02-19 15:26:02"
50114;HWM25E9TB0001245;"E9T NEGRO";8bdacd4e;inactivo;;"2026-02-06 13:29:20";26528;"CEDIS 2";2026-02-06;"2026-02-06 13:29:21"'''

    import io
    df_res = limpiar_reporte_series_csv(io.StringIO(csv_data))
    print("Reporte de Series:")
    print(df_res['VENTAS_SERIES'].head())
    print("\nTipos de datos:")
    print(df_res['VENTAS_SERIES'].dtypes)
