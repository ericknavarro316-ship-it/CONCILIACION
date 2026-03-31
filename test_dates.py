import pandas as pd
import sqlite3

# Caso 1: String guardado por pdf_reader (viejo comportamiento "DD/MM/YYYY")
df_old = pd.DataFrame({'FECHA': ['03/02/2026', '04/02/2026']})

# Simulamos cómo app.py lo lee
df_app = df_old.copy()
df_app['FECHA_DT_TMP'] = pd.to_datetime(df_app['FECHA'], dayfirst=True, errors='coerce')
print("--- Caso 1: String viejo (DD/MM/YYYY) leído con dayfirst=True ---")
print(df_app)
print()

# Caso 2: Datetime real guardado por pdf_reader (nuevo comportamiento)
df_new = pd.DataFrame({'FECHA': pd.to_datetime(['03/02/2026', '04/02/2026'], format='%d/%m/%Y')})
conn = sqlite3.connect(':memory:')
df_new.to_sql('test', conn, index=False)
df_from_sql = pd.read_sql_query("SELECT * FROM test", conn)

print("--- Caso 2: Datetime real desde SQL ---")
print(df_from_sql)

# Simulamos app.py
df_app2 = df_from_sql.copy()
df_app2['FECHA_DT_TMP'] = pd.to_datetime(df_app2['FECHA'], dayfirst=True, errors='coerce')
print("\n--- Caso 2 procesado por app.py ---")
print(df_app2)
