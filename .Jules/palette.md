## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-04 - Adding spinners to synchronous backend calls
**Learning:** Users lack feedback when triggering long-running python operations linked to Streamlit buttons, causing the app to feel unresponsive.
**Action:** Wrap synchronous backend operations behind a `with st.spinner()` context block to provide continuous visual feedback during execution.
