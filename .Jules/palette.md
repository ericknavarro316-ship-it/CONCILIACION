## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-01 - [Improve mass assignment UX]
**Learning:** Streamlit forms and buttons for destructive or mass assignment actions often lack explicit guidance, causing user hesitation or accidental data loss when empty inputs clear data.
**Action:** Always use native widget parameters like `placeholder` on text inputs to explain the impact of empty values and use `help` tooltips on submit buttons to warn about bulk overwrite actions.
