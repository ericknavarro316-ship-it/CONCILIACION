import sqlite3
import pandas as pd
import os
import numpy as np

DB_FILE = "conciliacion_data.db"

def init_db():
    """Inicializa la base de datos si no existe."""
    conn = sqlite3.connect(DB_FILE)
    conn.close()

def save_df_to_sql(df, table_name):
    """Guarda un DataFrame de Pandas directamente como una tabla SQL, evitando errores de desbordamiento entero."""
    if df is None or df.empty:
        return

    df_copy = df.copy()

    # SQLite tiene un límite de enteros de 8 bytes (hasta 9,223,372,036,854,775,807).
    # Las transacciones de bancos/MercadoPago suelen tener IDs gigantes que rompen este límite.
    # Solución: Convertir los enteros largos (y cualquier columna sospechosa) a texto.

    for col in df_copy.columns:
        # Si la columna es un objeto (string/mixed), nos aseguramos de que no haya enteros gigantes escondidos
        if df_copy[col].dtype == object or str(df_copy[col].dtype).startswith('int'):
             # Verificamos si hay algún valor numérico gigante (mayor a 10 dígitos)
             try:
                 # Convertimos a string de manera segura
                 df_copy[col] = df_copy[col].astype(str)
                 # Reemplazamos los 'nan' (strings) y 'None' con nulos reales de pandas
                 df_copy[col] = df_copy[col].replace(['nan', 'None', '<NA>'], np.nan)
             except Exception:
                 pass

    # Verificar si la tabla ya existe para implementar lógica de "append" con "deduplicación"
    # Así permitimos que el usuario suba archivos con nuevos meses sin perder los anteriores.
    df_existente = get_df_from_sql(table_name)

    if not df_existente.empty:
        # Alineamos las columnas en caso de que el nuevo archivo traiga menos o más columnas
        df_combinado = pd.concat([df_existente, df_copy], ignore_index=True)

        # Eliminamos duplicados exactos en toda la fila para no triplicar
        # meses si suben el mismo archivo varias veces.
        # Si la tabla tiene un ID único fuerte (ej. "Número del cargo" en MP_DETALLE),
        # podríamos usar subset=[ID], pero en bancos tradicionales (BBVA) a veces no hay,
        # así que validamos toda la fila.
        antes = len(df_combinado)

        # Columnas a considerar para deduplicación (evitar usar index ocultos si los hubiera)
        cols_dedup = df_combinado.columns.tolist()
        df_combinado = df_combinado.drop_duplicates(subset=cols_dedup, keep='last')

        print(f"[{table_name}] Base actual: {len(df_existente)} + Nuevo: {len(df_copy)} -> Combinado y Deduplicado: {len(df_combinado)} (Duplicados omitidos: {antes - len(df_combinado)})")
        df_final_to_save = df_combinado
    else:
        df_final_to_save = df_copy
        print(f"[{table_name}] Tabla nueva creada con {len(df_final_to_save)} registros.")

    conn = sqlite3.connect(DB_FILE)
    # Siempre usamos replace, pero sobre el df_final_to_save que ya trae lo viejo + lo nuevo deduplicado
    df_final_to_save.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

def get_df_from_sql(table_name):
    """Recupera una tabla de SQL como un DataFrame de Pandas"""
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        conn.close()
        return df
    except sqlite3.OperationalError:
        # La tabla no existe aún
        conn.close()
        return pd.DataFrame()

def get_all_tables():
    """Retorna una lista con los nombres de todas las tablas en la BD"""
    if not os.path.exists(DB_FILE):
        return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables
