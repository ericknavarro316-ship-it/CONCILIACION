import sqlite3
import pandas as pd
import os
import numpy as np

DB_FILE = "conciliacion_data.db"

def init_db():
    """Inicializa la base de datos si no existe."""
    conn = sqlite3.connect(DB_FILE)
    conn.close()

def update_table_from_df(df, table_name):
    """Sobrescribe completamente una tabla con un nuevo DataFrame (usado para edición manual)."""
    if df is None or df.empty:
        return False

    df_copy = df.copy()

    # Desduplicar nombres de columnas para evitar el error 'DataFrame' object has no attribute 'dtype'
    seen = {}
    new_cols = []
    for c in df_copy.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df_copy.columns = new_cols

    for col in df_copy.columns:
        if str(df_copy[col].dtype).startswith('datetime'):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df_copy[col].dtype == object or str(df_copy[col].dtype).startswith('int'):
             df_copy[col] = df_copy[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, pd.Timestamp) else x)
             try:
                 df_copy[col] = df_copy[col].astype(str)
                 df_copy[col] = df_copy[col].replace(['nan', 'None', '<NA>'], np.nan)
             except Exception:
                 pass

    try:
        conn = sqlite3.connect(DB_FILE)
        df_copy.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.close()
        return True
    except Exception as e:
        print(f"Error al actualizar la tabla {table_name}: {e}")
        return False

def save_df_to_sql(df, table_name):
    """Guarda un DataFrame de Pandas directamente como una tabla SQL, evitando errores de desbordamiento entero."""
    if df is None or df.empty:
        return

    df_copy = df.copy()

    # Desduplicar nombres de columnas para evitar el error 'DataFrame' object has no attribute 'dtype'
    seen = {}
    new_cols = []
    for c in df_copy.columns:
        if c in seen:
            seen[c] += 1
            new_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            new_cols.append(c)
    df_copy.columns = new_cols

    # SQLite tiene un límite de enteros de 8 bytes (hasta 9,223,372,036,854,775,807).
    # Las transacciones de bancos/MercadoPago suelen tener IDs gigantes que rompen este límite.
    # Solución: Convertir los enteros largos (y cualquier columna sospechosa) a texto.

    for col in df_copy.columns:
        # Prevenir "Error binding parameter: type 'Timestamp' is not supported" en columnas mixtas (object)
        if str(df_copy[col].dtype).startswith('datetime'):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S')

        # Si la columna es un objeto (string/mixed) o int, nos aseguramos de que no haya enteros gigantes escondidos
        elif df_copy[col].dtype == object or str(df_copy[col].dtype).startswith('int'):
             # Convertir valores de Timestamp puros a string antes de convertirlos a string global
             # (Si la columna es object pero contiene fechas pandas)
             df_copy[col] = df_copy[col].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S') if isinstance(x, pd.Timestamp) else x)
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

    # Primero verificamos si la tabla existe realmente consultando sqlite_master
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    existe = cursor.fetchone()

    if not existe:
        conn.close()
        return pd.DataFrame()

    try:
        df = pd.read_sql_query(f"SELECT * FROM '{table_name}'", conn)
        conn.close()
        return df
    except Exception as e:
        # Fallback genérico para atrapar pd.errors.DatabaseError u otros errores de Pandas
        print(f"Error al recuperar tabla {table_name}: {e}")
        conn.close()
        return pd.DataFrame()

def get_filtered_df_from_sql(table_name, search_text="", col_fecha=None, mes_sel="Todos", fecha_desde=None, fecha_hasta=None):
    """
    Recupera datos de SQL aplicando filtros de fecha y texto en la base de datos.
    Esto permite que la BD haga el trabajo pesado y reduzca el uso de RAM.
    """
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    if not cursor.fetchone():
        conn.close()
        return pd.DataFrame()

    try:
        # Extraer nombres de columnas reales de la tabla
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = [row[1] for row in cursor.fetchall()]

        if not columns:
            conn.close()
            return pd.DataFrame()

        # Asegurarse de que el col_fecha coincida en mayuscula/minuscula
        real_col_fecha = None
        if col_fecha:
            for c in columns:
                if c.lower() == col_fecha.lower():
                    real_col_fecha = c
                    break

        where_clauses = []
        params = []

        # 1. Filtro de Texto (Buscar en todas las columnas)
        if search_text:
            search_text_clean = search_text.replace("'", "''") # Basic sanitization
            text_conditions = []
            for col in columns:
                text_conditions.append(f"LOWER(CAST(\"{col}\" AS TEXT)) LIKE '%{search_text_clean.lower()}%'")
            where_clauses.append(f"({' OR '.join(text_conditions)})")

        # 2. Filtros de Fecha
        # Las fechas en SQLite suelen guardarse como 'YYYY-MM-DD HH:MM:SS' por save_df_to_sql
        # Pero podrían estar como 'YYYY-MM-DD' o cadenas mixtas si hubo errores de parseo
        if real_col_fecha:
            if mes_sel != "Todos":
                # Asumimos que empieza con YYYY-MM
                where_clauses.append(f"CAST(\"{real_col_fecha}\" AS TEXT) LIKE ?")
                params.append(f"{mes_sel}%")

            if fecha_desde:
                where_clauses.append(f"CAST(\"{real_col_fecha}\" AS TEXT) >= ?")
                params.append(fecha_desde.strftime('%Y-%m-%d'))

            if fecha_hasta:
                where_clauses.append(f"CAST(\"{real_col_fecha}\" AS TEXT) <= ?")
                params.append(fecha_hasta.strftime('%Y-%m-%d 23:59:59'))

        query = f"SELECT * FROM '{table_name}'"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        print(f"Error al recuperar tabla filtrada {table_name}: {e}")
        conn.close()
        return pd.DataFrame()

def drop_table_from_sql(table_name):
    """Elimina una tabla específica de la base de datos."""
    if not os.path.exists(DB_FILE):
        return False

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al eliminar la tabla {table_name}: {e}")
        return False

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
