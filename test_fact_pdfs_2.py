import pdfplumber
import os
import re

directory = "fact"
filename = "FGDL0000000637 OK.pdf"
filepath = os.path.join(directory, filename)
try:
    with pdfplumber.open(filepath) as pdf:
        print(f"--- Extrayendo de {filename} ---")
        text = ""
        for page in pdf.pages[:2]:
            text += page.extract_text() + "\n"

        # Look for the strange hyphen characters
        match = re.search(r'[0-9A-Fa-f]{8}[^\w][0-9A-Fa-f]{4}[^\w][0-9A-Fa-f]{4}[^\w][0-9A-Fa-f]{4}[^\w][0-9A-Fa-f]{12}', text)
        if match:
            print(f"✅ Flexible standalone match: {match.group(0)}")
            print("Unicode repr:", ascii(match.group(0)))
        else:
            print(f"❌ No UUID found. Text sample:\n{text[-500:]}")
except Exception as e:
    print(f"Error on {filename}: {e}")
