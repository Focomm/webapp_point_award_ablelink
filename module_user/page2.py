import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import time

from db import get_connection_app
from sqlalchemy import text

def user_page2():
    action = ["โอน Point", "แลก Point ส่วนตัว", "แลก Point ทีม","ประวัติการใช้งาน point"]
    st.sidebar.header("🔎 ตัวกรองข้อมูล")
    selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)

    if selected_dept == "โอน Point":
        st.title("🔄 โอนคะแนนให้ผู้อื่น")

        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("❌ ไม่พบ user_id ใน session")
            st.stop()

        try:
            # 🔹 ใช้ connection แรกสำหรับอ่านข้อมูล
            with get_connection_app() as conn_read:
                result = conn_read.execute(text("""
                    SELECT point_value FROM kpigoalpoint.personal_points
                    WHERE user_ref_id = :uid
                """), {"uid": user_id})
                row = result.fetchone()
                current_point = int(row[0]) if row and row[0] is not None else 0

                user_df = pd.read_sql(text("""
                    SELECT user_id, full_name, nickname
                    FROM kpigoalpoint.users
                    WHERE user_id != :uid
                    ORDER BY full_name
                """), conn_read, params={"uid": user_id})

            user_map = {
                f"{row['full_name']} ({row['nickname']})": row['user_id']
                for _, row in user_df.iterrows()
            }

            recipient_display = st.selectbox("👥 เลือกผู้รับ Point", list(user_map.keys()))
            recipient_user_id = user_map[recipient_display]

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
                        # 🔹 เปิด connection ใหม่แล้วค่อย begin transaction
                        with get_connection_app() as conn_write:
                            with conn_write.begin():
                                conn_write.execute(text("""
                                    UPDATE kpigoalpoint.personal_points
                                    SET point_value = point_value - :amount
                                    WHERE user_ref_id = :uid
                                """), {"amount": point_input, "uid": user_id})

                                conn_write.execute(text("""
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
            
    elif selected_dept == "แลก Point ส่วนตัว":
        st.title("🎁 แลก Point ส่วนตัว")
        st.write("------")

        # ✅ ตรวจสอบว่า user login อยู่
        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("⚠️ ไม่พบข้อมูลผู้ใช้ กรุณา login ใหม่")
            st.stop()

        try:
            conn = get_connection_app()

            # ✅ ดึง point คงเหลือของผู้ใช้
            result = conn.execute(text("""
                SELECT point_value
                FROM kpigoalpoint.personal_points
                WHERE user_ref_id = :user_id
            """), {"user_id": user_id})
            point_row = result.fetchone()
            user_point = point_row.point_value if point_row else 0
            st.markdown(f"💰 Point คงเหลือของคุณ: **{user_point:,}**")

            # ✅ ดึงรายการ reward เฉพาะของ user
            result = conn.execute(text("""
                SELECT id, reward_name, reward_point
                FROM kpigoalpoint.reward
                WHERE reward_type = 'user'
                ORDER BY reward_point, reward_name
            """))
            rewards = result.fetchall()

            if not rewards:
                st.info("📭 ยังไม่มีรางวัลสำหรับผู้ใช้")
            else:
                reward_dict = {
                    f"{row.reward_name} ({row.reward_point} pts)": (row.id, row.reward_point)
                    for row in rewards
                }

                selected_label = st.selectbox("เลือกรางวัลที่ต้องการแลก", list(reward_dict.keys()))
                selected_reward_id, selected_reward_point = reward_dict[selected_label]

                st.markdown(f"🎯 Point ที่ต้องใช้: **{selected_reward_point:,}**")

                if user_point < selected_reward_point:
                    st.warning("⚠️ Point ของคุณไม่เพียงพอสำหรับรางวัลนี้")
                else:
                    if st.button("📤 ส่งคำขอแลก Point"):
                        try:
                            # ✅ หัก point
                            result = conn.execute(text("""
                                UPDATE kpigoalpoint.personal_points
                                SET point_value = point_value - :used_point
                                WHERE user_ref_id = :user_id AND point_value >= :used_point
                            """), {
                                "used_point": selected_reward_point,
                                "user_id": user_id
                            })

                            if result.rowcount == 0:
                                st.error("❌ ไม่สามารถหัก point ได้ อาจจะมีการเปลี่ยนแปลงระหว่างทำรายการ")
                                st.stop()

                            # ✅ บันทึกคำร้อง
                            conn.execute(text("""
                                INSERT INTO kpigoalpoint.req_user_team (
                                    requester_type,
                                    requester_ref_id,
                                    reward_id
                                ) VALUES (
                                    'user',
                                    :user_id,
                                    :reward_id
                                )
                            """), {
                                "user_id": user_id,
                                "reward_id": selected_reward_id
                            })

                            conn.commit()
                            st.success("✅ ส่งคำขอแลก Point สำเร็จแล้ว")
                            time.sleep(2)  # ให้เวลาในการแสดงผลก่อน rerun
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาดในการส่งคำขอ: {e}")

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        
                
                
    elif selected_dept == "แลก Point ทีม":
        st.title("🏢 แลก Point ทีม")
        st.write("------")

        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("⚠️ ไม่พบข้อมูลผู้ใช้ กรุณา login ใหม่")
            st.stop()

        try:
            conn = get_connection_app()

            # 🔍 ดึง dept_id และ point ของทีม
            result = conn.execute(text("""
                SELECT d.id AS dept_id, d.point_dpmt
                FROM kpigoalpoint.users u
                JOIN kpigoalpoint.departments d ON u.dept_id = d.id
                WHERE u.user_id = :user_id
            """), {"user_id": user_id})
            dept_row = result.fetchone()

            if not dept_row or not dept_row.dept_id:
                st.error("⚠️ ไม่พบข้อมูลแผนกของผู้ใช้")
                st.stop()

            dept_id = str(dept_row.dept_id)
            dept_point = dept_row.point_dpmt or 0
            st.markdown(f"💰 Point คงเหลือของทีมคุณ: **{dept_point:,}**")

            # 🎯 ดึงรางวัลที่เป็นประเภททีม
            result = conn.execute(text("""
                SELECT id, reward_name, reward_point
                FROM kpigoalpoint.reward
                WHERE reward_type = 'team'
                ORDER BY reward_point, reward_name
            """))
            rewards = result.fetchall()

            if not rewards:
                st.info("📭 ยังไม่มีรางวัลสำหรับทีม")
            else:
                reward_dict = {
                    f"{row.reward_name} ({row.reward_point} pts)": (row.id, row.reward_point)
                    for row in rewards
                }

                selected_label = st.selectbox("เลือกรางวัลที่ต้องการแลก", list(reward_dict.keys()))
                selected_reward_id, selected_reward_point = reward_dict[selected_label]

                st.markdown(f"🎯 Point ที่ต้องใช้: **{selected_reward_point:,}**")

                if dept_point < selected_reward_point:
                    st.warning("⚠️ Point ของทีมไม่เพียงพอสำหรับรางวัลนี้")
                else:
                    if st.button("📤 ส่งคำขอแลก Point ทีม"):
                        try:
                            # ✅ หัก point ของทีม
                            result = conn.execute(text("""
                                UPDATE kpigoalpoint.departments
                                SET point_dpmt = point_dpmt - :used_point
                                WHERE id = :dept_id AND point_dpmt >= :used_point
                            """), {
                                "used_point": selected_reward_point,
                                "dept_id": dept_id
                            })

                            if result.rowcount == 0:
                                st.error("❌ ไม่สามารถหัก point ได้ อาจจะมีการเปลี่ยนแปลงระหว่างทำรายการ")
                                st.stop()

                            # ✅ บันทึกคำร้อง
                            conn.execute(text("""
                                INSERT INTO kpigoalpoint.req_user_team (
                                    requester_type,
                                    requester_ref_id,
                                    reward_id
                                ) VALUES (
                                    'team',
                                    :dept_id,
                                    :reward_id
                                )
                            """), {
                                "dept_id": dept_id,
                                "reward_id": selected_reward_id
                            })

                            conn.commit()
                            st.success("✅ ส่งคำขอแลก Point ทีมสำเร็จแล้ว")
                            time.sleep(2)  # ให้เวลาในการแสดงผลก่อน rerun
                            st.rerun()

                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาดในการส่งคำขอ: {e}")

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

                
    elif selected_dept == "ประวัติการใช้งาน point":
        st.title("📜 ประวัติการแลก Point")
        st.write("------")

        user_id = st.session_state.get("user_id")
        if not user_id:
            st.error("⚠️ ไม่พบข้อมูลผู้ใช้ กรุณา login ใหม่")
            st.stop()

        try:
            conn = get_connection_app()

            # ✅ ดึง dept_id ของผู้ใช้
            result = conn.execute(text("""
                SELECT dept_id
                FROM kpigoalpoint.users
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            dept_row = result.fetchone()
            if not dept_row or not dept_row.dept_id:
                st.error("❌ ไม่พบข้อมูลแผนกของผู้ใช้")
                st.stop()

            dept_id = str(dept_row.dept_id)

            # ✅ ดึงประวัติส่วนตัวเป็น DataFrame
            df_personal = pd.read_sql(text("""
                SELECT r.id AS "รหัสคำขอ",
                    rw.reward_name AS "รางวัล",
                    rw.reward_point AS "แต้มที่ใช้",
                    r.status AS "สถานะ",
                    r.upload_time AS "เวลาส่งคำขอ"
                FROM kpigoalpoint.req_user_team r
                LEFT JOIN kpigoalpoint.reward rw ON r.reward_id = rw.id
                WHERE r.requester_type = 'user' AND r.requester_ref_id = :user_id
                ORDER BY r.upload_time DESC
            """), conn, params={"user_id": user_id})

            # ✅ ดึงประวัติทีมเป็น DataFrame
            df_team = pd.read_sql(text("""
                SELECT r.id AS "รหัสคำขอ",
                    rw.reward_name AS "รางวัล",
                    rw.reward_point AS "แต้มที่ใช้",
                    r.status AS "สถานะ",
                    r.upload_time AS "เวลาส่งคำขอ"
                FROM kpigoalpoint.req_user_team r
                LEFT JOIN kpigoalpoint.reward rw ON r.reward_id = rw.id
                WHERE r.requester_type = 'team' AND r.requester_ref_id = :dept_id
                ORDER BY r.upload_time DESC
            """), conn, params={"dept_id": dept_id})

            # === แปลงเวลาทั้งสอง DataFrame เป็น string เพื่อ JSON serialize ===
            for df in [df_personal, df_team]:
                if "เวลาส่งคำขอ" in df.columns:
                    df["เวลาส่งคำขอ"] = pd.to_datetime(df["เวลาส่งคำขอ"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M")
                df = df.astype(object).where(pd.notnull(df), None)

            # ✅ แสดงประวัติส่วนตัว
            st.subheader("🙋‍♂️ ประวัติการแลกรางวัลส่วนตัว")
            if df_personal.empty:
                st.info("📭 ยังไม่มีการแลกรางวัลส่วนตัว")
            else:
                ui.table(df_personal, maxHeight=300)

            # ✅ แสดงประวัติทีม
            st.subheader("🤝 ประวัติการแลกรางวัลทีม")
            if df_team.empty:
                st.info("📭 ยังไม่มีการแลกรางวัลของทีม")
            else:
                ui.table(df_team, maxHeight=300)

        except Exception as e:
            st.error(f"❌ ไม่สามารถโหลดประวัติได้: {e}")

        finally:
            if 'conn' in locals():
                conn.close()
