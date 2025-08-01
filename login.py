# login.py
import streamlit as st
import bcrypt
from db import get_connection_readonly
from sqlalchemy import text
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
                conn = get_connection_readonly()  # ← SQLAlchemy Connection

                # 🔐 ดึง hashed_password จาก auth_credentials
                result = conn.execute(
                    text("""
                        SELECT hashed_password 
                        FROM kpigoalpoint.auth_credentials 
                        WHERE user_id = :user_id
                    """),
                    {"user_id": User_ID}
                )
                row = result.mappings().fetchone()  # ใช้ mappings() เพื่อให้ access ด้วยชื่อ column ได้

                if row and bcrypt.checkpw(password.encode(), row["hashed_password"].encode()):
                    # ✅ ดึง role จาก table users
                    result = conn.execute(
                        text("""
                            SELECT role_onweb 
                            FROM kpigoalpoint.users 
                            WHERE user_id = :user_id
                        """),
                        {"user_id": User_ID}
                    )
                    role_row = result.mappings().fetchone()

                    if role_row:
                        role = role_row["role_onweb"]
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
                    st.error("❌ User ID หรือ Password ไม่ถูกต้อง")

            except Exception as e:
                st.error(f"❌ Database error: {e}")
    else:
        st.success("✅ Already logged in.")
        time.sleep(0.5)
        st.query_params.update({"page": st.session_state.get("user_role", "user")})
        st.rerun()

if __name__ == "__main__":
    login_page()
