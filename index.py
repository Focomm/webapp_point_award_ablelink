import streamlit as st
from streamlit_option_menu import option_menu

import module_user.page1 as user_page1
import module_user.page2 as user_page2
import module_user.page3 as user_page3

import module_admin.page1 as admin_page1
import module_admin.page2 as admin_page2
import module_admin.page3 as admin_page3
import module_admin.page4 as admin_page4

st.set_page_config(page_title="Ablelink Dashboard", layout="wide")


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# 🔁 ตรวจสอบ redirect หลัง login
if "redirect_to" in st.session_state:
    st.query_params.update({"page": st.session_state.redirect_to})
    del st.session_state.redirect_to
    st.rerun()

# 🌐 อ่านค่าหน้าจาก URL
page = st.query_params.get("page", "login")

def main_user():
    
    with st.sidebar:
        selected = option_menu("User Menu", ["Your self", 'Manage point', 'Get Point'],
            icons=['house', 'receipt', 'star'], menu_icon="cast", default_index=0)

    if selected == 'Your self':
        user_page1.user_page1()
    elif selected == 'Manage point':
        user_page2.user_page2()
    elif selected == 'Get Point':
        user_page3.user_page3()


def main_admin():
    
    with st.sidebar:
        selected = option_menu("Admin Menu", ["Menu1", 'Menu2','Menu3','Menu4'],
            icons=['bar-chart', 'file-earmark-text'], menu_icon="tools", default_index=0)


    if selected == 'Menu1': # View all points
        admin_page1.admin_page1()
    elif selected == 'Menu2': # Edit user
        admin_page2.admin_page2()
    elif selected == 'Menu3': # Edit point
        admin_page3.admin_page3()
    elif selected == 'Menu4': # Checking req 
        admin_page4.admin_page4()


# 🚪 ตัดสินใจว่าจะแสดงหน้าอะไร
if st.session_state.authenticated and st.session_state.user_role:
    if page == "admin":
        main_admin()
    elif page == "user":
        main_user()
    else:
        st.error("⛔️ ไม่รู้ว่าจะไปหน้าไหน (page=?)")
else:
    from login import login_page
    login_page()
