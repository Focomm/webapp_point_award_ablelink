# login.py
import streamlit as st
import bcrypt
from db import get_connection
import time

def login_page():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔐 Login Page")
        with st.form("login_form"):
            User_ID = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

        if submit:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT hashed_password FROM kpigoalpoint.auth_credentials WHERE user_id = %s", (User_ID,))
                row = cur.fetchone()

                if row and bcrypt.checkpw(password.encode(), row[0].encode()):
                    cur.execute("SELECT role_onweb FROM kpigoalpoint.users WHERE user_id = %s", (User_ID,))
                    role_row = cur.fetchone()
                    if role_row:
                        role = role_row[0]
                        st.session_state.authenticated = True
                        st.session_state.user_id = User_ID
                        st.session_state.user_role = role
                        st.success("✅ Login success, redirecting...")
                        time.sleep(1)
                        st.query_params.update({"page": role})
                        st.rerun()
                    else:
                        st.error("❌ ไม่พบข้อมูลใน table users")
                else:
                    st.error("❌ Email หรือ password ไม่ถูกต้อง")
            except Exception as e:
                st.error(f"❌ Database error: {e}")
    else:
        st.success("✅ Already logged in.")
        time.sleep(0.5)
        st.query_params.update({"page": st.session_state.get("user_role", "user")})
        st.rerun()
        
if __name__ == "__main__":
    login_page()
