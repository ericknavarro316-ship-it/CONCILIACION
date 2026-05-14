## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback for long-running processes on buttons
**Learning:** Buttons that trigger complex backend calculations (like data reconciliation) can take seconds to complete, during which the UI appears frozen, leading users to repeatedly click or think the app crashed.
**Action:** Always wrap the execution code of these long-running actions within a `with st.spinner("Processing..."):` context manager. Additionally, to improve hit area and clarity on different screen sizes, set `use_container_width=True` on the button and provide a contextual description using the `help` parameter.
