import pandas as pd
df = pd.DataFrame({"ABONO": [1700.0, None, "None", pd.NA, float('nan')]})
format_dict = {"ABONO": "${:,.2f}"}

print(df.style.format(format_dict, na_rep="").to_html())
