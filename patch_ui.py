import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update Ventas UI to include UUID
search_ventas = """        cols_finales_v = ['ID VENTA', 'FECHA', 'SUCURSAL', 'PRODUCTO', 'NUMERO DE SERIE', 'PRECIO UNITARIO', 'nombre cliente', 'BANCOS COBRO', 'NUMERO TRANSACCION', 'SUCURSAL BAN']"""

replace_ventas = """        cols_finales_v = ['ID VENTA', 'FECHA', 'SUCURSAL', 'PRODUCTO', 'NUMERO DE SERIE', 'PRECIO UNITARIO', 'nombre cliente', 'BANCOS COBRO', 'NUMERO TRANSACCION', 'SUCURSAL BAN', 'UUID']"""

content = content.replace(search_ventas, replace_ventas)

# 2. Update CFDI UI to render PDF links
search_cfdi = """            # Asegurar que las columnas deseadas existan (llenar con vacío si son placeholders)
            for col in cols_deseadas:
                if col not in df_mostrar.columns:
                    df_mostrar[col] = ""

            # Filtrar solo las columnas solicitadas
            df_mostrar = df_mostrar[cols_deseadas]

            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")

            st.dataframe(df_mostrar.style.format(na_rep=""), use_container_width=True, hide_index=True)"""

replace_cfdi = """            # Asegurar que las columnas deseadas existan (llenar con vacío si son placeholders)
            for col in cols_deseadas:
                if col not in df_mostrar.columns:
                    df_mostrar[col] = ""

            # Filtrar solo las columnas solicitadas
            df_mostrar = df_mostrar[cols_deseadas]

            df_mostrar = df_mostrar.replace("None", "").replace("NaT", "")

            # Formatear el PDF como un link si existe el ID VENTA vinculado
            cc_cfdi = {}
            if 'PDF' in df_mostrar.columns and 'ID VENTA' in df_mostrar.columns:
                df_mostrar['LINK_PDF'] = df_mostrar.apply(
                    lambda row: f"/?expediente={row['ID VENTA']}" if pd.notnull(row['ID VENTA']) and str(row['ID VENTA']).strip() != "" and pd.notnull(row['PDF']) and str(row['PDF']).strip() != "" else row['PDF'],
                    axis=1
                )
                cc_cfdi['PDF'] = st.column_config.LinkColumn(
                    "PDF (Expediente)",
                    display_text=r"([^/]+)$" # Muestra solo el nombre del archivo al final del link o el valor original si no es link
                )
                # Solo reemplazar donde hay link, si no dejar el texto
                mask = df_mostrar['LINK_PDF'].str.startswith('/?expediente', na=False)
                df_mostrar.loc[mask, 'PDF'] = df_mostrar.loc[mask, 'LINK_PDF']
                df_mostrar = df_mostrar.drop(columns=['LINK_PDF'])

            st.dataframe(df_mostrar, use_container_width=True, hide_index=True, column_config=cc_cfdi)"""

content = content.replace(search_cfdi, replace_cfdi)

with open('app.py', 'w') as f:
    f.write(content)
