import pandas as pd
import io
from database_sqlite import get_df_from_sql, get_all_tables

def generate_final_report():
    """Toma la base de datos SQL y genera un Excel con múltiples pestañas para gerencia."""
    output = io.BytesIO()

    tablas_crudas = get_all_tables()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:

        # 1. Pestaña: Resumen Global (Simulado)
        df_resumen = pd.DataFrame({
            "Métrica": ["Total Abonos BBVA", "Total Abonos MP", "Diferencias Generadas", "Comprobantes Fiscales Procesados"],
            "Valor": ["Ver Detalle BBVA", "Ver Detalle MP", "Ver Detalle Faltantes", "Revisar Hojas CFDI"]
        })
        df_resumen.to_excel(writer, sheet_name='00_RESUMEN_GERENCIAL', index=False)

        # 2. Pestaña: BBVA Cruzado
        if "VENTAS_BBVA_CRUZADO" in tablas_crudas:
            df = get_df_from_sql("VENTAS_BBVA_CRUZADO")
            df.to_excel(writer, sheet_name='01_VENTAS_BBVA_OK', index=False)

        # 3. Pestaña: Faltantes BBVA
        if "VENTAS_BBVA_CRUZADO" in tablas_crudas:
            df = get_df_from_sql("VENTAS_BBVA_CRUZADO")
            if 'estado_cruce' in df.columns:
                df_faltantes = df[df['estado_cruce'] == 'PENDIENTE']
                df_faltantes.to_excel(writer, sheet_name='02_FALTANTES_BBVA', index=False)

        # 4. Pestaña: MP Cruzado
        if "VENTAS_MP_CRUZADO" in tablas_crudas:
            df = get_df_from_sql("VENTAS_MP_CRUZADO")
            df.to_excel(writer, sheet_name='03_VENTAS_MP_OK', index=False)

        # 5. Pestaña: Faltantes MP
        if "VENTAS_MP_CRUZADO" in tablas_crudas:
            df = get_df_from_sql("VENTAS_MP_CRUZADO")
            if 'estado_cruce' in df.columns:
                df_faltantes = df[df['estado_cruce'] == 'PENDIENTE']
                df_faltantes.to_excel(writer, sheet_name='04_FALTANTES_MP', index=False)

        # 6. Pestaña: CFDI Fiscal Completado
        if "CFDI_CFDI_I_PUE_CRUZADO" in tablas_crudas:
            df = get_df_from_sql("CFDI_CFDI_I_PUE_CRUZADO")
            if 'estado_conciliacion' in df.columns:
                df_fiscal = df[df['estado_conciliacion'].str.startswith('COMPLETO', na=False)]
                df_fiscal.to_excel(writer, sheet_name='05_CFDI_FISCAL_OK', index=False)

    return output.getvalue()
