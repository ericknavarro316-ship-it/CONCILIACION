## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-25 - Long-running action buttons UX
**Learning:** Buttons triggering heavy backend computations (like data reconciliation) can leave users wondering if the app froze, especially when multiple such buttons exist side-by-side without clear distinction of scope.
**Action:** Always wrap the execution logic of long-running operations in `st.spinner()` to provide visual loading feedback, apply `use_container_width=True` when grouped in columns for consistent alignment, and use the `help` parameter to add tooltips explaining what each button explicitly does.
