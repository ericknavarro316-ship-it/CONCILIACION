import pandas as pd
import warnings

warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# Importamos las funciones previas
from modulo_bancos_fix import limpiar_mp
from modulo_bancos import limpiar_modulo_bancos
from modulo_cfdi import limpiar_modulo_cfdi
from modulo_ventas_ajustado import limpiar_modulo_ventas_v2

def ejecutar_conciliacion_bbva(ruta_archivo):
    print("--- INICIANDO CONCILIACIÓN BBVA ---")

    # 1. INGESTA DE DATOS (Módulos P00)
    bancos = limpiar_modulo_bancos(ruta_archivo)
    cfdis = limpiar_modulo_cfdi(ruta_archivo)
    ventas = limpiar_modulo_ventas_v2(ruta_archivo)

    # Agregar columna de 'origen_split' (Petición del usuario: saber si viene combinado)
    df_ventas_bbva = ventas.get('VENTAS_BBVA', pd.DataFrame())
    if not df_ventas_bbva.empty:
        df_ventas_bbva['origen_split'] = df_ventas_bbva['bancos_cobro'].apply(
            lambda x: f"PAGO COMBINADO: {x}" if ',' in str(x) else "PAGO SENCILLO: BBVA"
        )
        df_ventas_bbva['cuenta_bancaria_cruce'] = None
        df_ventas_bbva['estado_cruce'] = 'PENDIENTE'

    # Filtrar diccionarios para obtener solo cuentas BBVA
    cuentas_bbva = {k: v for k, v in bancos.items() if k.startswith('BBVA_')}

    # 2. AGRUPAR VENTAS BBVA POR ID_VENTA
    if df_ventas_bbva.empty:
        print("No hay ventas BBVA para conciliar.")
        return

    # 'precio_real' es la columna de importe a cobrar en 'NOTA DE VENTA'
    if 'precio_real' not in df_ventas_bbva.columns:
        print("⚠️ No se encontró la columna 'precio_real' en Ventas. Cancelando cruce.")
        return

    # Agrupamos por id_venta y sumamos el precio_real (total del ticket)
    ventas_agrupadas = df_ventas_bbva.groupby('id_venta', as_index=False).agg({
        'precio_real': 'sum',
        'uuid': 'first' # Tomar el primero si lo hay
    })

    # 3. CRUCE CON TOLERANCIAS Y BÚSQUEDA DE ABONOS EN BBVA
    match_count = 0
    id_venta_a_cuenta = {} # Diccionario para propagar a CFDI {id_venta: cuenta_bbva}

    for _, grupo in ventas_agrupadas.iterrows():
        id_venta = grupo['id_venta']
        total_a_cobrar = grupo['precio_real']
        if pd.isna(total_a_cobrar) or total_a_cobrar <= 0:
            continue

        # Determinar tolerancia
        tolerancia = 1.0 if total_a_cobrar <= 50000 else 50.0

        match_encontrado = False

        # Buscar este abono en cada cuenta BBVA disponible
        for cuenta_nombre, df_banco in cuentas_bbva.items():
            if 'ABONO' not in df_banco.columns:
                continue

            # Buscar filas donde el ABONO esté dentro del margen (total_a_cobrar +/- tolerancia)
            # y que no hayan sido matcheadas antes ('ID_VENTA_CRUCE' == NaN)
            if 'ID_VENTA_CRUCE' not in df_banco.columns:
                df_banco['ID_VENTA_CRUCE'] = None

            abonos_libres = df_banco[pd.isna(df_banco['ID_VENTA_CRUCE']) & pd.notna(df_banco['ABONO'])]

            for idx_banco, abono_banco in abonos_libres.iterrows():
                abono_val = abono_banco['ABONO']
                diferencia = abs(abono_val - total_a_cobrar)

                if diferencia <= tolerancia:
                    # ¡HAY MATCH! 🚀
                    # 1. Marcar en Banco
                    cuentas_bbva[cuenta_nombre].at[idx_banco, 'ID_VENTA_CRUCE'] = id_venta
                    # 2. Guardar correspondencia para CFDI y Ventas
                    numero_cuenta_real = cuenta_nombre.replace('BBVA_', '')
                    id_venta_a_cuenta[id_venta] = numero_cuenta_real
                    match_encontrado = True
                    match_count += 1
                    break # Salir del bucle de abonos de esta cuenta

            if match_encontrado:
                break # Salir del bucle de buscar en otras cuentas BBVA

    # 4. ACTUALIZAR ESTADO EN EL DATAFRAME DETALLADO DE VENTAS BBVA
    for idx, venta in df_ventas_bbva.iterrows():
        id_v = venta['id_venta']
        if id_v in id_venta_a_cuenta:
            df_ventas_bbva.at[idx, 'estado_cruce'] = 'OK vs BANCO'
            df_ventas_bbva.at[idx, 'cuenta_bancaria_cruce'] = id_venta_a_cuenta[id_v]

    # 5. PROPAGAR A CFDI (Ingresos PUE y PPD)
    df_cfdi_pue = cfdis.get('CFDI_I_PUE', pd.DataFrame())
    df_cfdi_ppd = cfdis.get('CFDI_I_PPD', pd.DataFrame())

    # Asumimos que CFDI no tiene 'id_venta', así que cruzaremos el 'UUID' de la venta (si lo tiene)
    # y si está en el CFDI, le asignaremos la cuenta. (Ojo: requeriremos un mapeo si CFDI usa Folio)

    # Actualizamos el diccionario general de módulos (como en la App real)
    bancos.update(cuentas_bbva)
    ventas['VENTAS_BBVA'] = df_ventas_bbva

    print(f"✅ CRUCE BBVA FINALIZADO. Se encontraron {match_count} abonos conciliados automáticamente.")
    return bancos, ventas, cfdis

if __name__ == '__main__':
    ruta = 'CONCILIACION FEBRERO OK - copia.xlsm'
    b, v, c = ejecutar_conciliacion_bbva(ruta)

    print("\n--- EJEMPLOS DE VENTAS BBVA CON PAGO DIVIDIDO Y CRUCE ---")
    df_vbbva = v['VENTAS_BBVA']
    print(df_vbbva[['id_venta', 'precio_real', 'origen_split', 'estado_cruce', 'cuenta_bancaria_cruce']].head(10))
