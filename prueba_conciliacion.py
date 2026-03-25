import pandas as pd
import numpy as np

def conciliar_ventas_vs_cfdi(ruta_excel_entrada, ruta_excel_salida):
    """
    Simula la lógica de la macro I01_CONCILIAR_VENTAS_BBVA_VS_BANCOS
    Carga hojas de ventas y CFDI (PUE y PPD) y busca conciliaciones por UUID y Monto.
    """
    print(f"Cargando archivo: {ruta_excel_entrada}...")

    # Cargar las diferentes hojas a DataFrames de Pandas
    try:
        df_ventas = pd.read_excel(ruta_excel_entrada, sheet_name="VENTAS_BBVA")
        df_pue = pd.read_excel(ruta_excel_entrada, sheet_name="CFDI_I_PUE")
        df_ppd = pd.read_excel(ruta_excel_entrada, sheet_name="CFDI_I_PPD")
    except Exception as e:
        print(f"Error cargando hojas. Asegúrate de que existan VENTAS_BBVA, CFDI_I_PUE y CFDI_I_PPD. Detalle: {e}")
        return

    # Limpiar columnas: Poner todo en minúsculas para evitar problemas de mayúsculas/minúsculas
    df_ventas.columns = df_ventas.columns.str.lower().str.strip()
    df_pue.columns = df_pue.columns.str.lower().str.strip()
    df_ppd.columns = df_ppd.columns.str.lower().str.strip()

    # Identificar nombres de columnas clave (Manejo de variaciones)
    col_uuid_ventas = 'uuid' if 'uuid' in df_ventas.columns else None
    col_monto_ventas = 'total' if 'total' in df_ventas.columns else 'importe' if 'importe' in df_ventas.columns else 'monto' if 'monto' in df_ventas.columns else None

    if not col_uuid_ventas or not col_monto_ventas:
        print(f"No se encontraron columnas clave en ventas. Columnas actuales: {df_ventas.columns.tolist()}")
        return

    # Añadir columna de estado de conciliación
    df_ventas['Estado_Conciliacion'] = 'PENDIENTE'
    df_ventas['Origen_Conciliacion'] = ''

    # ==========================================
    # PASO 1: CONCILIAR POR UUID EXACTO (PUE)
    # ==========================================
    # Extraemos solo UUIDs que existen en PUE para hacer un 'merge' (cruce) rápido
    if 'uuid' in df_pue.columns:
        uuids_pue = df_pue['uuid'].dropna().unique()

        # Máscara (filtro) de ventas donde el UUID está en la lista de PUE
        mask_pue = df_ventas[col_uuid_ventas].isin(uuids_pue) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        # Actualizamos el estado para las que cruzaron
        df_ventas.loc[mask_pue, 'Estado_Conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_pue, 'Origen_Conciliacion'] = 'CFDI PUE (UUID)'

        print(f"Conciliados por UUID (PUE): {mask_pue.sum()} registros")

    # ==========================================
    # PASO 2: CONCILIAR POR UUID EXACTO (PPD)
    # ==========================================
    if 'uuid' in df_ppd.columns:
        uuids_ppd = df_ppd['uuid'].dropna().unique()
        mask_ppd = df_ventas[col_uuid_ventas].isin(uuids_ppd) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        df_ventas.loc[mask_ppd, 'Estado_Conciliacion'] = 'CONCILIADO OK'
        df_ventas.loc[mask_ppd, 'Origen_Conciliacion'] = 'CFDI PPD (UUID)'

        print(f"Conciliados por UUID (PPD): {mask_ppd.sum()} registros")

    # ==========================================
    # PASO 3: CONCILIAR POR MONTO (Si no hubo UUID)
    # Ejemplo: Búsqueda de montos exactos en PUE que no hayan cruzado
    # ==========================================
    col_monto_pue = 'total' if 'total' in df_pue.columns else 'importe' if 'importe' in df_pue.columns else 'monto' if 'monto' in df_pue.columns else None

    if col_monto_pue:
        montos_pue = df_pue[col_monto_pue].dropna().unique()
        mask_monto = df_ventas[col_monto_ventas].isin(montos_pue) & (df_ventas['Estado_Conciliacion'] == 'PENDIENTE')

        df_ventas.loc[mask_monto, 'Estado_Conciliacion'] = 'REVISIÓN MONTO'
        df_ventas.loc[mask_monto, 'Origen_Conciliacion'] = 'CFDI PUE (Monto Similar)'

        print(f"Conciliados parciales por Monto (PUE): {mask_monto.sum()} registros")

    # Guardar resultados
    print(f"Guardando resultados en: {ruta_excel_salida}...")
    with pd.ExcelWriter(ruta_excel_salida, engine='openpyxl') as writer:
        df_ventas.to_excel(writer, sheet_name='VENTAS_PROCESADAS', index=False)
        # Puedes añadir más hojas resumen aquí

    print("¡Proceso completado exitosamente!")

if __name__ == "__main__":
    # Ejemplo de uso (Asume que hay un archivo datos_prueba.xlsx con estas hojas)
    # conciliar_ventas_vs_cfdi('datos_prueba.xlsx', 'resultado_conciliacion.xlsx')
    pass
