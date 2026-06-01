## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-05-19 - Adding Tooltips to Destructive/Bulk Actions in Streamlit
**Learning:** Destructive actions like bulk edits (e.g., mass assignment where an empty input clears data) can lead to unintended data loss if users don't understand the consequences. Streamlit's `st.text_input` and `st.button` support `placeholder` and `help` parameters respectively, which are perfect for clarifying these actions without adding visual clutter.
**Action:** Always add explicit `help` text and `placeholder`s to bulk-edit inputs and destructive action buttons to clearly explain the impact of the action, especially when an empty value results in clearing existing data.
