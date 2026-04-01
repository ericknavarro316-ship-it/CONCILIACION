import re

with open("app.py", "r") as f:
    content = f.read()

old_code = """                        if diferencia > 1.0:
                            st.error(f"⚖️ **Posible Descuadre Detectado:** El Saldo Final reportado es **${ultimo_saldo:,.2f}**, pero según la suma de movimientos debería ser **${saldo_final_calculado:,.2f}** (Diferencia: **${diferencia:,.2f}**). Verifica si faltan páginas o registros.")"""

new_code = """                        if diferencia > 1.0:
                            if not st.session_state.get(f"warned_descuadre_{cuenta_sel}", False):
                                st.toast(f"⚖️ **Posible Descuadre Detectado en {cuenta_sel}:** Diferencia de **${diferencia:,.2f}**.", icon="⚠️")
                                st.session_state[f"warned_descuadre_{cuenta_sel}"] = True
                            with st.expander("⚠️ Alerta de Posible Descuadre"):
                                st.error(f"El Saldo Final reportado es **${ultimo_saldo:,.2f}**, pero según la suma de movimientos debería ser **${saldo_final_calculado:,.2f}** (Diferencia: **${diferencia:,.2f}**). Verifica si faltan páginas o registros.")"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open("app.py", "w") as f:
        f.write(content)
    print("Replaced!")
else:
    print("Not found!")
