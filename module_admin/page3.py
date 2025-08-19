import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from sqlalchemy import text
from db import get_connection_app

def admin_page3():
    st.title("จัดการ Point")
    st.write('------')

    action = ["เพิ่ม Point ส่วนตัว", "เพิ่ม Point ทีม"]
    st.sidebar.header("การดำเนินการ")
    selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)

    try:
        conn = get_connection_app()

        if selected_dept == "เพิ่ม Point ส่วนตัว":
            st.markdown("### เพิ่ม/ลด Point รายบุคคล")

            user_df = pd.read_sql(
                text("SELECT user_id, full_name, nickname FROM kpigoalpoint.users ORDER BY full_name"),
                conn
            )
            user_map = {
                f"{row['full_name']} ({row['nickname']})": row['user_id']
                for _, row in user_df.iterrows()
            }

            selected_display = st.selectbox("เลือกผู้ใช้", list(user_map.keys()))
            selected_user_id = user_map[selected_display]

            # ดึง point ปัจจุบัน
            try:
                result = conn.execute(
                    text("SELECT point_value FROM kpigoalpoint.personal_points WHERE user_ref_id = :uid"),
                    {"uid": selected_user_id}
                )
                row = result.fetchone()
                current_point = row[0] if row else 0
            except Exception as e:
                current_point = 0
                st.warning(f"⚠️ ดึงข้อมูล point ไม่สำเร็จ: {e}")

            point_input = st.number_input("จำนวน Point", min_value=1, step=1)

            # preview
            col_preview1, col_preview2, col_preview3 = st.columns(3)
            with col_preview1:
                ui.metric_card(title="Point ปัจจุบัน", content=int(current_point), description="คะแนนสะสมรายบุคคล", key="card1")
            with col_preview2:
                ui.metric_card(title="Point หลังจากเพิ่ม", content=int(current_point + point_input), description="หากเพิ่มคะแนน", key="card2")
            with col_preview3:
                ui.metric_card(title="Point หลังจากลด", content=int(max(0, current_point - point_input)), description="หากลดคะแนน", key="card3")

            col1, col2, col3 = st.columns(3)
            
            with col2:
                add_point = ui.button("เพิ่ม Point", key="add_point", variant="default")
                if add_point:
                    try:
                        conn.execute(text("""
                            UPDATE kpigoalpoint.personal_points
                            SET point_value = point_value + :point
                            WHERE user_ref_id = :uid
                        """), {"point": point_input, "uid": selected_user_id})
                        conn.commit()
                        st.success(f"✅ เพิ่ม {point_input} คะแนนให้ {selected_display} สำเร็จแล้ว")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ เพิ่มคะแนนไม่สำเร็จ: {e}")
            with col3:
                reduce_point = ui.button("ลด Point", key="reduce_point", variant="destructive")
                if reduce_point:
                    try:
                        conn.execute(text("""
                            UPDATE kpigoalpoint.personal_points
                            SET point_value = GREATEST(0, point_value - :point)
                            WHERE user_ref_id = :uid
                        """), {"point": point_input, "uid": selected_user_id})
                        conn.commit()
                        st.success(f"✅ ลด {point_input} คะแนนของ {selected_display} สำเร็จแล้ว")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ ลดคะแนนไม่สำเร็จ: {e}")

        elif selected_dept == "เพิ่ม Point ทีม":
            st.markdown("### เพิ่ม/ลด Point รายแผนก")

            dept_df = pd.read_sql(
                text("SELECT id, dept_name, point_dpmt FROM kpigoalpoint.departments ORDER BY dept_name"),
                conn
            )
            dept_map = {
                row['dept_name']: (row['id'], row['point_dpmt'])
                for _, row in dept_df.iterrows()
            }

            selected_dept_name = st.selectbox("เลือกแผนก", list(dept_map.keys()))
            selected_dept_id, current_point = dept_map[selected_dept_name]

            point_input = st.number_input("จำนวน Point", min_value=1, step=1, key="team_point")

            col_preview1, col_preview2, col_preview3 = st.columns(3)
            with col_preview1:
                ui.metric_card(title="Point ปัจจุบัน", content=int(current_point), description="คะแนนสะสมของแผนก", key="team_card1")
            with col_preview2:
                ui.metric_card(title="Point หลังจากเพิ่ม", content=int(current_point + point_input), description="หากเพิ่มคะแนน", key="team_card2")
            with col_preview3:
                ui.metric_card(title="Point หลังจากลด", content=int(max(0, current_point - point_input)), description="หากลดคะแนน", key="team_card3")

            col1, col2, col3 = st.columns(3)


            with col2:
                add_point = ui.button("เพิ่ม Point", key="add_point", variant="default")
                if add_point:
                    try:
                        conn.execute(text("""
                            UPDATE kpigoalpoint.departments
                            SET point_dpmt = point_dpmt + :point
                            WHERE id = :dept_id
                        """), {"point": point_input, "dept_id": selected_dept_id})
                        conn.commit()
                        st.success(f"✅ เพิ่ม {point_input} คะแนนให้ทีม {selected_dept_name} สำเร็จแล้ว")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ เพิ่มคะแนนทีมไม่สำเร็จ: {e}")

            with col3:
                reduce_point = ui.button("ลด Point", key="reduce_point", variant="destructive")
                if reduce_point:
                    try:
                        conn.execute(text("""
                            UPDATE kpigoalpoint.departments
                            SET point_dpmt = GREATEST(0, point_dpmt - :point)
                            WHERE id = :dept_id
                        """), {"point": point_input, "dept_id": selected_dept_id})
                        conn.commit()
                        st.success(f"✅ ลด {point_input} คะแนนของทีม {selected_dept_name} สำเร็จแล้ว")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ ลดคะแนนทีมไม่สำเร็จ: {e}")

    except Exception as e:
        st.error(f"❌ โหลดข้อมูลล้มเหลว: {e}")
