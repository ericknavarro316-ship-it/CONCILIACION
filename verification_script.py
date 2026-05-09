import time
from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})

        print("Navigating to local Streamlit app...")
        page.goto("http://localhost:8501")
        time.sleep(5) # Wait for Streamlit to load

        print("Navigating to Módulo I00...")
        page.locator('text="🔄 I00: CRUCE INGRESOS (Ventas)"').evaluate("el => el.click()")
        time.sleep(2)

        print("Taking screenshot of Módulo I00...")
        page.screenshot(path="verification_i00_crosschecks.png")

        browser.close()

if __name__ == "__main__":
    verify()
