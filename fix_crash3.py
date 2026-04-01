import re

with open("app.py", "r") as f:
    content = f.read()

# check if the format_dict lambda checks pd.notnull. It might crash if it is not nan but empty string
# Actually we can do: lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else ""

old_lambda_banco = """                        format_dict[c] = lambda x: f"${x:,.2f}" if pd.notnull(x) else "" """
new_lambda_banco = """                        format_dict[c] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else "" """

if old_lambda_banco in content:
    content = content.replace(old_lambda_banco, new_lambda_banco)
    print("Fixed lambda banco")

old_lambda_vr = """                            format_dict_resumen[col] = lambda x: f"${x:,.2f}" if pd.notnull(x) else "" """
new_lambda_vr = """                            format_dict_resumen[col] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else "" """

if old_lambda_vr in content:
    content = content.replace(old_lambda_vr, new_lambda_vr)
    print("Fixed lambda vr")

old_lambda_vn = """                        format_dict_v['PRECIO UNITARIO'] = lambda x: f"${x:,.2f}" if pd.notnull(x) else "" """
new_lambda_vn = """                        format_dict_v['PRECIO UNITARIO'] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else "" """

if old_lambda_vn in content:
    content = content.replace(old_lambda_vn, new_lambda_vn)
    print("Fixed lambda vn")

with open("app.py", "w") as f:
    f.write(content)
