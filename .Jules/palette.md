## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-18 - Visual feedback and alignment for long-running actions
**Learning:** Grouped action buttons that trigger long-running backend processes (like cross-checks) without immediate feedback can make the interface feel unresponsive, and poorly aligned buttons in columns look messy.
**Action:** Always wrap the execution logic in `st.spinner()` for visual feedback, provide contextual tooltips using the native `help` parameter, and improve layout alignment by applying `use_container_width=True` on grouped action buttons.
