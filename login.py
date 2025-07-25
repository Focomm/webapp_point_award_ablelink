import streamlit as st
import time

# ตรวจสอบว่า authenticated มีอยู่ใน session_state หรือไม่
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ตั้งค่าข้อมูลล็อกอินจริง
actual_email = "admin"
actual_password = "admin1234"

# ถ้าผู้ใช้ล็อกอินแล้ว ให้เปลี่ยนไปที่ index.py ทันที
if st.session_state.authenticated:
    st.query_params["page"] = "index"  # ✅ ใช้ query_params แทน experimental_set_query_params
    st.rerun()  

# สร้าง container สำหรับ login form
placeholder = st.empty()

# แสดงฟอร์มล็อกอิน
with placeholder.form("login"):
    st.markdown("#### Enter your credentials")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("Login")

# ตรวจสอบการล็อกอิน
if submit:
    if email == actual_email and password == actual_password:
        st.session_state.authenticated = True
        placeholder.empty()
        st.success("Login successful, redirecting...")
        time.sleep(1)

        # ตั้งค่าหน้าไปที่ index.py
        st.query_params["page"] = "index"  # ✅ ใช้ query_params
        st.rerun()
    else:
        st.error("Login failed")
