import pandas as pd
from database_sqlite import get_df_from_sql, save_df_to_sql, get_all_tables, update_table_from_df, drop_table_from_sql

def run_bbva_crosscheck():
    """Ejecuta el cruce de Ventas BBVA contra Bancos BBVA leyendo y escribiendo en SQL."""

    # 1. Leer Ventas BBVA
    df_ventas = get_df_from_sql("VENTAS_BBVA")
    if df_ventas.empty:
        return {"error": "No hay tabla VENTAS_BBVA en la base de datos."}

    # Inicializar columnas de cruce
    if 'origen_split' not in df_ventas.columns:
        df_ventas['origen_split'] = df_ventas['bancos_cobro'].apply(
            lambda x: f"PAGO COMBINADO: {x}" if ',' in str(x) else "PAGO SENCILLO: BBVA"
        )
    df_ventas['cuenta_bancaria_cruce'] = None
    df_ventas['estado_cruce'] = 'PENDIENTE'

    # 2. Leer Cuentas Bancarias BBVA
    tablas = get_all_tables()
    cuentas_bbva = {t: get_df_from_sql(t) for t in tablas if t.startswith("BANCO_") and (
        t.replace("BANCO_", "").isdigit() or
        t.startswith("BANCO_BBVA_EST_") or
        t.startswith("BANCO_BBVA_DET_")
    )}

    if not cuentas_bbva:
         return {"error": "No se encontraron tablas de cuentas bancarias (BANCO_XXXXX o BANCO_BBVA_...)."}

    # Asegurar fechas en bancos
    for cuenta_nombre, df_banco in cuentas_bbva.items():
        if 'FECHA' in df_banco.columns:
            # Intentar convertir formato ISO primero, luego con fallback
            df_banco['FECHA_DT'] = pd.to_datetime(df_banco['FECHA'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            df_banco['FECHA_DT'] = df_banco['FECHA_DT'].fillna(pd.to_datetime(df_banco['FECHA'], format='mixed', dayfirst=True, errors='coerce'))

    # 3. Agrupar Ventas por ID
    df_ventas['precio_real'] = pd.to_numeric(df_ventas['precio_real'], errors='coerce')

    # Manejar fecha en ventas (probablemente 'fecha' o 'FECHA')
    col_fecha_venta = 'fecha' if 'fecha' in df_ventas.columns else 'FECHA' if 'FECHA' in df_ventas.columns else None
    if col_fecha_venta:
        df_ventas['FECHA_DT'] = pd.to_datetime(df_ventas[col_fecha_venta], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df_ventas['FECHA_DT'] = df_ventas['FECHA_DT'].fillna(pd.to_datetime(df_ventas[col_fecha_venta], format='mixed', dayfirst=True, errors='coerce'))
    else:
        df_ventas['FECHA_DT'] = pd.NaT

    ventas_agrupadas = df_ventas.groupby('id_venta', as_index=False).agg({
        'precio_real': 'sum',
        'uuid': 'first',
        'FECHA_DT': 'first'
    })

    match_count = 0
    id_venta_a_cuenta = {}

    # 4. Cruce con tolerancias y fechas
    for _, grupo in ventas_agrupadas.iterrows():
        id_venta = grupo['id_venta']
        total_a_cobrar = grupo['precio_real']
        fecha_venta = grupo['FECHA_DT']

        if pd.isna(total_a_cobrar) or total_a_cobrar <= 0:
            continue

        tolerancia = 1.0 if total_a_cobrar <= 50000 else 50.0

        # Recopilar todos los candidatos viables
        candidatos = []

        for cuenta_nombre, df_banco in cuentas_bbva.items():
            if 'ABONO' not in df_banco.columns:
                continue

            if 'ID_VENTA_CRUCE' not in df_banco.columns:
                df_banco['ID_VENTA_CRUCE'] = None

            # Asegurar numérico
            df_banco['ABONO'] = pd.to_numeric(df_banco['ABONO'], errors='coerce')

            abonos_libres = df_banco[pd.isna(df_banco['ID_VENTA_CRUCE']) & pd.notna(df_banco['ABONO'])]

            # Buscar candidatos matemáticamente viables
            for idx_banco, abono_banco in abonos_libres.iterrows():
                abono_val = abono_banco['ABONO']
                diferencia = abs(abono_val - total_a_cobrar)

                if diferencia <= tolerancia:
                    fecha_banco = abono_banco.get('FECHA_DT', pd.NaT)

                    candidato = {
                        'cuenta': cuenta_nombre,
                        'idx': idx_banco,
                        'diff_monto': diferencia,
                        'fecha_banco': fecha_banco
                    }

                    # Filtro de mes si tenemos ambas fechas
                    if pd.notna(fecha_venta) and pd.notna(fecha_banco):
                        if fecha_venta.year == fecha_banco.year and fecha_venta.month == fecha_banco.month:
                            # Mismo mes y año -> Calcular diferencia en días
                            candidato['diff_dias'] = abs((fecha_banco - fecha_venta).days)
                            candidatos.append(candidato)
                        # Si no es del mismo mes, lo ignoramos de acuerdo a la regla solicitada
                    else:
                        # Si alguna fecha es NaT, lo permitimos pero lo mandamos al final de la prioridad
                        candidato['diff_dias'] = 9999
                        candidatos.append(candidato)

        # Si encontramos candidatos, elegir el mejor
        if candidatos:
            # Ordenar por diferencia de días ascendente (el más cercano primero)
            # En caso de empate en días, la diferencia de monto ya la cumple.
            candidatos.sort(key=lambda x: x['diff_dias'])

            mejor_candidato = candidatos[0]
            c_cuenta = mejor_candidato['cuenta']
            c_idx = mejor_candidato['idx']

            cuentas_bbva[c_cuenta].at[c_idx, 'ID_VENTA_CRUCE'] = id_venta
            numero_cuenta_real = c_cuenta.replace('BANCO_', '')
            id_venta_a_cuenta[id_venta] = numero_cuenta_real
            match_count += 1

    # 5. Marcar Ventas cruzadas
    for idx, venta in df_ventas.iterrows():
        id_v = venta['id_venta']
        if id_v in id_venta_a_cuenta:
            df_ventas.at[idx, 'estado_cruce'] = 'OK vs BANCO'
            df_ventas.at[idx, 'cuenta_bancaria_cruce'] = id_venta_a_cuenta[id_v]

    # 6. Guardar resultados
    # Guardar resultados in-place para ventas BBVA
    update_table_from_df(df_ventas, "VENTAS_BBVA")
    drop_table_from_sql("VENTAS_BBVA_CRUZADO")

    # Guardar resultados in-place para cuentas BBVA
    for cuenta_nombre, df_banco in cuentas_bbva.items():
        update_table_from_df(df_banco, cuenta_nombre)
        drop_table_from_sql(f"{cuenta_nombre}_CRUZADO")

    return {
        "success": True,
        "matches": match_count,
        "sample": df_ventas[df_ventas['estado_cruce'] == 'OK vs BANCO'].head()
    }
