import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from db import get_connection_app
from sqlalchemy import text

def user_page2():
    action = ["โอน Point", "แลก Point ส่วนตัว", "แลก Point ทีม"]
    st.sidebar.header("🔎 ตัวกรองข้อมูล")
    selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)

    if selected_dept == "โอน Point":
        st.title("🔄 โอนคะแนนให้ผู้อื่น")

        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("❌ ไม่พบ user_id ใน session")
            return

        try:
            conn = get_connection_app()

            # ดึง point ของตัวเอง
            result = conn.execute(text("""
                SELECT point_value FROM kpigoalpoint.personal_points
                WHERE user_ref_id = :uid
            """), {"uid": user_id})
            row = result.fetchone()
            current_point = int(row[0]) if row and row[0] is not None else 0

            # ดึงรายชื่อผู้ใช้อื่น (ไม่รวมตัวเอง)
            user_df = pd.read_sql(text("""
                SELECT user_id, full_name, nickname
                FROM kpigoalpoint.users
                WHERE user_id != :uid
                ORDER BY full_name
            """), conn, params={"uid": user_id})

            user_map = {
                f"{row['full_name']} ({row['nickname']})": row['user_id']
                for _, row in user_df.iterrows()
            }

            recipient_display = st.selectbox("👥 เลือกผู้รับ Point", list(user_map.keys()))
            recipient_user_id = user_map[recipient_display]

            # จำนวน point ที่ต้องการโอน
            point_input = st.number_input("📤 จำนวน Point ที่ต้องการโอน", min_value=1, step=1)

            col_preview1, col_preview2 = st.columns(2)
            with col_preview1:
                ui.metric_card(title="Point ของคุณ", content=current_point, description="คะแนนสะสมรายบุคคล", key="card1")
            with col_preview2:
                ui.metric_card(title="Point ของคุณหลังจากโอน", content=max(0, current_point - point_input), description="หากโอนคะแนน", key="card2")

            if st.button("✅ ยืนยันการโอน"):
                if point_input > current_point:
                    st.warning("⚠️ คุณมี Point ไม่เพียงพอสำหรับการโอนนี้")
                else:
                    try:
                        with conn.begin():
                            conn.execute(text("""
                                UPDATE kpigoalpoint.personal_points
                                SET point_value = point_value - :amount
                                WHERE user_ref_id = :uid
                            """), {"amount": point_input, "uid": user_id})

                            conn.execute(text("""
                                UPDATE kpigoalpoint.personal_points
                                SET point_value = point_value + :amount
                                WHERE user_ref_id = :rid
                            """), {"amount": point_input, "rid": recipient_user_id})

                        st.success(f"✅ โอน {point_input} Point ให้ {recipient_display} เรียบร้อยแล้ว")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ โอน Point ไม่สำเร็จ: {e}")

        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
