## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-18 - Visual Feedback for Long-Running Actions in Streamlit
**Learning:** In Streamlit, when clicking a button triggers a long-running backend process (like database cross-checks), the UI can appear unresponsive, leading users to double-click or feel confused.
**Action:** Always wrap the execution logic of long-running `st.button` actions within a `with st.spinner('Descriptive message...'):` context block to provide immediate visual feedback that the application is working.

## 2024-05-18 - Streamlit Button Alignment and Prerequisite UX
**Learning:** Grouped action buttons in Streamlit can look misaligned if they don't share consistent sizing, and hiding them until prerequisites are met (short-circuiting rendering) leaves users guessing what actions exist.
**Action:** Use `use_container_width=True` on grouped `st.button`s to ensure they fill their columns evenly. Instead of hiding buttons, render them unconditionally using the native `disabled` parameter combined with the `help` parameter to explain the required data state.
