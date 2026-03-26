import streamlit as st

def check_password():
    """Retorna True si el usuario ingresó una contraseña correcta."""

    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No guardamos el password en memoria por seguridad
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Acceso Restringido - ERP de Conciliación")
        st.text_input("Contraseña de Acceso", type="password", on_change=password_entered, key="password")
        return False

    elif not st.session_state["password_correct"]:
        st.title("🔐 Acceso Restringido - ERP de Conciliación")
        st.text_input("Contraseña de Acceso", type="password", on_change=password_entered, key="password")
        st.error("❌ Contraseña incorrecta")
        return False

    else:
        return True
