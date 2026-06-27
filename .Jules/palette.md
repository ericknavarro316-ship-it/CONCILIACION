## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.
## 2024-05-18 - Native disabled states for Streamlit buttons based on data prerequisites
**Learning:** Streamlit action buttons (like for data reconciliation) shouldn't be blindly enabled if the prerequisite data isn't loaded. It leads to user confusion and error messages when the actions fail.
**Action:** Use the `disabled` property combined with `help` text on `st.button`s to cleanly disable the UI element and explain what data needs to be uploaded first before the action can be taken.
