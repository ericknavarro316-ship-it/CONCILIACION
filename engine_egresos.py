import pandas as pd
import numpy as np
from database_sqlite import get_df_from_sql, save_df_to_sql, get_all_tables, update_table_from_df, drop_table_from_sql

def safe_parse_dates(serie):
    """Intenta parsear fechas de forma segura asumiendo múltiples formatos posibles."""
    # Limpiar strings de fecha (ej. "2026-02-03T17:37:53" -> "2026-02-03 17:37:53")
    serie_str = serie.astype(str).str.replace('T', ' ', regex=False).str.split('.').str[0].str.strip()

    s_iso_full = pd.to_datetime(serie_str, format='%Y-%m-%d %H:%M:%S', errors='coerce')
    s_iso_short = pd.to_datetime(serie_str, format='%Y-%m-%d', errors='coerce')
    s_eu = pd.to_datetime(serie_str, format='%d/%m/%Y', errors='coerce')
    s_eu_full = pd.to_datetime(serie_str, format='%d/%m/%Y %H:%M:%S', errors='coerce')

    # Fallback genérico de pandas si los formatos estrictos fallan
    s_auto = pd.to_datetime(serie, errors='coerce')

    return s_iso_full.fillna(s_iso_short).fillna(s_eu_full).fillna(s_eu).fillna(s_auto)

