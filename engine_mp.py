import pandas as pd
from database_sqlite import get_df_from_sql, save_df_to_sql

def run_mp_crosscheck():
    """Ejecuta el cruce de Ventas Mercado Pago leyendo y escribiendo en SQL."""

    # 1. Leer Ventas MP
    df_ventas = get_df_from_sql("VENTAS_MP")
    if df_ventas.empty:
        return {"error": "No hay tabla VENTAS_MP en la base de datos."}

    # Inicializar columnas de cruce si no existen
    if 'origen_split' not in df_ventas.columns:
        df_ventas['origen_split'] = df_ventas['bancos_cobro'].apply(
            lambda x: f"PAGO COMBINADO: {x}" if ',' in str(x) else "PAGO SENCILLO: MP"
        )
    df_ventas['estado_cruce'] = 'PENDIENTE'
    df_ventas['referencia_cruce'] = None

    # 2. Leer Detalle de Mercado Pago (MP_DETALLE)
    df_mp_detalle = get_df_from_sql("BANCO_MP_DETALLE")
    if df_mp_detalle.empty:
         return {"error": "No se encontró el detalle operativo de Mercado Pago (BANCO_MP_DETALLE)."}

    # La columna 'numero_transaccion' en ventas suele cruzar con 'Número del cargo' o 'Número de la operación' en MP
    col_id_mp = next((col for col in ['Número del cargo', 'Número de la operación', 'Número del movimiento'] if col in df_mp_detalle.columns), None)

    if not col_id_mp:
         return {"error": f"No se encontró la columna de ID en MP_DETALLE. Columnas actuales: {df_mp_detalle.columns.tolist()}"}

    # Asegurarnos de que las columnas de cruce sean strings sin espacios (para evitar falsos negativos)
    df_ventas['numero_transaccion'] = df_ventas['numero_transaccion'].astype(str).str.strip()
    df_mp_detalle[col_id_mp] = df_mp_detalle[col_id_mp].astype(str).str.strip()

    # Columna para registrar el match en el banco
    if 'ID_VENTA_CRUCE' not in df_mp_detalle.columns:
        df_mp_detalle['ID_VENTA_CRUCE'] = None

    match_count = 0
    match_por_transaccion = 0
    id_venta_a_ref = {}

    # 3. CRUCE: Mercado Pago requiere coincidencia EXACTA de Número de Transacción
    # A diferencia de BBVA, no sumamos ni usamos tolerancias de monto como prioridad 1,
    # la prioridad 1 es el ID de la transacción.

    # Agrupamos por id_venta solo para iterar (aunque en MP la clave es numero_transaccion)
    # Una venta puede tener un "144553492726 - 144553543188" (Múltiples transacciones)

    for idx, venta in df_ventas.iterrows():
        if venta['estado_cruce'] != 'PENDIENTE':
            continue

        transaccion = str(venta['numero_transaccion']).strip()
        id_venta = venta['id_venta']

        if transaccion == 'nan' or transaccion == 'None' or not transaccion:
            continue

        # Limpiar transacciones múltiples si las hay (ej. "123 - 456")
        transacciones_lista = [t.strip() for t in transaccion.replace(' - ', ',').split(',')]

        match_encontrado_venta = False

        for t_id in transacciones_lista:
            # Buscar este ID de transacción en la base de MP
            mask_mp = df_mp_detalle[col_id_mp] == t_id
            if mask_mp.any():
                # Encontramos la transacción en el banco de MP
                idx_mp = df_mp_detalle[mask_mp].index[0]

                # Marcar en banco
                df_mp_detalle.at[idx_mp, 'ID_VENTA_CRUCE'] = id_venta

                # Guardar correspondencia
                id_venta_a_ref[id_venta] = t_id

                match_encontrado_venta = True
                match_por_transaccion += 1
                break # Con encontrar uno de los recibos, damos la venta como conciliada operativamente

        if match_encontrado_venta:
            df_ventas.at[idx, 'estado_cruce'] = 'OK vs MP'
            df_ventas.at[idx, 'referencia_cruce'] = id_venta_a_ref[id_venta]
            match_count += 1

    # 4. Guardar resultados en SQL
    save_df_to_sql(df_ventas, "VENTAS_MP_CRUZADO")
    save_df_to_sql(df_mp_detalle, "BANCO_MP_DETALLE_CRUZADO")

    return {
        "success": True,
        "matches": match_count,
        "sample": df_ventas[df_ventas['estado_cruce'] == 'OK vs MP'].head()
    }
