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

    # 2. Leer Detalle de Mercado Pago (AUX_MP_DETALLE)
    df_mp_detalle = get_df_from_sql("AUX_MP_DETALLE")
    if df_mp_detalle.empty:
         return {"error": "No se encontró el detalle operativo de Mercado Pago (AUX_MP_DETALLE)."}

    # La columna a cruzar en el banco es 'Operación relacionada' (case-insensitive search just in case)
    col_id_mp = next((col for col in df_mp_detalle.columns if col.strip().lower() == 'operación relacionada'), None)

    if not col_id_mp:
         # Fallback si no está "Operación relacionada"
         col_id_mp = next((col for col in ['Número del cargo', 'Número de la operación', 'Número del movimiento'] if col in df_mp_detalle.columns), None)

    if not col_id_mp:
         return {"error": f"No se encontró la columna de 'Operación relacionada' o ID en AUX_MP_DETALLE. Columnas actuales: {df_mp_detalle.columns.tolist()}"}

    # Asegurar columna de sucursal ban en ventas
    if 'sucursal ban' not in df_ventas.columns and 'sucursal_ban' not in df_ventas.columns:
        df_ventas['sucursal_ban'] = ''
    col_sucursal = 'sucursal_ban' if 'sucursal_ban' in df_ventas.columns else 'sucursal ban'

    # Asegurar columna ID VENTA en banco
    if 'ID VENTA' not in df_mp_detalle.columns and 'ID_VENTA' not in df_mp_detalle.columns:
        df_mp_detalle['ID VENTA'] = None
    col_id_venta_banco = 'ID VENTA' if 'ID VENTA' in df_mp_detalle.columns else 'ID_VENTA'

    # Asegurarnos de que las columnas de cruce sean strings sin espacios (para evitar falsos negativos)
    df_ventas['numero_transaccion'] = df_ventas['numero_transaccion'].astype(str).str.strip()
    df_mp_detalle[col_id_mp] = df_mp_detalle[col_id_mp].astype(str).str.strip()

    match_count = 0

    import re

    for idx, venta in df_ventas.iterrows():
        if venta['estado_cruce'] == 'OK vs MP':
            continue

        transaccion = str(venta['numero_transaccion']).strip()
        id_venta = venta['id_venta']

        if transaccion == 'nan' or transaccion == 'None' or not transaccion:
            df_ventas.at[idx, col_sucursal] = 'SIN REFERENCIA VALIDA'
            continue

        # Extraer todas las secuencias de 10 a 12 dígitos, ya que puede venir "123456789012 - 987654321098"
        transacciones_lista = re.findall(r'\b\d{10,12}\b', transaccion)

        if not transacciones_lista:
             df_ventas.at[idx, col_sucursal] = 'SIN REFERENCIA VALIDA'
             continue

        match_encontrado_venta = False

        for t_id in transacciones_lista:
            # Buscar este ID de transacción en la base de MP
            mask_mp = df_mp_detalle[col_id_mp] == t_id
            if mask_mp.any():
                # Encontramos la transacción en el banco de MP
                # Como puede haber múltiples match por fila si hay duplicados, actualizamos todos
                df_mp_detalle.loc[mask_mp, col_id_venta_banco] = id_venta

                match_encontrado_venta = True
                # Eliminado el break para que continúe buscando y marcando todas las transacciones de esta venta

        if match_encontrado_venta:
            df_ventas.at[idx, 'estado_cruce'] = 'OK vs MP'
            df_ventas.at[idx, col_sucursal] = 'MP'
            # Guardamos la referencia que coincidió
            df_ventas.at[idx, 'referencia_cruce'] = ', '.join(transacciones_lista)
            match_count += 1
        else:
            df_ventas.at[idx, col_sucursal] = 'NO ENCONTRADO EN MP'

    # 4. Guardar resultados en SQL
    save_df_to_sql(df_ventas, "VENTAS_MP_CRUZADO")
    # Es muy importante guardar con el nombre original AUX_MP_DETALLE para que se mantenga en el UI o como se espere
    # Revisando el app.py, se espera "AUX_MP_DETALLE"
    save_df_to_sql(df_mp_detalle, "AUX_MP_DETALLE")

    return {
        "success": True,
        "matches": match_count,
        "sample": df_ventas[df_ventas['estado_cruce'] == 'OK vs MP'].head()
    }
