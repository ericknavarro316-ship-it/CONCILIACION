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
from engine_o00 import run_o01_preclasificar_bancos, run_o07_conciliar_pagos_e

# Nuevas características avanzadas
from security import check_password
from export_excel import generate_final_report
from engine_egresos import run_egresos_crosscheck
from pdf_reader import parse_bank_pdf

st.set_page_config(page_title="ERP Conciliación PRO", layout="wide", page_icon="🏢", initial_sidebar_state="collapsed")

# 1. ESTILOS CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 1. AUTENTICACIÓN (DESACTIVADA TEMPORALMENTE PARA PRUEBAS)
# if not check_password():
#     st.stop()

# 2. INICIALIZACIÓN DE DB
if not os.path.exists("conciliacion_data.db"):
    import database_sqlite
    database_sqlite.init_db()

# ==========================================================
# MENÚ LATERAL
# ==========================================================
st.sidebar.title("🏢 Módulos Avanzados")
opciones = ["🏠 Ingesta (Excel / PDF)", "🏦 BANCOS", "📄 CFDI (Facturas)", "🛒 VENTAS", "📊 O00: PRE-CLÁSICOS FISCALES", "📈 I00: CRUCE INGRESOS (Ventas)", "💸 CRUCE EGRESOS", "📈 DASHBOARD & REPORTES"]
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

    st.markdown("Carga tus archivos de forma individual o un archivo consolidado.")

    # Pestañas para subir Excel o PDF
    tab1, tab2, tab3, tab4 = st.tabs([
        "Carga Consolidada (Mega Excel)",
        "Carga de Bancos",
        "Carga de Ventas",
        "Carga de CFDI"
    ])

    with tab1:
        st.markdown("### Carga de Archivo Consolidado")
        st.markdown("Sube un solo archivo Excel con todas las hojas (Bancos, Ventas, CFDI).")
        archivo_subido = st.file_uploader("📂 Cargar Mega Excel", type=['xlsx', 'xlsm'], key="consolidado")

        if st.button("Procesar Archivo Consolidado y Guardar en BD", type="primary", key="btn_consolidado"):
            if archivo_subido is not None:
                with st.spinner("Procesando Bancos..."):
                    bancos = limpiar_modulo_bancos(archivo_subido)
                    for nombre_cuenta, df_banco in bancos.items():
                        # MP_DETALLE is an auxiliary detail table, not a standard bank statement.
                        # We save it without the BANCO_ prefix to isolate it from the "BANCOS" UI.
                        if nombre_cuenta == "MP_DETALLE":
                            save_df_to_sql(df_banco, "AUX_MP_DETALLE")
                        else:
                            save_df_to_sql(df_banco, f"BANCO_{nombre_cuenta}")

                with st.spinner("Procesando CFDI..."):
                    cfdis = limpiar_modulo_cfdi(archivo_subido)
                    for nombre_cfdi, df_cfdi in cfdis.items():
                        save_df_to_sql(df_cfdi, f"CFDI_{nombre_cfdi}")

                with st.spinner("Procesando Ventas..."):
                    ventas = limpiar_modulo_ventas_v2(archivo_subido)
                    for nombre_venta, df_venta in ventas.items():
                        save_df_to_sql(df_venta, nombre_venta)

                st.success("✅ ¡Datos consolidados guardados en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo consolidado primero.")

    with tab2:
        st.markdown("### Carga de Bancos (Individual)")
        st.markdown("Sube archivos de estados de cuenta (Excel o PDF).")
        archivo_banco_excel = st.file_uploader("📂 Cargar Banco (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="banco_excel")
        archivo_banco_pdf = st.file_uploader("📂 Cargar Estado de Cuenta (PDF)", type=['pdf'], accept_multiple_files=True, key="banco_pdf")

        if st.button("Procesar Bancos", type="primary", key="btn_bancos"):
            procesados = False
            if archivo_banco_excel:
                for archivo in archivo_banco_excel:
                    with st.spinner(f"Procesando {archivo.name}..."):
                        bancos = limpiar_modulo_bancos(archivo)
                        for nombre_cuenta, df_banco in bancos.items():
                            if nombre_cuenta == "MP_DETALLE":
                                save_df_to_sql(df_banco, "AUX_MP_DETALLE")
                            else:
                                save_df_to_sql(df_banco, f"BANCO_{nombre_cuenta}")
                procesados = True

            if archivo_banco_pdf:
                for pdf in archivo_banco_pdf:
                    parse_bank_pdf(pdf)
                procesados = True

            if procesados:
                st.success("✅ ¡Bancos guardados en la Base de Datos SQL!")
            else:
                 st.warning("Sube un archivo de banco primero.")

    with tab3:
        st.markdown("### Carga de Notas de Venta (Individual)")
        st.markdown("Sube los archivos que contengan las ventas registradas.")
        archivo_ventas = st.file_uploader("📂 Cargar Ventas (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="ventas")

        if st.button("Procesar Ventas", type="primary", key="btn_ventas"):
            if archivo_ventas:
                for archivo in archivo_ventas:
                    with st.spinner(f"Procesando {archivo.name}..."):
                        ventas = limpiar_modulo_ventas_v2(archivo)
                        for nombre_venta, df_venta in ventas.items():
                            save_df_to_sql(df_venta, nombre_venta)
                st.success("✅ ¡Ventas guardadas en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo de ventas primero.")

    with tab4:
        st.markdown("### Carga de CFDI (Individual)")
        st.markdown("Sube los reportes del SAT (Ingresos/Egresos).")
        archivo_cfdi = st.file_uploader("📂 Cargar CFDI (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="cfdi")

        if st.button("Procesar CFDI", type="primary", key="btn_cfdi"):
            if archivo_cfdi:
                for archivo in archivo_cfdi:
                    with st.spinner(f"Procesando {archivo.name}..."):
                        cfdis = limpiar_modulo_cfdi(archivo)
                        for nombre_cfdi, df_cfdi in cfdis.items():
                            save_df_to_sql(df_cfdi, f"CFDI_{nombre_cfdi}")
                st.success("✅ ¡CFDI guardados en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo CFDI primero.")

# ==========================================================
# MÓDULOS DE VISUALIZACIÓN BÁSICA
# ==========================================================
elif eleccion == "🏦 BANCOS":
    st.title("🏦 Módulo BANCOS")
    tablas = [t for t in get_all_tables() if t.startswith("BANCO_")]

    if not tablas:
        st.warning("La BD está vacía o no hay bancos procesados.")
    else:
        # Agrupar dinámicamente las tablas por el nombre del banco
        bancos_dict = {}
        for tabla in tablas:
            # Formato esperado: BANCO_NOMBREBANCO_CUENTA o BANCO_NOMBREBANCO
            partes = tabla.split('_')

            # Normalizar nombres comunes si es necesario
            if "MP" in tabla.upper() or "MERCADO PAGO" in tabla.upper() or "MERCADOPAGO" in tabla.upper():
                banco_key = "Mercado Pago"
            elif len(partes) >= 2:
                # Extraer la segunda parte (el nombre del banco), por ejemplo "BBVA" de "BANCO_BBVA_123"
                banco_key = partes[1].upper()
            else:
                banco_key = "Otros"

            if banco_key not in bancos_dict:
                bancos_dict[banco_key] = []
            bancos_dict[banco_key].append(tabla)

        # Ordenar las llaves para que se vea mejor (opcional: poner "Otros" al final si existiera)
        nombres_bancos = sorted(list(bancos_dict.keys()))
        if "Otros" in nombres_bancos:
            nombres_bancos.remove("Otros")
            nombres_bancos.append("Otros")

        # Crear pestañas dinámicas
        tabs = st.tabs(nombres_bancos)

        # Función auxiliar para renderizar el panel de control de un banco
        def render_bank_panel(cuenta_sel, key_prefix):
            df = get_df_from_sql(cuenta_sel)
            if df.empty:
                st.info("La tabla seleccionada no contiene registros.")
                return

            # --- PREPARACIÓN DE DATOS ---
            # Asegurar que FECHA es datetime para poder filtrar
            if 'FECHA' in df.columns:
                df['FECHA_DT'] = pd.to_datetime(df['FECHA'], errors='coerce')
                # Obtener lista de meses únicos (ej. "2024-01")
                meses_unicos = df['FECHA_DT'].dt.to_period('M').dropna().unique()
                lista_meses = ["Todos"] + sorted([str(m) for m in meses_unicos], reverse=True)
            else:
                lista_meses = ["Todos"]
                df['FECHA_DT'] = pd.NaT

            # --- UI: FILTROS SUPERIORES ---
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                mes_sel = st.selectbox("📅 Filtrar por Mes:", lista_meses, key=f"mes_{key_prefix}")

            with col2:
                # Determinar min y max dates
                min_date = df['FECHA_DT'].min() if not pd.isna(df['FECHA_DT'].min()) else None
                max_date = df['FECHA_DT'].max() if not pd.isna(df['FECHA_DT'].max()) else None

                if min_date and max_date:
                    col2_1, col2_2 = st.columns(2)
                    with col2_1:
                        fecha_desde = st.date_input(
                            "Desde:",
                            value=None,
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"desde_{key_prefix}"
                        )
                    with col2_2:
                        fecha_hasta = st.date_input(
                            "Hasta:",
                            value=None,
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"hasta_{key_prefix}"
                        )
                else:
                    fecha_desde = None
                    fecha_hasta = None
                    st.write("Sin fechas válidas")

            with col3:
                busqueda = st.text_input("🔍 Buscar (Concepto, Referencia, Monto, etc):", "", key=f"buscar_{key_prefix}")

            # --- APLICAR FILTROS ---
            df_filtrado = df.copy()

            # Filtro por Mes
            if mes_sel != "Todos":
                df_filtrado = df_filtrado[df_filtrado['FECHA_DT'].dt.strftime('%Y-%m') == mes_sel]

            # Filtro Rango Fechas
            if fecha_desde is not None:
                df_filtrado = df_filtrado[df_filtrado['FECHA_DT'].dt.date >= fecha_desde]
            if fecha_hasta is not None:
                df_filtrado = df_filtrado[df_filtrado['FECHA_DT'].dt.date <= fecha_hasta]

            # Filtro por Búsqueda (Texto Libre)
            if busqueda:
                busqueda_lower = str(busqueda).lower()
                # Buscar en todas las columnas convirtiendo la fila a string
                mask_busqueda = df_filtrado.astype(str).apply(lambda row: row.str.lower().str.contains(busqueda_lower).any(), axis=1)
                df_filtrado = df_filtrado[mask_busqueda]

            # --- UI: MÉTRICAS RESUMEN ---
            # Calcular totales del dataframe filtrado
            tot_cargo = pd.to_numeric(df_filtrado['CARGO'], errors='coerce').sum() if 'CARGO' in df_filtrado.columns else 0
            tot_abono = pd.to_numeric(df_filtrado['ABONO'], errors='coerce').sum() if 'ABONO' in df_filtrado.columns else 0

            # Obtener el último saldo (ordenando por fecha si es posible, o simplemente el último de la lista)
            saldo_final = 0
            if 'SALDO' in df_filtrado.columns and not df_filtrado.empty:
                 # Si la fecha está ordenada ascendente, el último registro tiene el saldo final
                 ultimo_saldo = pd.to_numeric(df_filtrado['SALDO'], errors='coerce').dropna().tail(1)
                 if not ultimo_saldo.empty:
                     saldo_final = ultimo_saldo.iloc[0]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🟢 Total Abonos", f"${tot_abono:,.2f}")
            m2.metric("🔴 Total Cargos", f"${tot_cargo:,.2f}")
            m3.metric("💰 Saldo Final", f"${saldo_final:,.2f}")
            m4.metric("📝 Movimientos", len(df_filtrado))

            # --- UI: TABLA DE DATOS ---
            # Quitar columna auxiliar FECHA_DT
            df_mostrar = df_filtrado.drop(columns=['FECHA_DT']) if 'FECHA_DT' in df_filtrado.columns else df_filtrado

            # Reordenar columnas a 10 columnas estándar si existen
            columnas_orden = ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']
            cols_existentes = [c for c in columnas_orden if c in df_mostrar.columns]
            otras_cols = [c for c in df_mostrar.columns if c not in cols_existentes]
            df_mostrar = df_mostrar[cols_existentes + otras_cols]

            # Reemplazar explícitamente "None" y nulls con cadena vacía para limpiar la UI
            df_mostrar = df_mostrar.fillna("")
            df_mostrar = df_mostrar.replace("None", "")

            # Asegurar que las fechas se vean bonitas
            if 'FECHA' in df_mostrar.columns:
                df_mostrar['FECHA'] = pd.to_datetime(df_mostrar['FECHA'], errors='coerce').dt.strftime('%d/%m/%Y')

            # Formatear montos para que se vean como moneda ($)
            for col_moneda in ['CARGO', 'ABONO', 'SALDO']:
                if col_moneda in df_mostrar.columns:
                    # Convertir a float y luego a string formateado
                    df_mostrar[col_moneda] = pd.to_numeric(df_mostrar[col_moneda], errors='coerce').apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")

            # Reemplazar el literal 'NaT' por cadena vacía
            df_mostrar = df_mostrar.replace("NaT", "")

            # Mostrar dataframe estilizado
            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)


        # Llenar cada pestaña dinámicamente
        for i, nombre_banco in enumerate(nombres_bancos):
            with tabs[i]:
                st.subheader(f"Cuentas {nombre_banco}")
                tablas_banco = bancos_dict[nombre_banco]

                # Usar selectbox para elegir la tabla específica de ese banco
                cuenta_sel = st.selectbox(f"Selecciona cuenta:", tablas_banco, key=f"sel_{nombre_banco}")

                st.divider()
                # Llamar a la función que dibuja filtros y tabla
                render_bank_panel(cuenta_sel, key_prefix=f"{nombre_banco}_{cuenta_sel}")

elif eleccion == "📄 CFDI (Facturas)":
    st.title("📄 Módulo CFDI")

    tablas_todas = get_all_tables()
    tablas_cfdi_ingresos = [t for t in tablas_todas if t.startswith("CFDI_I_") or t == "PAGOS_I"]
    tablas_cfdi_egresos = [t for t in tablas_todas if t.startswith("CFDI_E_") or t == "PAGOS_E"]

    if not tablas_cfdi_ingresos and not tablas_cfdi_egresos:
        st.warning("La BD está vacía o no hay CFDI/Pagos procesados.")
    else:
        # Top-level filter for INGRESOS vs EGRESOS
        tipo_cfdi = st.radio("Selecciona Categoría:", ["INGRESOS", "EGRESOS"], horizontal=True)
        st.divider()

        tablas_mostrar = tablas_cfdi_ingresos if tipo_cfdi == "INGRESOS" else tablas_cfdi_egresos

        if not tablas_mostrar:
            st.info(f"No hay registros cargados para la categoría {tipo_cfdi}.")
        else:
            bloque_cfdi = st.selectbox("Selecciona bloque fiscal:", tablas_mostrar)
            df = get_df_from_sql(bloque_cfdi)
            df_mostrar = df.copy()

            # Lógica de Columnas a Mostrar según el tipo de archivo seleccionado
            # Agregamos placeholders vacíos para conciliaciones futuras si no existen
            if "CFDI_I" in bloque_cfdi:
                cols_deseadas = ['UUID', 'Fecha Emisión', 'PDF', 'Serie', 'Folio', 'RFC',
                                 'Nombre, denominación o razón social del Receptor', 'Forma de Pago',
                                 'Método de Pago', 'SubTotal XML', 'IVA 16', 'Total', 'Conceptos',
                                 'BANCOS', 'ID VENTA']
            elif "PAGOS_I" in bloque_cfdi or "PAGOS_E" in bloque_cfdi:
                # Calcular Subtotal Pagado = Total Pagado (Monto en PAGOS = Total Pagado/ImportePagado, pero acá es "Monto" o "Total"?)
                # SAT reports typically have 'Monto' for Pagos. The user calls it 'Total Pagado'.
                # Let's try to find it safely.
                total_col = next((c for c in ['Monto', 'Total', 'Total Pagado'] if c in df_mostrar.columns), None)
                iva_col = next((c for c in ['IVA', 'IVA 16'] if c in df_mostrar.columns), None)

                if total_col and iva_col:
                    try:
                        t = pd.to_numeric(df_mostrar[total_col], errors='coerce').fillna(0)
                        i = pd.to_numeric(df_mostrar[iva_col], errors='coerce').fillna(0)
                        df_mostrar['Subtotal Pagado'] = t - i
                    except:
                        df_mostrar['Subtotal Pagado'] = None
                else:
                    df_mostrar['Subtotal Pagado'] = None

                # Asignar nombres estándar si varían
                if total_col and total_col != 'Total Pagado':
                    df_mostrar['Total Pagado'] = df_mostrar[total_col]

                nombre_entidad = 'Nombre, denominación o razón social del Receptor' if "PAGOS_I" in bloque_cfdi else 'Nombre, denominación o razón social del Emisor'

                cols_deseadas = ['UUID', 'PDF', 'Fecha Pago', 'Fecha Emisión', 'UUID Madre', 'Folio', 'RFC',
                                 nombre_entidad, 'Forma de Pago', 'Subtotal Pagado',
                                 'IVA 16' if 'IVA 16' in df_mostrar.columns else 'IVA',
                                 'Total Pagado', 'BANCOS']
            elif "CFDI_E" in bloque_cfdi:
                cols_deseadas = ['UUID', 'Fecha Emisión', 'PDF', 'Serie', 'Folio', 'RFC',
                                 'Nombre, denominación o razón social del Emisor', 'Forma de Pago',
                                 'Método de Pago', 'Uso CFDI Receptor', 'SubTotal No Obj de Impuesto', # Usamos este como el subtotal IVA 16 si no hay otro, o SubTotal XML
                                 'RET. ISR', 'RET. IVA', 'IVA 16', 'Total', 'Conceptos', 'BANCOS']
                if 'SubTotal XML' in df_mostrar.columns and 'SubTotal No Obj de Impuesto' not in cols_deseadas:
                    cols_deseadas[10] = 'SubTotal XML' # Fallback
            else:
                cols_deseadas = df_mostrar.columns.tolist()

            # Asegurar que las columnas deseadas existan (llenar con vacío si son placeholders)
            for col in cols_deseadas:
                if col not in df_mostrar.columns:
                    df_mostrar[col] = ""

            # Filtrar solo las columnas solicitadas
            df_mostrar = df_mostrar[cols_deseadas]

            df_mostrar = df_mostrar.fillna("")
            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")

            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

elif eleccion == "🛒 VENTAS":
    st.title("🛒 Módulo VENTAS")
    tablas = [t for t in get_all_tables() if t.startswith("VENTAS_") and not t.endswith("CRUZADO")]
    if not tablas: st.warning("La BD está vacía.")
    else:
        bloque = st.selectbox("Selecciona bloque operativo:", tablas)
        st.dataframe(get_df_from_sql(bloque), use_container_width=True)

# ==========================================================
# 📊 O00: PRE-CLÁSICOS FISCALES (NUEVO)
# ==========================================================
elif eleccion == "📊 O00: PRE-CLÁSICOS FISCALES":
    st.title("📊 Módulo O00: Reglas Fiscales y Pre-clasificación")
    st.markdown("Este módulo aplica las reglas iniciales sobre los bancos y CFDI antes de conciliar ventas. **(Recomendado ejecutar primero)**.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Preclasificación Bancos")
        st.markdown("Busca patrones (ej. 'Comisión', 'Nómina') en el concepto y auto-asigna categoría.")
        if st.button("🔍 O01 - Ejecutar Preclasificación", type="primary"):
            with st.spinner("Analizando conceptos bancarios..."):
                res = run_o01_preclasificar_bancos()
                if "success" in res:
                    st.success(f"✅ {res['matches']} movimientos auto-clasificados por concepto.")
                else:
                    st.error(res.get("error", "Error desconocido."))

    with col2:
        st.subheader("2. Conciliación Complementos (PAGOS E)")
        st.markdown("Cruza las salidas bancarias directamente contra los Pagos de Egresos emitidos.")
        if st.button("🧾 O07 - Conciliar PAGOS E", type="primary"):
            with st.spinner("Buscando cargos para PAGOS E..."):
                res = run_o07_conciliar_pagos_e()
                if "success" in res:
                    st.success(f"✅ {res['matches']} complementos PAGOS E conciliados con banco.")
                else:
                    st.error(res.get("error", "Error desconocido."))


# ==========================================================
# 📈 I00: CRUCE INGRESOS
# ==========================================================
elif eleccion == "📈 I00: CRUCE INGRESOS (Ventas)":
    st.title("📈 Módulo I00: Cruce de Ventas vs Bancos")

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
elif eleccion == "💸 CRUCE EGRESOS":
    st.title("💸 Motor de Conciliación de Egresos")
    st.markdown("Cruza las **Facturas de Gastos (CFDI E PUE)** contra los **Cargos (Salidas)** del banco BBVA.")

    if st.button("💳 O06 - Ejecutar Cruce Egresos (CFDI E PUE vs Bancos BBVA)", type="primary"):
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
