import re

with open("app.py", "r") as f:
    content = f.read()

# Let's fix the lambdas to handle strings securely
def replace_lambda(old, new):
    global content
    if old in content:
        content = content.replace(old, new)
        print("Replaced!")

# 1. format_dict[c] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
old_1 = """format_dict[c] = lambda x: f"${x:,.2f}" if pd.notnull(x) else \"\""""
new_1 = """format_dict[c] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else \"\""""
replace_lambda(old_1, new_1)

# 2. format_dict_resumen[col] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
old_2 = """format_dict_resumen[col] = lambda x: f"${x:,.2f}" if pd.notnull(x) else \"\""""
new_2 = """format_dict_resumen[col] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else \"\""""
replace_lambda(old_2, new_2)

# 3. format_dict_v['PRECIO UNITARIO'] = lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
old_3 = """format_dict_v['PRECIO UNITARIO'] = lambda x: f"${x:,.2f}" if pd.notnull(x) else \"\""""
new_3 = """format_dict_v['PRECIO UNITARIO'] = lambda x: f"${float(x):,.2f}" if pd.notnull(x) and str(x).strip() != "" else \"\""""
replace_lambda(old_3, new_3)

with open("app.py", "w") as f:
    f.write(content)
