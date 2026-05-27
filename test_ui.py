import pytest
from playwright.sync_api import sync_playwright
import sqlite3
import pandas as pd
import os

def seed_db():
    conn = sqlite3.connect("conciliacion_data.db")
    df = pd.DataFrame({
        "FECHA": ["2026-05-01", "2026-05-02"],
        "CONCEPTO": ["A", "B"],
        "REFERENCE": ["", ""],
        "ABONO": ["100", ""],
        "CARGO": ["", "50"],
        "SALDO": ["100", "50"]
    })
    df.to_sql("BANCO_TEST_EST", conn, if_exists="replace", index=False)

    df_ventas = pd.DataFrame({
        "ID VENTA": ["V1"],
        "FECHA": ["2026-05-01"],
        "PRODUCTO": ["Prod"],
        "PRECIO UNITARIO": [100]
    })
    df_ventas.to_sql("VENTAS_TEST", conn, if_exists="replace", index=False)
    conn.close()

def test_mass_assignment_placeholder():
    seed_db()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.wait_for_selector('text=Módulos Avanzados', timeout=10000)

        # Test Ventas button widths first
        page.evaluate("() => { Array.from(document.querySelectorAll('label')).find(el => el.textContent.includes('VENTAS')).click(); }")

        page.wait_for_selector('text=🗑️ Eliminar Bloque VENTAS_TEST', timeout=10000)
        assert page.locator('button:has-text("🗑️ Eliminar Bloque VENTAS_TEST")').first.is_visible()
        assert page.locator('text=Exportar Notas a Excel').first.is_visible()

        browser.close()

if __name__ == "__main__":
    test_mass_assignment_placeholder()
