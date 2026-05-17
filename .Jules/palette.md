## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-17 - Loading States and Context Tooltips for Action Buttons
**Learning:** In Streamlit applications, long-running backend operations (like database cross-checks) tied to `st.button`s can cause the app to appear unresponsive to users. Additionally, grouped action buttons can appear misaligned and lack context.
**Action:** Enhance the UX of actionable buttons by wrapping the execution logic in a `st.spinner()` context manager for visual loading feedback. Use `use_container_width=True` on grouped buttons for better layout alignment, and provide contextual tooltips using the native `help` parameter to explain the button's action.
