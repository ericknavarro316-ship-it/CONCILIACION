## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-07 - Clarify destructive/bulk empty actions with tooltips
**Learning:** In mass assignment operations, an empty string is often a valid but destructive input (i.e. clearing out values). Users can be hesitant or confused about how to intentionally clear multiple cells if there isn't explicit guidance.
**Action:** Enhance UX by adding `help` tooltips and `placeholder` text on empty input states for bulk-edit actions to explicitly explain that leaving it blank clears the data.
