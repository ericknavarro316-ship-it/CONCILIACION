## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-07-06 - Explicit warnings for implicit destructive actions
**Learning:** In mass assignment components where leaving an input blank implicitly acts as a destructive "clear all" command, users can easily cause accidental data loss without realizing it.
**Action:** Always enhance the UX of such inputs by adding clear `placeholder` text (e.g., "Leave blank to clear") and a `help` tooltip explicitly warning about the destructive consequence.
