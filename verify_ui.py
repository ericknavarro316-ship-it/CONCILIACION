from playwright.sync_api import sync_playwright

def verify_bancos_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # The app runs on localhost:8501
            page.goto("http://localhost:8501")

            import time
            time.sleep(2)
            # Try to see if login is needed
            if page.get_by_placeholder("Contraseña").is_visible():
                page.get_by_placeholder("Contraseña").fill("admin123")
                page.get_by_role("button", name="Ingresar").click()

            # Take a generic screenshot to figure out why the login/navigation failed
            page.screenshot(path="/home/jules/verification/bancos_ui.png", full_page=True)
        finally:
            browser.close()

if __name__ == "__main__":
    import os
    os.makedirs("/home/jules/verification", exist_ok=True)
    verify_bancos_ui()
