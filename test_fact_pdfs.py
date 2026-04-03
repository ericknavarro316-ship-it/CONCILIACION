import pdfplumber
import os
import re

directory = "fact"
for filename in os.listdir(directory):
    if filename.endswith(".pdf"):
        filepath = os.path.join(directory, filename)
        try:
            with pdfplumber.open(filepath) as pdf:
                print(f"--- Extrayendo de {filename} ---")
                text = ""
                for page in pdf.pages[:2]: # First two pages
                    text += page.extract_text() + "\n"

                # Check for "Folio fiscal:"
                match1 = re.search(r'Folio[ \t]*fiscal\s*:?\s*([0-9A-Fa-f\-]{36})', text, re.IGNORECASE)
                if match1:
                    print(f"✅ Folio fiscal match: {match1.group(1)}")
                else:
                    # check for standalone
                    match2 = re.search(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}', text)
                    if match2:
                        print(f"✅ Standalone match: {match2.group(0)}")
                    else:
                        print(f"❌ No UUID found. Text sample:\n{text[-500:]}")
                print("====================\n")
        except Exception as e:
            print(f"Error on {filename}: {e}")
