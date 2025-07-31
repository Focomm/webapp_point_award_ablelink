import streamlit as st
import streamlit_shadcn_ui as ui
from db import get_connection_readonly

def user_page1():
   
   def get_full():
      full_name_user = "Unknown User"
      try:
         conn = get_connection_readonly()
         cur = conn.cursor()
         cur.execute("SELECT full_name FROM kpigoalpoint.users WHERE user_id = %s", (st.session_state.user_id,))
         row = cur.fetchone()
         if row:
            full_name_user = row[0]
      except Exception as e:
         st.error(f"❌ Failed to load user name: {e}")
      return full_name_user


   def get_personal_point():
      personal_point = 0
      try:
         conn = get_connection_readonly()
         cur = conn.cursor()
         cur.execute("""
               SELECT SUM(point_value)
               FROM kpigoalpoint.personal_points
               WHERE user_ref_id = %s
         """, (st.session_state.user_id,))
         row = cur.fetchone()
         if row and row[0] is not None:
               personal_point = row[0]
      except Exception as e:
         st.error(f"❌ Failed to load personal point: {e}")
      return personal_point
   
   
   def get_team_point():
    point_dpmt = 0
    try:
        conn = get_connection_readonly()
        cur = conn.cursor()

        user_id = st.session_state.get("user_id")

        cur.execute("""
            SELECT d.point_dpmt
            FROM kpigoalpoint.users u
            JOIN kpigoalpoint.departments d ON u.dept_id = d.id
            WHERE u.user_id = %s
        """, (user_id,))

        row = cur.fetchone()
        if row and row[0] is not None:
            point_dpmt = row[0]
        else:
            st.warning("⚠️ ไม่พบคะแนนแผนกของผู้ใช้นี้")

    except Exception as e:
        st.error(f"❌ Failed to load team point: {e}")
    return point_dpmt
   
   
         

   full_name_user = get_full()
   st.title(f"👤 Hello {full_name_user}")


   col1, col2 = st.columns(2)
   with col1:
        ui.metric_card(title="Personal Point", content=get_personal_point(), description="test", key="card1")
   with col2:
        ui.metric_card(title="Team Point", content=get_team_point(), description="test", key="card2")
   
   