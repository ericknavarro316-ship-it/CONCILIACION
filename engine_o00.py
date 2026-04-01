import pandas as pd
import numpy as np
from database_sqlite import get_df_from_sql, update_table_from_df, get_all_tables

def run_o01_preclasificar_bancos():
    """Identifica patrones de texto en el Concepto de los bancos para pre-clasificar cargos y abonos"""
    tablas = get_all_tables()
    # Now it dynamically selects any table with BANCO_ prefix to be inclusive
    bancos = [t for t in tablas if t.startswith("BANCO_")]

    # Lista de patrones comunes (ejemplo extraído y expandible)
    patrones_comunes = {
        'PUNTO DE VENTA': 'ND-COMISION',
        'TDC INTER': 'ND-COMISION',
        'NAL. AMEX': 'ND-COMISION',
        'SECRETARIA DE LA HAC': '3% NOMINA GDL',
        'GOBIERNO DEL ESTADO/GUIA': '3% NOMINA PUE',
        'RECIBO NO./': 'ND-SEGURO',
        'EFECTIVALE S DE RL': 'EFECTIVALE',
        'PREST.': 'PRESTAMO',
        'PAGO DE NOMINA': 'NOMINA',
        'ADOBE 2': 'ND-SUSCRIPCION',
        'FACEBOOK': 'FACEBOOK',
        'SAT/GUIA': 'IMPUESTOS FEDERALES',
        'PAGO SUA': 'PAGO SUA'
    }

    total_clasificados = 0

    for cuenta_nombre in bancos:
        df_banco = get_df_from_sql(cuenta_nombre)

        # Priority column is CONCEPTO, fallback to DESCRIPCION
        col_concepto = 'CONCEPTO' if 'CONCEPTO' in df_banco.columns else 'DESCRIPCION' if 'DESCRIPCION' in df_banco.columns else None

        if not col_concepto:
            continue

        # Ensure CARGO column exists to filter
        if 'CARGO' not in df_banco.columns:
            continue

        # Clean up the old erroneous column if it exists
        if 'CATEGORIA_PREVIA' in df_banco.columns:
            df_banco = df_banco.drop(columns=['CATEGORIA_PREVIA'])

        if 'OBSERVACION' not in df_banco.columns:
             df_banco['OBSERVACION'] = ""

        # Replace literal "None" or np.nan with empty strings in OBSERVACION
        df_banco['OBSERVACION'] = df_banco['OBSERVACION'].fillna("").astype(str).replace({'None': '', 'nan': '', '<NA>': ''})

        # Convert CARGO to numeric to ensure filtering works
        df_banco['CARGO'] = pd.to_numeric(df_banco['CARGO'], errors='coerce')

        # Determine which rows to process (only empty observations AND are cargos)
        mask_to_process = (df_banco['OBSERVACION'] == "") & (df_banco['CARGO'] > 0)

        if not mask_to_process.any():
            # Still update the table to remove duplicates and the old column if they existed
            df_banco = df_banco.drop_duplicates()
            update_table_from_df(df_banco, cuenta_nombre)
            continue

        concepto_series = df_banco.loc[mask_to_process, col_concepto].astype(str).str.upper()

        condiciones = []
        opciones = []

        for clave, categoria in patrones_comunes.items():
            condiciones.append(concepto_series.str.contains(clave, regex=False, na=False))
            opciones.append(categoria)

        # Apply np.select
        if condiciones:
            # Default is empty string
            new_categories = np.select(condiciones, opciones, default="")

            # Create a mask for rows that got a new categorization
            mask_newly_classified = (new_categories != "")

            if mask_newly_classified.any():
                # Assign to df
                df_banco.loc[mask_to_process, 'OBSERVACION'] = new_categories

                # Count matches
                total_clasificados += mask_newly_classified.sum()

        # --- Special rule for TRASPASOS ---
        # "TRASPASO CUENTAS PROPIAS ➔ TRASPASO CUENTAS PROPIAS | "últimos 5 datos de la cuenta"
        # (viene después de CUENTA: ejemplo "CUENTA: 0121923773" se tendría que poner "23773",
        # además quiero que este dato este en la columna "UUID COMPL." )

        # Find rows that match the keyword and have CARGO > 0 and haven't been classified yet
        mask_traspasos = df_banco[col_concepto].astype(str).str.upper().str.contains('TRASPASO CUENTAS PROPIAS', regex=False, na=False) & (df_banco['CARGO'] > 0) & (df_banco['OBSERVACION'] == "")

        if mask_traspasos.any():
            if 'UUID COMPL.' not in df_banco.columns:
                df_banco['UUID COMPL.'] = ""

            # Extract the account number after "CUENTA: " (capture 5 to 20 digits to be safe)
            # The regex looks for "CUENTA:" followed by optional spaces, then captures digits.
            extracted_accounts = df_banco.loc[mask_traspasos, col_concepto].astype(str).str.extract(r'CUENTA:\s*(\d+)', expand=False)

            # Loop through the matches to get the last 5 digits and apply formatting
            for idx, val in extracted_accounts.items():
                if pd.notna(val) and len(str(val)) >= 5:
                    last_5 = str(val)[-5:]
                    new_obs = f'TRASPASO CUENTAS PROPIAS | {last_5}'

                    df_banco.at[idx, 'OBSERVACION'] = new_obs
                    df_banco.at[idx, 'UUID COMPL.'] = last_5
                    # Do not double-count matches if it was already processed, just add to sum safely
                    # We assume these are new matches if not caught by the dictionary
                    total_clasificados += 1
                elif pd.notna(val) and len(str(val)) > 0:
                    # Fallback if account number is less than 5 digits long
                    last_5 = str(val)
                    new_obs = f'TRASPASO CUENTAS PROPIAS | {last_5}'
                    df_banco.at[idx, 'OBSERVACION'] = new_obs
                    df_banco.at[idx, 'UUID COMPL.'] = last_5
                    total_clasificados += 1

        # Drop duplicates caused by previous save_df_to_sql bug
        df_banco = df_banco.drop_duplicates()

        # Save explicitly overwriting the whole table
        update_table_from_df(df_banco, cuenta_nombre)

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

    # Remove duplicates before saving if there were any
    df_pagos = df_pagos.drop_duplicates()
    update_table_from_df(df_pagos, "CFDI_PAGOS_E_CRUZADO")

    for cuenta_nombre, df_banco in cuentas_bbva.items():
        df_banco = df_banco.drop_duplicates()
        update_table_from_df(df_banco, cuenta_nombre) # Se sobreescribe la cruda para agregar la columna

    return {"success": True, "matches": match_count}
