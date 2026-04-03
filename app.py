import streamlit as st
import pandas as pd
import os

# Módulos core
from modulo_bancos_fix import limpiar_mp
from modulo_bancos import limpiar_modulo_bancos
from modulo_cfdi import limpiar_modulo_cfdi
from modulo_ventas_ajustado import limpiar_modulo_ventas_v2
from modulo_ventas_resumen import limpiar_reporte_series_csv
from database_sqlite import save_df_to_sql, get_df_from_sql, get_filtered_df_from_sql, get_all_tables, drop_table_from_sql, update_table_from_df

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

st.set_page_config(page_title="ERP Conciliación PRO", layout="wide", page_icon=":material/account_balance:", initial_sidebar_state="collapsed")

# Modal para Expedientes
@st.dialog("📁 Expediente de Venta", width="large")
def abrir_expediente(id_venta_raw):
    import os
    import shutil
    import subprocess
    import platform
    import pandas as pd
    import re

    # Sanitizar id_venta para evitar Path Traversal vulnerabilities
    id_venta = re.sub(r'[^a-zA-Z0-9_\-]', '', str(id_venta_raw))
    if not id_venta:
        st.error("ID de venta inválido.")
        return

    def open_local_path(path):
        """Abre un archivo o carpeta usando la aplicación por defecto del sistema."""
        try:
            if platform.system() == 'Windows':
                os.startfile(path)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', path])
            else:
                subprocess.call(['xdg-open', path])
        except Exception as e:
            st.error(f"No se pudo abrir: {e}")

    # Determinar la ruta base de la carpeta
    ruta_base = os.path.join("EXPEDIENTES", "MANUAL", id_venta) # Fallback
    tablas_todas = get_all_tables()
    tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]

    for tb in tablas_ventas:
        df_tb = get_df_from_sql(tb)
        col_id = 'id_venta' if 'id_venta' in df_tb.columns else 'ID VENTA' if 'ID VENTA' in df_tb.columns else None
        col_fecha = 'fecha' if 'fecha' in df_tb.columns else 'FECHA' if 'FECHA' in df_tb.columns else None

        if col_id and col_fecha and not df_tb.empty:
            fila_match = df_tb[df_tb[col_id].astype(str).str.strip() == id_venta]
            if not fila_match.empty:
                banco_folder = tb.replace('VENTAS_', '')
                fecha_val = fila_match.iloc[0][col_fecha]
                mes_folder = "GENERAL"
                try:
                    dt_fecha = pd.to_datetime(fecha_val, errors='coerce')
                    if pd.notna(dt_fecha):
                        mes_folder = dt_fecha.strftime("%Y_%m")
                except: pass
                ruta_base = os.path.join("EXPEDIENTES", "VENTAS", mes_folder, banco_folder, id_venta)
                break

    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.write(f"Gestionando documentos para: **{id_venta}**")
    with col_h2:
        if os.path.exists(ruta_base):
            if st.button("📂 Abrir Carpeta", help="Abre la carpeta física en Windows/Mac."):
                open_local_path(ruta_base)

    # Buscar si existe en la base de datos de expedientes
    df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
    if df_exp.empty:
        df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

    archivos_venta = df_exp[df_exp['ID_VENTA'] == id_venta] if not df_exp.empty else pd.DataFrame()

    # Mostrar archivos existentes
    if not archivos_venta.empty:
        st.subheader("Documentos Guardados")
        for idx, row in archivos_venta.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📄 {row['NOMBRE_ARCHIVO']} ({row['TIPO_DOCUMENTO']})")
            with col2:
                # Botón Funcional
                if st.button("Abrir", key=f"abrir_{idx}", help="Abre el archivo con tu lector de PDF o imágenes."):
                    if os.path.exists(row['RUTA_LOCAL']):
                        open_local_path(row['RUTA_LOCAL'])
                    else:
                        st.error("El archivo físico ya no existe en esa ruta.")
    else:
        st.info("Aún no hay documentos para esta venta. Sube los archivos arrastrándolos aquí abajo.")

    st.divider()
    st.subheader("Subir Nuevos Archivos")
    uploaded_files = st.file_uploader("Arrastra aquí PDF, XML, PNG, JPG...", accept_multiple_files=True, key=f"uploader_{id_venta}")

    if uploaded_files and st.button("💾 Guardar Archivos"):
        from database_sqlite import update_table_from_df

        os.makedirs(ruta_base, exist_ok=True)

        nuevos_registros = []
        for uf in uploaded_files:
            # Sanitizar nombre de archivo
            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', uf.name)
            ruta_destino = os.path.join(ruta_base, safe_name)

            with open(ruta_destino, "wb") as f:
                f.write(uf.getbuffer())

            nuevos_registros.append({
                "ID_VENTA": id_venta,
                "NOMBRE_ARCHIVO": safe_name,
                "TIPO_DOCUMENTO": safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO',
                "RUTA_LOCAL": ruta_destino
            })

        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)
            if df_exp.empty:
                df_exp = df_nuevos
            else:
                df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)

            save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
            st.success("Archivos guardados correctamente.")
            import time
            time.sleep(1)
            st.rerun()

# Interceptar query params para abrir modal
if "expediente" in st.query_params:
    id_venta_target = st.query_params["expediente"]
    # Limpiar el query param para que al cerrar el modal no se vuelva a abrir al refrescar
    st.query_params.clear()
    abrir_expediente(id_venta_target)

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

# 3. HELPER DE FECHAS ROBUSTO
def safe_parse_dates(serie):
    """
    Intenta parsear fechas de forma segura para no invertir Día y Mes.
    Intenta primero formatos ISO estándar de SQLite, y si falla, asume DD/MM/YYYY.
    """
    s_iso_full = pd.to_datetime(serie, format='%Y-%m-%d %H:%M:%S', errors='coerce')
    s_iso_short = pd.to_datetime(serie, format='%Y-%m-%d', errors='coerce')
    s_eu = pd.to_datetime(serie, format='%d/%m/%Y', errors='coerce')

    return s_iso_full.fillna(s_iso_short).fillna(s_eu)

# 4. HELPER DE FILTROS GLOBALES (OPTIMIZADO CON SQL-FIRST)
def render_filtros_globales_sql(table_name, col_fecha, key_prefix):
    """
    Renderiza controles de filtrado. Extrae únicamente metadatos de fechas (DISTINCT) y luego
    delega todo el filtro (fechas + texto) a SQL directamente mediante get_filtered_df_from_sql,
    cargando a memoria (Pandas) solamente los registros estrictamente necesarios.
    """
    import sqlite3

    conn = sqlite3.connect("conciliacion_data.db")
    cursor = conn.cursor()

    lista_meses = ["Todos"]
    min_date = None
    max_date = None

    # 1. Obtener los límites de fecha rápidamente mediante SQL
    try:
        # Asegurarnos de que la columna existe en la tabla (case-insensitive)
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columnas = [row[1] for row in cursor.fetchall()]

        real_col_fecha = None
        if col_fecha:
            for c in columnas:
                if c.lower() == col_fecha.lower():
                    real_col_fecha = c
                    break

        if real_col_fecha:
            # Obtener meses únicos (YYYY-MM) usando substr (sqlite natively supports YYYY-MM-DD strings)
            cursor.execute(f'''
                SELECT DISTINCT substr(CAST("{real_col_fecha}" AS TEXT), 1, 7)
                FROM "{table_name}"
                WHERE "{real_col_fecha}" IS NOT NULL AND "{real_col_fecha}" != ""
            ''')
            meses_raw = [row[0] for row in cursor.fetchall() if row[0] and len(row[0]) == 7]

            if meses_raw:
                # Ordenar descendente (recientes arriba)
                lista_meses += sorted(meses_raw, reverse=True)

            # Obtener MIN y MAX para el date_input
            cursor.execute(f'''
                SELECT MIN(CAST("{real_col_fecha}" AS TEXT)), MAX(CAST("{real_col_fecha}" AS TEXT))
                FROM "{table_name}"
                WHERE "{real_col_fecha}" IS NOT NULL AND "{real_col_fecha}" != ""
            ''')
            limites = cursor.fetchone()
            if limites and limites[0] and limites[1]:
                min_s = pd.to_datetime(limites[0][:10], errors='coerce')
                max_s = pd.to_datetime(limites[1][:10], errors='coerce')
                if not pd.isna(min_s) and not pd.isna(max_s):
                    min_date = min_s
                    max_date = max_s
    except Exception as e:
        pass
    finally:
        conn.close()

    # Determinar el índice por defecto para el mes
    from datetime import datetime
    current_month_str = datetime.now().strftime('%Y-%m')
    default_index = 0
    if current_month_str in lista_meses:
        default_index = lista_meses.index(current_month_str)
    elif len(lista_meses) > 1:
        default_index = 1

    # --- UI: FILTROS SUPERIORES ---
    with st.expander("🛠️ Opciones de Filtrado Búsqueda (Optimizado)", expanded=True):
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            mes_sel = st.selectbox("📅 Filtrar por Mes:", lista_meses, index=default_index, key=f"mes_{key_prefix}")

        with col2:
            if min_date and max_date:
                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    fecha_desde = st.date_input("Desde:", value=None, min_value=min_date.date(), max_value=max_date.date(), key=f"desde_{key_prefix}")
                with col2_2:
                    fecha_hasta = st.date_input("Hasta:", value=None, min_value=min_date.date(), max_value=max_date.date(), key=f"hasta_{key_prefix}")
            else:
                fecha_desde = None
                fecha_hasta = None

        with col3:
            busqueda = st.text_input("🔍 Buscar (Texto libre):", "", key=f"buscar_{key_prefix}", placeholder="Ej. concepto, monto o UUID", help="Búsqueda ultrarrápida usando SQL sobre todas las columnas.")

    # 2. Descargar datos delegando todo el filtro (fecha y texto) a SQLite
    df_filtrado = get_filtered_df_from_sql(
        table_name,
        search_text=busqueda,
        col_fecha=col_fecha,
        mes_sel=mes_sel,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta
    )

    return df_filtrado

