import pandas as pd
import streamlit as st
import pdfplumber
import io
import re
from database_sqlite import save_df_to_sql

def parse_bank_pdf(file_obj):
    """
    Procesa estados de cuenta en PDF (Principalmente BBVA).
    Extrae tablas de movimientos, limpia encabezados y estandariza a:
    FECHA, DESCRIPCION, CARGO, ABONO, SALDO.
    """
    st.info(f"📄 Procesando PDF: {file_obj.name}...")

    # Leer el PDF desde el objeto BytesIO en memoria
    all_rows = []

    try:
        with pdfplumber.open(file_obj) as pdf:
            for i, page in enumerate(pdf.pages):
                table = page.extract_table()
                if table:
                    # Limpiamos las celdas de la tabla (quitamos saltos de linea extraños)
                    for row in table:
                        cleaned_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                        # Filtrar filas completamente vacías
                        if any(cleaned_row):
                            all_rows.append(cleaned_row)

        if not all_rows:
            st.warning(f"⚠️ No se encontraron tablas estructuradas en el PDF {file_obj.name}.")
            return pd.DataFrame()

        # Convertir a DataFrame crudo
        df_raw = pd.DataFrame(all_rows)

        # Buscar la fila de encabezados (buscamos 'FECHA' o 'DIA')
        fila_encabezado = -1
        for i, row in df_raw.iterrows():
            row_str = " ".join(row.astype(str).str.upper())
            if 'FECHA' in row_str or 'DIA' in row_str or 'DÍA' in row_str:
                fila_encabezado = i
                break

        if fila_encabezado == -1:
            st.error(f"❌ No se pudo identificar la fila de encabezados en {file_obj.name}.")
            return pd.DataFrame()

        # Asignar encabezados y recortar las filas superiores
        # Usamos df_raw para evitar errores de longitud dispar en las listas (pandas lo rellena con None)
        df = df_raw.iloc[fila_encabezado+1:].copy()

        # El encabezado será la fila que encontramos (convertido a strings limpios)
        encabezados = [str(col).strip() if pd.notna(col) else f"COL_{i}" for i, col in enumerate(df_raw.iloc[fila_encabezado])]
        df.columns = encabezados

        # Limpiar y mapear columnas
        cols_map = {}
        for col in df.columns:
            if not col: continue
            col_str = str(col).strip().upper()
            if 'FECHA' in col_str or 'DIA' in col_str or 'DÍA' in col_str:
                cols_map[col] = 'FECHA'
            elif 'CONCEPTO' in col_str or 'DESCRIPCIÓN' in col_str or 'DESCRIPCION' in col_str or 'REFERENCIA' in col_str:
                cols_map[col] = 'DESCRIPCION'
            elif 'CARGO' in col_str or 'RETIRO' in col_str:
                cols_map[col] = 'CARGO'
            elif 'ABONO' in col_str or 'DEPOSITO' in col_str or 'DEPÓSITO' in col_str:
                cols_map[col] = 'ABONO'
            elif 'SALDO' in col_str:
                cols_map[col] = 'SALDO'

        df = df.rename(columns=cols_map)

        # Quedarnos solo con las columnas estandarizadas
        columnas_finales = [c for c in ['FECHA', 'DESCRIPCION', 'CARGO', 'ABONO', 'SALDO'] if c in df.columns]

        if not columnas_finales:
             st.error(f"❌ No se pudieron mapear las columnas requeridas en {file_obj.name}.")
             return pd.DataFrame()

        df = df[columnas_finales].dropna(how='all')

        # Limpieza final de montos numéricos (quitar comas y signos de $)
        for num_col in ['CARGO', 'ABONO', 'SALDO']:
            if num_col in df.columns:
                df[num_col] = df[num_col].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce')

        # Guardar en SQLite (Usamos un nombre generico + identificador único simple para evitar colisiones)
        # Extraemos solo letras y numeros del nombre original para el nombre de la tabla
        nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '_', file_obj.name.split('.')[0]).upper()
        nombre_tabla = f"BANCO_PDF_{nombre_limpio}"

        save_df_to_sql(df, nombre_tabla)
        st.success(f"✅ PDF '{file_obj.name}' procesado y guardado como {nombre_tabla} ({len(df)} movimientos).")
        return df

    except Exception as e:
        st.error(f"❌ Error al procesar el PDF {file_obj.name}: {str(e)}")
        return pd.DataFrame()
