import streamlit as st
import pandas as pd
import os

# Importamos nuestros scripts que creamos paso a paso
from modulo_bancos_fix import limpiar_mp
from modulo_bancos import limpiar_modulo_bancos
from modulo_cfdi import limpiar_modulo_cfdi
from modulo_ventas_ajustado import limpiar_modulo_ventas_v2
from database_sqlite import save_df_to_sql, get_df_from_sql, get_all_tables

st.set_page_config(page_title="ERP Conciliación", layout="wide", page_icon="🏦")

# Inicializamos la base de datos SQL local si no existe
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
    st.markdown("Sube tu archivo crudo (Excel mensual). La aplicación procesará la información, la limpiará y la guardará de forma permanente en tu base de datos **SQL Local**, sin depender de descargar Excels intermedios.")

    archivo_subido = st.file_uploader("📂 Cargar Excel Crudo (ej. CONCILIACION FEBRERO OK)", type=['xlsx', 'xlsm'])

    if st.button("Procesar Archivo y Guardar en SQL", type="primary"):
        if archivo_subido is not None:
            with st.spinner("Procesando Módulo Bancos..."):
                bancos = limpiar_modulo_bancos(archivo_subido)
                for nombre_cuenta, df_banco in bancos.items():
                    save_df_to_sql(df_banco, f"BANCO_{nombre_cuenta}")

            with st.spinner("Procesando Módulo CFDI..."):
                cfdis = limpiar_modulo_cfdi(archivo_subido)
                for nombre_cfdi, df_cfdi in cfdis.items():
                    save_df_to_sql(df_cfdi, f"CFDI_{nombre_cfdi}")

            with st.spinner("Procesando Módulo Ventas..."):
                ventas = limpiar_modulo_ventas_v2(archivo_subido)
                for nombre_venta, df_venta in ventas.items():
                    save_df_to_sql(df_venta, nombre_venta)

            st.success("✅ ¡Datos procesados, limpios y guardados en la Base de Datos SQL exitosamente!")
            st.info("Ahora puedes navegar por los demás módulos en el menú lateral para ver la información almacenada.")
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
              col2.metric("Total Ingresado (Abonos)", f"${df['ABONO'].sum():,.2f}")

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
    tablas_ventas = [t for t in tablas if t.startswith("VENTAS_")]

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
    st.title("📊 Análisis y Conciliación")
    st.markdown("En este módulo cruzaremos la base de datos SQL para encontrar los empates operativos vs bancarios vs SAT. *(El motor completo se irá construyendo paso a paso)*.")

    # Aquí irá el motor completo de BBVA, luego el de Mercado Pago
    st.info("Actualmente estamos validando BBVA. ¡En la siguiente fase conectaremos el motor completo de cruce BBVA y Mercado Pago a este botón!")

# ==========================================================
# 📈 DASHBOARD
# ==========================================================
elif eleccion == "📈 DASHBOARD":
    st.title("📈 Tablero Ejecutivo")
    st.markdown("Este será el resumen global de la salud de tu negocio, con gráficas, totales pendientes de facturar, y alertas de cruces fallidos.")
    # Aquí haremos métricas globales
