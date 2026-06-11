## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.
## 2026-05-18 - Opening Streamlit sidebar in Playwright tests
**Learning:** Streamlit's default collapsed sidebar hamburger menu can be difficult to target using generic locators or roles. Standard attempts to open it via `button[kind="header"]` or text might fail.
**Action:** When writing Playwright UI tests for Streamlit where the sidebar needs to be opened, reliably target the hamburger menu using the internal test-id: `page.locator('button[data-testid="baseButton-headerNoPadding"]').click()`.

## 2026-05-18 - Clicking Streamlit radio buttons in Playwright tests
**Learning:** Streamlit's radio buttons (`st.radio`) are rendered using hidden `<input type="radio">` elements wrapped in custom `<label>` and `<div>` containers. Calling `.click()` on the text node directly often fails with "Element is outside of the viewport" because Playwright cannot scroll the underlying hidden input into view properly.
**Action:** Use `page.evaluate()` to inject a JavaScript snippet that finds the `<label>` containing the target text and triggers a native `.click()` event on it. For example: `page.evaluate("() => { const labels = Array.from(document.querySelectorAll('label')); const target = labels.find(label => label.textContent.includes('Target Text')); if (target) target.click(); }")`.
