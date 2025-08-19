import streamlit as st
from streamlit_option_menu import option_menu

import module_user.page1 as user_page1
import module_user.page2 as user_page2
import module_user.page3 as user_page3

import module_admin.page1 as admin_page1
import module_admin.page2 as admin_page2
import module_admin.page3 as admin_page3
import module_admin.page4 as admin_page4
import module_admin.page5 as admin_page5

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ตรวจสอบ redirect หลัง login
if "redirect_to" in st.session_state:
    st.query_params.update({"page": st.session_state.redirect_to})
    del st.session_state.redirect_to
    st.rerun()

# อ่านค่าหน้าจาก URL
page = st.query_params.get("page", "login")

def load_local_css(file_name):
    with open(file_name, encoding="utf-8") as f:   # บังคับใช้ UTF-8
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main_user():
    st.set_page_config(page_title="Goalpoint Focomm", 
                       layout="wide", 
                       page_icon=""
                       )
    load_local_css("static/custom.css")

    with st.sidebar:
        selected = option_menu("User Menu", ["Your self", 'Manage point', 'Get Point'],
            icons=['house', 'receipt', 'star'], 
            menu_icon="cast",
            default_index=0
            )

    if selected == 'Your self':
        user_page1.user_page1()
    elif selected == 'Manage point':
        user_page2.user_page2()
    elif selected == 'Get Point':
        user_page3.user_page3()

def main_admin():
    
    st.set_page_config(page_title="Goalpoint Focomm", 
                       layout="wide", 
                       page_icon=""
                       )
    load_local_css("static/custom.css")
    
    with st.sidebar:
        
        st.markdown("""<div style='margin-top: 0px;'></div>""", unsafe_allow_html=True)
        st.markdown("""
            <div style='text-align: center; color: gray; font-size: 12px; margin-bottom: 15px;'>
                Made by IceSu <br>Beta 1.0.2
            </div>
        """, unsafe_allow_html=True)
        
        selected = option_menu("Admin Menu", ["View point", 'Edit user','Edit point','View requirement','Manage KPI & Award'],
            icons=['bar-chart', 'file-earmark-text', 'gear', 'check-circle',"flag"],
            menu_icon="tools",
            default_index=0
            )
        
    if selected == 'View point': # View all points
        admin_page1.admin_page1()
    elif selected == 'Edit user': # Edit user
        admin_page2.admin_page2()
    elif selected == 'Edit point': # Edit point
        admin_page3.admin_page3()
    elif selected == 'View requirement': # Checking  
        admin_page4.admin_page4()
    elif selected == 'Manage KPI & Award': # Manage KPI
        admin_page5.admin_page5()

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
    st.set_page_config(page_title="Goalpoint Focomm")
    login_page()
