## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-06-30 - Added tooltips and disabled states to cross-check buttons
**Learning:** Cross-check buttons in O00, I00, and Egresos modules were lacking contextual information and feedback.
**Action:** Added `disabled` properties depending on data availability (based on `get_all_tables()`), `help` properties to explain why a button is disabled, and `use_container_width=True` for better layout alignment, avoiding the anti-pattern of completely hiding un-clickable actions.