# ==========================================================
# MENÚ LATERAL
# ==========================================================
st.sidebar.title(":material/dashboard_customize: Módulos Avanzados")
opciones = [
    "📥 Ingesta (Excel / PDF)",
    "🏦 BANCOS",
    "📄 CFDI (Facturas)",
    "🛒 VENTAS",
    "⚙️ O00: PRE-CLÁSICOS FISCALES",
    "🔄 I00: CRUCE INGRESOS (Ventas)",
    "💸 CRUCE EGRESOS",
    "📊 DASHBOARD & REPORTES"
]
eleccion = st.sidebar.radio("Navegar:", opciones)

# Logout en Sidebar
st.sidebar.divider()
if st.sidebar.button(":material/logout: Cerrar Sesión"):
    st.session_state["password_correct"] = False
    st.rerun()

# ==========================================================
# 📥 INICIO E INGESTA
# ==========================================================
if eleccion == "📥 Ingesta (Excel / PDF)":
    st.title(":material/cloud_upload: Procesamiento de Archivos (ETL)")

    st.markdown("Carga tus archivos de forma individual o un archivo consolidado.")

    # Pestañas para subir Excel o PDF
    tab1, tab4 = st.tabs([
        "Carga Consolidada (Mega Excel)",
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
                        # Evitar prefijo doble "CFDI_CFDI_"
                        nombre_tabla = nombre_cfdi if nombre_cfdi.startswith(("CFDI_", "PAGOS_")) else f"CFDI_{nombre_cfdi}"
                        save_df_to_sql(df_cfdi, nombre_tabla)

                with st.spinner("Procesando Ventas..."):
                    ventas = limpiar_modulo_ventas_v2(archivo_subido)
                    for nombre_venta, df_venta in ventas.items():
                        save_df_to_sql(df_venta, nombre_venta)

                st.success("✅ ¡Datos consolidados guardados en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo consolidado primero.")

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
                            nombre_tabla = nombre_cfdi if nombre_cfdi.startswith(("CFDI_", "PAGOS_")) else f"CFDI_{nombre_cfdi}"
                            save_df_to_sql(df_cfdi, nombre_tabla)
                st.success("✅ ¡CFDI guardados en la Base de Datos SQL!")
            else:
                st.warning("⚠️ Sube un archivo CFDI primero.")

# ==========================================================
# MÓDULOS DE VISUALIZACIÓN BÁSICA
# ==========================================================
elif eleccion == "🏦 BANCOS":
    st.title(":material/account_balance: Módulo BANCOS")

    # 1. Selector principal
    tipo_vista = st.radio("Selecciona la vista:", ["Estados de Cuenta", "Movimientos Operativos"], horizontal=True)
    st.divider()

    # 2. Ingesta de Bancos (integrada)
    with st.expander(f"📥 Cargar archivos para {tipo_vista}", expanded=False):
        if tipo_vista == "Estados de Cuenta":
            st.markdown("Sube archivos de **Estados de Cuenta** (PDF o Excel).")
            archivo_est_excel = st.file_uploader("📂 Cargar Estado de Cuenta (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="est_excel")
            archivo_est_pdf = st.file_uploader("📂 Cargar Estado de Cuenta (PDF)", type=['pdf'], accept_multiple_files=True, key="est_pdf")

            if st.button("Procesar Estados de Cuenta", type="primary"):
                procesados = False

                if archivo_est_excel:
                    for archivo in archivo_est_excel:
                        with st.spinner(f"Procesando {archivo.name}..."):
                            # Guardar copia física
                            dir_guardado = os.path.join("PROCESADOS", "BANCOS", "ESTADOS_CUENTA")
                            os.makedirs(dir_guardado, exist_ok=True)
                            ruta_guardado = os.path.join(dir_guardado, archivo.name)
                            with open(ruta_guardado, "wb") as f:
                                f.write(archivo.getbuffer())

                            bancos = limpiar_modulo_bancos(archivo)
                            for nombre_cuenta, df_banco in bancos.items():
                                if nombre_cuenta == "MP_DETALLE":
                                    save_df_to_sql(df_banco, "AUX_MP_DETALLE")
                                elif "MP_ESTADO_CUENTA" in nombre_cuenta:
                                    save_df_to_sql(df_banco, "BANCO_MP_ESTADO_CUENTA")
                                else:
                                    # Asegurar que tenga EST_ en el nombre
                                    nombre_final = nombre_cuenta if "_EST_" in nombre_cuenta else nombre_cuenta.replace("_DET_", "_EST_")
                                    if "_EST_" not in nombre_final:
                                         partes = nombre_final.split("_", 1)
                                         if len(partes) == 2:
                                             nombre_final = f"{partes[0]}_EST_{partes[1]}"
                                         else:
                                             nombre_final = f"{nombre_final}_EST"
                                    save_df_to_sql(df_banco, f"BANCO_{nombre_final}")
                    procesados = True

                if archivo_est_pdf:
                    for pdf in archivo_est_pdf:
                        # Guardar copia física
                        dir_guardado = os.path.join("PROCESADOS", "BANCOS", "ESTADOS_CUENTA")
                        os.makedirs(dir_guardado, exist_ok=True)
                        ruta_guardado = os.path.join(dir_guardado, pdf.name)
                        with open(ruta_guardado, "wb") as f:
                            f.write(pdf.getbuffer())
                        # parse_bank_pdf ya guarda en SQLite con nombre BANCO_BBVA_EST_...
                        parse_bank_pdf(pdf)
                    procesados = True

                if procesados:
                    st.success("✅ ¡Estados de Cuenta guardados en la Base de Datos SQL y archivados!")
                    import time
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.warning("Sube un archivo primero.")

        else: # Movimientos Operativos
            st.markdown("Sube archivos de **Movimientos Operativos** (Excel).")
            archivo_det_excel = st.file_uploader("📂 Cargar Movimientos (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="det_excel")

            if st.button("Procesar Movimientos", type="primary"):
                if archivo_det_excel:
                    for archivo in archivo_det_excel:
                        with st.spinner(f"Procesando {archivo.name}..."):
                            # Guardar copia física
                            dir_guardado = os.path.join("PROCESADOS", "BANCOS", "MOVIMIENTOS")
                            os.makedirs(dir_guardado, exist_ok=True)
                            ruta_guardado = os.path.join(dir_guardado, archivo.name)
                            with open(ruta_guardado, "wb") as f:
                                f.write(archivo.getbuffer())

                            bancos = limpiar_modulo_bancos(archivo)
                            for nombre_cuenta, df_banco in bancos.items():
                                if nombre_cuenta == "MP_DETALLE":
                                    save_df_to_sql(df_banco, "AUX_MP_DETALLE")
                                elif "MP_ESTADO_CUENTA" in nombre_cuenta:
                                    # Omitir estados de cuenta si se suben por error aquí, o guardarlos donde corresponde
                                    save_df_to_sql(df_banco, "BANCO_MP_ESTADO_CUENTA")
                                else:
                                    # Asegurar que tenga DET_ en el nombre
                                    nombre_final = nombre_cuenta if "_DET_" in nombre_cuenta else nombre_cuenta.replace("_EST_", "_DET_")
                                    if "_DET_" not in nombre_final:
                                         partes = nombre_final.split("_", 1)
                                         if len(partes) == 2:
                                             nombre_final = f"{partes[0]}_DET_{partes[1]}"
                                         else:
                                             nombre_final = f"{nombre_final}_DET"
                                    save_df_to_sql(df_banco, f"BANCO_{nombre_final}")
                    st.success("✅ ¡Movimientos guardados en la Base de Datos SQL y archivados!")
                    import time
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.warning("Sube un archivo de Excel primero.")

    st.divider()

    # 3. Filtrar tablas según la vista seleccionada
    todas_las_tablas = get_all_tables()
    if tipo_vista == "Estados de Cuenta":
        tablas = [t for t in todas_las_tablas if t.startswith("BANCO_") and ("_EST_" in t or "ESTADO_CUENTA" in t)]
    else:
        # Movimientos: Todo lo que sea BANCO_ y NO sea EST, además de AUX_MP_DETALLE
        tablas = [t for t in todas_las_tablas if (t.startswith("BANCO_") and "_EST_" not in t and "ESTADO_CUENTA" not in t) or t == "AUX_MP_DETALLE"]


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

        # Crear pestañas dinámicas (incluyendo Resumen Global al principio)
        tabs_names = ["📊 Resumen Global"] + nombres_bancos
        tabs = st.tabs(tabs_names)

        # --- Pestaña de Resumen Global ---
        with tabs[0]:
            st.subheader(f"Resumen Consolidado de {tipo_vista}")

            # Recolectar totales de todas las tablas mostradas
            tot_abono_global = 0
            tot_cargo_global = 0
            tot_saldo_global = 0
            tot_movimientos_global = 0

            # Datos para el mini dashboard
            resumen_data = []

            for banco_key, cuentas in bancos_dict.items():
                for cta in cuentas:
                    df_res = get_df_from_sql(cta)
                    if not df_res.empty:
                        # Si es MP, tenemos que hacer la conversión de la misma manera
                        if cta == "AUX_MP_DETALLE" or "MP_DETALLE" in cta:
                            if 'Valor del cargo' in df_res.columns:
                                df_res['monto_num'] = pd.to_numeric(df_res['Valor del cargo'].astype(str).str.replace(',', ''), errors='coerce')
                                df_res['ABONO'] = df_res['monto_num'].apply(lambda x: x if pd.notnull(x) and x > 0 else 0)
                                df_res['CARGO'] = df_res['monto_num'].apply(lambda x: abs(x) if pd.notnull(x) and x < 0 else 0)

                        abono_cta = pd.to_numeric(df_res.get('ABONO', pd.Series(dtype=float)), errors='coerce').sum()
                        cargo_cta = pd.to_numeric(df_res.get('CARGO', pd.Series(dtype=float)), errors='coerce').sum()
                        movs_cta = len(df_res)

                        saldo_cta = 0
                        if 'SALDO' in df_res.columns:
                             u_saldo = pd.to_numeric(df_res['SALDO'], errors='coerce').dropna().tail(1)
                             if not u_saldo.empty:
                                 saldo_cta = u_saldo.iloc[0]

                        tot_abono_global += abono_cta
                        tot_cargo_global += cargo_cta
                        tot_saldo_global += saldo_cta
                        tot_movimientos_global += movs_cta

                        resumen_data.append({
                            "Banco": banco_key,
                            "Cuenta": cta.replace("BANCO_", ""),
                            "Total Abonos": abono_cta,
                            "Total Cargos": cargo_cta,
                            "Último Saldo": saldo_cta,
                            "Movimientos": movs_cta
                        })

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🟢 Total Abonos Global", f"${tot_abono_global:,.2f}")
            m2.metric("🔴 Total Cargos Global", f"${tot_cargo_global:,.2f}")
            m3.metric("💰 Suma de Saldos (Aprox)", f"${tot_saldo_global:,.2f}")
            m4.metric("📝 Movimientos Totales", tot_movimientos_global)

            if resumen_data:
                st.divider()
                df_resumen = pd.DataFrame(resumen_data)

                # Configuración de columnas para que se vean bien los dineros
                cc_resumen_global = {
                    "Total Abonos": st.column_config.NumberColumn("Total Abonos"),
                    "Total Cargos": st.column_config.NumberColumn("Total Cargos"),
                    "Último Saldo": st.column_config.NumberColumn("Último Saldo")
                }

                # Format to strings with commas and dollar signs using Pandas Styler
                st.dataframe(df_resumen.style.format({
                    "Total Abonos": "${:,.2f}",
                    "Total Cargos": "${:,.2f}",
                    "Último Saldo": "${:,.2f}"
                }, na_rep=""), use_container_width=True, hide_index=True, column_config=cc_resumen_global)


        # Función auxiliar para renderizar el panel de control de un banco
        def render_bank_panel(cuenta_sel, key_prefix):
            es_mp_detalle = cuenta_sel == "AUX_MP_DETALLE" or "MP_DETALLE" in cuenta_sel
            col_fecha_filtro = 'Fecha del cargo' if es_mp_detalle else 'FECHA'

            # Usar la nueva función SQL-First
            df_filtrado = render_filtros_globales_sql(cuenta_sel, col_fecha=col_fecha_filtro, key_prefix=key_prefix)

            if df_filtrado.empty:
                st.info("La tabla seleccionada no contiene registros o no coincide con los filtros.")
                return

            # --- UI: MÉTRICAS RESUMEN ---
            if es_mp_detalle:
                # Mercado Pago maneja todo en 'Valor del cargo'
                if 'Valor del cargo' in df_filtrado.columns:
                    monto_num = pd.to_numeric(df_filtrado['Valor del cargo'].astype(str).str.replace(',', ''), errors='coerce')
                    tot_abono = monto_num[monto_num > 0].sum()
                    tot_cargo = abs(monto_num[monto_num < 0].sum())
                else:
                    tot_abono = tot_cargo = 0
                saldo_final = 0 # No hay saldo final en MP_DETALLE usualmente
            else:
                tot_cargo = pd.to_numeric(df_filtrado['CARGO'], errors='coerce').sum() if 'CARGO' in df_filtrado.columns else 0
                tot_abono = pd.to_numeric(df_filtrado['ABONO'], errors='coerce').sum() if 'ABONO' in df_filtrado.columns else 0
                saldo_final = 0
                if 'SALDO' in df_filtrado.columns and not df_filtrado.empty:
                     ultimo_saldo = pd.to_numeric(df_filtrado['SALDO'], errors='coerce').dropna().tail(1)
                     if not ultimo_saldo.empty:
                         saldo_final = ultimo_saldo.iloc[0]

            # --- UI: INDICADOR DE CALIDAD DE DATOS ---
            if es_mp_detalle:
                missing_concepts = df_filtrado['Detalle'].isnull().sum() + (df_filtrado['Detalle'] == '').sum() if 'Detalle' in df_filtrado.columns else 0
                missing_dates = df_filtrado['Fecha del cargo'].isnull().sum() if 'Fecha del cargo' in df_filtrado.columns else 0
            else:
                missing_concepts = df_filtrado['CONCEPTO'].isnull().sum() + (df_filtrado['CONCEPTO'] == '').sum() if 'CONCEPTO' in df_filtrado.columns else 0
                missing_dates = df_filtrado['FECHA'].isnull().sum() if 'FECHA' in df_filtrado.columns else 0

            if missing_concepts > 0 or missing_dates > 0:
                st.warning(f"⚠️ **Calidad de Datos:** Tienes {missing_concepts} movimientos sin 'Concepto/Detalle' y {missing_dates} sin 'Fecha' en este periodo. Esto podría dificultar la conciliación.")

            # --- UI: ALERTA DE DESCUADRE ---
            if not es_mp_detalle and 'SALDO' in df_filtrado.columns and not df_filtrado.empty:
                try:
                    saldos_validos = pd.to_numeric(df_filtrado['SALDO'], errors='coerce').dropna()
                    if len(saldos_validos) > 1:
                        # Asumiendo que el df está ordenado cronológicamente (viejo arriba, nuevo abajo)
                        # El saldo "inicial" antes del primer movimiento se puede deducir o tomar el primero
                        # Si el orden es (nuevo arriba, viejo abajo) tomamos iloc[-1]. Asumimos (viejo arriba) por Excel genérico.
                        # Para ser seguros, sumamos (Abonos - Cargos) y vemos si la diferencia coincide entre primer y último saldo

                        primer_saldo = saldos_validos.iloc[0]
                        ultimo_saldo = saldos_validos.iloc[-1]

                        # Sin embargo, el "primer saldo" del mes en un estado de cuenta a menudo YA incluye
                        # el primer cargo/abono de esa fila. Así que la fórmula real:
                        # Saldo Inicial (previo al mes) = Primer_Saldo_del_Periodo - Primer_Abono + Primer_Cargo
                        idx_primer_saldo = saldos_validos.index[0]
                        primer_abono = pd.to_numeric(df_filtrado['ABONO'], errors='coerce').fillna(0).loc[idx_primer_saldo]
                        primer_cargo = pd.to_numeric(df_filtrado['CARGO'], errors='coerce').fillna(0).loc[idx_primer_saldo]

                        saldo_inicial_real = primer_saldo - primer_abono + primer_cargo
                        saldo_final_calculado = saldo_inicial_real + tot_abono - tot_cargo

                        diferencia = abs(saldo_final_calculado - ultimo_saldo)

                        # Si la diferencia es mayor a $1 peso, podría haber un descuadre (ej. filas borradas, PDF mal leído)
                        if diferencia > 1.0:
                            if not st.session_state.get(f"warned_descuadre_{cuenta_sel}", False):
                                st.toast(f"⚖️ **Posible Descuadre Detectado en {cuenta_sel}:** Diferencia de **${diferencia:,.2f}**.", icon="⚠️")
                                st.session_state[f"warned_descuadre_{cuenta_sel}"] = True
                            with st.expander("⚠️ Alerta de Posible Descuadre"):
                                st.error(f"El Saldo Final reportado es **${ultimo_saldo:,.2f}**, pero según la suma de movimientos debería ser **${saldo_final_calculado:,.2f}** (Diferencia: **${diferencia:,.2f}**). Verifica si faltan páginas o registros.")
                except Exception as e:
                    pass

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🟢 Total Abonos", f"${tot_abono:,.2f}")
            m2.metric("🔴 Total Cargos", f"${tot_cargo:,.2f}")
            m3.metric("💰 Saldo Final", f"${saldo_final:,.2f}")
            m4.metric("📝 Movimientos", len(df_filtrado))

            # --- UI: GRÁFICO DE TENDENCIAS ---
            if not df_filtrado.empty:
                try:
                    df_graf = df_filtrado.copy()
                    if es_mp_detalle:
                        df_graf['FECHA'] = safe_parse_dates(df_graf['Fecha del cargo'])
                        if 'Valor del cargo' in df_graf.columns:
                            mnt = pd.to_numeric(df_graf['Valor del cargo'].astype(str).str.replace(',', ''), errors='coerce')
                            df_graf['ABONO_NUM'] = mnt.apply(lambda x: x if pd.notnull(x) and x > 0 else 0)
                            df_graf['CARGO_NUM'] = mnt.apply(lambda x: abs(x) if pd.notnull(x) and x < 0 else 0)
                        else:
                            df_graf['ABONO_NUM'] = 0
                            df_graf['CARGO_NUM'] = 0
                    else:
                        df_graf['FECHA'] = safe_parse_dates(df_graf['FECHA'])
                        df_graf['ABONO_NUM'] = pd.to_numeric(df_graf['ABONO'], errors='coerce').fillna(0)
                        df_graf['CARGO_NUM'] = pd.to_numeric(df_graf['CARGO'], errors='coerce').fillna(0)

                    df_graf = df_graf.dropna(subset=['FECHA'])
                    if not df_graf.empty:
                        df_graf_grp = df_graf.groupby(df_graf['FECHA'].dt.date)[['ABONO_NUM', 'CARGO_NUM']].sum().reset_index()
                        df_graf_melt = pd.melt(df_graf_grp, id_vars=['FECHA'], value_vars=['ABONO_NUM', 'CARGO_NUM'],
                                               var_name='Tipo de Movimiento', value_name='Monto')
                        df_graf_melt['Tipo de Movimiento'] = df_graf_melt['Tipo de Movimiento'].map({'ABONO_NUM': 'Ingresos (Abonos)', 'CARGO_NUM': 'Egresos (Cargos)'})
                        df_graf_melt['FECHA'] = pd.to_datetime(df_graf_melt['FECHA'])

                        import altair as alt
                        chart = alt.Chart(df_graf_melt).mark_line(point=True, strokeWidth=3).encode(
                            x=alt.X('FECHA:T', title='Fecha del Movimiento', axis=alt.Axis(format='%d %b')),
                            y=alt.Y('Monto:Q', title='Monto Total ($)', axis=alt.Axis(format='$,.0f')),
                            color=alt.Color('Tipo de Movimiento:N', scale=alt.Scale(domain=['Ingresos (Abonos)', 'Egresos (Cargos)'], range=['#2e7d32', '#d32f2f']), legend=alt.Legend(title="Movimiento")),
                            tooltip=[alt.Tooltip('FECHA:T', format='%Y-%m-%d', title='Día'), alt.Tooltip('Tipo de Movimiento:N'), alt.Tooltip('Monto:Q', format='$,.2f')]
                        ).properties(height=200)

                        st.altair_chart(chart, use_container_width=True)
                except Exception as e:
                    pass

            st.divider()



            # --- UI: TABLA DE DATOS ---
            df_mostrar = df_filtrado.copy()

            if es_mp_detalle:
                # Mostrar solo las columnas analíticas de MP solicitadas + las nuevas (EST MP, COMISION, OBSERVACION)
                columnas_orden = ['Fecha del cargo', 'Detalle', 'Valor del cargo', 'Operación relacionada', 'Nombre de sucursal', 'Valor de la operación', 'ID VENTA', 'EST MP', 'COMISION', 'OBSERVACION']

                # Rellenar con vacío las columnas que no existan
                for c in columnas_orden:
                    if c not in df_mostrar.columns:
                        df_mostrar[c] = ""

                # Ocultar estrictamente el resto de columnas que trae Mercado Pago por defecto
                df_mostrar = df_mostrar[columnas_orden]

                # Definir qué columnas puede editar manualmente el usuario
                col_conceptos_editables = ['Detalle', 'Nombre de sucursal', 'ID VENTA', 'EST MP', 'COMISION', 'OBSERVACION']
            else:
                # Reordenar columnas a 10 columnas estándar si existen
                columnas_orden = ['FECHA', 'CONCEPTO', 'REFERENCE', 'ABONO', 'CARGO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']
                cols_existentes = [c for c in columnas_orden if c in df_mostrar.columns]
                otras_cols = [c for c in df_mostrar.columns if c not in cols_existentes]
                df_mostrar = df_mostrar[cols_existentes + otras_cols]
                col_conceptos_editables = ['CONCEPTO', 'OBSERVACION']

            # Reemplazar explícitamente "None" para limpiar la UI.
            df_mostrar = df_mostrar.replace("None", "")

            # Asegurar que las fechas se vean bonitas
            if 'FECHA' in df_mostrar.columns:
                try:
                    df_mostrar['FECHA'] = safe_parse_dates(df_mostrar['FECHA']).dt.strftime('%d/%m/%Y')
                except Exception:
                    df_mostrar['FECHA'] = pd.to_datetime(df_mostrar['FECHA'], errors='coerce').dt.strftime('%d/%m/%Y')

            if 'Fecha del cargo' in df_mostrar.columns:
                try:
                    df_mostrar['Fecha del cargo'] = safe_parse_dates(df_mostrar['Fecha del cargo']).dt.strftime('%d/%m/%Y')
                except Exception:
                    df_mostrar['Fecha del cargo'] = pd.to_datetime(df_mostrar['Fecha del cargo'], errors='coerce').dt.strftime('%d/%m/%Y')

            # Función para colorear montos
            def color_negative_red(val):
                if pd.isna(val) or val == "":
                    return ""

                # Intentar limpiar el texto para ver si es negativo
                val_str = str(val).replace('$', '').replace(',', '')
                try:
                    num = float(val_str)
                    color = 'red' if num < 0 else 'green' if num > 0 else 'black'
                    return f'color: {color}'
                except:
                    return ""

            # --- UI: EDICIÓN MANUAL ---
            # Mostramos un editor interactivo en lugar de un dataframe estático

            # Recuperar estado de cambios
            if f"edit_{key_prefix}" not in st.session_state:
                st.session_state[f"edit_{key_prefix}"] = False

            # Botón para activar/desactivar modo edición


            # Al usar data_editor y formatters (.style), Streamlit 1.30+ puede quejarse si los tipos no coinciden.
            # Convertimos a strings bonitos y usamos Dataframe/Editor nativos.
            cc_format = {}
            for col_moneda in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                if col_moneda in df_mostrar.columns:
                    try:
                        # Lo mantenemos como numérico en el dataframe subyacente para permitir ordenamiento y style
                        temp_num = pd.to_numeric(df_mostrar[col_moneda].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
                        df_mostrar[col_moneda] = temp_num
                        cc_format[col_moneda] = st.column_config.NumberColumn(col_moneda)
                    except:
                        pass

            # Reemplazar el literal 'NaT' por cadena vacía para fechas (las de tipo moneda ahora son numéricas o nulas)
            df_mostrar = df_mostrar.replace("NaT", "")

            # Configurar un styled dataframe para la vista (no aplica a data_editor directamente, pero sí a dataframe de lectura)
            cols_to_style = [c for c in ['CARGO', 'ABONO', 'Valor del cargo', 'Valor de la operación'] if c in df_mostrar.columns]

            # Preparamos el Styler para la lectura (Si no es MP DETALLE, CARGO lo mostramos rojo y ABONO verde, si es MP, según el signo)
            def style_bancos(val, col_name):
                if pd.isna(val) or val == "":
                    return ""
                try:
                    num = float(val)
                    if col_name == 'CARGO':
                         return 'color: #d32f2f;' if num > 0 else '' # Rojo si hay cargo
                    elif col_name == 'ABONO':
                         return 'color: #2e7d32;' if num > 0 else '' # Verde si hay abono
                    elif col_name == 'Valor del cargo':
                         return 'color: #d32f2f;' if num < 0 else 'color: #2e7d32;' if num > 0 else '' # MP: Rojo neg, verde pos
                    return ""
                except:
                    return ""

            if st.session_state[f"edit_{key_prefix}"]:
                nombres_editables_txt = " / ".join(col_conceptos_editables)
                st.info(f"💡 Modo de Edición Activado: Doble clic en **{nombres_editables_txt}** para editar. Presiona Enter para confirmar y luego haz clic en Guardar.")

                # --- UI: ASIGNACIÓN MASIVA DE CONCEPTOS ---
                with st.expander("⚡ Asignación Masiva", expanded=False):
                    st.markdown("Aplica un mismo valor a todas las filas actualmente visibles en esta tabla. *(Útil si filtraste por un texto específico en el buscador superior)*.")
                    col_masiva1, col_masiva2, col_masiva3 = st.columns([1, 2, 1])
                    with col_masiva1:
                        columna_masiva = st.selectbox("Columna a modificar:", col_conceptos_editables, key=f"masiva_col_{key_prefix}")
                    with col_masiva2:
                        valor_masivo = st.text_input("Nuevo Valor:", "", key=f"masiva_val_{key_prefix}")
                    with col_masiva3:
                        st.write("") # Espaciador
                        st.write("")
                        if st.button("Aplicar a Filas Visibles", key=f"masiva_btn_{key_prefix}", type="secondary"):
                            if len(df_filtrado) > 0:
                                df_crudo_masivo = get_df_from_sql(cuenta_sel)
                                # Asegurar que las columnas nuevas existan en el df original antes de guardar
                                for c in col_conceptos_editables:
                                    if c not in df_crudo_masivo.columns:
                                        df_crudo_masivo[c] = ""

                                # Asignamos el nuevo valor a las filas visibles basándonos en sus índices originales
                                for idx in df_filtrado.index:
                                    df_crudo_masivo.at[idx, columna_masiva] = valor_masivo

                                if update_table_from_df(df_crudo_masivo, cuenta_sel):
                                    st.success(f"✅ ¡{len(df_filtrado)} filas actualizadas correctamente!")
                                    import time
                                    time.sleep(1.5)
                                    st.rerun()
                            else:
                                st.warning("No hay filas visibles para modificar.")

                edited_df = st.data_editor(
                    df_mostrar,
                    use_container_width=True,
                    hide_index=True,
                    column_config=cc_format,
                    disabled=[c for c in df_mostrar.columns if c not in col_conceptos_editables],
                    key=f"editor_{key_prefix}"
                )

                # Mostramos el botón siempre que el modo edición esté activo para evitar bugs de detección
                if st.button("💾 Guardar Cambios en BD", key=f"save_edit_{key_prefix}", type="primary"):
                    df_crudo = get_df_from_sql(cuenta_sel)

                    # Asegurar que las columnas nuevas existan en el df original antes de intentar asignarlas
                    for c in col_conceptos_editables:
                        if c not in df_crudo.columns:
                            df_crudo[c] = ""

                    for i in range(len(df_filtrado)):
                        idx_original = df_filtrado.index[i]
                        for c_edit in col_conceptos_editables:
                             if c_edit in edited_df.columns:
                                  df_crudo.at[idx_original, c_edit] = edited_df[c_edit].iloc[i]

                    # Guardar a SQL
                    if update_table_from_df(df_crudo, cuenta_sel):
                        st.success("✅ ¡Cambios guardados con éxito!")
                        import time
                        time.sleep(1)
                        st.session_state[f"edit_{key_prefix}"] = False
                        st.rerun()
            else:
                # Mostrar dataframe estilizado (Solo Lectura) usando Pandas Styler
                # Create format dict for money columns using a lambda for safer formatting and coercion to numeric
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        # Ensure string representations of empty are actual nans
                        df_mostrar[c] = pd.to_numeric(df_mostrar[c].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
                        cc_format[c] = st.column_config.NumberColumn(c, format="$%.2f")

                # Preparar hipervínculos en modo lectura
                for col_id_pos in ['ID VENTA', 'ID_VENTA_CRUCE']:
                    if col_id_pos in df_mostrar.columns:
                        df_mostrar[f'LINK_EXPEDIENTE_{col_id_pos}'] = df_mostrar[col_id_pos].apply(
                            lambda x: f"/?expediente={x}" if pd.notnull(x) and str(x).strip() != "" else None
                        )
                        cc_format[col_id_pos] = st.column_config.LinkColumn(
                            f"{col_id_pos} (Expediente)",
                            display_text=r"/\?expediente=(.*)"
                        )
                        df_mostrar[col_id_pos] = df_mostrar[f'LINK_EXPEDIENTE_{col_id_pos}']
                        df_mostrar = df_mostrar.drop(columns=[f'LINK_EXPEDIENTE_{col_id_pos}'])

                # Reemplazar explicitly in the dataframe just in case
                # Asegurar que todas las columnas en general no muestren NaNs literales
                df_mostrar = df_mostrar.fillna("")
                df_mostrar = df_mostrar.replace("None", "")

                # Se omite el Styler (.style.map) para permitir que los hipervínculos nativos (LinkColumn) funcionen
                st.dataframe(df_mostrar, use_container_width=True, hide_index=True, column_config=cc_format)

            st.divider()
            # Botones de Acción Múltiple
            col_act1, col_act2, col_act3 = st.columns(3)

            with col_act1:
                from io import BytesIO
                def to_excel(df_to_export):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_to_export.to_excel(writer, index=False, sheet_name='Export')
                    return output.getvalue()

                st.download_button(
                    label="📥 Exportar a Excel",
                    data=to_excel(df_filtrado),
                    file_name=f"{cuenta_sel}_Exportado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"export_{key_prefix}",
                    use_container_width=True
                )

            with col_act2:
                btn_text = "❌ Cancelar Edición" if st.session_state.get(f"edit_{key_prefix}") else "✏️ Editar Manualmente"
                if st.button(btn_text, key=f"btn_edit_{key_prefix}", help="Activa el modo de edición de celdas.", use_container_width=True):
                    st.session_state[f"edit_{key_prefix}"] = not st.session_state.get(f"edit_{key_prefix}", False)
                    st.rerun()

            with col_act3:
                if st.button("🗑️ Eliminar Tabla", key=f"del_{key_prefix}", type="secondary", help="Borra definitivamente esta cuenta/tabla de la base de datos.", use_container_width=True):
                    st.session_state[f"confirm_del_{key_prefix}"] = True

                if st.session_state.get(f"confirm_del_{key_prefix}", False):
                    st.warning("¿Estás seguro?")
                    c_yes, c_no = st.columns(2)
                    if c_yes.button("✅ Sí", key=f"yes_{key_prefix}", type="primary"):
                        if drop_table_from_sql(cuenta_sel):
                            st.success(f"Tabla {cuenta_sel} eliminada.")
                            st.session_state[f"confirm_del_{key_prefix}"] = False
                            import time
                            time.sleep(1.5)
                            st.rerun()
                    if c_no.button("❌ No", key=f"no_{key_prefix}"):
                        st.session_state[f"confirm_del_{key_prefix}"] = False
                        st.rerun()


        # Llenar cada pestaña de banco dinámicamente (desplazadas +1 por el resumen)
        for i, nombre_banco in enumerate(nombres_bancos):
            with tabs[i + 1]:
                st.subheader(f"Cuentas {nombre_banco}")
                tablas_banco = bancos_dict[nombre_banco]

                # Usar selectbox para elegir la tabla específica de ese banco
                cuenta_sel = st.selectbox(f"Selecciona cuenta:", tablas_banco, key=f"sel_{nombre_banco}")

                st.divider()
                # Llamar a la función que dibuja filtros y tabla
                render_bank_panel(cuenta_sel, key_prefix=f"{nombre_banco}_{cuenta_sel}")

elif eleccion == "📄 CFDI (Facturas)":
    st.title(":material/receipt_long: Módulo CFDI")

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

            # Identificar la columna de fecha para este bloque para los filtros
            col_fecha = 'Fecha Emisión'
            if "PAGOS" in bloque_cfdi:
                col_fecha = 'Fecha Pago'

            # Aplicar filtros globales usando SQL
            df_filtrado = render_filtros_globales_sql(bloque_cfdi, col_fecha=col_fecha, key_prefix=f"cfdi_{bloque_cfdi}")

            df_mostrar = df_filtrado.copy()

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

            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")

            st.dataframe(df_mostrar.style.format(na_rep=""), use_container_width=True, hide_index=True)

elif eleccion == "🛒 VENTAS":
    st.title(":material/point_of_sale: Módulo VENTAS")

    # 1. Ingesta de Ventas (integrada)
    with st.expander("📥 Cargar archivos de Ventas (Excel/CSV)", expanded=False):
        st.markdown("Sube los archivos que contengan las **notas de ventas detalladas (Excel)** y el **archivo de Series (CSV)** para rellenar los números de serie.")

        archivo_ventas = st.file_uploader("📂 Cargar Notas de Ventas (Excel)", type=['xlsx', 'xls'], accept_multiple_files=True, key="ventas")
        archivo_ventas_csv = st.file_uploader("📂 Cargar Reporte de Series (CSV con ;)", type=['csv'], accept_multiple_files=True, key="ventas_csv", help="Archivo CSV que contiene ID Venta, Producto y Número de Serie.")
        archivo_ventas_pdf = st.file_uploader("📂 Cargar Notas de Ventas en lote (PDF)", type=['pdf'], accept_multiple_files=True, key="ventas_pdf", help="Se extraerá el Folio y se guardará en su respectivo expediente de venta automáticamente.")
        archivo_ventas_zip = st.file_uploader("📂 Cargar Expedientes (ZIP)", type=['zip'], accept_multiple_files=True, key="ventas_zip", help="Sube archivos ZIP donde el nombre de la carpeta o archivo contenga el ID VENTA (ej. carpeta 28336/).")

        if st.button("Procesar Archivos de Ventas", type="primary", key="btn_ventas_integrado"):
            procesados_ventas = False
            import os

            if archivo_ventas_zip:
                import zipfile

                df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                if df_exp.empty:
                    df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

                tablas_todas = get_all_tables()
                tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]

                nuevos_registros_expediente = []

                for zip_file in archivo_ventas_zip:
                    with st.spinner(f"Procesando ZIP: {zip_file.name}..."):
                        try:
                            with zipfile.ZipFile(zip_file) as z:
                                for file_info in z.infolist():
                                    if file_info.is_dir():
                                        continue

                                    # Extraer ID Venta a partir del directorio superior, o del nombre del ZIP si esta en la raiz
                                    path_parts = file_info.filename.split('/')
                                    if len(path_parts) > 1:
                                        # Buscar la carpeta mas profunda que parezca un ID (numerica)
                                        # O simplemente tomar la carpeta contenedora directa
                                        id_venta_raw = path_parts[-2]
                                    else:
                                        id_venta_raw = zip_file.name.replace('.zip', '')

                                    # Extraer el numero de la cadena
                                    num_match = re.search(r'\d+', id_venta_raw)
                                    if num_match:
                                        id_venta = num_match.group(0)
                                    else:
                                        id_venta = id_venta_raw

                                    id_venta_saneado = re.sub(r'[^a-zA-Z0-9_\-]', '', str(id_venta))
                                    if not id_venta_saneado:
                                        continue

                                    # Buscar ruta de expediente
                                    ruta_base = os.path.join("EXPEDIENTES", "MANUAL", id_venta_saneado)
                                    for tb in tablas_ventas:
                                        df_tb = get_df_from_sql(tb)
                                        col_id = 'id_venta' if 'id_venta' in df_tb.columns else 'ID VENTA' if 'ID VENTA' in df_tb.columns else None
                                        col_fecha = 'fecha' if 'fecha' in df_tb.columns else 'FECHA' if 'FECHA' in df_tb.columns else None

                                        if col_id and col_fecha and not df_tb.empty:
                                            fila_match = df_tb[df_tb[col_id].astype(str).str.strip() == id_venta_saneado]
                                            if not fila_match.empty:
                                                banco_folder = tb.replace('VENTAS_', '')
                                                fecha_val = fila_match.iloc[0][col_fecha]
                                                mes_folder = "GENERAL"
                                                try:
                                                    dt_fecha = pd.to_datetime(fecha_val, errors='coerce')
                                                    if pd.notna(dt_fecha):
                                                        mes_folder = dt_fecha.strftime("%Y_%m")
                                                except: pass
                                                ruta_base = os.path.join("EXPEDIENTES", "VENTAS", mes_folder, banco_folder, id_venta_saneado)
                                                break

                                    # Guardar archivo
                                    os.makedirs(ruta_base, exist_ok=True)
                                    file_name = path_parts[-1]
                                    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', file_name)
                                    ruta_destino = os.path.join(ruta_base, safe_name)

                                    with open(ruta_destino, "wb") as f:
                                        f.write(z.read(file_info.filename))

                                    tipo_doc = safe_name.split('.')[-1].upper() if '.' in safe_name else 'DESCONOCIDO'

                                    nuevos_registros_expediente.append({
                                        "ID_VENTA": id_venta_saneado,
                                        "NOMBRE_ARCHIVO": safe_name,
                                        "TIPO_DOCUMENTO": tipo_doc,
                                        "RUTA_LOCAL": ruta_destino
                                    })

                        except Exception as e:
                            st.error(f"Error procesando ZIP {zip_file.name}: {e}")

                if nuevos_registros_expediente:
                    df_nuevos = pd.DataFrame(nuevos_registros_expediente)
                    if df_exp.empty:
                        df_exp = df_nuevos
                    else:
                        df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)

                    save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
                    procesados_ventas = True
                    st.success(f"✅ Se guardaron {len(nuevos_registros_expediente)} archivos extraídos de ZIP en sus respectivos expedientes.")

            if archivo_ventas_pdf:
                import pdfplumber
                import re

                df_exp = get_df_from_sql("EXPEDIENTES_ARCHIVOS")
                if df_exp.empty:
                    df_exp = pd.DataFrame(columns=["ID_VENTA", "NOMBRE_ARCHIVO", "TIPO_DOCUMENTO", "RUTA_LOCAL"])

                tablas_todas = get_all_tables()
                tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]

                nuevos_registros_expediente = []

                for pdf_file in archivo_ventas_pdf:
                    with st.spinner(f"Procesando PDF: {pdf_file.name}..."):
                        try:
                            # 1. Extraer Folio
                            id_venta = None
                            with pdfplumber.open(pdf_file) as pdf:
                                text = pdf.pages[0].extract_text()
                                if text:
                                    match = re.search(r'Folio:\s*(.*?)(?=\n|Fecha|$)', text, re.IGNORECASE)
                                    if match:
                                        id_venta_raw = match.group(1).strip()
                                        # Extraer solo los números del folio (ignorando P1, P2, etc.)
                                        num_match = re.search(r'\d+', id_venta_raw)
                                        if num_match:
                                            id_venta = num_match.group(0)
                                        else:
                                            id_venta = id_venta_raw

                            if not id_venta:
                                st.warning(f"No se encontró 'Folio:' en el archivo {pdf_file.name}. Se omitirá.")
                                continue

                            id_venta_saneado = re.sub(r'[^a-zA-Z0-9_\-]', '', str(id_venta))

                            # 2. Buscar ruta de expediente (idéntico a abrir_expediente)
                            ruta_base = os.path.join("EXPEDIENTES", "MANUAL", id_venta_saneado) # Fallback

                            encontrado = False
                            for tb in tablas_ventas:
                                df_tb = get_df_from_sql(tb)
                                col_id = 'id_venta' if 'id_venta' in df_tb.columns else 'ID VENTA' if 'ID VENTA' in df_tb.columns else None
                                col_fecha = 'fecha' if 'fecha' in df_tb.columns else 'FECHA' if 'FECHA' in df_tb.columns else None

                                if col_id and col_fecha and not df_tb.empty:
                                    fila_match = df_tb[df_tb[col_id].astype(str).str.strip() == id_venta_saneado]
                                    if not fila_match.empty:
                                        banco_folder = tb.replace('VENTAS_', '')
                                        fecha_val = fila_match.iloc[0][col_fecha]
                                        mes_folder = "GENERAL"
                                        try:
                                            dt_fecha = pd.to_datetime(fecha_val, errors='coerce')
                                            if pd.notna(dt_fecha):
                                                mes_folder = dt_fecha.strftime("%Y_%m")
                                        except: pass
                                        ruta_base = os.path.join("EXPEDIENTES", "VENTAS", mes_folder, banco_folder, id_venta_saneado)
                                        encontrado = True
                                        break

                            # 3. Guardar archivo
                            os.makedirs(ruta_base, exist_ok=True)
                            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', pdf_file.name)
                            ruta_destino = os.path.join(ruta_base, safe_name)

                            with open(ruta_destino, "wb") as f:
                                f.write(pdf_file.getbuffer())

                            nuevos_registros_expediente.append({
                                "ID_VENTA": id_venta_saneado,
                                "NOMBRE_ARCHIVO": safe_name,
                                "TIPO_DOCUMENTO": "PDF",
                                "RUTA_LOCAL": ruta_destino
                            })

                        except Exception as e:
                            st.error(f"Error procesando PDF {pdf_file.name}: {e}")

                if nuevos_registros_expediente:
                    df_nuevos = pd.DataFrame(nuevos_registros_expediente)
                    if df_exp.empty:
                        df_exp = df_nuevos
                    else:
                        df_exp = pd.concat([df_exp, df_nuevos], ignore_index=True)

                    save_df_to_sql(df_exp, "EXPEDIENTES_ARCHIVOS")
                    procesados_ventas = True
                    st.success(f"✅ Se guardaron {len(nuevos_registros_expediente)} PDFs en sus respectivos expedientes.")

            if archivo_ventas:
                for archivo in archivo_ventas:
                    with st.spinner(f"Procesando Notas de Venta de {archivo.name}..."):
                        dir_guardado = os.path.join("PROCESADOS", "VENTAS", "NOTAS")
                        os.makedirs(dir_guardado, exist_ok=True)
                        ruta_guardado = os.path.join(dir_guardado, archivo.name)
                        with open(ruta_guardado, "wb") as f:
                            f.write(archivo.getbuffer())

                        ventas = limpiar_modulo_ventas_v2(archivo)
                        for nombre_venta, df_venta in ventas.items():
                            save_df_to_sql(df_venta, nombre_venta)
                procesados_ventas = True

            if archivo_ventas_csv:
                for archivo in archivo_ventas_csv:
                    with st.spinner(f"Procesando Reporte de Series CSV de {archivo.name}..."):
                        dir_guardado = os.path.join("PROCESADOS", "VENTAS", "SERIES")
                        os.makedirs(dir_guardado, exist_ok=True)
                        ruta_guardado = os.path.join(dir_guardado, archivo.name)
                        with open(ruta_guardado, "wb") as f:
                            f.write(archivo.getbuffer())

                        ventas_series = limpiar_reporte_series_csv(archivo)
                        for nombre_venta, df_venta in ventas_series.items():
                            save_df_to_sql(df_venta, nombre_venta)
                procesados_ventas = True

            if procesados_ventas:
                st.success("✅ ¡Ventas y Series guardadas en la Base de Datos SQL y archivadas!")
                import time
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("⚠️ Sube al menos un archivo de ventas o reporte de series CSV primero.")

    st.divider()

    tablas_todas = get_all_tables()
    # Check what tables are available
    tablas_ventas = [t for t in tablas_todas if t.startswith("VENTAS_") and not t.endswith("CRUZADO") and t != "VENTAS_SERIES"]

    if not tablas_ventas:
        st.warning("La BD está vacía o no hay tablas de ventas procesadas. Usa el botón superior para subir tus archivos.")
    else:
        # Cross-reference logic block
        if "VENTAS_SERIES" in tablas_todas:
            col_cruce1, col_cruce2 = st.columns([2, 1])
            with col_cruce1:
                 st.info("💡 Detectamos un archivo de Series cargado en el sistema. Puedes cruzarlo ahora para rellenar los números de serie faltantes en tus Notas de Ventas.")
            with col_cruce2:
                 if st.button("🔄 Rellenar Números de Serie", type="primary", use_container_width=True):
                     df_series = get_df_from_sql("VENTAS_SERIES")
                     if not df_series.empty and 'ID VENTA' in df_series.columns and 'PRODUCTO' in df_series.columns and 'NUMERO DE SERIE' in df_series.columns:
                         with st.spinner("Cruzando números de serie..."):
                             # Convert to string and clean for matching
                             df_series['ID_MATCH'] = df_series['ID VENTA'].astype(str).str.strip().str.lower()
                             df_series['PROD_MATCH'] = df_series['PRODUCTO'].astype(str).str.strip().str.lower()

                             # Crear un índice secuencial para manejar multiplicidad (ej. mismo producto 3 veces en un ticket)
                             df_series['SEQ_MATCH'] = df_series.groupby(['ID_MATCH', 'PROD_MATCH']).cumcount()

                             tot_actualizados = 0
                             for bloque_venta in tablas_ventas:
                                 df_v = get_df_from_sql(bloque_venta)

                                 # Standardize column names if needed
                                 col_id = 'id_venta' if 'id_venta' in df_v.columns else 'ID VENTA'
                                 col_prod = 'producto' if 'producto' in df_v.columns else 'PRODUCTO'

                                 if col_id in df_v.columns and col_prod in df_v.columns:
                                     df_v['ID_MATCH'] = df_v[col_id].astype(str).str.strip().str.lower()
                                     df_v['PROD_MATCH'] = df_v[col_prod].astype(str).str.strip().str.lower()

                                     # Crear el mismo índice secuencial en la tabla destino
                                     df_v['SEQ_MATCH'] = df_v.groupby(['ID_MATCH', 'PROD_MATCH']).cumcount()

                                     if 'NUMERO DE SERIE' not in df_v.columns:
                                         df_v['NUMERO DE SERIE'] = ""

                                     # Hacemos un left join incluyendo SEQ_MATCH para alinear 1-a-1
                                     df_merged = pd.merge(df_v, df_series[['ID_MATCH', 'PROD_MATCH', 'SEQ_MATCH', 'NUMERO DE SERIE']],
                                                          on=['ID_MATCH', 'PROD_MATCH', 'SEQ_MATCH'],
                                                          how='left', suffixes=('', '_new'))

                                     # Actualizamos los vacíos con los nuevos valores encontrados
                                     mask = df_merged['NUMERO DE SERIE_new'].notna() & (df_merged['NUMERO DE SERIE_new'] != "")
                                     df_merged.loc[mask, 'NUMERO DE SERIE'] = df_merged.loc[mask, 'NUMERO DE SERIE_new']

                                     tot_actualizados += mask.sum()

                                     # Limpieza antes de guardar
                                     df_merged = df_merged.drop(columns=['ID_MATCH', 'PROD_MATCH', 'SEQ_MATCH', 'NUMERO DE SERIE_new'], errors='ignore')

                                     update_table_from_df(df_merged, bloque_venta)

                             if tot_actualizados > 0:
                                 st.success(f"✅ ¡Cruce exitoso! Se rellenaron {tot_actualizados} números de serie en las notas de ventas.")
                             else:
                                 st.warning("⚠️ No se encontraron coincidencias exactas de ID Venta + Producto para rellenar.")
                     else:
                         st.error("El archivo de series no contiene las columnas necesarias (ID Venta, Producto, Número de Serie).")
            st.divider()

        # Mostrar Pestaña Única de Notas de Ventas
        st.subheader("🛒 Notas de Ventas (Detalle)")

        bloque = st.selectbox("Selecciona bloque operativo:", tablas_ventas)

        # La columna suele llamarse FECHA o fecha
        col_fecha_v = 'FECHA' # Fallback default
        # Podríamos consultar el schema, o simplemente pasar FECHA, render_filtros es tolerante

        # Aplicar filtros globales SQL-first
        df_v = render_filtros_globales_sql(bloque, col_fecha=col_fecha_v, key_prefix=f"ventas_{bloque}")

        # Formatear columnas para visualizacion
        mapa_cols = {
            'id_venta': 'ID VENTA',
            'fecha': 'FECHA',
            'sucursal': 'SUCURSAL',
            'producto': 'PRODUCTO',
            'precio_unitario': 'PRECIO UNITARIO',
            'nombre cliente': 'nombre cliente',
            'bancos_cobro': 'BANCOS COBRO',
            'numero_transaccion': 'NUMERO TRANSACCION',
        }

        # Renombrar si existen en la BD original
        for col_old, col_new in mapa_cols.items():
            if col_old in df_v.columns:
                df_v = df_v.rename(columns={col_old: col_new})

        # Crear columnas nuevas vacias (placeholders de conciliacion)
        if 'NUMERO DE SERIE' not in df_v.columns:
            df_v['NUMERO DE SERIE'] = ""
        if 'SUCURSAL BAN' not in df_v.columns:
            df_v['SUCURSAL BAN'] = ""

        # Columnas finales a mostrar
        cols_finales_v = ['ID VENTA', 'FECHA', 'SUCURSAL', 'PRODUCTO', 'NUMERO DE SERIE', 'PRECIO UNITARIO', 'nombre cliente', 'BANCOS COBRO', 'NUMERO TRANSACCION', 'SUCURSAL BAN']

        # Asegurar que existan (por si el excel viene distinto)
        for c in cols_finales_v:
            if c not in df_v.columns:
                df_v[c] = ""

        df_v_vista = df_v[cols_finales_v].copy()

        # Formatear a datetime/string si existe
        if 'FECHA' in df_v_vista.columns:
            try:
                df_v_vista['FECHA'] = safe_parse_dates(df_v_vista['FECHA']).dt.strftime('%d/%m/%Y')
            except Exception:
                df_v_vista['FECHA'] = df_v_vista['FECHA'].astype(str).str.replace(' 00:00:00', '')

        # Convertir a float
        if 'PRECIO UNITARIO' in df_v_vista.columns:
            df_v_vista['PRECIO UNITARIO'] = pd.to_numeric(df_v_vista['PRECIO UNITARIO'], errors='coerce')

        df_v_vista = df_v_vista.replace("None", "").replace("NaT", "")

        cc_v = {}
        if 'PRECIO UNITARIO' in df_v_vista.columns:
            df_v_vista['PRECIO UNITARIO'] = pd.to_numeric(df_v_vista['PRECIO UNITARIO'].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
            cc_v['PRECIO UNITARIO'] = st.column_config.NumberColumn('PRECIO UNITARIO', format="$%.2f")

        df_v_vista = df_v_vista.replace("None", "")

        # Export & Delete UI para Ventas
        st.divider()

        col_vbtn3, col_vbtn4 = st.columns(2)
        with col_vbtn3:
            from io import BytesIO
            def to_excel_ventas_det(df_to_export):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_to_export.to_excel(writer, index=False, sheet_name='Export')
                return output.getvalue()

            st.download_button(
                label=f"📥 Exportar Notas a Excel ({bloque})",
                data=to_excel_ventas_det(df_v_vista),
                file_name=f"{bloque}_Exportado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"export_{bloque}"
            )

        with col_vbtn4:
            if st.button(f"🗑️ Eliminar Bloque {bloque}", key=f"del_{bloque}", type="secondary"):
                st.session_state[f"confirm_del_{bloque}"] = True

            if st.session_state.get(f"confirm_del_{bloque}", False):
                st.warning("¿Estás seguro?")
                c_yes, c_no = st.columns(2)
                if c_yes.button("✅ Sí, borrar", key=f"yes_{bloque}", type="primary"):
                    if drop_table_from_sql(bloque):
                        st.success(f"Bloque {bloque} eliminado.")
                        st.session_state[f"confirm_del_{bloque}"] = False
                        import time
                        time.sleep(1.5)
                        st.rerun()
                if c_no.button("❌ No", key=f"no_{bloque}"):
                    st.session_state[f"confirm_del_{bloque}"] = False
                    st.rerun()

        # Preparar hipervínculo para abrir Expediente
        if 'ID VENTA' in df_v_vista.columns:
            df_v_vista['LINK_EXPEDIENTE'] = df_v_vista['ID VENTA'].apply(
                lambda x: f"/?expediente={x}" if pd.notnull(x) and str(x).strip() != "" else ""
            )
            cc_v['ID VENTA'] = st.column_config.LinkColumn(
                "ID VENTA (Clic para Expediente)",
                display_text=r"/\?expediente=(.*)"
            )
            df_v_vista['ID VENTA'] = df_v_vista['LINK_EXPEDIENTE']
            df_v_vista = df_v_vista.drop(columns=['LINK_EXPEDIENTE'])

        # Mostrar tabla estándar con hipervínculos (Sin Styler para evitar conflicto con column_config)
        st.dataframe(
            df_v_vista,
            use_container_width=True,
            hide_index=True,
            column_config=cc_v
        )


# ==========================================================
# ⚙️ O00: PRE-CLÁSICOS FISCALES (NUEVO)
# ==========================================================
elif eleccion == "⚙️ O00: PRE-CLÁSICOS FISCALES":
    st.title(":material/manufacturing: Módulo O00: Reglas Fiscales y Pre-clasificación")
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
# 🔄 I00: CRUCE INGRESOS
# ==========================================================
elif eleccion == "🔄 I00: CRUCE INGRESOS (Ventas)":
    st.title(":material/sync_alt: Módulo I00: Cruce de Ventas vs Bancos")

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
    with tab_a:
        cc_pendientes_bbva = {}
        if not df_alertas_bbva.empty and 'id_venta' in df_alertas_bbva.columns:
            df_alertas_bbva['LINK_EXPEDIENTE'] = df_alertas_bbva['id_venta'].apply(
                lambda x: f"/?expediente={x}" if pd.notnull(x) and str(x).strip() != "" else None
            )
            cc_pendientes_bbva['id_venta'] = st.column_config.LinkColumn(
                "ID VENTA (Expediente)",
                display_text=r"/\?expediente=(.*)"
            )
            df_alertas_bbva['id_venta'] = df_alertas_bbva['LINK_EXPEDIENTE']
            df_alertas_bbva = df_alertas_bbva.drop(columns=['LINK_EXPEDIENTE'])

        st.dataframe(df_alertas_bbva, use_container_width=True, column_config=cc_pendientes_bbva)

    with tab_b:
        st.markdown("✍️ **Edita directamente la columna `numero_transaccion`** para corregir las referencias y presiona el botón para guardar.")
        if not df_alertas_mp.empty:
            # Preparar hipervínculo en id_venta
            if 'id_venta' in df_alertas_mp.columns:
                df_alertas_mp['LINK_EXPEDIENTE'] = df_alertas_mp['id_venta'].apply(
                    lambda x: f"/?expediente={x}" if pd.notnull(x) and str(x).strip() != "" else None
                )

            # Habilitar edición solo para numero_transaccion
            column_config = {}
            for col in df_alertas_mp.columns:
                if col == "numero_transaccion":
                    column_config[col] = st.column_config.TextColumn("NUMERO TRANSACCION (Editable)", disabled=False)
                elif col == "id_venta":
                    column_config[col] = st.column_config.LinkColumn("ID VENTA (Expediente)", display_text=r"/\?expediente=(.*)", disabled=True)
                elif col != "LINK_EXPEDIENTE":
                    column_config[col] = st.column_config.Column(disabled=True)

            if 'id_venta' in df_alertas_mp.columns:
                df_alertas_mp['id_venta'] = df_alertas_mp['LINK_EXPEDIENTE']
                df_alertas_mp = df_alertas_mp.drop(columns=['LINK_EXPEDIENTE'])

            edited_mp = st.data_editor(
                df_alertas_mp,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
                key="editor_pendientes_mp"
            )

            if st.button("💾 Guardar Correcciones MP", type="primary"):
                # Detectar cambios
                cambios = edited_mp[edited_mp['numero_transaccion'] != df_alertas_mp['numero_transaccion']]
                if not cambios.empty:
                    with st.spinner("Guardando..."):
                        # Actualizar en la DB
                        df_original = get_df_from_sql("VENTAS_MP")
                        if not df_original.empty:
                            # Hacer merge o update
                            for idx, fila in cambios.iterrows():
                                # Restaurar el ID crudo eliminando el prefijo del hipervínculo
                                raw_id = str(fila['id_venta']).replace("/?expediente=", "") if pd.notna(fila['id_venta']) else fila['id_venta']
                                df_original.loc[df_original['id_venta'] == raw_id, 'numero_transaccion'] = fila['numero_transaccion']
                            update_table_from_df(df_original, "VENTAS_MP")
                        st.success(f"✅ Se guardaron {len(cambios)} correcciones. ¡Ya puedes volver a intentar el cruce!")
                else:
                    st.info("No se detectaron cambios para guardar.")
        else:
            st.success("No hay pendientes para Mercado Pago.")

# ==========================================================
# 💸 ANÁLISIS EGRESOS
# ==========================================================
elif eleccion == "💸 CRUCE EGRESOS":
    st.title(":material/payments: Motor de Conciliación de Egresos")
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
             st.dataframe(pendientes.style.format(na_rep=""), use_container_width=True)

# ==========================================================
# 📊 DASHBOARD Y REPORTES
# ==========================================================
elif eleccion == "📊 DASHBOARD & REPORTES":
    st.title(":material/analytics: Tablero Ejecutivo y Generador de Reportes")

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
    # Incluir cuentas BBVA antiguas y las nuevas con prefijos EST y DET
    bancos_bbva = [t for t in tablas if t.startswith("BANCO_") and (
        t.replace("BANCO_", "").isdigit() or
        t.startswith("BANCO_BBVA_EST_") or
        t.startswith("BANCO_BBVA_DET_")
    )]
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
