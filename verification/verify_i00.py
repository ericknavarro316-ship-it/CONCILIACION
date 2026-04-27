from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_tooltips(page: Page):
    # Set a large viewport
    page.set_viewport_size({"width": 1920, "height": 1080})

    # 1. Navigate to the app
    page.goto("http://localhost:8501")

    # 2. Wait for Streamlit to load completely
    page.wait_for_selector(".stApp")
    time.sleep(3) # Give it a bit extra time to render sidebar

    # 3. Click the "I00: CRUCE INGRESOS (Ventas)" in the sidebar
    # We use javascript evaluation because Streamlit radio buttons can be tricky
    page.locator('label:has-text("I00: CRUCE INGRESOS (Ventas)")').evaluate("el => el.click()")

    # Wait for the main content to update
    page.wait_for_selector('h1:has-text("Módulo I00: Cruce de Ventas vs Bancos")')
    time.sleep(2)

    # 4. Take a screenshot showing the buttons
    page.screenshot(path="/app/verification/i00_buttons_overview.png")

    # 5. Hover over the first button to show the tooltip
    btn_bbva = page.get_by_role("button", name="Cruce BBVA")
    btn_bbva.hover()
    time.sleep(1) # wait for tooltip to appear
    page.screenshot(path="/app/verification/tooltip_bbva.png")

    # 6. Click the button to show the spinner state
    btn_bbva.click()
    # take screenshot immediately to catch the spinner
    page.screenshot(path="/app/verification/spinner_bbva.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_tooltips(page)
        finally:
            browser.close()
