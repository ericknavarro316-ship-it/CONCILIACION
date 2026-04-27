import sqlite3
import pandas as pd

conn = sqlite3.connect("conciliacion_data.db")

df_bbva = pd.DataFrame({'id_venta': [1], 'estado_cruce': ['PENDIENTE'], 'precio_real': [100.0], 'fecha': ['2023-01-01'], 'bancos_cobro': ['BBVA']})
df_bbva.to_sql('VENTAS_BBVA', conn, if_exists='replace', index=False)

df_mp = pd.DataFrame({'id_venta': [2], 'estado_cruce': ['PENDIENTE'], 'precio_real': [200.0], 'fecha': ['2023-01-02'], 'numero_transaccion': ['123'], 'bancos_cobro': ['MP']})
df_mp.to_sql('VENTAS_MP_CRUZADO', conn, if_exists='replace', index=False)
df_mp.to_sql('VENTAS_MP', conn, if_exists='replace', index=False)

conn.close()
