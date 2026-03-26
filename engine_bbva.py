import pandas as pd
from database_sqlite import get_df_from_sql, save_df_to_sql, get_all_tables

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
    cuentas_bbva = {t: get_df_from_sql(t) for t in tablas if t.startswith("BANCO_") and t.replace("BANCO_", "").isdigit()}

    if not cuentas_bbva:
         return {"error": "No se encontraron tablas de cuentas bancarias (BANCO_XXXXX)."}

    # 3. Agrupar Ventas por ID
    df_ventas['precio_real'] = pd.to_numeric(df_ventas['precio_real'], errors='coerce')

    ventas_agrupadas = df_ventas.groupby('id_venta', as_index=False).agg({
        'precio_real': 'sum',
        'uuid': 'first'
    })

    match_count = 0
    id_venta_a_cuenta = {}

    # 4. Cruce con tolerancias
    for _, grupo in ventas_agrupadas.iterrows():
        id_venta = grupo['id_venta']
        total_a_cobrar = grupo['precio_real']
        if pd.isna(total_a_cobrar) or total_a_cobrar <= 0:
            continue

        tolerancia = 1.0 if total_a_cobrar <= 50000 else 50.0
        match_encontrado = False

        for cuenta_nombre, df_banco in cuentas_bbva.items():
            if 'ABONO' not in df_banco.columns:
                continue

            if 'ID_VENTA_CRUCE' not in df_banco.columns:
                df_banco['ID_VENTA_CRUCE'] = None

            # Asegurar numérico
            df_banco['ABONO'] = pd.to_numeric(df_banco['ABONO'], errors='coerce')

            abonos_libres = df_banco[pd.isna(df_banco['ID_VENTA_CRUCE']) & pd.notna(df_banco['ABONO'])]

            for idx_banco, abono_banco in abonos_libres.iterrows():
                abono_val = abono_banco['ABONO']
                diferencia = abs(abono_val - total_a_cobrar)

                if diferencia <= tolerancia:
                    cuentas_bbva[cuenta_nombre].at[idx_banco, 'ID_VENTA_CRUCE'] = id_venta
                    numero_cuenta_real = cuenta_nombre.replace('BANCO_', '')
                    id_venta_a_cuenta[id_venta] = numero_cuenta_real
                    match_encontrado = True
                    match_count += 1
                    break

            if match_encontrado:
                break

    # 5. Marcar Ventas cruzadas
    for idx, venta in df_ventas.iterrows():
        id_v = venta['id_venta']
        if id_v in id_venta_a_cuenta:
            df_ventas.at[idx, 'estado_cruce'] = 'OK vs BANCO'
            df_ventas.at[idx, 'cuenta_bancaria_cruce'] = id_venta_a_cuenta[id_v]

    # 6. Guardar resultados
    save_df_to_sql(df_ventas, "VENTAS_BBVA_CRUZADO")
    for cuenta_nombre, df_banco in cuentas_bbva.items():
        save_df_to_sql(df_banco, f"{cuenta_nombre}_CRUZADO")

    return {
        "success": True,
        "matches": match_count,
        "sample": df_ventas[df_ventas['estado_cruce'] == 'OK vs BANCO'].head()
    }
