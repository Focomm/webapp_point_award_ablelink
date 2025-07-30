import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from db import get_connection_app

def user_page2():
   action = ["โอน Point", "แลก Point ส่วนตัว", "แลก Point ทีม"]
   st.sidebar.header("🔎 ตัวกรองข้อมูล")
   selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)
   
   if selected_dept == "โอน Point":
      st.title("🔄 โอนคะแนนให้ผู้อื่น")

      user_id = st.session_state.user_id

      try:
         conn = get_connection_app()
         cur = conn.cursor()

         # ดึง point ของตัวเอง
         cur.execute("""
               SELECT point_value FROM kpigoalpoint.personal_points
               WHERE user_ref_id = %s
         """, (user_id,))
         row = cur.fetchone()
         current_point = row[0] if row else 0

         # ดึงรายชื่อผู้ใช้อื่น (ไม่รวมตัวเอง)
         user_df = pd.read_sql("""
               SELECT user_id, full_name, nickname
               FROM kpigoalpoint.users
               WHERE user_id != %s
               ORDER BY full_name
         """, conn, params=(user_id,))

         user_map = {
               f"{row['full_name']} ({row['nickname']})": row['user_id']
               for _, row in user_df.iterrows()
         }

         # dropdown เลือกคนที่จะโอนให้
         recipient_display = st.selectbox("👥 เลือกผู้รับ Point", list(user_map.keys()))
         recipient_user_id = user_map[recipient_display]

         # กรอกจำนวน point ที่ต้องการโอน
         point_input = st.number_input("📤 จำนวน Point ที่ต้องการโอน", min_value=1, step=1)
         col_preview1, col_preview2 = st.columns(2)
            
         with col_preview1:
               ui.metric_card(title="Point ของคุณ", content=int(current_point), description="คะแนนสะสมรายบุคคล", key="card1")
         with col_preview2:
               ui.metric_card(title="Point ของคุณหลังจากโอน", content=int(max(0, current_point - point_input)), description="หากโอนคะแนน", key="card2")

         if st.button("✅ ยืนยันการโอน"):
               if point_input > current_point:
                  st.warning("⚠️ คุณมี Point ไม่เพียงพอสำหรับการโอนนี้")
               else:
                  try:
                     # หัก point ตัวเอง
                     cur.execute("""
                           UPDATE kpigoalpoint.personal_points
                           SET point_value = point_value - %s
                           WHERE user_ref_id = %s
                     """, (point_input, user_id))

                     # เพิ่ม point ให้ผู้รับ
                     cur.execute("""
                           UPDATE kpigoalpoint.personal_points
                           SET point_value = point_value + %s
                           WHERE user_ref_id = %s
                     """, (point_input, recipient_user_id))

                     conn.commit()
                     st.success(f"✅ โอน {point_input} Point ให้ {recipient_display} เรียบร้อยแล้ว")
                     st.rerun()

                  except Exception as e:
                     conn.rollback()
                     st.error(f"❌ โอน Point ไม่สำเร็จ: {e}")

      except Exception as e:
         st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")

