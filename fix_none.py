import re

with open("app.py", "r") as f:
    content = f.read()

# For pandas .style.format, if the column contains the string "None", the string formatter might throw an exception or just string-format it.
# Oh wait, if the value is the literal string "None", `.style.format` won't apply `.replace('None', '')` properly or na_rep.
# Let's see where the user reported this. The user showed an image where the ABONO/CARGO/SALDO columns have the literal text "None".
# In app.py line 614:
# df_mostrar = df_mostrar.fillna("")
# df_mostrar = df_mostrar.replace("None", "")
# BUT right after that, in line 630:
# temp_num = pd.to_numeric(df_mostrar[col_moneda].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False), errors='coerce')
# df_mostrar[col_moneda] = temp_num

# Wait, if temp_num is generated with errors='coerce', it becomes NaN.
# But maybe we fill it with None?
# Wait, let's look at what Streamlit does. If a dataframe has NaN, Streamlit renders it as `None` in the frontend table sometimes unless it's handled.

# If the DataFrame is stylized with `df.style.format(..., na_rep="")`, pandas NaNs should be formatted as "".
# Why did it show "None" in the screenshot?
# Because the formatting dictionary format_dict = {'CARGO': '${:,.2f}'} is applied.
# However, if format_dict is only applied using `.format(format_dict, na_rep="")`, maybe there are other columns like SALDO that are not in format_dict?
# Let's check `format_dict` creation:
old_format_dict = """                # Create format dict for money columns
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        format_dict[c] = "${:,.2f}" """

new_format_dict = """                # Create format dict for money columns
                format_dict = {}
                for c in ['CARGO', 'ABONO', 'SALDO', 'Valor del cargo', 'Valor de la operación']:
                    if c in df_mostrar.columns:
                        # Asegurar que la columna es verdaderamente numérica para el formateo
                        df_mostrar[c] = pd.to_numeric(df_mostrar[c], errors='coerce')
                        format_dict[c] = lambda x: f"${x:,.2f}" if pd.notnull(x) else "" """

if old_format_dict in content:
    content = content.replace(old_format_dict, new_format_dict)
    print("Fixed format dict lambda")

with open("app.py", "w") as f:
    f.write(content)
