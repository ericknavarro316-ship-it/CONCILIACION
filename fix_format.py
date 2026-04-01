import re

with open("app.py", "r") as f:
    content = f.read()

# Replace format="$%,.2f" back to None in NumberColumn
# Actually wait, we should just use st.column_config.NumberColumn(col_moneda) without format
# and then use df.style.format() when displaying the dataframe.

content = content.replace('format="$%,.2f"', 'format="$%.2f"')
with open("app.py", "w") as f:
    f.write(content)
