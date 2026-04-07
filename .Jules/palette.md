## 2024-05-18 - Improved file upload button states
**Learning:** Using post-click alerts (`st.warning`) for missing file uploads creates friction and feels unresponsive.
**Action:** Utilized native Streamlit properties (`disabled=True` conditionally and `help="..."`) on `st.button` components tied to file uploaders. This provides immediate visual feedback and prevents unnecessary clicks, improving the UX and accessibility while reducing boilerplate warning code.
