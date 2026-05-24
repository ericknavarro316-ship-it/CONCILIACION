## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-24 - Guidance for bulk-edit and destructive actions
**Learning:** Bulk-edit or destructive actions (e.g., mass assignment where an empty input clears data) can be risky if users are not fully aware of the consequences.
**Action:** Enhance UX by adding `help` tooltips that explicitly explain the impact of the action, and use `placeholder` text in inputs to guide the user without cluttering the UI.
