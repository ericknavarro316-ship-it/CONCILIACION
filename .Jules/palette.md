## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-12 - Adding loading spinners and tooltips to cross-check buttons
**Learning:** Streamlit buttons that trigger long-running backend cross-check processes provide no visual feedback to the user while executing, which can lead to confusion or multiple clicks. Additionally, without `use_container_width=True`, buttons in columns might look unbalanced, and without tooltips, their exact function isn't always clear to new users.
**Action:** Wrapped long-running functions triggered by buttons in `with st.spinner("...")` contexts. Added `help` tooltips and `use_container_width=True` to improve layout and context.
