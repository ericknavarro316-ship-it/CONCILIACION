## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback for long-running operations in Streamlit
**Learning:** Actions that trigger backend processing (like cross-checks) without visual feedback lead to poor UX as users don't know if the system is working or frozen.
**Action:** Wrap long-running operations triggered by buttons in a `st.spinner()` context manager to provide immediate visual feedback.
