import streamlit as st
from streamlit_option_menu import option_menu

import module.page1 as page1
import module.page2 as page2
import module.page3 as page3

import time

st.set_page_config(page_title="Ablelink Dashboard", 
                   layout="wide")

# ตรวจสอบว่ามีค่า authenticated ใน session_state หรือไม่
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ตรวจสอบ Query Parameters เพื่อสลับหน้า
page = st.query_params.get("page", "login")

def login():
    """ ฟังก์ชันสำหรับแสดงฟอร์มล็อกอิน """
    st.title("Login Page")

    actual_email = "admin"
    actual_password = "admin1234"

    # สร้าง container สำหรับ login form
    placeholder = st.empty()

    with placeholder.form("login"):
        st.markdown("#### Enter your credentials")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if email == actual_email and password == actual_password:
            st.session_state.authenticated = True
            placeholder.empty()
            st.success("Login successful, redirecting...")
            time.sleep(1)

            # ตั้งค่าหน้าไปที่ index
            st.query_params["page"] = "index"
            st.rerun()
        else:
            st.error("Login failed")


def main():
    with st.sidebar:
    
        selected = option_menu("Main Menu", ["Menu1", 'Menu2','Menu3'], 
            icons=['house', 'receipt','box2'], menu_icon="cast", default_index=0)
        
        for i in range(10):
            st.write('')
        

        st.image("https://ablelink.co.th/wp-content/uploads/2024/02/logo350-100.png", use_container_width=True)

        
    


    if selected == 'Menu1':
        page1.menu_1()

    elif selected == 'Menu2':
        page2.menu_2()

    elif selected == 'Menu3':
        page3.menu_3()


if page == "index" and st.session_state.authenticated:
    main()
else:
    login()