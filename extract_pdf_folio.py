import sys
import pdfplumber
import re

def extract_folio(filepath):
    try:
        with pdfplumber.open(filepath) as pdf:
            text = pdf.pages[0].extract_text()
            match = re.search(r'Folio:\s*(.*?)(?=\n|Fecha|$)', text, re.IGNORECASE)
            if match:
                id_venta = match.group(1).strip()
                # Extract only the numbers from the Folio
                number_match = re.search(r'\d+', id_venta)
                if number_match:
                    return number_match.group(0)
                return id_venta
            return "Not found"
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(extract_folio(sys.argv[1]))
