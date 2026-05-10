## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-18 - Better visual and context feedback for long-running operations
**Learning:** Action buttons that trigger long backend processes (cross-checking, analysis) leave users unsure if the app is still working. Default buttons can look misaligned when grouped.
**Action:** Enhance button UX by wrapping execution logic in `st.spinner("...")` for clear visual feedback. Additionally, apply `use_container_width=True` on buttons for a cleaner layout and include `help="description"` to explain the button's action before clicking.
