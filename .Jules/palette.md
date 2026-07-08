## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-07-08 - Enhancing long-running tasks in Streamlit with native UI wrappers
**Learning:** Streamlit buttons linked to heavy backend processing (like data cross-checks) can make the app appear frozen if clicked without immediate visual feedback. Furthermore, grouped action buttons look misaligned if they don't share the same width parameters.
**Action:** Always wrap long-running logic triggered by `st.button` in a `with st.spinner("Processing..."):` context manager. Additionally, apply `use_container_width=True` to standard action buttons within column layouts for consistent alignment, and use the `help` attribute to describe the button's purpose to the user.
