## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Safe destructive bulk actions
**Learning:** Mass assignments or bulk editing operations where an empty field effectively clears/deletes data can easily lead to accidental data loss, as users might intuitively assume empty means "no change" rather than "clear".
**Action:** Always add explicit warnings to the `placeholder` text (e.g., "Dejar en blanco borrará los datos") and `help` tooltips explaining the destructive nature of the action to prevent user errors.
