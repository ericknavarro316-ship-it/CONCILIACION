## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Visual feedback and alignment for major actions in Streamlit
**Learning:** High-impact execution buttons (like cross-checks) can be confusing if they execute synchronously without visual feedback, and uneven button widths disrupt layout hierarchy.
**Action:** For primary actions, always combine `disabled` states with `help` tooltips, use `use_container_width=True` to create a cohesive horizontal layout for button groups, and wrap execution logic in a `st.spinner("...")` block to clearly signal asynchronous processing states to the user.
