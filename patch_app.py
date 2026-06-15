import re

with open("app.py", "r") as f:
    content = f.read()

search_str = """elif eleccion == "🔄 I00: CRUCE INGRESOS (Ventas)":
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
        else: st.success(f"✅ {res.get('matches_pue',0)} PUE / {res.get('matches_ppd',0)} PPD.")"""

replace_str = """elif eleccion == "🔄 I00: CRUCE INGRESOS (Ventas)":
    st.title(":material/sync_alt: Módulo I00: Cruce de Ventas vs Bancos")

    tablas_i00 = get_all_tables()
    can_bbva = "VENTAS_BBVA" in tablas_i00 and any(t.startswith("BANCO_") for t in tablas_i00)
    can_mp = "VENTAS_MP" in tablas_i00 and "AUX_MP_DETALLE" in tablas_i00
    can_cfdi = any(t in tablas_i00 for t in ["CFDI_I_PUE", "CFDI_I_PPD", "CFDI_CFDI_I_PUE", "CFDI_CFDI_I_PPD"])

    col1, col2, col3 = st.columns(3)
    if col1.button("🚀 Cruce BBVA", type="primary", disabled=not can_bbva, help="Requiere subir Notas de Venta (BBVA) y Estados de Cuenta Bancarios (BANCO_)." if not can_bbva else "Ejecuta el cruce de ventas con depósitos BBVA."):
        res = run_bbva_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res['matches']} abonos BBVA conciliados.")

    if col2.button("⚙️ Cruce Mercado Pago", type="primary", disabled=not can_mp, help="Requiere subir Notas de Venta (MP) y Detalle de Movimientos Operativos (AUX_MP_DETALLE)." if not can_mp else "Ejecuta el cruce de ventas con tickets de Mercado Pago."):
        res = run_mp_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res['matches']} tickets MP conciliados.")

    if col3.button("📄 Propagar a CFDI Ingresos", type="primary", disabled=not can_cfdi, help="Requiere subir facturas CFDI de Ingresos (PUE o PPD)." if not can_cfdi else "Propaga los UUID de CFDI a las ventas conciliadas."):
        res = run_cfdi_crosscheck()
        if "error" in res: st.error(res["error"])
        else: st.success(f"✅ {res.get('matches_pue',0)} PUE / {res.get('matches_ppd',0)} PPD.")"""

if search_str in content:
    content = content.replace(search_str, replace_str)
    with open("app.py", "w") as f:
        f.write(content)
    print("Patch applied successfully.")
else:
    print("Search string not found in app.py")
