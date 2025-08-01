import streamlit as st
import streamlit_shadcn_ui as ui
from db import get_connection_readonly
from sqlalchemy import text

def user_page1():
    user_id = st.session_state.get("user_id", None)
    if not user_id:
        st.error("⚠️ ไม่พบ user_id ใน session")
        return

    def get_full_name(conn):
        try:
            result = conn.execute(text("""
                SELECT full_name FROM kpigoalpoint.users WHERE user_id = :uid
            """), {"uid": user_id})
            row = result.fetchone()
            return row[0] if row else "Unknown User"
        except Exception as e:
            st.error(f"❌ Failed to load user name: {e}")
            return "Unknown User"

    def get_personal_point(conn):
        try:
            result = conn.execute(text("""
                SELECT SUM(point_value)
                FROM kpigoalpoint.personal_points
                WHERE user_ref_id = :uid
            """), {"uid": user_id})
            row = result.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
        except Exception as e:
            st.error(f"❌ Failed to load personal point: {e}")
            return 0

    def get_team_point(conn):
        try:
            result = conn.execute(text("""
                SELECT d.point_dpmt
                FROM kpigoalpoint.users u
                JOIN kpigoalpoint.departments d ON u.dept_id = d.id
                WHERE u.user_id = :uid
            """), {"uid": user_id})
            row = result.fetchone()
            return int(row[0]) if row and row[0] is not None else 0
        except Exception as e:
            st.error(f"❌ Failed to load team point: {e}")
            return 0

    try:
        conn = get_connection_readonly()
        full_name = get_full_name(conn)
        personal_point = get_personal_point(conn)
        team_point = get_team_point(conn)

        st.title(f"👤 Hello {full_name}")

        col1, col2 = st.columns(2)
        with col1:
            ui.metric_card(title="Personal Point", content=personal_point, description="คะแนนสะสมของคุณ", key="card1")
        with col2:
            ui.metric_card(title="Team Point", content=team_point, description="คะแนนรวมของแผนก", key="card2")

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดระหว่างโหลดข้อมูล: {e}")
