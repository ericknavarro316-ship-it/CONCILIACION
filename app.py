import streamlit as st
import pandas as pd
import os

# Importamos módulos y utilidades
from modulo_bancos_fix import limpiar_mp
from modulo_bancos import limpiar_modulo_bancos
from modulo_cfdi import limpiar_modulo_cfdi
from modulo_ventas_ajustado import limpiar_modulo_ventas_v2
from database_sqlite import save_df_to_sql, get_df_from_sql, get_all_tables
from engine_bbva import run_bbva_crosscheck
from engine_mp import run_mp_crosscheck
from engine_cfdi import run_cfdi_crosscheck

st.set_page_config(page_title="ERP Conciliación", layout="wide", page_icon="🏦")

if not os.path.exists("conciliacion_data.db"):
    import database_sqlite
    database_sqlite.init_db()

# ==========================================================
# MENÚ LATERAL (SIDEBAR)
# ==========================================================
st.sidebar.title("🗂️ Módulos")
opciones = ["🏠 Inicio e Ingesta", "🏦 BANCOS", "📄 CFDI", "🛒 VENTAS", "📊 ANÁLISIS (Cruces)", "📈 DASHBOARD"]
eleccion = st.sidebar.radio("Ir a:", opciones)

# ==========================================================
# 🏠 INICIO E INGESTA
# ==========================================================
if eleccion == "🏠 Inicio e Ingesta":
    st.title("Sistema Integral de Conciliación")
    st.markdown("Sube tu archivo crudo (Excel mensual). La aplicación procesará la información, la limpiará y la guardará de forma permanente en tu base de datos **SQL Local**.")

    archivo_subido = st.file_uploader("📂 Cargar Excel Crudo", type=['xlsx', 'xlsm'])

    if st.button("Procesar Archivo y Guardar en SQL", type="primary"):
        if archivo_subido is not None:
            with st.spinner("Procesando Módulo Bancos..."):
                bancos = limpiar_modulo_bancos(archivo_subido)
                for nombre_cuenta, df_banco in bancos.items():
                    save_df_to_sql(df_banco, f"BANCO_{nombre_cuenta.replace('BBVA_', '')}")

            with st.spinner("Procesando Módulo CFDI..."):
                cfdis = limpiar_modulo_cfdi(archivo_subido)
                for nombre_cfdi, df_cfdi in cfdis.items():
                    save_df_to_sql(df_cfdi, f"CFDI_{nombre_cfdi}")

            with st.spinner("Procesando Módulo Ventas..."):
                ventas = limpiar_modulo_ventas_v2(archivo_subido)
                for nombre_venta, df_venta in ventas.items():
                    save_df_to_sql(df_venta, nombre_venta)

            st.success("✅ ¡Datos procesados, limpios y guardados en la Base de Datos SQL exitosamente!")
        else:
            st.warning("⚠️ Primero sube un archivo.")

# ==========================================================
# 🏦 MÓDULO BANCOS
# ==========================================================
elif eleccion == "🏦 BANCOS":
    st.title("🏦 Módulo BANCOS")
    tablas = get_all_tables()
    tablas_bancos = [t for t in tablas if t.startswith("BANCO_")]

    if not tablas_bancos:
         st.warning("La base de datos está vacía. Sube un archivo en 'Inicio' primero.")
    else:
         cuenta_seleccionada = st.selectbox("Selecciona una cuenta bancaria a visualizar:", tablas_bancos)
         df = get_df_from_sql(cuenta_seleccionada)
         col1, col2 = st.columns(2)
         col1.metric(f"Registros en {cuenta_seleccionada}", len(df))
         if 'ABONO' in df.columns:
              col2.metric("Total Ingresado (Abonos)", f"${pd.to_numeric(df['ABONO'], errors='coerce').sum():,.2f}")
         st.dataframe(df, use_container_width=True)

# ==========================================================
# 📄 MÓDULO CFDI
# ==========================================================
elif eleccion == "📄 CFDI":
    st.title("📄 Módulo CFDI (Facturación SAT)")
    tablas = get_all_tables()
    tablas_cfdi = [t for t in tablas if t.startswith("CFDI_")]

    if not tablas_cfdi:
         st.warning("La base de datos está vacía. Sube un archivo en 'Inicio' primero.")
    else:
         cfdi_seleccionado = st.selectbox("Selecciona un bloque de facturación:", tablas_cfdi)
         df = get_df_from_sql(cfdi_seleccionado)
         st.metric(f"Comprobantes en {cfdi_seleccionado}", len(df))
         st.dataframe(df, use_container_width=True)

# ==========================================================
# 🛒 MÓDULO VENTAS
# ==========================================================
elif eleccion == "🛒 VENTAS":
    st.title("🛒 Módulo VENTAS")
    tablas = get_all_tables()
    tablas_ventas = [t for t in tablas if t.startswith("VENTAS_") and not t.endswith("_CRUZADO")]

    if not tablas_ventas:
         st.warning("La base de datos está vacía. Sube un archivo en 'Inicio' primero.")
    else:
         bloque_seleccionado = st.selectbox("Selecciona un bloque operativo:", tablas_ventas)
         df = get_df_from_sql(bloque_seleccionado)
         st.metric(f"Ventas totales en bloque {bloque_seleccionado}", len(df))
         st.dataframe(df, use_container_width=True)

