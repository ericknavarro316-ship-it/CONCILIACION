## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback and alignment for long-running grouped buttons
**Learning:** In Streamlit, action buttons for long backend operations (like cross-checks) without visual feedback (like spinners) and proper layout constraints can feel unresponsive and look misaligned, particularly when grouped.
**Action:** Always wrap long-running operations triggered by `st.button` in a `st.spinner()` context, provide explicit `help` tooltips, and use `use_container_width=True` on grouped buttons to ensure they span evenly and provide clear context and status to the user.
