import pandas as pd
import numpy as np
from database_sqlite import get_df_from_sql, update_table_from_df, get_all_tables, drop_table_from_sql
from engine_egresos import safe_parse_dates

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

        if mask_to_process.any():
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

        # Find rows that match the keyword and haven't been classified yet (applies to both CARGOS and ABONOS)
        mask_traspasos = df_banco[col_concepto].astype(str).str.upper().str.contains('TRASPASO CUENTAS PROPIAS', regex=False, na=False) & (df_banco['OBSERVACION'] == "")

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

    if 'estado_cruce_pago' not in df_pagos.columns:
        df_pagos['estado_cruce_pago'] = 'PENDIENTE BANCARIO'
    if 'cuenta_bancaria_cruce' not in df_pagos.columns:
        df_pagos['cuenta_bancaria_cruce'] = None

    col_fecha_cfdi = 'Fecha Emisión' if 'Fecha Emisión' in df_pagos.columns else 'FECHA'
    if col_fecha_cfdi in df_pagos.columns:
        df_pagos['FECHA_PARSED'] = safe_parse_dates(df_pagos[col_fecha_cfdi])
    else:
        df_pagos['FECHA_PARSED'] = pd.NaT

    tablas = get_all_tables()
    # Solo buscar en tablas de movimientos (DET) como solicitó el usuario, ignorando estados de cuenta (EST)
    bancos = [t for t in tablas if t.startswith("BANCO_") and "_DET_" in t and not t.endswith("_CRUZADO")]

    col_total = next((col for col in ['Monto', 'Total', 'Total Pago'] if col in df_pagos.columns), None)
    if not col_total:
         return {"error": f"No se encontró columna de monto en PAGOS E. Columnas son: {df_pagos.columns.tolist()}"}

    cuentas_bancos = {}
    for t in bancos:
        df_t = get_df_from_sql(t)
        if not df_t.empty and 'CARGO' in df_t.columns:
            cuentas_bancos[t] = df_t

    if not cuentas_bancos:
         return {"error": "No se encontraron tablas bancarias con la columna 'CARGO'."}

    # Construir "pool" de cargos bancarios
    pool_cargos_list = []
    for cuenta_nombre, df_banco in cuentas_bancos.items():
        if 'OBSERVACION' not in df_banco.columns:
            df_banco['OBSERVACION'] = None

        df_banco['OBSERVACION'] = df_banco['OBSERVACION'].replace(['None', 'nan', 'NaN', ''], np.nan)

        # Parsear fecha bancaria
        col_fecha_banco = 'FECHA' if 'FECHA' in df_banco.columns else 'Fecha del cargo' if 'Fecha del cargo' in df_banco.columns else None
        if col_fecha_banco:
            df_banco['FECHA_PARSED'] = safe_parse_dates(df_banco[col_fecha_banco])
        else:
            df_banco['FECHA_PARSED'] = pd.NaT

        df_banco['CARGO_NUM'] = pd.to_numeric(
            df_banco['CARGO'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False),
            errors='coerce'
        )

        cargos_libres = df_banco[
            pd.isna(df_banco['OBSERVACION']) &
            pd.notna(df_banco['CARGO_NUM']) &
            (df_banco['CARGO_NUM'] > 0)
        ].copy()

        if not cargos_libres.empty:
            cargos_libres['ORIGEN_TABLA'] = cuenta_nombre
            cargos_libres['ORIGEN_IDX'] = cargos_libres.index
            pool_cargos_list.append(cargos_libres[['ORIGEN_TABLA', 'ORIGEN_IDX', 'CARGO_NUM', 'FECHA_PARSED']])

    if pool_cargos_list:
        df_pool = pd.concat(pool_cargos_list, ignore_index=True)
    else:
        df_pool = pd.DataFrame(columns=['ORIGEN_TABLA', 'ORIGEN_IDX', 'CARGO_NUM', 'FECHA_PARSED'])

    match_count = 0
    tolerancia = 1.0
    tolerancia_dias = 31

    for idx_pago, pago in df_pagos.iterrows():
        if pago.get('estado_cruce_pago') == 'PAGADO OK':
            continue

        total_pagar = pd.to_numeric(pago[col_total], errors='coerce')
        if pd.isna(total_pagar) or total_pagar <= 0:
            continue

        fecha_cfdi = pago['FECHA_PARSED']

        if df_pool.empty:
            break

        # Buscar por monto
        candidatos = df_pool[np.abs(df_pool['CARGO_NUM'] - total_pagar) <= tolerancia].copy()

        if candidatos.empty:
            continue

        # Si la fecha del CFDI es válida, usar la tolerancia de días
        if pd.notna(fecha_cfdi):
            candidatos['DIFF_DIAS'] = (candidatos['FECHA_PARSED'] - fecha_cfdi).dt.days.abs()
            candidatos_validos = candidatos[candidatos['DIFF_DIAS'] <= tolerancia_dias].copy()

            if candidatos_validos.empty:
                continue

            # Ordenar por fecha más cercana y luego monto exacto
            candidatos_validos['DIFF_MONTO'] = np.abs(candidatos_validos['CARGO_NUM'] - total_pagar)
            candidatos_validos = candidatos_validos.sort_values(by=['DIFF_DIAS', 'DIFF_MONTO'])
            mejor_match = candidatos_validos.iloc[0]
        else:
            # Si no hay fecha en el CFDI, nos quedamos con el monto exacto como única referencia
            candidatos['DIFF_MONTO'] = np.abs(candidatos['CARGO_NUM'] - total_pagar)
            candidatos_validos = candidatos.sort_values(by=['DIFF_MONTO'])
            mejor_match = candidatos_validos.iloc[0]

        tabla_origen = mejor_match['ORIGEN_TABLA']
        idx_origen = mejor_match['ORIGEN_IDX']

        uuid_pago = str(pago.get('UUID', f"PAGO_{idx_pago}")).strip()
        uuid_madre = str(pago.get('UUID MADRE', "")).strip()

        # Inicializar columnas si no existen en el banco
        if 'UUID COMPL.' not in cuentas_bancos[tabla_origen].columns:
            cuentas_bancos[tabla_origen]['UUID COMPL.'] = None
        if 'UUID MADRE' not in cuentas_bancos[tabla_origen].columns:
            cuentas_bancos[tabla_origen]['UUID MADRE'] = None

        # Actualizar la tabla del banco con las nuevas reglas
        cuentas_bancos[tabla_origen].at[idx_origen, 'OBSERVACION'] = "PPD"
        cuentas_bancos[tabla_origen].at[idx_origen, 'UUID COMPL.'] = f"/?expediente_egreso={uuid_pago}"
        cuentas_bancos[tabla_origen].at[idx_origen, 'UUID MADRE'] = uuid_madre

        # Actualizar estado del pago CFDI
        df_pagos.at[idx_pago, 'estado_cruce_pago'] = 'PAGADO OK'
        df_pagos.at[idx_pago, 'cuenta_bancaria_cruce'] = tabla_origen.replace('BANCO_', '')

        df_pool = df_pool.drop(mejor_match.name)
        match_count += 1

    # Limpieza de temporales y guardado de resultados
    df_pagos = df_pagos.drop(columns=['FECHA_PARSED'], errors='ignore')
    update_table_from_df(df_pagos, "CFDI_PAGOS_E")
    drop_table_from_sql("CFDI_PAGOS_E_CRUZADO")

    for cuenta_nombre, df_banco in cuentas_bancos.items():
        df_banco = df_banco.drop(columns=['CARGO_NUM', 'FECHA_PARSED'], errors='ignore')
        update_table_from_df(df_banco, cuenta_nombre)

    return {"success": True, "matches": match_count}
