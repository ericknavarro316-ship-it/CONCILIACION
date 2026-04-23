## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-18 - Asignación Masiva Tooltips
**Learning:** Adding helpful tooltips to bulk-edit forms clarifies the impact of the action (especially when empty inputs clear data). Providing placeholder text in `st.text_input` and `help` on buttons makes the UX more robust without cluttering the UI.
**Action:** Always include tooltips for bulk or destructive actions to ensure users understand the scope of their changes.
