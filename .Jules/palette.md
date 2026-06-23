## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.
## 2026-06-23 - Improve UX for Data Action Buttons
**Learning:** In Streamlit, users often encounter action buttons (like data crosschecks) that fail when prerequisites aren't met, or the buttons are simply hidden (), which causes confusion.
**Action:** Use native `disabled=not(prerequisite)` on action buttons and leverage the `help` parameter to explain the required prerequisites directly on hover. Also, improve visual feedback by wrapping the button logic in a `st.spinner()` context manager.
## 2026-06-23 - Improve UX for Data Action Buttons
**Learning:** In Streamlit, users often encounter action buttons (like data crosschecks) that fail when prerequisites aren't met, or the buttons are simply hidden (`if data and st.button...`), which causes confusion.
**Action:** Use native `disabled=not(prerequisite)` on action buttons and leverage the `help` parameter to explain the required prerequisites directly on hover. Also, improve visual feedback by wrapping the button logic in a `st.spinner()` context manager.
