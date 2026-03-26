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
    st.markdown("Ejecuta los motores de conciliación para cruzar las ventas operativas contra los estados de cuenta bancarios (SQL).")

    # BOTÓN PARA BBVA
    if st.button("🚀 Ejecutar Cruce BBVA", type="primary"):
        with st.spinner("Conciliando Ventas BBVA vs Abonos (Agrupando por ID_VENTA con tolerancias)..."):
            res = run_bbva_crosscheck()
            if "error" in res:
                st.error(res["error"])
            else:
                st.success(f"✅ ¡Cruce Finalizado! Se encontraron {res['matches']} abonos BBVA perfectamente conciliados.")
                st.info("Los resultados se han guardado en las tablas SQL: 'VENTAS_BBVA_CRUZADO' y 'BANCO_XXXXX_CRUZADO'")
                st.subheader("Vista previa de Ventas BBVA cruzadas exitosamente:")
                st.dataframe(res['sample'][['id_venta', 'precio_real', 'origen_split', 'estado_cruce', 'cuenta_bancaria_cruce']])

    # ESPACIO PARA MP (Siguiente iteración)
    st.button("⚙️ Ejecutar Cruce Mercado Pago (Próximamente)", disabled=True)

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
        st.subheader("Visualización Gráfica")

        # Gráfica simple de bloques de venta (volumen)
        datos_ventas = []
        for t in [x for x in tablas if x.startswith("VENTAS_") and not x.endswith("_CRUZADO")]:
            df = get_df_from_sql(t)
            datos_ventas.append({"Bloque": t.replace("VENTAS_", ""), "Cantidad Tickets": len(df)})

        if datos_ventas:
            df_grafico = pd.DataFrame(datos_ventas).set_index("Bloque")
            st.bar_chart(df_grafico)
