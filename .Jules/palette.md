## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-06-22 - Missing disabled states for functional action buttons
**Learning:** Several action buttons in the app (`st.button`) that perform long-running synchronization or data changes failed to disable themselves when the required data (tables, uploads) was missing, which creates a frustrating UX where users click buttons and nothing happens or errors occur.
**Action:** Always wrap data-dependent `st.button` actions with `disabled=not data` and provide a helpful `help="Falta cargar X"` tooltip so users instantly know why an action is blocked without needing to click it.