def run_egresos_crosscheck():
    """Cruza los CFDI de Egresos PUE contra los CARGOS en cuentas bancarias."""

    # 1. Leer Egresos (CFDI E PUE)
    # Intentamos primero con CFDI_E_PUE (nombre correcto sin prefijo doble) y luego el antiguo
    df_egresos = get_df_from_sql("CFDI_E_PUE")
    nombre_tabla_egresos = "CFDI_E_PUE"

    if df_egresos.empty:
        df_egresos = get_df_from_sql("CFDI_CFDI_E_PUE")
        nombre_tabla_egresos = "CFDI_CFDI_E_PUE"

    if df_egresos.empty:
        return {"error": "No hay tabla CFDI_E_PUE (Egresos) en la base de datos."}

    # Inicializar estado en CFDI
    if 'cuenta_origen_pago' not in df_egresos.columns:
        df_egresos['cuenta_origen_pago'] = None
    if 'BANCOS' not in df_egresos.columns:
        df_egresos['BANCOS'] = None
    df_egresos['estado_cruce_egreso'] = 'PENDIENTE BANCARIO'

    col_fecha_cfdi = 'Fecha Emisión' if 'Fecha Emisión' in df_egresos.columns else 'FECHA'
    if col_fecha_cfdi in df_egresos.columns:
        df_egresos['FECHA_PARSED'] = safe_parse_dates(df_egresos[col_fecha_cfdi])
    else:
        df_egresos['FECHA_PARSED'] = pd.NaT

    # 2. Leer Cuentas Bancarias (Todas, no solo BBVA)
    tablas = get_all_tables()
    # Buscamos todas las tablas que empiecen con BANCO_ y filtramos las de cruce.
    nombres_cuentas_banco = [t for t in tablas if t.startswith("BANCO_") and not t.endswith("_CRUZADO") and not t.endswith("_CRUZADO_EGRESOS")]

    if not nombres_cuentas_banco:
         return {"error": "No se encontraron tablas de cuentas bancarias (BANCO_...) para buscar cargos."}

    cuentas_bancos = {}
    for t in nombres_cuentas_banco:
        df_t = get_df_from_sql(t)
        if not df_t.empty and 'CARGO' in df_t.columns:
            cuentas_bancos[t] = df_t

    if not cuentas_bancos:
         return {"error": "No se encontraron tablas bancarias con la columna 'CARGO'."}

    # 3. Construir "pool" de cargos bancarios para optimización vectorial
    pool_cargos_list = []
    for cuenta_nombre, df_banco in cuentas_bancos.items():
        if 'UUID_EGRESO_CRUCE' not in df_banco.columns:
            df_banco['UUID_EGRESO_CRUCE'] = None
        if 'UUID COMPL.' not in df_banco.columns:
            df_banco['UUID COMPL.'] = None

        df_banco['CARGO_NUM'] = pd.to_numeric(df_banco['CARGO'], errors='coerce')

        # Parsear fecha bancaria
        col_fecha_banco = 'FECHA' if 'FECHA' in df_banco.columns else 'Fecha del cargo' if 'Fecha del cargo' in df_banco.columns else None
        if col_fecha_banco:
            df_banco['FECHA_PARSED'] = safe_parse_dates(df_banco[col_fecha_banco])
        else:
            df_banco['FECHA_PARSED'] = pd.NaT

        # Limpiar columnas de UUID para estandarizar valores vacíos o nulos que vengan de SQLite como strings
        for col_uuid in ['UUID_EGRESO_CRUCE', 'UUID COMPL.']:
            df_banco[col_uuid] = df_banco[col_uuid].replace(['None', 'nan', 'NaN', ''], np.nan)

        # Extraer cargos numéricos limpiando posibles símbolos $ y comas
        df_banco['CARGO_NUM'] = pd.to_numeric(
            df_banco['CARGO'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False),
            errors='coerce'
        )

        # Solo necesitamos los cargos libres, válidos y con fecha (opcional, pero ideal)
        cargos_libres = df_banco[
            pd.isna(df_banco['UUID_EGRESO_CRUCE']) &
            pd.isna(df_banco['UUID COMPL.']) &
            pd.notna(df_banco['CARGO_NUM']) &
            (df_banco['CARGO_NUM'] > 0)
        ].copy()

        if not cargos_libres.empty:
            cargos_libres['ORIGEN_TABLA'] = cuenta_nombre
            cargos_libres['ORIGEN_IDX'] = cargos_libres.index
            # Extraer mes-año para filtro rápido (YYYY-MM)
            cargos_libres['MES_AÑO'] = cargos_libres['FECHA_PARSED'].dt.to_period('M')
            pool_cargos_list.append(cargos_libres[['ORIGEN_TABLA', 'ORIGEN_IDX', 'CARGO_NUM', 'FECHA_PARSED', 'MES_AÑO']])

    if pool_cargos_list:
        df_pool = pd.concat(pool_cargos_list, ignore_index=True)
    else:
        df_pool = pd.DataFrame(columns=['ORIGEN_TABLA', 'ORIGEN_IDX', 'CARGO_NUM', 'FECHA_PARSED', 'MES_AÑO'])

    match_count = 0

    # 4. Cruzar Egresos vs Pool
    col_total = next((col for col in ['Total', 'TOTAL', 'Monto'] if col in df_egresos.columns), None)
    if not col_total:
         return {"error": "No se encontró columna 'Total' en los Egresos CFDI para hacer el cruce."}

    tolerancia = 1.0 # Tolerancia 1 peso para egresos PUE
    tolerancia_dias = 31 # Maximo de dias de diferencia para aceptar un match, para tolerar cruces de mes

    for idx_egreso, egreso in df_egresos.iterrows():
        total_pagar = pd.to_numeric(egreso[col_total], errors='coerce')
        if pd.isna(total_pagar) or total_pagar <= 0:
            continue

        fecha_cfdi = egreso['FECHA_PARSED']
        if pd.isna(fecha_cfdi):
            continue

        # Buscar en el pool por monto primero (ya que es más estricto)
        candidatos = df_pool[np.abs(df_pool['CARGO_NUM'] - total_pagar) <= tolerancia].copy()

        if not candidatos.empty:
            # Calcular diferencia en días absolutos para verificar proximidad
            candidatos['DIFF_DIAS'] = (candidatos['FECHA_PARSED'] - fecha_cfdi).dt.days.abs()

            # Filtrar solo candidatos que ocurrieron dentro del límite de días (ej. mismo mes calendario o muy cercano)
            candidatos_validos = candidatos[candidatos['DIFF_DIAS'] <= tolerancia_dias].copy()

            if candidatos_validos.empty:
                continue

            # Ordenar por el que tenga la fecha más cercana al comprobante y luego el que más se acerque al monto exacto
            candidatos_validos['DIFF_MONTO'] = np.abs(candidatos_validos['CARGO_NUM'] - total_pagar)
            candidatos_validos = candidatos_validos.sort_values(by=['DIFF_DIAS', 'DIFF_MONTO'])

            # Seleccionar el mejor
            mejor_match = candidatos_validos.iloc[0]

            tabla_origen = mejor_match['ORIGEN_TABLA']
            idx_origen = mejor_match['ORIGEN_IDX']

            uuid_egreso = str(egreso.get('UUID', f"EGRESO_{idx_egreso}")).strip()

            # Actualizar la tabla en memoria
            cuentas_bancos[tabla_origen].at[idx_origen, 'UUID_EGRESO_CRUCE'] = uuid_egreso
            cuentas_bancos[tabla_origen].at[idx_origen, 'UUID COMPL.'] = uuid_egreso

            # Actualizar estado del egreso
            df_egresos.at[idx_egreso, 'estado_cruce_egreso'] = 'PAGADO OK'
            nombre_banco = tabla_origen.replace('BANCO_', '')
            df_egresos.at[idx_egreso, 'cuenta_origen_pago'] = nombre_banco
            df_egresos.at[idx_egreso, 'BANCOS'] = nombre_banco

            # Eliminar del pool para que no vuelva a ser usado por otro CFDI
            df_pool = df_pool.drop(mejor_match.name)

            match_count += 1

    # 5. Limpieza de columnas temporales y guardado de resultados
    df_egresos = df_egresos.drop(columns=['FECHA_PARSED'], errors='ignore')

    # Actualizar las tablas bancarias modificadas (sin crear copias "_CRUZADO_EGRESOS")
    for cuenta_nombre, df_banco in cuentas_bancos.items():
        df_banco = df_banco.drop(columns=['CARGO_NUM', 'FECHA_PARSED'], errors='ignore')
        # Guardar sobre la tabla original usando update_table_from_df
        update_table_from_df(df_banco, cuenta_nombre)

    # Actualizar el CFDI original (para que la columna BANCOS perdure)
    update_table_from_df(df_egresos, nombre_tabla_egresos)

    # Limpiar tabla residual anterior si existiera para que no estorbe en la UI
    drop_table_from_sql(f"{nombre_tabla_egresos}_CRUZADO")

    return {
        "success": True,
        "matches": match_count
    }
