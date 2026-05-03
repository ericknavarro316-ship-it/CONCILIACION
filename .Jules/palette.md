## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.
## 2026-05-03 - [Mass Assignment Placeholder]
**Learning:** Adding a placeholder and a help tooltip to a text input field used for mass deletion/modification gives immediate context to the user about what to input, and clarifies what happens when the field is left blank. This prevents accidental data loss and makes bulk actions safer and more intuitive without needing extra UI components.
**Action:** Always use native widget parameters like `placeholder` and `help` to clarify the behavior of potentially destructive or mass-assignment input fields.
