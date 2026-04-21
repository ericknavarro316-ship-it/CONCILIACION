## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback for sync execution and layout balance
**Learning:** In Streamlit, synchronous backend tasks (like running a reconciliation engine) tied to buttons will cause the UI to "freeze" without visual cues, confusing the user. Also, using column groupings for actions looks messy if the buttons don't scale.
**Action:** Always wrap long-running logic triggered by `st.button` in a `st.spinner()` block for immediate visual feedback. Additionally, apply `use_container_width=True` to grouped action buttons to guarantee balanced alignment and use `help="..."` to provide context via native tooltips.
