from playwright.sync_api import sync_playwright, expect
import time
import os

def verify_mass_assignment():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        os.system("streamlit run app.py & sleep 10")

        try:
            page.goto("http://localhost:8501")
            expect(page.locator("h1").first).to_be_visible(timeout=10000)

            import sqlite3
            import pandas as pd
            conn = sqlite3.connect('conciliacion_data.db')
            pd.DataFrame({'FECHA': ['2023-01-01'], 'CONCEPTO': ['Prueba'], 'CARGO': [100], 'ABONO': [0], 'CATEGORIA': ['Test']}).to_sql('BANCO_PRUEBA_123_DET', conn, if_exists='replace', index=False)
            conn.close()

            page.reload()
            time.sleep(3)

            page.evaluate('const btn = document.querySelector(\'button[kind="headerNoPadding"]\'); if (btn) btn.click();')
            time.sleep(1)

            page.evaluate('''() => {
                const labels = document.querySelectorAll('label');
                for (let i = 0; i < labels.length; i++) {
                    if (labels[i].innerText.includes("BANCOS")) {
                        labels[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(3)

            page.evaluate('''() => {
                const labels = document.querySelectorAll('label');
                for (let i = 0; i < labels.length; i++) {
                    if (labels[i].innerText.includes("Movimientos Operativos")) {
                        labels[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(3)

            # Click PRUEBA tab
            page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (let i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText.includes("PRUEBA")) {
                        buttons[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(3)

            # We need to click "Editar Manualmente" to show the RESUMEN Y EDICIÓN features
            page.evaluate('''() => {
                const buttons = document.querySelectorAll('button');
                for (let i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText.includes("Editar Manualmente")) {
                        buttons[i].click();
                        break;
                    }
                }
            }''')
            time.sleep(3)

            page.evaluate('''() => {
                const span = Array.from(document.querySelectorAll('span')).find(el => el.textContent === '⚡ Asignación Masiva');
                if (span) span.click();
            }''')
            time.sleep(2)

            page.screenshot(path="verification_mass_assignment.png")
            print("Screenshot taken.")

        finally:
            browser.close()
            os.system("kill $(lsof -t -i :8501) 2>/dev/null || true")

if __name__ == "__main__":
    verify_mass_assignment()
