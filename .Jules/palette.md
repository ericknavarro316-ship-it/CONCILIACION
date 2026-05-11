## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-18 - Visual feedback for long-running processes
**Learning:** Streamlit buttons that trigger long-running backend operations (like database queries or data reconciliation) can make the app appear frozen if they lack visual feedback. Furthermore, grouped action buttons without explanations can be ambiguous for users.
**Action:** Always wrap the execution logic of long-running operations triggered by buttons in a `with st.spinner('Loading...'):` block. Use the `help` parameter on buttons to provide contextual tooltips, and apply `use_container_width=True` to improve the layout of grouped buttons.
