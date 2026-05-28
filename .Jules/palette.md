## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-28 - Visual feedback for synchronous operations in Streamlit
**Learning:** Streamlit handles synchronous backend operations linearly. When a user clicks a button that triggers a heavy backend task (like data cross-checks or ML inference), the UI appears completely frozen until the task finishes, leading to a poor user experience and potential double-clicks.
**Action:** Always wrap heavy operations linked to `st.button` elements within a `st.spinner("Descriptive message...")` context manager to provide immediate, native visual feedback that work is happening. Also utilize `use_container_width=True` on the buttons for consistent layouts and the `help` attribute to explain what the button does.
