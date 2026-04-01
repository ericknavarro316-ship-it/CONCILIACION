import pandas as pd
import numpy as np
from database_sqlite import get_df_from_sql, save_df_to_sql, get_all_tables

def run_o01_preclasificar_bancos():
    """Identifica patrones de texto en el Concepto de los bancos para pre-clasificar cargos y abonos"""
    tablas = get_all_tables()
    # Now it dynamically selects any table with BANCO_ prefix to be inclusive
    bancos = [t for t in tablas if t.startswith("BANCO_")]

    # Lista de patrones comunes (ejemplo extraído y expandible)
    patrones_comunes = {
        'COMISION': 'COMISIONES BANCARIAS',
        'IVA': 'IMPUESTOS',
        'TRASPASO': 'TRASPASO ENTRE CUENTAS PROPIAS',
        'NOMINA': 'NOMINA',
        'SPEI ENVIADO': 'PAGO PROVEEDORES',
        'PAGO DE IMPUESTOS': 'IMPUESTOS SAT'
    }

    total_clasificados = 0

    for cuenta_nombre in bancos:
        df_banco = get_df_from_sql(cuenta_nombre)

        # Priority column is CONCEPTO, fallback to DESCRIPCION
        col_concepto = 'CONCEPTO' if 'CONCEPTO' in df_banco.columns else 'DESCRIPCION' if 'DESCRIPCION' in df_banco.columns else None

        if not col_concepto:
            continue

        if 'CATEGORIA_PREVIA' not in df_banco.columns:
             df_banco['CATEGORIA_PREVIA'] = None

        # Determine which rows to process
        mask_to_process = df_banco['CATEGORIA_PREVIA'].isna()
        if not mask_to_process.any():
            continue

        concepto_series = df_banco.loc[mask_to_process, col_concepto].astype(str).str.upper()

        condiciones = []
        opciones = []

        for clave, categoria in patrones_comunes.items():
            condiciones.append(concepto_series.str.contains(clave, regex=False, na=False))
            opciones.append(categoria)

        # Apply np.select
        if condiciones:
            # Default is the existing CATEGORIA_PREVIA or None (actually pd.NA or similar, we'll keep None)
            new_categories = np.select(condiciones, opciones, default=None)

            # Create a mask for rows that got a new categorization
            mask_newly_classified = (new_categories != None) & (pd.notna(new_categories))

            if mask_newly_classified.any():
                # Assign to df
                # new_categories is an array same size as concepto_series
                df_banco.loc[mask_to_process, 'CATEGORIA_PREVIA'] = new_categories

                # Count matches
                total_clasificados += mask_newly_classified.sum()

                # Save only if modified
                save_df_to_sql(df_banco, cuenta_nombre)

    return {"success": True, "matches": total_clasificados}


def run_o07_conciliar_pagos_e():
    """Cruza Salidas de Bancos (Cargos) vs Complementos de Pago de Egresos (PAGOS E)"""
    df_pagos = get_df_from_sql("CFDI_PAGOS_E")
    if df_pagos.empty:
         return {"error": "No hay tabla de PAGOS E en la base de datos."}

    df_pagos['estado_cruce_pago'] = 'PENDIENTE BANCARIO'
    df_pagos['cuenta_bancaria_cruce'] = None

    tablas = get_all_tables()
    bancos = [t for t in tablas if t.startswith("BANCO_") and (
        t.replace("BANCO_", "").isdigit() or
        t.startswith("BANCO_BBVA_EST_") or
        t.startswith("BANCO_BBVA_DET_")
    )]

    col_total = next((col for col in ['Monto', 'Total', 'Total Pago'] if col in df_pagos.columns), None)
    if not col_total:
         return {"error": f"No se encontró columna de monto en PAGOS E. Columnas son: {df_pagos.columns.tolist()}"}

    match_count = 0
    cuentas_bbva = {t: get_df_from_sql(t) for t in bancos}

    for idx_pago, pago in df_pagos.iterrows():
        total_pagar = pd.to_numeric(pago[col_total], errors='coerce')
        if pd.isna(total_pagar) or total_pagar <= 0: continue

        match_encontrado = False
        tolerancia = 1.0

        for cuenta_nombre, df_banco in cuentas_bbva.items():
            if 'CARGO' not in df_banco.columns: continue

            if 'UUID_PAGO_CRUCE' not in df_banco.columns:
                df_banco['UUID_PAGO_CRUCE'] = None

            df_banco['CARGO'] = pd.to_numeric(df_banco['CARGO'], errors='coerce')
            cargos_libres = df_banco[pd.isna(df_banco['UUID_PAGO_CRUCE']) & pd.notna(df_banco['CARGO'])]

            for idx_banco, cargo_banco in cargos_libres.iterrows():
                cargo_val = cargo_banco['CARGO']
                if abs(cargo_val - total_pagar) <= tolerancia:
                    # Match
                    uuid_pago = pago.get('UUID', f"PAGO_{idx_pago}")
                    cuentas_bbva[cuenta_nombre].at[idx_banco, 'UUID_PAGO_CRUCE'] = uuid_pago

                    df_pagos.at[idx_pago, 'estado_cruce_pago'] = 'PAGADO OK'
                    df_pagos.at[idx_pago, 'cuenta_bancaria_cruce'] = cuenta_nombre.replace('BANCO_', '')

                    match_encontrado = True
                    match_count += 1
                    break

            if match_encontrado: break

    save_df_to_sql(df_pagos, "CFDI_PAGOS_E_CRUZADO")
    for cuenta_nombre, df_banco in cuentas_bbva.items():
        save_df_to_sql(df_banco, cuenta_nombre) # Se sobreescribe la cruda para agregar la columna

    return {"success": True, "matches": match_count}
