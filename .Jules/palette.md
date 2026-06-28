## 2026-06-28 - Native Streamlit Action Buttons
**Learning:** Short-circuiting UI elements (e.g. `if has_data: st.button("Do Work")`) creates a confusing experience as users don't know the action exists or what its prerequisites are.
**Action:** Unconditionally render action buttons but use the `disabled` parameter along with a `help` tooltip to instruct the user on the required prerequisite state.
