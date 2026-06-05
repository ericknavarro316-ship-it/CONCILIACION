## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Improve grouping of primary actions in Streamlit
**Learning:** In Streamlit, primary actions grouped in columns (like in the "I00: CRUCE INGRESOS" module) can feel disconnected and lack proper feedback, especially if they perform heavy database queries. Also, users might click them when prerequisite data isn't uploaded, leading to hidden backend errors or confusing silent failures.
**Action:** Enhance grouped `st.button` actions by setting `use_container_width=True` for alignment, using the native `disabled` parameter to enforce prerequisites via database table presence checks, providing a contextual `help` tooltip, and wrapping the execution in a `st.spinner()` block for immediate visual feedback.
