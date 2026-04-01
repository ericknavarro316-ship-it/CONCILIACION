from playwright.sync_api import sync_playwright

def verify_bancos_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        try:
            page.goto("http://localhost:8501")

            import time
            time.sleep(5)

            # The sidebar starts collapsed `initial_sidebar_state="collapsed"`
            # Force click to BANCOS via JS
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const bancosLabel = labels.find(l => l.innerText && l.innerText.includes('BANCOS'));
                if(bancosLabel) bancosLabel.click();
            }''')
            time.sleep(3)

            # Click on Movimientos Operativos
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const movsLabel = labels.find(l => l.innerText && l.innerText.includes('Movimientos Operativos'));
                if(movsLabel) movsLabel.click();
            }''')
            time.sleep(2)

            # Click on a bank tab
            page.evaluate('''() => {
                const tabs = Array.from(document.querySelectorAll('button[role="tab"]'));
                if(tabs.length > 1) tabs[1].click();
            }''')
            time.sleep(2)

            # Click "Editar Manualmente"
            page.evaluate('''() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const editBtn = buttons.find(b => b.innerText && b.innerText.includes('Editar Manualmente'));
                if(editBtn) editBtn.click();
            }''')
            time.sleep(2)

            # Try to expand "Asignacion Masiva"
            page.evaluate('''() => {
                const summaries = Array.from(document.querySelectorAll('summary'));
                const masivaExp = summaries.find(s => s.innerText && s.innerText.includes('Asignación Masiva'));
                if(masivaExp) masivaExp.click();
            }''')
            time.sleep(2)

            # Take screenshot of bank panel to see editor and masiva features
            page.screenshot(path="/home/jules/verification/bancos_masiva.png", full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    verify_bancos_ui()
