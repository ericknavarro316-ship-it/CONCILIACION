
## 2024-04-17 - Prevent empty file uploads
**Learning:** In Streamlit, `st.file_uploader(accept_multiple_files=True)` returns an empty list `[]` when no files are selected, making it evaluate to falsy.
**Action:** Use `disabled=not uploaded_variable` on related action buttons to gracefully prevent clicks when no files are uploaded, avoiding the need for `st.warning` post-click alerts.
