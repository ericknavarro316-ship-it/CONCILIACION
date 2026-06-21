## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback and alignment for long-running grouped actions in Streamlit
**Learning:** Actions that trigger heavy backend processing (like data reconciliation) without visual feedback cause users to think the app froze. Furthermore, grouping buttons side-by-side using `st.columns()` without `use_container_width=True` creates poor layout alignment.
**Action:** Always wrap long-running operations triggered by `st.button` in a `st.spinner()` context manager. For grouped action buttons in columns, consistently apply `use_container_width=True` to improve spatial alignment.
