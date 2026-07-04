## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2024-05-18 - Clear instructions for destructive bulk actions in Streamlit
**Learning:** Destructive actions or bulk updates in forms (like mass assignment where empty input equals clearing data) can be terrifying for users if not explicitly explained.
**Action:** Enhance UX by adding `help` tooltips that explicitly state the impact of the action, and use `placeholder` text in inputs to guide the user without cluttering the UI. Combine this with `use_container_width=True` on the action button to make it a prominent touch target.
