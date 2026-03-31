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
        data = []
        year_extracted = None
        cuenta_extracted = None

        with pdfplumber.open(file_obj) as pdf:
            # Primero intentar extraer Año y No. de Cuenta de las primeras páginas
            for page in pdf.pages[:3]:
                text = page.extract_text()
                if text:
                    if not year_extracted:
                        match_year = re.search(r'Periodo\s+DEL\s+\d{2}/\d{2}/(\d{4})', text)
                        if match_year:
                            year_extracted = match_year.group(1)
                    if not cuenta_extracted:
                        match_cuenta = re.search(r'No\.\s*de\s*Cuenta\s+(\d+)', text)
                        if match_cuenta:
                            cuenta_str = match_cuenta.group(1)
                            cuenta_extracted = cuenta_str[-5:] if len(cuenta_str) >= 5 else cuenta_str

            for i, page in enumerate(pdf.pages):
                words = page.extract_words()
                if not words: continue

                # Agrupar palabras por su coordenada Y (con tolerancia de 2px para alinear la misma fila)
                lines_by_y = {}
                for w in words:
                    y = round(w['top'] / 2) * 2
                    if y not in lines_by_y:
                        lines_by_y[y] = []
                    lines_by_y[y].append(w)

                in_table = False
                for y in sorted(lines_by_y.keys()):
                    row_words = sorted(lines_by_y[y], key=lambda w: w['x0'])
                    text = ' '.join([w['text'] for w in row_words])

                    # Detectar inicio de tabla BBVA
                    if 'OPER' in text and 'LIQ' in text and 'COD.' in text and 'DESCRIPCIÓN' in text:
                        in_table = True
                        continue

                    # Detectar fin de tabla
                    if in_table and ('Total de Movimientos' in text or 'Total de Cargos' in text or 'Total de' in text):
                        in_table = False
                        continue

                    if in_table:
                        # Buscar si la fila inicia con una fecha (DD/MMM)
                        primary_date = next((w for w in row_words if w['x0'] < 50 and re.match(r'^\d{2}/[A-Z]{3}$', w['text'])), None)

                        if primary_date:
                            # Formatear la fecha si tenemos el año
                            fecha_str = primary_date['text']
                            if year_extracted:
                                meses = {'ENE': '01', 'FEB': '02', 'MAR': '03', 'ABR': '04', 'MAY': '05', 'JUN': '06',
                                         'JUL': '07', 'AGO': '08', 'SEP': '09', 'OCT': '10', 'NOV': '11', 'DIC': '12'}
                                parts = fecha_str.split('/')
                                if len(parts) == 2 and parts[1] in meses:
                                    fecha_str = f"{parts[0]}/{meses[parts[1]]}/{year_extracted}"

                            # Es una nueva fila de movimiento. Agrupar palabras por coordenada X
                            cod_words = [w['text'] for w in row_words if 65 <= w['x0'] < 105]
                            desc_words = [w['text'] for w in row_words if 105 <= w['x0'] < 225]
                            ref_words = [w['text'] for w in row_words if 225 <= w['x0'] < 355]
                            cargo_words = [w['text'] for w in row_words if 355 <= w['x0'] < 415]
                            abono_words = [w['text'] for w in row_words if 415 <= w['x0'] < 470]
                            saldo_words = [w['text'] for w in row_words if 470 <= w['x0'] < 535]

                            row_data = {
                                'FECHA': fecha_str,
                                'COD': ' '.join(cod_words),
                                'CONCEPTO': ' '.join(desc_words),
                                'REFERENCE': ' '.join(ref_words),
                                'CARGO': ' '.join(cargo_words),
                                'ABONO': ' '.join(abono_words),
                                'SALDO': ' '.join(saldo_words)
                            }
                            # Agregar el código al concepto para mayor contexto si existe
                            if row_data['COD']:
                                row_data['CONCEPTO'] = f"{row_data['COD']} {row_data['CONCEPTO']}".strip()

                            data.append(row_data)
                        else:
                            # Fila de continuación (texto descriptivo en multilínea)
                            if data and row_words:
                                # Prevenir que se capture texto del footer o márgenes (ej. "Estimado Cliente...")
                                # verificando que el texto de descripción no esté demasiado a la izquierda
                                extra_desc = ' '.join([w['text'] for w in row_words if 65 <= w['x0'] < 225])
                                extra_ref = ' '.join([w['text'] for w in row_words if 225 <= w['x0'] < 355])

                                # Evitar agregar avisos genéricos del banco que aparecen en el pie de página
                                invalid_phrases = ['Estimado Cliente', 'Estado de Cuenta ha sido', 'También le informamos', 'rendimiento que obtendría', 'INSTITUCION DE BANCA', 'Reforma 510', 'cual puede consultarlo', 'modificado y ahora tiene', 'en cualquier sucursal', 'Con BBVA adelante', 'la inflación estimada', 'GRUPO FINANCIERO BBVA MEXICO', 'C.P. 06600', 'Ciudad de México', 'México', 'BBVA México', 'que su Contrato']
                                if extra_desc and not any(phrase in extra_desc for phrase in invalid_phrases):
                                    data[-1]['CONCEPTO'] += ' ' + extra_desc
                                if extra_ref and not any(phrase in extra_ref for phrase in invalid_phrases):
                                    data[-1]['REFERENCE'] += ' ' + extra_ref

        if not data:
            st.warning(f"⚠️ No se encontraron movimientos estructurados en el PDF {file_obj.name}.")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Parsear fechas de DD/MM/YYYY a datetime real para que SQLite y Pandas no inviertan mes/día
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], format='%d/%m/%Y', errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')

        # Limpieza final de montos numéricos (quitar comas y signos de $)
        for num_col in ['CARGO', 'ABONO', 'SALDO']:
            df[num_col] = df[num_col].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df[num_col] = pd.to_numeric(df[num_col], errors='coerce')

        # Agregar columnas faltantes para tener el esquema estandar de 10 columnas
        for col in ['OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']:
            df[col] = ''

        df = df[['FECHA', 'CONCEPTO', 'REFERENCE', 'CARGO', 'ABONO', 'SALDO', 'OBSERVACION', 'UUID COMPL.', 'UUID MADRE', 'ID VENTA']]

        # Guardar en SQLite
        # Si logramos extraer la cuenta, usamos su terminación para nombrar la tabla (ej. BANCO_BBVA_EST_21387)
        # EST = Estado de Cuenta (oficial) para separarlo del Detalle en Excel
        if cuenta_extracted:
            nombre_tabla = f"BANCO_BBVA_EST_{cuenta_extracted}"
        else:
            nombre_limpio = re.sub(r'[^a-zA-Z0-9]', '_', file_obj.name.split('.')[0]).upper()
            nombre_tabla = f"BANCO_PDF_{nombre_limpio}"

        save_df_to_sql(df, nombre_tabla)
        st.success(f"✅ PDF '{file_obj.name}' procesado y guardado como {nombre_tabla} ({len(df)} movimientos).")
        return df

    except Exception as e:
        st.error(f"❌ Error al procesar el PDF {file_obj.name}: {str(e)}")
        return pd.DataFrame()
