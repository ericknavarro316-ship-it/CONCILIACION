## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-06-18 - Clear state visibility for Streamlit actions
**Learning:** Hiding execution buttons entirely until data is present leaves users confused about how the application works. Additionally, asynchronous operations without visual loading indicators give the false impression that nothing is happening.
**Action:** Render action buttons unconditionally with `disabled=True` combined with contextual `help` text when prerequisites are unmet. Wrap execution logic in `with st.spinner("..."):` blocks to provide immediate visual feedback during cross-check operations.
