import streamlit as st
import streamlit_shadcn_ui as ui
from sqlalchemy import text
from db import get_connection_app


def admin_page5():
    action = ["Add KPI Personal", "Add KPI TEAM","Delete KPI Personal","Delete KPI TEAM"]
    st.sidebar.header("🔎 ตัวกรองข้อมูล")
    selected_KPI = st.sidebar.selectbox("เลือกการจัดการ", action)
    
    
    if selected_KPI == "Add KPI Personal":
        st.title("📊 เพิ่ม KPI ส่วนบุคคล test")

        try:
            conn = get_connection_app()

            # ดึงรายชื่อผู้ใช้จากตาราง users
            users_query = text("SELECT user_id, full_name FROM kpigoalpoint.users ORDER BY full_name")
            result = conn.execute(users_query)
            users = result.fetchall()

            if not users:
                st.warning("⚠️ ยังไม่มีผู้ใช้งานในระบบ กรุณาเพิ่มผู้ใช้ก่อนสร้าง KPI")
                conn.close()
                return

            # แสดง dropdown ให้เลือก user
            user_dict = {f"{row.full_name} ({row.user_id})": row.user_id for row in users}
            selected_user_display = st.selectbox("👤 เลือกผู้ใช้", list(user_dict.keys()))
            selected_user_id = user_dict[selected_user_display]

            # กรอกข้อมูล KPI
            kpi_name = st.text_input("🎯 ชื่อ KPI")
            kpi_goal = st.text_area("📌 เป้าหมายของ KPI")
            point_value = st.number_input("🪙 คะแนน", min_value=0, step=1)

            if st.button("➕ เพิ่ม KPI"):
                if not kpi_name.strip() or not kpi_goal.strip():
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
                else:
                    try:
                        insert_query = text("""
                            INSERT INTO kpigoalpoint.kpi_personal (
                                user_ref_id, kpi_name, kpi_goal, point_value
                            ) VALUES (
                                :user_ref_id, :kpi_name, :kpi_goal, :point_value
                            )
                        """)
                        conn.execute(insert_query, {
                            "user_ref_id": selected_user_id,
                            "kpi_name": kpi_name.strip(),
                            "kpi_goal": kpi_goal.strip(),
                            "point_value": point_value
                        })

                        conn.commit()  # ✅ commit ให้ชัดเจน
                        st.success(f"✅ เพิ่ม KPI สำเร็จให้กับผู้ใช้: {selected_user_id}")

                    except Exception as e:
                        conn.rollback()  # ✅ rollback หากมี error
                        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                    finally:
                        conn.close()

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")


    elif selected_KPI == "Add KPI TEAM":
        st.title("📊 KPI ทีม")

        try:
            conn = get_connection_app()

            # ดึงรายชื่อแผนก
            dept_query = text("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name")
            result = conn.execute(dept_query)
            departments = result.fetchall()

            if not departments:
                st.warning("⚠️ ยังไม่มีแผนกในระบบ กรุณาเพิ่มแผนกก่อนสร้าง KPI")
                return

            # แสดง dropdown ให้เลือกแผนก
            dept_dict = {f"{row.dept_name}": row.id for row in departments}
            selected_dept_display = st.selectbox("🏢 เลือกแผนก", list(dept_dict.keys()))
            selected_dept_id = dept_dict[selected_dept_display]

            # กรอกข้อมูล KPI
            kpi_name = st.text_input("🎯 ชื่อ KPI ทีม")
            kpi_goal = st.text_area("📌 เป้าหมายของ KPI ทีม")
            point_value = st.number_input("🪙 คะแนน", min_value=0, step=1)

            if st.button("➕ เพิ่ม KPI ทีม"):
                if not kpi_name.strip() or not kpi_goal.strip():
                    st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
                    return

                try:
                    insert_query = text("""
                        INSERT INTO kpigoalpoint.kpi_team (
                            dept_ref_id, kpi_name, kpi_goal, point_value
                        ) VALUES (
                            :dept_ref_id, :kpi_name, :kpi_goal, :point_value
                        )
                    """)
                    conn.execute(insert_query, {
                        "dept_ref_id": selected_dept_id,
                        "kpi_name": kpi_name.strip(),
                        "kpi_goal": kpi_goal.strip(),
                        "point_value": point_value
                    })

                    conn.commit()
                    st.success(f"✅ เพิ่ม KPI ทีมสำเร็จให้กับแผนก: {selected_dept_display}")

                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")
                finally:
                    conn.close()

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
    
    elif selected_KPI == "Delete KPI Personal":
        st.title("🗑️ ลบ KPI ส่วนบุคคล")
        try:
            conn = get_connection_app()

            result = conn.execute(text("""
                SELECT p.id, u.full_name, p.kpi_name
                FROM kpigoalpoint.kpi_personal p
                JOIN kpigoalpoint.users u ON p.user_ref_id = u.user_id
                ORDER BY u.full_name, p.kpi_name
            """))
            rows = result.fetchall()

            if not rows:
                st.info("📭 ยังไม่มี KPI ส่วนบุคคลให้ลบ")
                return

            kpi_dict = {f"{row.full_name} → {row.kpi_name} (ID: {row.id})": row.id for row in rows}
            selected_label = st.selectbox("เลือก KPI ที่ต้องการลบ", list(kpi_dict.keys()))
            selected_id = kpi_dict[selected_label]

            confirm = st.checkbox(f"คุณแน่ใจหรือไม่ว่าต้องการลบ KPI นี้?", key="confirm_kpi_personal")

            if st.button("✅ ยืนยันการลบ KPI"):
                if confirm:
                    try:
                        conn.execute(text("DELETE FROM kpigoalpoint.kpi_personal WHERE id = :id"), {"id": selected_id})
                        conn.commit()
                        st.success("✅ ลบ KPI ส่วนบุคคลเรียบร้อยแล้ว")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ ลบไม่สำเร็จ: {e}")
                else:
                    st.warning("⚠️ กรุณายืนยันก่อนลบ KPI นี้")

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
    
    elif selected_KPI == "Delete KPI TEAM":
        st.title("🗑️ ลบ KPI ทีม")
        try:
            conn = get_connection_app()

            result = conn.execute(text("""
                SELECT t.id, d.dept_name, t.kpi_name
                FROM kpigoalpoint.kpi_team t
                JOIN kpigoalpoint.departments d ON t.dept_ref_id = d.id
                ORDER BY d.dept_name, t.kpi_name
            """))
            rows = result.fetchall()

            if not rows:
                st.info("📭 ยังไม่มี KPI ทีมให้ลบ")
                return

            kpi_dict = {f"{row.dept_name} → {row.kpi_name} (ID: {row.id})": row.id for row in rows}
            selected_label = st.selectbox("เลือก KPI ทีมที่จะลบ", list(kpi_dict.keys()))
            selected_id = kpi_dict[selected_label]

            confirm = st.checkbox(f"ยืนยันการลบ KPI ทีมนี้?", key="confirm_kpi_team")

            if st.button("✅ ยืนยันการลบ KPI"):
                if confirm:
                    try:
                        conn.execute(text("DELETE FROM kpigoalpoint.kpi_team WHERE id = :id"), {"id": selected_id})
                        conn.commit()
                        st.success("✅ ลบ KPI ทีมเรียบร้อยแล้ว")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ ลบไม่สำเร็จ: {e}")
                else:
                    st.warning("⚠️ กรุณายืนยันก่อนลบ KPI ทีมนี้")

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")

