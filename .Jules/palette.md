## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.
## 2026-05-02 - Improve UX for Action Buttons
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering or lack visual feedback during long-running background tasks.
**Action:** Always use the native `disabled` property or provide context using the `help` parameter. Always wrap long-running operations triggered by buttons with a `with st.spinner('...'):` context block to provide immediate visual feedback. Align action buttons using `use_container_width=True` for visual consistency.
