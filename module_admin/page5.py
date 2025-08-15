import streamlit as st
import streamlit_shadcn_ui as ui
from sqlalchemy import text
import pandas as pd
from db import get_connection_app


def admin_page5():
    action = ["Add KPI","Delete KPI", "Manage Award", "View KPI ALL"]
    st.sidebar.header("การดำเนินการ")
    selected_KPI = st.sidebar.selectbox("เลือกการจัดการ", action)
    
    
    if selected_KPI == "Add KPI":
        st.title("📊 เพิ่ม KPI")
        st.write('------')

        try:
            conn = get_connection_app()

            # เลือกประเภท KPI
            # kpi_type = st.radio("เลือกประเภท KPI", ("ส่วนบุคคล", "ทีม"))
            kpi_type = ui.tabs(options=['ส่วนบุคคล', 'ทีม'], default_value='ส่วนบุคคล', key="kanaries")

            if kpi_type == "ส่วนบุคคล":
                # ดึงรายชื่อผู้ใช้
                users_query = text("SELECT user_id, full_name FROM kpigoalpoint.users ORDER BY full_name")
                result = conn.execute(users_query)
                users = result.fetchall()

                if not users:
                    st.warning("⚠️ ยังไม่มีผู้ใช้งานในระบบ กรุณาเพิ่มผู้ใช้ก่อนสร้าง KPI")
                else:
                    user_dict = {f"{row.full_name} ({row.user_id})": row.user_id for row in users}
                    selected_user_display = st.selectbox("👤 เลือกผู้ใช้", list(user_dict.keys()))
                    selected_user_id = user_dict[selected_user_display]

                    st.write('------')
                    kpi_name = st.text_input("🎯 ชื่อ KPI ส่วนบุคคล")
                    kpi_goal = st.text_area("📌 เป้าหมายของ KPI")
                    point_value = st.number_input("คะแนน", min_value=0, step=1)
                    # add_kpi_button = ui.button("เพิ่ม KPI ส่วนบุคคล", key="add_kpi_personal",variant="destructive")
                    add_kpi_button_personal = ui.button("เพิ่ม KPI ส่วนบุคคล", key="add_kpi_personal",variant="default")

                    if add_kpi_button_personal:
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
                                conn.commit()
                                st.success(f"✅ เพิ่ม KPI สำเร็จให้กับผู้ใช้: {selected_user_id}")
                            except Exception as e:
                                conn.rollback()
                                st.error(f"❌ เกิดข้อผิดพลาด: {e}")

            elif kpi_type == "ทีม":
                # ดึงรายชื่อแผนก
                dept_query = text("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name")
                result = conn.execute(dept_query)
                departments = result.fetchall()

                if not departments:
                    st.warning("⚠️ ยังไม่มีแผนกในระบบ กรุณาเพิ่มแผนกก่อนสร้าง KPI")
                else:
                    dept_dict = {f"{row.dept_name}": row.id for row in departments}
                    selected_dept_display = st.selectbox("เลือกแผนก", list(dept_dict.keys()))
                    selected_dept_id = dept_dict[selected_dept_display]

                    st.write('------')
                    kpi_name = st.text_input("🎯 ชื่อ KPI ทีม")
                    kpi_goal = st.text_area("📌 เป้าหมายของ KPI ทีม")
                    point_value = st.number_input("คะแนน", min_value=0, step=1)
                    add_kpi_button_team = ui.button("เพิ่ม KPI ทีม", key="add_kpi_team",variant="default")


                    if add_kpi_button_team:
                        if not kpi_name.strip() or not kpi_goal.strip():
                            st.warning("⚠️ กรุณากรอกข้อมูลให้ครบถ้วน")
                        else:
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

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

        
    
    elif selected_KPI == "Delete KPI":
        st.title("🗑️ ลบ KPI")
        st.write("------")

        try:
            conn = get_connection_app()

            # kpi_type = st.radio("เลือกประเภท KPI ที่ต้องการลบ", ("ส่วนบุคคล", "ทีม"))
            kpi_type = ui.tabs(options=['ส่วนบุคคล', 'ทีม'], default_value='ส่วนบุคคล', key="kanaries")

            if kpi_type == "ส่วนบุคคล":
                # ดึง KPI ส่วนบุคคล
                result = conn.execute(text("""
                    SELECT p.id, u.full_name, p.kpi_name
                    FROM kpigoalpoint.kpi_personal p
                    JOIN kpigoalpoint.users u ON p.user_ref_id = u.user_id
                    ORDER BY u.full_name, p.kpi_name
                """))
                rows = result.fetchall()

                if not rows:
                    st.info("📭 ยังไม่มี KPI ส่วนบุคคลให้ลบ")
                else:
                    kpi_dict = {
                        f"{row.full_name} → {row.kpi_name} (ID: {row.id})": row.id for row in rows
                    }
                    selected_label = st.selectbox("เลือก KPI ที่ต้องการลบ", list(kpi_dict.keys()), key="kpi_personal_select")
                    selected_id = kpi_dict[selected_label]

                    confirm = st.checkbox("คุณแน่ใจหรือไม่ว่าต้องการลบ KPI นี้?", key="confirm_kpi_personal")
                    delete_kpi_button_personal = ui.button("ลบ KPI ส่วนบุคคล", key="delete_kpi_personal",variant="destructive")

                    if delete_kpi_button_personal:
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

            elif kpi_type == "ทีม":
                # ดึง KPI ทีม
                result = conn.execute(text("""
                    SELECT t.id, d.dept_name, t.kpi_name
                    FROM kpigoalpoint.kpi_team t
                    JOIN kpigoalpoint.departments d ON t.dept_ref_id = d.id
                    ORDER BY d.dept_name, t.kpi_name
                """))
                rows = result.fetchall()

                if not rows:
                    st.info("📭 ยังไม่มี KPI ทีมให้ลบ")
                else:
                    kpi_dict = {
                        f"{row.dept_name} → {row.kpi_name} (ID: {row.id})": row.id for row in rows
                    }
                    selected_label = st.selectbox("เลือก KPI ทีมที่จะลบ", list(kpi_dict.keys()), key="kpi_team_select")
                    selected_id = kpi_dict[selected_label]

                    confirm = st.checkbox("คุณแน่ใจหรือไม่ว่าต้องการลบ KPI ทีมนี้?", key="confirm_kpi_team")
                    delete_kpi_button_team = ui.button("ลบ KPI ทีม", key="delete_kpi_team",variant="destructive")


                    if delete_kpi_button_team:
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
        finally:
            if 'conn' in locals():
                conn.close()
        
    elif selected_KPI == "Manage Award":
        
        st.title("🏆 จัดการรางวัล (Reward)")
        st.write("------")

        try:
            conn = get_connection_app()

            # --- ส่วนเพิ่มรางวัล ---
            st.subheader("เพิ่มรางวัลใหม่")
            # reward_type = st.radio("🎯 ประเภทของรางวัล", ("user", "team"), key="reward_type_add")
            reward_type = ui.tabs(options=['ส่วนบุคคล', 'ทีม'], default_value='ส่วนบุคคล', key="kanaries")
            reward_name = st.text_input("🏅 ชื่อรางวัล", key="reward_name_add")
            reward_point = st.number_input("🎁 Point ที่ใช้แลก", min_value=1, step=1, key="reward_point_add")


            add_reward_button = ui.button("เพิ่มรางวัล", key="add_reward",variant="default")

            if add_reward_button:
                if not reward_name.strip():
                    st.warning("⚠️ กรุณากรอกชื่อรางวัล")
                else:
                    try:
                        conn.execute(text("""
                            INSERT INTO kpigoalpoint.reward (reward_type, reward_name, reward_point)
                            VALUES (:reward_type, :reward_name, :reward_point)
                        """), {
                            "reward_type": reward_type,
                            "reward_name": reward_name.strip(),
                            "reward_point": reward_point
                        })
                        conn.commit()
                        st.success(f"✅ เพิ่มรางวัลสำเร็จ: {reward_name.strip()}")
                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ เพิ่มรางวัลไม่สำเร็จ: {e}")

            st.divider()

            # --- ส่วนลบรางวัล ---
            st.subheader("ลบรางวัล")

            result = conn.execute(text("""
                SELECT id, reward_type, reward_name, reward_point
                FROM kpigoalpoint.reward
                ORDER BY reward_type, reward_name
            """))
            rewards = result.fetchall()

            if not rewards:
                st.info("📭 ยังไม่มีรายการรางวัลในระบบ")
            else:
                reward_dict = {
                    f"[{row.reward_type}] {row.reward_name} ({row.reward_point} pts)": row.id
                    for row in rewards
                }

                selected_label = st.selectbox("เลือกรางวัลที่จะลบ", list(reward_dict.keys()), key="reward_delete_select")
                selected_id = reward_dict[selected_label]

                confirm = st.checkbox("⚠️ ยืนยันการลบรางวัลนี้", key="confirm_delete_reward")
                delete_reward_button = ui.button("ลบรางวัล", key="delete_reward", variant="destructive")

                if delete_reward_button:
                    if not confirm:
                        st.warning("⚠️ กรุณาติ๊กยืนยันก่อนลบ")
                    else:
                        try:
                            conn.execute(text("""
                                DELETE FROM kpigoalpoint.reward
                                WHERE id = :id
                            """), {"id": selected_id})
                            conn.commit()
                            st.success("✅ ลบรางวัลเรียบร้อยแล้ว")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ ลบรางวัลไม่สำเร็จ: {e}")

        except Exception as e:
            st.error(f"❌ ไม่สามารถเชื่อมต่อฐานข้อมูล: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    elif selected_KPI == "View KPI ALL":
        st.title("📋 ดูรายการ KPI ทั้งหมด")

        conn = get_connection_app()

        # ดึงข้อมูล KPI ส่วนตัว + ชื่อพนักงาน + ชื่อแผนก
        personal_query = """
            SELECT 
                d.dept_name,
                u.full_name AS owner,
                p.kpi_name,
                p.kpi_goal,
                p.point_value
            FROM kpigoalpoint.kpi_personal p
            JOIN kpigoalpoint.users u ON p.user_ref_id = u.user_id
            JOIN kpigoalpoint.departments d ON u.dept_id = d.id
        """


        # ดึงข้อมูล KPI ทีม + ชื่อแผนก
        team_query = """
            SELECT 
                d.dept_name,
                d.dept_name AS owner,
                t.kpi_name,
                t.kpi_goal,
                t.point_value
            FROM kpigoalpoint.kpi_team t
            JOIN kpigoalpoint.departments d ON t.dept_ref_id = d.id
        """


        df_personal = pd.read_sql(personal_query, conn)
        df_personal["type"] = "ส่วนตัว"

        df_team = pd.read_sql(team_query, conn)
        df_team["type"] = "ทีม"

        # รวมตารางแล้วเรียงตามชื่อแผนกและประเภท
        df_all = pd.concat([df_personal, df_team], ignore_index=True)
        df_all = df_all.rename(columns={
            "owner": "ชื่อผู้รับผิดชอบ",
            "kpi_name": "ชื่อ KPI",
            "kpi_goal": "เป้าหมาย",
            "point_value": "คะแนน",
            "dept_name": "ทีม"
        })

        df_all = df_all.sort_values(by=["ทีม", "type", "ชื่อ KPI"])

        # แสดงแบบกลุ่มตามแผนก
        for team_name, group_df in df_all.groupby("ทีม"):
            st.markdown(f"### ทีม: {team_name}")
            ui.table(
                    group_df[["type", "ชื่อผู้รับผิดชอบ", "ชื่อ KPI", "เป้าหมาย", "คะแนน"]],
                    maxHeight=300
                )
            # st.dataframe(
            #     group_df[["type", "ชื่อผู้รับผิดชอบ", "ชื่อ KPI", "เป้าหมาย", "คะแนน"]],
            #     use_container_width=True
            # )

