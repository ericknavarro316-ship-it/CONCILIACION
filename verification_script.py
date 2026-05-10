from playwright.sync_api import sync_playwright
import time

def run_cuj(page):
    page.goto("http://localhost:8501")
    page.wait_for_timeout(3000)

    # Open sidebar if collapsed
    print("Opening sidebar")
    try:
        # Check if collapsed sidebar toggle exists and click it if so
        page.locator('button[data-testid="collapsedControl"]').click(timeout=2000)
        page.wait_for_timeout(1000)
    except:
        pass

    # Use JS evaluation to click navigation items safely (prevents 'outside of viewport' errors)
    print("Clicking Nav I00")
    page.locator('label', has_text="🔄 I00: CRUCE INGRESOS (Ventas)").evaluate("el => el.click()")
    page.wait_for_timeout(3000)

    page.screenshot(path="/home/jules/verification/screenshots/verification_i00.png", full_page=True)
    page.wait_for_timeout(1000)

    print("Clicking Nav O00")
    page.locator('label', has_text="⚙️ O00: PRE-CLÁSICOS FISCALES").evaluate("el => el.click()")
    page.wait_for_timeout(3000)

    page.screenshot(path="/home/jules/verification/screenshots/verification_o00.png", full_page=True)
    page.wait_for_timeout(1000)

    print("Clicking Nav Egresos")
    page.locator('label', has_text="💸 CRUCE EGRESOS").evaluate("el => el.click()")
    page.wait_for_timeout(3000)

    page.screenshot(path="/home/jules/verification/screenshots/verification_egresos.png", full_page=True)
    page.wait_for_timeout(1000)


if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
