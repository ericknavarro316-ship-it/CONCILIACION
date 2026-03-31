import pandas as pd
from database_sqlite import get_df_from_sql, save_df_to_sql, get_all_tables

def run_egresos_crosscheck():
    """Cruza los CFDI de Egresos PUE contra los CARGOS en cuentas bancarias."""

    # 1. Leer Egresos (CFDI E PUE)
    df_egresos = get_df_from_sql("CFDI_CFDI_E_PUE")
    if df_egresos.empty:
        return {"error": "No hay tabla CFDI_E_PUE (Egresos) en la base de datos."}

    # Inicializar estado en CFDI
    df_egresos['cuenta_origen_pago'] = None
    df_egresos['estado_cruce_egreso'] = 'PENDIENTE BANCARIO'

    # 2. Leer Cuentas Bancarias BBVA
    tablas = get_all_tables()
    cuentas_bbva = {t: get_df_from_sql(t) for t in tablas if t.startswith("BANCO_") and (
        t.replace("BANCO_", "").isdigit() or
        t.startswith("BANCO_BBVA_EST_") or
        t.startswith("BANCO_BBVA_DET_")
    )}

    if not cuentas_bbva:
         return {"error": "No se encontraron tablas de cuentas bancarias (BANCO_XXXXX o BANCO_BBVA_...) para buscar cargos."}

    match_count = 0

    # 3. Buscar cargos (salidas) en bancos
    # En CFDI el monto está en 'Total'
    col_total = next((col for col in ['Total', 'TOTAL', 'Monto'] if col in df_egresos.columns), None)

    if not col_total:
         return {"error": "No se encontró columna 'Total' en los Egresos CFDI para hacer el cruce."}

    for idx_egreso, egreso in df_egresos.iterrows():
        total_pagar = pd.to_numeric(egreso[col_total], errors='coerce')
        if pd.isna(total_pagar) or total_pagar <= 0:
            continue

        tolerancia = 1.0 # Tolerancia 1 peso para egresos PUE
        match_encontrado = False

        # Buscar en cada banco BBVA
        for cuenta_nombre, df_banco in cuentas_bbva.items():
            if 'CARGO' not in df_banco.columns:
                continue

            if 'UUID_EGRESO_CRUCE' not in df_banco.columns:
                df_banco['UUID_EGRESO_CRUCE'] = None

            df_banco['CARGO'] = pd.to_numeric(df_banco['CARGO'], errors='coerce')
            cargos_libres = df_banco[pd.isna(df_banco['UUID_EGRESO_CRUCE']) & pd.notna(df_banco['CARGO'])]

            for idx_banco, cargo_banco in cargos_libres.iterrows():
                cargo_val = cargo_banco['CARGO']
                diferencia = abs(cargo_val - total_pagar)

                if diferencia <= tolerancia:
                    # Encontramos la salida de dinero
                    uuid_egreso = egreso.get('UUID', f"EGRESO_{idx_egreso}")

                    cuentas_bbva[cuenta_nombre].at[idx_banco, 'UUID_EGRESO_CRUCE'] = uuid_egreso

                    df_egresos.at[idx_egreso, 'estado_cruce_egreso'] = 'PAGADO OK'
                    df_egresos.at[idx_egreso, 'cuenta_origen_pago'] = cuenta_nombre.replace('BANCO_', '')

                    match_encontrado = True
                    match_count += 1
                    break

            if match_encontrado:
                break

    # 4. Guardar resultados
    save_df_to_sql(df_egresos, "CFDI_CFDI_E_PUE_CRUZADO")
    for cuenta_nombre, df_banco in cuentas_bbva.items():
        save_df_to_sql(df_banco, f"{cuenta_nombre}_CRUZADO_EGRESOS")

    return {
        "success": True,
        "matches": match_count
    }
