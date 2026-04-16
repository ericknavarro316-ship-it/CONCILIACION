## 2024-04-16 - UX Principles for Streamlit ERP
**Learning:** Native `st.button`s connected to `st.file_uploader` conditionally throw warnings instead of simply using disabled states, causing unnecessary interaction friction.
**Action:** Use `disabled=not uploaded_variable` on the submit button so that users get visual feedback the form cannot be submitted rather than encountering an explicit warning post-click. Streamlit's `help` parameter can also serve as a tooltip to explain the disabled state seamlessly.
