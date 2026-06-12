## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-24 - Tooltips and placeholders for bulk actions
**Learning:** Bulk actions or destructive UI operations (like assigning a blank value to clear out multiple rows) can be intimidating or confusing without clear guidance.
**Action:** Always add `placeholder` text and descriptive `help` parameters to inputs and buttons associated with bulk-edit or destructive actions to guide the user without cluttering the UI.
