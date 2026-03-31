from playwright.sync_api import sync_playwright

def verify_bancos_ui():
    with sync_playwright() as p:
        # Increase window size significantly to make sure we can see everything
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        try:
            page.goto("http://localhost:8501")

            import time
            time.sleep(5)

            # The sidebar starts collapsed `initial_sidebar_state="collapsed"`
            # If standard clicks fail, let's force the click via javascript
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const bancosLabel = labels.find(l => l.innerText && l.innerText.includes('BANCOS'));
                if(bancosLabel) bancosLabel.click();
            }''')
            time.sleep(3)

            # Try to click the "Movimientos Operativos" via evaluation to bypass "out of viewport" errors
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const movsLabel = labels.find(l => l.innerText && l.innerText.includes('Movimientos Operativos'));
                if(movsLabel) movsLabel.click();
            }''')
            time.sleep(2)

            page.screenshot(path="/home/jules/verification/bancos_movimientos.png", full_page=True)

            # Try to click the "Estados de Cuenta" via evaluation
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const estLabel = labels.find(l => l.innerText && l.innerText.includes('Estados de Cuenta'));
                if(estLabel) estLabel.click();
            }''')
            time.sleep(2)

            page.screenshot(path="/home/jules/verification/bancos_estados.png", full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    verify_bancos_ui()