# ==========================================================
# 📊 ANÁLISIS (Cruces)
# ==========================================================
elif eleccion == "📊 ANÁLISIS (Cruces)":
    st.title("📊 Análisis y Conciliación Automática")
    st.markdown("Ejecuta los motores de conciliación para cruzar las ventas operativas contra los estados de cuenta bancarios, y luego propagar al SAT (CFDI).")

    col1, col2, col3 = st.columns(3)

    # BOTÓN PARA BBVA
    with col1:
        if st.button("🚀 Ejecutar Cruce BBVA", type="primary", use_container_width=True):
            with st.spinner("Conciliando BBVA..."):
                res = run_bbva_crosscheck()
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(f"✅ BBVA: {res['matches']} abonos conciliados.")

    # BOTÓN PARA MERCADO PAGO
    with col2:
        if st.button("⚙️ Ejecutar Cruce Mercado Pago", type="primary", use_container_width=True):
            with st.spinner("Conciliando Mercado Pago..."):
                res = run_mp_crosscheck()
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(f"✅ Mercado Pago: {res['matches']} tickets conciliados.")

    # BOTÓN PARA CFDI
    with col3:
        if st.button("📄 Propagar a CFDI", type="primary", use_container_width=True):
            with st.spinner("Buscando UUIDs cruzados en CFDI PUE y PPD..."):
                res = run_cfdi_crosscheck()
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(f"✅ CFDI: {res.get('matches_pue', 0)} PUE y {res.get('matches_ppd', 0)} PPD Completados.")

    st.divider()

    # ==========================================
    # ALERTAS Y DIFERENCIAS (DASHBOARD OPERATIVO)
    # ==========================================
    st.subheader("⚠️ Alertas de Diferencias (Pendientes Operativos)")

    tablas = get_all_tables()
    df_alertas_bbva = pd.DataFrame()
    df_alertas_mp = pd.DataFrame()

    if "VENTAS_BBVA_CRUZADO" in tablas:
        df_bbva = get_df_from_sql("VENTAS_BBVA_CRUZADO")
        if not df_bbva.empty and 'estado_cruce' in df_bbva.columns:
            df_alertas_bbva = df_bbva[df_bbva['estado_cruce'] == 'PENDIENTE']

    if "VENTAS_MP_CRUZADO" in tablas:
        df_mp = get_df_from_sql("VENTAS_MP_CRUZADO")
        if not df_mp.empty and 'estado_cruce' in df_mp.columns:
            df_alertas_mp = df_mp[df_mp['estado_cruce'] == 'PENDIENTE']

    if df_alertas_bbva.empty and df_alertas_mp.empty:
        st.info("No hay tablas cruzadas aún o no hay ventas pendientes. (Ejecuta los cruces primero).")
    else:
        tab1, tab2 = st.tabs(["Faltantes en Banco BBVA", "Faltantes en Mercado Pago"])
        with tab1:
            st.metric("Ventas BBVA No Encontradas en Banco", len(df_alertas_bbva))
            st.dataframe(df_alertas_bbva[['id_venta', 'precio_real', 'fecha', 'origen_split', 'estado_cruce']], use_container_width=True)
        with tab2:
            st.metric("Transacciones Mercado Pago No Encontradas en Banco", len(df_alertas_mp))
            st.dataframe(df_alertas_mp[['id_venta', 'numero_transaccion', 'precio_real', 'fecha', 'origen_split', 'estado_cruce']], use_container_width=True)


# ==========================================================
# 📈 DASHBOARD
# ==========================================================
elif eleccion == "📈 DASHBOARD":
    st.title("📈 Tablero Ejecutivo (Dashboard)")
    st.markdown("Resumen global del estado de la conciliación.")

    tablas = get_all_tables()
    if not tablas:
        st.warning("No hay datos en SQL para graficar.")
    else:
        col1, col2, col3 = st.columns(3)

        # Métrica 1: Total de Abonos BBVA
        total_bbva = 0
        bancos_bbva = [t for t in tablas if t.startswith("BANCO_") and t.replace("BANCO_", "").isdigit()]
        for t in bancos_bbva:
            df = get_df_from_sql(t)
            if 'ABONO' in df.columns:
                total_bbva += pd.to_numeric(df['ABONO'], errors='coerce').sum()
        col1.metric("Total Ingresado (BBVA)", f"${total_bbva:,.2f}")

        # Métrica 2: Total Ventas BBVA
        total_ventas_bbva = 0
        df_vbbva = get_df_from_sql("VENTAS_BBVA")
        if not df_vbbva.empty and 'precio_real' in df_vbbva.columns:
            total_ventas_bbva = pd.to_numeric(df_vbbva['precio_real'], errors='coerce').sum()
        col2.metric("Total Ventas (Bloque BBVA)", f"${total_ventas_bbva:,.2f}")

        # Métrica 3: Avance Conciliación BBVA
        avance = "0%"
        df_cruzadas = get_df_from_sql("VENTAS_BBVA_CRUZADO")
        if not df_cruzadas.empty:
            cruzadas = len(df_cruzadas[df_cruzadas['estado_cruce'] == 'OK vs BANCO'])
            total = len(df_cruzadas)
            avance = f"{(cruzadas/total)*100:.1f}%" if total > 0 else "0%"
        col3.metric("Avance Conciliación BBVA (Por Tickets)", avance)

        st.divider()
        st.subheader("Visualización Operativa")

        # Gráfica simple de bloques de venta (volumen)
        datos_ventas = []
        for t in [x for x in tablas if x.startswith("VENTAS_") and not x.endswith("_CRUZADO")]:
            df = get_df_from_sql(t)
            datos_ventas.append({"Bloque": t.replace("VENTAS_", ""), "Cantidad Tickets": len(df)})

        if datos_ventas:
            df_grafico = pd.DataFrame(datos_ventas).set_index("Bloque")
            st.bar_chart(df_grafico)
