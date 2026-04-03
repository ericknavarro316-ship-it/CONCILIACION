import re

with open('app.py', 'r') as f:
    content = f.read()

search = """    tab_a, tab_b = st.tabs(["Pendientes BBVA", "Pendientes MP"])
    with tab_a:"""

replace = """    def render_sugerencias_inteligentes(df_pendientes):
        st.info("💡 **Sugerencias de Conciliación Inteligente:** Hemos encontrado pagos en el banco que se acercan a los montos de estas ventas huérfanas pero exceden la tolerancia estricta, o cayeron en meses diferentes. Puedes forzar la conciliación manualmente aquí.")

        # 1. Buscar abonos bancarios huérfanos
        tablas_todas = get_all_tables()
        cuentas_bbva = [t for t in tablas_todas if t.startswith("BANCO_") and t.endswith("_CRUZADO")]

        abonos_huerfanos = []
        for cta in cuentas_bbva:
            df_cta = get_df_from_sql(cta)
            if not df_cta.empty and 'ABONO' in df_cta.columns and 'ID_VENTA_CRUCE' in df_cta.columns:
                huerfanos = df_cta[pd.isna(df_cta['ID_VENTA_CRUCE']) & pd.notna(df_cta['ABONO'])].copy()
                if not huerfanos.empty:
                    huerfanos['CUENTA_ORIGEN'] = cta
                    huerfanos['IDX_ORIGEN'] = huerfanos.index
                    abonos_huerfanos.append(huerfanos)

        if not abonos_huerfanos:
            st.success("No se detectaron depósitos huérfanos en los bancos para sugerir.")
            return

        df_abonos_libres = pd.concat(abonos_huerfanos, ignore_index=True)
        df_abonos_libres['ABONO_NUM'] = pd.to_numeric(df_abonos_libres['ABONO'], errors='coerce')

        # 2. Generar sugerencias
        sugerencias = []
        # Agrupar ventas pendientes por ID
        df_pend_grp = df_pendientes.groupby('id_venta', as_index=False).agg({
            'precio_real': 'sum',
            'fecha': 'first'
        })

        for _, venta in df_pend_grp.iterrows():
            total_venta = pd.to_numeric(venta['precio_real'], errors='coerce')
            if pd.isna(total_venta) or total_venta <= 0: continue

            # Buscar abonos que varíen hasta en un 5% del valor (tolerancia holgada)
            tolerancia_holgada = total_venta * 0.05
            if tolerancia_holgada < 100: tolerancia_holgada = 100 # minimo 100 pesos de busqueda

            candidatos = df_abonos_libres[abs(df_abonos_libres['ABONO_NUM'] - total_venta) <= tolerancia_holgada]

            for _, cand in candidatos.iterrows():
                sugerencias.append({
                    'ID_VENTA_PENDIENTE': venta['id_venta'],
                    'TOTAL_VENTA': total_venta,
                    'FECHA_VENTA': venta['fecha'],
                    'ABONO_CANDIDATO': cand['ABONO_NUM'],
                    'FECHA_BANCO': cand.get('FECHA', ''),
                    'CUENTA_BANCO': cand['CUENTA_ORIGEN'].replace('BANCO_', '').replace('_CRUZADO', ''),
                    'DIFERENCIA': cand['ABONO_NUM'] - total_venta,
                    '_CTA_ORIGEN': cand['CUENTA_ORIGEN'],
                    '_IDX_ORIGEN': cand['IDX_ORIGEN']
                })

        if sugerencias:
            df_sug = pd.DataFrame(sugerencias)

            # Quitar nulos y formatear
            df_sug_ui = df_sug.copy()
            for col in ['TOTAL_VENTA', 'ABONO_CANDIDATO', 'DIFERENCIA']:
                df_sug_ui[col] = df_sug_ui[col].apply(lambda x: f"${x:,.2f}")

            # Mostramos las sugerencias con checkbox
            st.dataframe(df_sug_ui[['ID_VENTA_PENDIENTE', 'FECHA_VENTA', 'TOTAL_VENTA', 'ABONO_CANDIDATO', 'FECHA_BANCO', 'CUENTA_BANCO', 'DIFERENCIA']], use_container_width=True)

            st.markdown("⚠️ *Por el momento, las sugerencias son sólo de lectura/análisis para que sepas dónde pudo haber quedado el depósito. En la próxima actualización habilitaremos el botón para auto-aprobarlas.*")
        else:
            st.success("No se detectaron depósitos bancarios que se asemejen a las ventas pendientes.")

    tab_a, tab_b, tab_c = st.tabs(["Pendientes BBVA", "Pendientes MP", "Sugerencias Inteligentes 🧠"])
    with tab_a:"""

content = content.replace(search, replace)

search_tab_b = """            if st.button("💾 Guardar Correcciones MP", type="primary"):"""

replace_tab_b = """            if st.button("💾 Guardar Correcciones MP", type="primary"):"""

search_tab_c = """    with tab_b:"""

replace_tab_c = """    with tab_c:
        if not df_alertas_bbva.empty:
            render_sugerencias_inteligentes(df_alertas_bbva)
        else:
            st.info("No hay ventas de BBVA pendientes para analizar.")

    with tab_b:"""

content = content.replace(search_tab_c, replace_tab_c)

with open('app.py', 'w') as f:
    f.write(content)
