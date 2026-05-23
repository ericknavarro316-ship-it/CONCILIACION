## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback and alignment for Streamlit backend operations
**Learning:** Triggering long-running backend functions directly from a `st.button` without wrapping them in an asynchronous context or visual feedback freezes the UI and leaves the user guessing if an action registered. Similarly, placing buttons adjacent to each other without layout constraints causes uneven layouts.
**Action:** Always wrap long-running backend functions triggered by `st.button` in a `st.spinner()` block to provide immediate visual feedback. Additionally, apply `use_container_width=True` to grouped action buttons (e.g., within `st.columns`) for a balanced layout.
