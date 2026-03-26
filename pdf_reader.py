import pandas as pd
import streamlit as st

def parse_bank_pdf(file_obj):
    """
    Función Placeholder para procesar estados de cuenta en PDF.
    En un entorno real de producción, aquí importaríamos `pdfplumber` o `PyPDF2`.

    Ejemplo de flujo real:
    1. with pdfplumber.open(file_obj) as pdf:
    2.     for page in pdf.pages:
    3.         table = page.extract_table()
    4.         # Limpiar encabezados, convertir a DataFrame
    """
    st.info("💡 Módulo de Extracción de PDFs (OCR):")
    st.markdown("""
    *Esta es una característica avanzada en desarrollo.*

    El flujo de trabajo automatizará esto:
    1. **Extracción:** Leemos las tablas ocultas dentro de tu Estado de Cuenta en PDF (BBVA o Santander).
    2. **Transformación:** Las columnas se estandarizan a `FECHA`, `DESCRIPCION`, `CARGO`, `ABONO`, `SALDO`.
    3. **Carga:** Se inyectan directamente a la base de datos SQL como si hubieras subido el Excel.

    *(Para habilitar esto en producción, instalaremos la librería `pdfplumber` y pediremos un PDF de prueba).*
    """)
    return pd.DataFrame()
