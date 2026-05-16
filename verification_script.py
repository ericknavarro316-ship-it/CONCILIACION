from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:8501")
    page.wait_for_timeout(5000) # give time for streamlit to load

    # Click the "I00: CRUCE INGRESOS (Ventas)" radio button
    page.evaluate('''() => {
        const labels = Array.from(document.querySelectorAll('label'));
        const target = labels.find(label => label.textContent.includes('🔄 I00: CRUCE INGRESOS (Ventas)'));
        if (target) {
            target.click();
        }
    }''')

    page.wait_for_timeout(2000)

    # Hover the first button "Cruce BBVA" to trigger tooltip
    page.get_by_role("button", name="Cruce BBVA").hover()
    page.wait_for_timeout(1000)

    # Take screenshot at the key moment
    page.screenshot(path="/home/jules/verification/screenshots/verification_bbva_tooltip.png")

    # Hover the second button "Cruce Mercado Pago" to trigger tooltip
    page.get_by_role("button", name="Cruce Mercado Pago").hover()
    page.wait_for_timeout(1000)

    page.screenshot(path="/home/jules/verification/screenshots/verification_mp_tooltip.png")

    # Hover the third button "Propagar a CFDI Ingresos" to trigger tooltip
    page.get_by_role("button", name="Propagar a CFDI Ingresos").hover()
    page.wait_for_timeout(1000)

    page.screenshot(path="/home/jules/verification/screenshots/verification_cfdi_tooltip.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
