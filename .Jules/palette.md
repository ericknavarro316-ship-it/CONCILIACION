## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Safe destructive mass actions
**Learning:** During mass updates or destructive actions (such as leaving an input empty to clear multiple records), users may accidentally wipe data if the intention of an empty field isn't explicit.
**Action:** Always combine `placeholder` text with explicit `help` tooltips on inputs and buttons used for mass or destructive actions to ensure the user clearly understands the consequence of their action before clicking apply.
