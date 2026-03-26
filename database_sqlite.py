import sqlite3
import pandas as pd
import os

DB_FILE = "conciliacion_data.db"

def init_db():
    """Inicializa la base de datos si no existe."""
    conn = sqlite3.connect(DB_FILE)
    # Por ahora no necesitamos CREATE TABLE explícitos complejos
    # porque pandas.to_sql crea las tablas automáticamente.
    conn.close()

def save_df_to_sql(df, table_name):
    """Guarda un DataFrame de Pandas directamente como una tabla SQL"""
    if df is None or df.empty:
        return

    conn = sqlite3.connect(DB_FILE)
    # Reemplazamos la tabla si ya existe para cargar la info fresca del mes
    # (En el futuro se puede usar if_exists='append' para un histórico real)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
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
