
## 2024-04-09 - Button Disabled States with Explanations
**Learning:** Utilizing Streamlit's native `disabled` parameter along with the `help` parameter (for tooltips) on `st.button` elements is an excellent, native way to prevent invalid form submissions (e.g., clicking process without uploading a file) without needing post-click warnings or custom CSS.
**Action:** Always prefer disabling buttons with a helpful tooltip explaining *why* they are disabled, rather than letting the user click and showing an error/warning message afterwards.
