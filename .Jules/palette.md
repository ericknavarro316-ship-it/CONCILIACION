## 2026-04-18 - Native disabled states for Streamlit forms
**Learning:** Streamlit forms and buttons often use a pattern of short-circuiting rendering (e.g., `if data and st.button(...)`) which hides the action entirely until valid data is provided. This is a UX anti-pattern because users don't know what actions are available or why they can't proceed.
**Action:** Always use the native `disabled` property on interactive elements (e.g., `st.button('Action', disabled=not data)`) combined with the `help` parameter to provide contextual tooltips explaining the required prerequisites.

## 2026-04-19 - Loading feedback and tooltips for critical action buttons
**Learning:** Users lack visibility into system processes during long-running tasks like cross-checks or data reconciliation if there's no visual feedback. Additionally, icon-heavy or concise button labels might not provide enough context on what the action does.
**Action:** Wrap long-running operations inside a `st.spinner("...")` context manager to indicate background activity. Further, use the native `help` parameter on `st.button` to provide an accessible tooltip that explains the outcome of the action. Ensure layout consistency using `use_container_width=True` on grouped buttons.
