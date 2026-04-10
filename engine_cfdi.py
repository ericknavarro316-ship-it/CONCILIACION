import pandas as pd
from database_sqlite import get_df_from_sql, save_df_to_sql

def run_cfdi_crosscheck():
    """Propaga la información bancaria desde las ventas cruzadas hacia los CFDI."""

    # 1. Leer las tablas de Ventas ya cruzadas con bancos
    df_bbva = get_df_from_sql("VENTAS_BBVA")
    df_mp = get_df_from_sql("VENTAS_MP_CRUZADO")

    # Unificamos todas las ventas cruzadas en un solo dataframe maestro para buscar sus UUIDs
    ventas_cruzadas = []

    if not df_bbva.empty and 'cuenta_bancaria_cruce' in df_bbva.columns:
        ventas_cruzadas.append(df_bbva[['id_venta', 'uuid', 'cuenta_bancaria_cruce', 'estado_cruce']])

    if not df_mp.empty and 'referencia_cruce' in df_mp.columns:
        # MP se marca a la cuenta "Mercado Pago" o su identificador interno
        df_mp['cuenta_bancaria_cruce'] = "MERCADO_PAGO"
        ventas_cruzadas.append(df_mp[['id_venta', 'uuid', 'cuenta_bancaria_cruce', 'estado_cruce']])

    if not ventas_cruzadas:
         return {"error": "No se han ejecutado los cruces bancarios previos (BBVA o MP). Ejecútalos primero."}

    df_ventas_master = pd.concat(ventas_cruzadas, ignore_index=True)
    df_ventas_master = df_ventas_master[df_ventas_master['estado_cruce'].str.startswith('OK', na=False)]

    # 2. Leer CFDI PUE y PPD
    df_pue = get_df_from_sql("CFDI_CFDI_I_PUE")
    df_ppd = get_df_from_sql("CFDI_CFDI_I_PPD")

    if df_pue.empty and df_ppd.empty:
         return {"error": "No se encontraron tablas CFDI I en la base de datos."}

    # Inicializar columnas en CFDI
    if not df_pue.empty:
        df_pue['cuenta_bancaria_cruce'] = None
        df_pue['estado_conciliacion'] = 'PENDIENTE BANCARIO'

    if not df_ppd.empty:
        df_ppd['cuenta_bancaria_cruce'] = None
        df_ppd['estado_conciliacion'] = 'PENDIENTE BANCARIO'

    match_count_pue = 0
    match_count_ppd = 0

    # 3. Propagar usando el UUID de la venta hacia el UUID del CFDI
    # Limpiamos UUIDs en ventas
    df_ventas_master['uuid'] = df_ventas_master['uuid'].astype(str).str.strip().str.upper()

    # Crear diccionario UUID -> Cuenta Bancaria
    uuid_a_cuenta = df_ventas_master.set_index('uuid')['cuenta_bancaria_cruce'].to_dict()

    # CRUCE CON PUE
    if not df_pue.empty:
        df_pue['UUID'] = df_pue['UUID'].astype(str).str.strip().str.upper()

        for idx, row in df_pue.iterrows():
            uuid_cfdi = row['UUID']
            if uuid_cfdi in uuid_a_cuenta:
                df_pue.at[idx, 'cuenta_bancaria_cruce'] = uuid_a_cuenta[uuid_cfdi]
                df_pue.at[idx, 'estado_conciliacion'] = 'COMPLETO: BANCARIO Y FISCAL'
                match_count_pue += 1

    # CRUCE CON PPD
    if not df_ppd.empty:
        df_ppd['UUID'] = df_ppd['UUID'].astype(str).str.strip().str.upper()

        for idx, row in df_ppd.iterrows():
            uuid_cfdi = row['UUID']
            if uuid_cfdi in uuid_a_cuenta:
                df_ppd.at[idx, 'cuenta_bancaria_cruce'] = uuid_a_cuenta[uuid_cfdi]
                df_ppd.at[idx, 'estado_conciliacion'] = 'COMPLETO: BANCARIO Y FISCAL'
                match_count_ppd += 1

    # 4. Guardar resultados
    if not df_pue.empty:
        save_df_to_sql(df_pue, "CFDI_CFDI_I_PUE_CRUZADO")
    if not df_ppd.empty:
        save_df_to_sql(df_ppd, "CFDI_CFDI_I_PPD_CRUZADO")

    return {
        "success": True,
        "matches_pue": match_count_pue,
        "matches_ppd": match_count_ppd,
        "sample_pue": df_pue[df_pue['estado_conciliacion'].str.startswith('COMPLETO', na=False)].head() if not df_pue.empty else pd.DataFrame()
    }
