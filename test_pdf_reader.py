import pandas as pd
from pdf_reader import parse_bank_pdf

class MockFileObj:
    def __init__(self, name):
        self.name = name

file_obj = MockFileObj("test_file.pdf")

try:
    print("Testing parse_bank_pdf import and initialization...")
    import pdfplumber
    print("pdfplumber imported successfully")
except Exception as e:
    print(f"Error: {e}")
