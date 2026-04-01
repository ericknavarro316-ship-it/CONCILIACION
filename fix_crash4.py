import re
with open("app.py", "r") as f:
    content = f.read()

# Let's ensure no other formatting lambda is crashing
# Also make sure there are no remaining fillna("")
import pandas as pd
print("Any fillna in file?", "fillna(\"\")" in content)
