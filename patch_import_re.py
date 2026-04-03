with open('app.py', 'r') as f:
    content = f.read()

search = """import streamlit as st
import pandas as pd
import os"""

replace = """import streamlit as st
import pandas as pd
import os
import re"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
