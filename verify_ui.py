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

            # Click on Movimientos Operativos
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const movsLabel = labels.find(l => l.innerText && l.innerText.includes('Movimientos Operativos'));
                if(movsLabel) movsLabel.click();
            }''')
            time.sleep(2)

            # We want to see the new elements (export button, delete button, global resume)
            # Take screenshot of Global Resume tab
            page.screenshot(path="/home/jules/verification/bancos_global_resume.png", full_page=True)

            # Now click on one of the banks tabs (should be the second tab)
            page.evaluate('''() => {
                const tabs = Array.from(document.querySelectorAll('button[role="tab"]'));
                if(tabs.length > 1) tabs[1].click();
            }''')
            time.sleep(2)

            # Take screenshot of bank panel to see export/delete buttons and data quality
            page.screenshot(path="/home/jules/verification/bancos_bank_panel.png", full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    verify_bancos_ui()
