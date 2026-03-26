import streamlit as st
import pandas as pd
import os

# Módulos core
from modulo_bancos_fix import limpiar_mp
from modulo_bancos import limpiar_modulo_bancos
from modulo_cfdi import limpiar_modulo_cfdi
from modulo_ventas_ajustado import limpiar_modulo_ventas_v2
from database_sqlite import save_df_to_sql, get_df_from_sql, get_all_tables

# Motores de análisis
from engine_bbva import run_bbva_crosscheck
from engine_mp import run_mp_crosscheck
from engine_cfdi import run_cfdi_crosscheck

# Nuevas características avanzadas
from security import check_password
from export_excel import generate_final_report
from engine_egresos import run_egresos_crosscheck
from pdf_reader import parse_bank_pdf

st.set_page_config(page_title="ERP Conciliación PRO", layout="wide", page_icon="🏢")

# 1. AUTENTICACIÓN
if not check_password():
    st.stop()  # Detiene la carga del resto de la página hasta que la contraseña sea correcta.

# 2. INICIALIZACIÓN DE DB
if not os.path.exists("conciliacion_data.db"):
    import database_sqlite
    database_sqlite.init_db()

# ==========================================================
# MENÚ LATERAL
# ==========================================================
st.sidebar.title("🏢 Módulos Avanzados")
opciones = ["🏠 Ingesta (Excel / PDF)", "🏦 BANCOS", "📄 CFDI (Facturas)", "🛒 VENTAS", "📊 ANÁLISIS (Ingresos)", "💸 ANÁLISIS (Egresos)", "📈 DASHBOARD & REPORTES"]
eleccion = st.sidebar.radio("Navegar:", opciones)

# Logout en Sidebar
st.sidebar.divider()
if st.sidebar.button("🔒 Cerrar Sesión"):
    st.session_state["password_correct"] = False
    st.rerun()

# ==========================================================
# 🏠 INICIO E INGESTA
# ==========================================================
if eleccion == "🏠 Ingesta (Excel / PDF)":
    st.title("Procesamiento de Archivos (ETL)")

    # Pestañas para subir Excel o PDF
    tab1, tab2 = st.tabs(["Subir Archivo Crudo (Excel)", "Subir Estado de Cuenta (PDF)"])

    with tab1:
        st.markdown("El sistema limpiará automáticamente Bancos, Ventas y separará los CFDI (PUE/PPD).")
        archivo_subido = st.file_uploader("📂 Cargar Excel", type=['xlsx', 'xlsm'])

        if st.button("Procesar Archivo y Guardar en BD", type="primary"):
            if archivo_subido is not None:
                with st.spinner("Procesando Bancos..."):
                    bancos = limpiar_modulo_bancos(archivo_subido)
                    for nombre_cuenta, df_banco in bancos.items():
                        save_df_to_sql(df_banco, f"BANCO_{nombre_cuenta.replace('BBVA_', '')}")

                with st.spinner("Procesando CFDI..."):
                    cfdis = limpiar_modulo_cfdi(archivo_subido)
                    for nombre_cfdi, df_cfdi in cfdis.items():
                        save_df_to_sql(df_cfdi, f"CFDI_{nombre_cfdi}")

                with st.spinner("Procesando Ventas..."):
                    ventas = limpiar_modulo_ventas_v2(archivo_subido)
                    for nombre_venta, df_venta in ventas.items():
                        save_df_to_sql(df_venta, nombre_venta)

                st.success("✅ ¡Datos guardados en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo primero.")

    with tab2:
        st.subheader("Lector Inteligente de PDFs Bancarios")
        pdf_subido = st.file_uploader("📂 Cargar Estado de Cuenta (PDF)", type=['pdf'])
        if st.button("Procesar PDF"):
            if pdf_subido:
                parse_bank_pdf(pdf_subido)
            else:
                 st.warning("Sube un PDF primero.")

# ==========================================================
# MÓDULOS DE VISUALIZACIÓN BÁSICA
# ==========================================================
elif eleccion == "🏦 BANCOS":
    st.title("🏦 Módulo BANCOS")
    tablas = [t for t in get_all_tables() if t.startswith("BANCO_")]
    if not tablas: st.warning("La BD está vacía.")
    else:
        cuenta = st.selectbox("Selecciona cuenta:", tablas)
        st.dataframe(get_df_from_sql(cuenta), use_container_width=True)

elif eleccion == "📄 CFDI (Facturas)":
    st.title("📄 Módulo CFDI")
    tablas = [t for t in get_all_tables() if t.startswith("CFDI_")]
    if not tablas: st.warning("La BD está vacía.")
    else:
        cfdi = st.selectbox("Selecciona bloque fiscal:", tablas)
        st.dataframe(get_df_from_sql(cfdi), use_container_width=True)

elif eleccion == "🛒 VENTAS":
    st.title("🛒 Módulo VENTAS")
    tablas = [t for t in get_all_tables() if t.startswith("VENTAS_") and not t.endswith("CRUZADO")]
    if not tablas: st.warning("La BD está vacía.")
    else:
        bloque = st.selectbox("Selecciona bloque operativo:", tablas)
        st.dataframe(get_df_from_sql(bloque), use_container_width=True)

