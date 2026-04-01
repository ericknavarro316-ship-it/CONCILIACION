from playwright.sync_api import sync_playwright

def verify_cfdi_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        try:
            page.goto("http://localhost:8501")

            import time
            time.sleep(5)

            # Click on CFDI in sidebar using JS evaluate
            page.evaluate('''() => {
                const labels = Array.from(document.querySelectorAll('label'));
                const cfdiLabel = labels.find(l => l.innerText && l.innerText.includes('CFDI'));
                if(cfdiLabel) cfdiLabel.click();
            }''')
            time.sleep(3)

            # Take screenshot of the new CFDI layout (empty state or populated)
            page.screenshot(path="/home/jules/verification/cfdi_layout.png", full_page=True)

        finally:
            browser.close()

if __name__ == "__main__":
    verify_cfdi_ui()
