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
    conn.close()

def test_mass_assignment_placeholder():
    seed_db()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8501")
        page.wait_for_selector('text=Módulos Avanzados', timeout=10000)

        # Test Banco -> Asignación Masiva Placeholder
        page.evaluate("() => { Array.from(document.querySelectorAll('label')).find(el => el.textContent.includes('BANCOS')).click(); }")

        # Let's find any element containing TEST
        page.wait_for_selector('*:has-text("TEST")', timeout=10000)
        # Often Streamlit tabs are button elements under a specific div
        tabs = page.locator('button[data-baseweb="tab"]')
        count = tabs.count()
        for i in range(count):
            if "TEST" in tabs.nth(i).text_content():
                tabs.nth(i).click()
                break

        page.wait_for_selector('text=✏️ Editar Manualmente', timeout=10000)
        page.locator('button:has-text("✏️ Editar Manualmente")').first.click()

        page.wait_for_selector('text=⚡ Asignación Masiva', timeout=10000)
        page.locator('text=⚡ Asignación Masiva').first.click()

        input_locator = page.locator('input[placeholder="Dejar en blanco borrará los datos"]')
        assert input_locator.is_visible()

        browser.close()

if __name__ == "__main__":
    test_mass_assignment_placeholder()
