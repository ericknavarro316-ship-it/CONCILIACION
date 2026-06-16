## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-06-16 - Safe Bulk-Edit UX in Streamlit
**Learning:** Bulk-edit features or destructive actions (like mass assignment where leaving an input empty clears data) can lead to accidental data loss. Users need explicit guidance on the consequences of their actions before executing them.
**Action:** Always add `help` tooltips that explicitly explain the impact of the action (e.g., "Leaving this empty will clear the data"), use `placeholder` text in inputs for immediate context, and apply `use_container_width=True` on buttons for better visual alignment without custom CSS.
