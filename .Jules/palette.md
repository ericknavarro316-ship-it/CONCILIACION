## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-24 - Visual feedback and alignment for long-running actions
**Learning:** In Streamlit, when action buttons trigger long-running backend processes without visual indicators, users often think the app is unresponsive and may click multiple times. Also, grouped action buttons look unpolished when they have varying widths based on their text.
**Action:** Always wrap the execution logic of long-running operations triggered by `st.button` in a `st.spinner()` block for immediate visual feedback. Additionally, add the native `help` parameter to explain the action's effect, and apply `use_container_width=True` to evenly align clustered buttons and improve the overall interface density.
