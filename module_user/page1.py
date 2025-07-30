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
      get_personal_point = 0
      try:
         conn = get_connection_readonly()
         cur = conn.cursor()
         cur.execute("SELECT point_value FROM kpigoalpoint.personal_points WHERE user_ref_id = %s", (st.session_state.user_id,))
         row = cur.fetchone()
         if row:
            get_personal_point = row[0]
      except Exception as e:
         st.error(f"❌ Failed to load user name: {e}")
      return get_personal_point
   
   
         

   full_name_user = get_full()
   st.title(f"👤 Hello {full_name_user}")

   col1, col2 = st.columns(2)
   with col1:
        ui.metric_card(title="Personal Point", content=get_personal_point(), description="test", key="card1")
   with col2:
        ui.metric_card(title="Team Point", content='TEST', description="test", key="card2")
   
   