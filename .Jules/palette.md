## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback and alignment for long-running action buttons
**Learning:** Action buttons that trigger long-running backend processes (like cross-checks) without visual feedback can lead users to think the application is frozen or unresponsive. Additionally, grouping buttons without using the available width causes layout misalignment on different screen sizes.
**Action:** Always combine `use_container_width=True` with descriptive `help` tooltips on grouped action buttons, and wrap their associated backend execution logic in a `with st.spinner("..."):` block for immediate visual feedback.
