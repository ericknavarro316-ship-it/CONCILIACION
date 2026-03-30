import re
import os
from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 2560, "height": 1440})

        page.goto("http://localhost:8501")

        try:
            page.wait_for_selector("input[type='password']", timeout=5000)
            password = os.environ.get("ADMIN_PASSWORD", "admin123")
            page.fill("input[type='password']", password)
            page.press("input[type='password']", "Enter")
        except:
            pass

        page.wait_for_selector("text=Procesamiento de Archivos (ETL)", timeout=15000)

        page.click("p:has-text('Carga de Ventas')")
        page.wait_for_timeout(2000)

        # Take screenshot to see if there is an error
        page.screenshot(path="debug_ventas_ingesta2.png", full_page=True)

        # We need the second input file
        inputs = page.query_selector_all("input[type='file']")
        if len(inputs) > 1:
            inputs[1].set_input_files("dummy_ventas.csv")
            page.wait_for_timeout(2000)

            # click the button to process
            page.click("button:has-text('Procesar Ventas y Resumen')")
            page.wait_for_timeout(5000)
            page.screenshot(path="debug_ventas_ingesta_after_process.png", full_page=True)

        page.wait_for_timeout(3000)

        # Go to VENTAS
        page.evaluate('''() => {
            const labels = Array.from(document.querySelectorAll("label"));
            const ventasLabel = labels.find(l => l.innerText === "VENTAS" || (l.innerText.includes("VENTAS") && !l.innerText.includes("CRUCE")));
            if(ventasLabel) {
                const input = document.getElementById(ventasLabel.getAttribute("for"));
                if(input) input.click();
                else ventasLabel.click();
            }
        }''')

        # Just grab whatever is in the Ventas module to verify our UI fixes
        page.wait_for_timeout(5000)

        page.screenshot(path="verification_ventas_resumen_tab2.png", full_page=True)

        browser.close()

if __name__ == "__main__":
    run()