# ==========================================================
# 📊 ANÁLISIS INGRESOS
# ==========================================================
elif eleccion == "📊 ANÁLISIS (Ingresos)":
    st.title("📊 Motores de Conciliación de Ingresos")

    col1, col2, col3 = st.columns(3)
    if col1.button("🚀 Cruce BBVA", type="primary"):
        res = run_bbva_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res['matches']} abonos BBVA conciliados.")

    if col2.button("⚙️ Cruce Mercado Pago", type="primary"):
        res = run_mp_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res['matches']} tickets MP conciliados.")

    if col3.button("📄 Propagar a CFDI Ingresos", type="primary"):
        res = run_cfdi_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res.get('matches_pue',0)} PUE / {res.get('matches_ppd',0)} PPD.")

    st.divider()
    st.subheader("⚠️ Alertas de Diferencias (Ventas sin Cobro)")
    tablas = get_all_tables()
    df_alertas_bbva = pd.DataFrame()
    df_alertas_mp = pd.DataFrame()

    if "VENTAS_BBVA_CRUZADO" in tablas:
        df = get_df_from_sql("VENTAS_BBVA_CRUZADO")
        if not df.empty and 'estado_cruce' in df.columns: df_alertas_bbva = df[df['estado_cruce'] == 'PENDIENTE']

    if "VENTAS_MP_CRUZADO" in tablas:
        df = get_df_from_sql("VENTAS_MP_CRUZADO")
        if not df.empty and 'estado_cruce' in df.columns: df_alertas_mp = df[df['estado_cruce'] == 'PENDIENTE']

    tab_a, tab_b = st.tabs(["Pendientes BBVA", "Pendientes MP"])
    with tab_a: st.dataframe(df_alertas_bbva, use_container_width=True)
    with tab_b: st.dataframe(df_alertas_mp, use_container_width=True)

# ==========================================================
# 💸 ANÁLISIS EGRESOS
# ==========================================================
elif eleccion == "💸 ANÁLISIS (Egresos)":
    st.title("💸 Motor de Conciliación de Egresos")
    st.markdown("Cruza las **Facturas de Gastos (CFDI E PUE)** contra los **Cargos (Salidas)** del banco BBVA.")

    if st.button("💳 Ejecutar Cruce Egresos (CFDI E PUE vs Bancos BBVA)", type="primary"):
        with st.spinner("Buscando cargos en cuentas BBVA..."):
            res = run_egresos_crosscheck()
            if "error" in res: st.error(res["error"])
            else: st.success(f"✅ ¡Cruce Exitoso! {res['matches']} Egresos PUE encontrados en el banco.")

    st.subheader("Gastos Pendientes de Identificar en Banco")
    tablas = get_all_tables()
    if "CFDI_CFDI_E_PUE_CRUZADO" in tablas:
         df_egresos = get_df_from_sql("CFDI_CFDI_E_PUE_CRUZADO")
         if not df_egresos.empty and 'estado_cruce_egreso' in df_egresos.columns:
             pendientes = df_egresos[df_egresos['estado_cruce_egreso'] == 'PENDIENTE BANCARIO']
             st.metric("Total Facturas Gasto Sin Salida de Banco Visible", len(pendientes))
             st.dataframe(pendientes, use_container_width=True)

# ==========================================================
# 📈 DASHBOARD Y REPORTES
# ==========================================================
elif eleccion == "📈 DASHBOARD & REPORTES":
    st.title("📈 Tablero Ejecutivo y Generador de Reportes")

    # 1. Botón de Exportación Excel (Nuevo)
    st.subheader("📦 Descargar Consolidado Gerencial")
    st.markdown("Genera un libro de Excel con múltiples pestañas (Ventas OK, Faltantes, Fiscal) usando la información procesada.")

    excel_bytes = generate_final_report()
    st.download_button(
        label="📥 Descargar Reporte Final Mensual (.xlsx)",
        data=excel_bytes,
        file_name="Reporte_Gerencial_Conciliacion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

    st.divider()

    # 2. Métricas (Igual que antes)
    col1, col2, col3 = st.columns(3)
    tablas = get_all_tables()

    total_bbva = 0
    bancos_bbva = [t for t in tablas if t.startswith("BANCO_") and t.replace("BANCO_", "").isdigit()]
    for t in bancos_bbva:
        df = get_df_from_sql(t)
        if 'ABONO' in df.columns:
            total_bbva += pd.to_numeric(df['ABONO'], errors='coerce').sum()
    col1.metric("Total Ingresado (BBVA)", f"${total_bbva:,.2f}")

    total_ventas_bbva = 0
    df_vbbva = get_df_from_sql("VENTAS_BBVA")
    if not df_vbbva.empty and 'precio_real' in df_vbbva.columns:
        total_ventas_bbva = pd.to_numeric(df_vbbva['precio_real'], errors='coerce').sum()
    col2.metric("Total Ventas (Bloque BBVA)", f"${total_ventas_bbva:,.2f}")

    avance = "0%"
    df_cruzadas = get_df_from_sql("VENTAS_BBVA_CRUZADO")
    if not df_cruzadas.empty:
        cruzadas = len(df_cruzadas[df_cruzadas['estado_cruce'] == 'OK vs BANCO'])
        total = len(df_cruzadas)
        avance = f"{(cruzadas/total)*100:.1f}%" if total > 0 else "0%"
    col3.metric("Avance Conciliación BBVA (Por Tickets)", avance)
