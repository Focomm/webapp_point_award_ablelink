import streamlit as st
import streamlit_shadcn_ui as ui
import os
import shutil
import datetime
import pandas as pd   

from sqlalchemy import text
from db import get_connection_app

def admin_page4():
    action = ["Req get point", "Req use point", "History get point","History use point"]

    st.sidebar.header("การดำเนินการ")
    selected_action = st.sidebar.selectbox("เลือกการจัดการ", action)

    if selected_action == "Req get point":
        st.title("📥 Request Get Point")
        st.write("------")

        # เลือกประเภทคำร้อง
        # request_type = st.radio("เลือกประเภทคำร้อง", ("ส่วนบุคคล", "ทีม"))
        request_type = ui.tabs(options=['ส่วนบุคคล', 'ทีม'], default_value='ส่วนบุคคล', key="kanaries")

        conn = get_connection_app()

        if request_type == "ส่วนบุคคล":
            query = text("""
                SELECT 
                    f.id,
                    f.user_ref_id,
                    u.full_name,
                    u.nickname,
                    f.message,
                    f.original_name,
                    f.new_name,
                    f.file_type,
                    f.path,
                    f.upload_time,
                    k.kpi_name,
                    k.point_value
                FROM kpigoalpoint.file_messages_personal f
                JOIN kpigoalpoint.users u ON f.user_ref_id = u.user_id
                LEFT JOIN kpigoalpoint.kpi_personal k ON f.kpi_id = k.id
                WHERE f.status = 'onprocess'
                ORDER BY f.upload_time ASC
            """)

            result = conn.execute(query)
            rows = result.fetchall()

            if not rows:
                st.info("✅ ยังไม่มีคำร้องส่วนบุคคล")
            else:
                for row in rows:
                    col1, col2 = st.columns([0.5, 15])
                    with col1:
                        st.checkbox("เลือก", key=f"select_{row.id}", label_visibility="collapsed")
                    with col2:
                        with st.expander(f"📨 จาก {row.full_name} ({row.nickname}) เวลา {row.upload_time.strftime('%Y-%m-%d %H:%M')}"):
                            st.markdown(f"**ข้อความคำร้อง:**\n\n{row.message}")
                            if row.kpi_name:
                                st.markdown(f"📌 **KPI ที่เกี่ยวข้อง:** {row.kpi_name}")
                                st.markdown(f"🎯 **Point:** {row.point_value}")
                            else:
                                st.markdown("📌 ไม่มีข้อมูล KPI")

                            # แนบไฟล์
                            if row.original_name and row.new_name and row.path:
                                try:
                                    with open(f"{row.path}/{row.new_name}", "rb") as f:
                                        st.download_button(
                                            label=f"⬇️ ดาวน์โหลด: {row.original_name}",
                                            data=f.read(),
                                            file_name=row.original_name,
                                            mime=row.file_type
                                        )
                                except:
                                    st.warning("⚠️ ไม่สามารถโหลดไฟล์ได้")
                            else:
                                st.markdown("📭 ไม่มีไฟล์แนบ")

                selected_rows = [row for row in rows if st.session_state.get(f"select_{row.id}", False)]
                
                submit_personal = ui.button("Submit คำร้องที่เลือก (ส่วนบุคคล)", key="add_point", variant="default")

                if submit_personal:
                    if not selected_rows:
                        st.warning("⚠️ กรุณาเลือกคำร้อง")
                    else:
                        for row in selected_rows:
                            try:
                                if not row.user_ref_id or row.point_value is None:
                                    st.warning(f"❗ ข้อมูลไม่ครบของ {row.full_name}")
                                    continue

                                # อัปเดตคะแนน
                                result = conn.execute(text("""
                                    UPDATE kpigoalpoint.personal_points
                                    SET point_value = point_value + :add_point
                                    WHERE user_ref_id = :user_id
                                """), {"add_point": row.point_value, "user_id": row.user_ref_id})

                                if result.rowcount == 0:
                                    st.error(f"❌ ไม่พบข้อมูลคะแนนเดิมของ {row.full_name}")
                                    continue

                                # จัดการไฟล์และสถานะ
                                now = datetime.datetime.now()
                                year = str(now.year)
                                month = str(now.month).zfill(2)
                                save_dir = os.path.join("uploads", "personal", "done", year, month)
                                os.makedirs(save_dir, exist_ok=True)

                                if row.path and row.new_name:
                                    old_path = os.path.join(row.path, row.new_name)
                                    if os.path.exists(old_path):
                                        file_ext = os.path.splitext(row.original_name)[-1]
                                        new_name = row.new_name + file_ext
                                        new_path = os.path.join(save_dir, new_name)
                                        shutil.move(old_path, new_path)

                                        conn.execute(text("""
                                            UPDATE kpigoalpoint.file_messages_personal
                                            SET status = 'done', new_name = :new_name, path = :path, updated_at = now()
                                            WHERE id = :id
                                        """), {"new_name": new_name, "path": save_dir, "id": row.id})
                                    else:
                                        conn.execute(text("""
                                            UPDATE kpigoalpoint.file_messages_personal
                                            SET status = 'done', updated_at = now()
                                            WHERE id = :id
                                        """), {"id": row.id})
                                else:
                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_personal
                                        SET status = 'done', updated_at = now()
                                        WHERE id = :id
                                    """), {"id": row.id})

                                st.success(f"✅ อัปเดตคำร้องของ {row.full_name} แล้ว")
                            except Exception as e:
                                st.error(f"❌ {row.full_name}: {e}")
                        conn.commit()

        # ---------------------------------------------

        elif request_type == "ทีม":
            query = text("""
                SELECT 
                    f.id,
                    f.dept_ref_id,
                    d.dept_name,
                    f.message,
                    f.original_name,
                    f.new_name,
                    f.file_type,
                    f.path,
                    f.upload_time,
                    k.kpi_name,
                    k.point_value
                FROM kpigoalpoint.file_messages_team f
                JOIN kpigoalpoint.departments d ON f.dept_ref_id = d.id
                LEFT JOIN kpigoalpoint.kpi_team k ON f.kpi_id = k.id
                WHERE f.status = 'onprocess'
                ORDER BY f.upload_time ASC
            """)
            result = conn.execute(query)
            rows = result.fetchall()

            if not rows:
                st.info("✅ ยังไม่มีคำร้องของทีม")
            else:
                for row in rows:
                    col1, col2 = st.columns([0.5, 15])
                    with col1:
                        st.checkbox("เลือก", key=f"select_team_{row.id}", label_visibility="collapsed")
                    with col2:
                        with st.expander(f"📨 จากแผนก {row.dept_name} เวลา {row.upload_time.strftime('%Y-%m-%d %H:%M')}"):
                            st.markdown(f"**ข้อความคำร้อง:**\n\n{row.message}")
                            if row.kpi_name:
                                st.markdown(f"📌 **KPI ที่เกี่ยวข้อง:** {row.kpi_name}")
                                st.markdown(f"🎯 **Point:** {row.point_value}")
                            else:
                                st.markdown("📌 ไม่มีข้อมูล KPI")

                            if row.original_name and row.new_name and row.path:
                                try:
                                    with open(f"{row.path}/{row.new_name}", "rb") as f:
                                        st.download_button(
                                            label=f"⬇️ ดาวน์โหลด: {row.original_name}",
                                            data=f.read(),
                                            file_name=row.original_name,
                                            mime=row.file_type
                                        )
                                except:
                                    st.warning("⚠️ ไม่สามารถโหลดไฟล์ได้")
                            else:
                                st.markdown("📭 ไม่มีไฟล์แนบ")

                selected_rows = [row for row in rows if st.session_state.get(f"select_team_{row.id}", False)]
                
                submit_team = ui.button("Submit คำร้องที่เลือก (ทีม)", key="add_point", variant="default")

                if submit_team:
                    if not selected_rows:
                        st.warning("⚠️ กรุณาเลือกคำร้อง")
                    else:
                        for row in selected_rows:
                            try:
                                if row.point_value is None or not row.dept_ref_id:
                                    st.warning(f"❗ ข้อมูลไม่ครบของ {row.dept_name}")
                                    continue

                                result = conn.execute(text("""
                                    UPDATE kpigoalpoint.departments
                                    SET point_dpmt = point_dpmt + :add_point
                                    WHERE id = :dept_ref_id
                                """), {"add_point": row.point_value, "dept_ref_id": row.dept_ref_id})

                                if result.rowcount == 0:
                                    st.error(f"❌ ไม่พบข้อมูลแผนก {row.dept_name}")
                                    continue

                                now = datetime.datetime.now()
                                year = str(now.year)
                                month = str(now.month).zfill(2)
                                save_dir = os.path.join("uploads", "team", "done", year, month)
                                os.makedirs(save_dir, exist_ok=True)

                                if row.path and row.new_name:
                                    old_path = os.path.join(row.path, row.new_name)
                                    if os.path.exists(old_path):
                                        file_ext = os.path.splitext(row.original_name)[-1]
                                        new_name = row.new_name + file_ext
                                        new_path = os.path.join(save_dir, new_name)
                                        shutil.move(old_path, new_path)

                                        conn.execute(text("""
                                            UPDATE kpigoalpoint.file_messages_team
                                            SET status = 'done', new_name = :new_name, path = :path, updated_at = now()
                                            WHERE id = :id
                                        """), {"new_name": new_name, "path": save_dir, "id": row.id})
                                    else:
                                        conn.execute(text("""
                                            UPDATE kpigoalpoint.file_messages_team
                                            SET status = 'done', updated_at = now()
                                            WHERE id = :id
                                        """), {"id": row.id})
                                else:
                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_team
                                        SET status = 'done', updated_at = now()
                                        WHERE id = :id
                                    """), {"id": row.id})

                                st.success(f"✅ อัปเดตคำร้องของแผนก {row.dept_name} แล้ว")
                            except Exception as e:
                                st.error(f"❌ {row.dept_name}: {e}")
                        conn.commit()
                        
                        
    elif selected_action == "Req use point":
        st.title("📥 ตรวจสอบคำขอแลก Point")
        st.write("------")

        # ✅ เลือกประเภทคำร้อง
        # request_type = st.radio("เลือกประเภทคำร้อง", ("ส่วนบุคคล", "ทีม"))
        request_type = ui.tabs(options=['ส่วนบุคคล', 'ทีม'], default_value='ส่วนบุคคล', key="kanaries")
        requester_type = "user" if request_type == "ส่วนบุคคล" else "team"

        try:
            conn = get_connection_app()

            result = conn.execute(text(f"""
                SELECT 
                    r.id,
                    r.requester_ref_id,
                    r.status,
                    r.upload_time,
                    u.full_name,
                    u.nickname,
                    rw.reward_name,
                    rw.reward_point
                FROM kpigoalpoint.req_user_team r
                LEFT JOIN kpigoalpoint.reward rw ON r.reward_id = rw.id
                LEFT JOIN kpigoalpoint.users u ON r.requester_ref_id = u.user_id
                WHERE r.requester_type = :req_type AND r.status = 'pending'
                ORDER BY r.upload_time ASC
            """), {"req_type": requester_type})
            rows = result.fetchall()

            if not rows:
                st.info(f"✅ ยังไม่มีคำขอแลก Point{'ส่วนบุคคล' if requester_type == 'user' else 'ทีม'}")
            else:
                for row in rows:
                    col1, col2 = st.columns([0.5, 15])

                    with col1:
                        st.checkbox("เลือก", key=f"approve_req_{row.id}", label_visibility="collapsed")

                    with col2:
                        name_display = (
                            f"{row.full_name} ({row.nickname})"
                            if requester_type == "user"
                            else f"แผนก ID: {row.requester_ref_id}"
                        )
                        with st.expander(f"📨 จาก {name_display} เวลา {row.upload_time.strftime('%Y-%m-%d %H:%M')}"):
                            st.markdown(f"🎁 **ของรางวัล:** {row.reward_name or 'ไม่ระบุ'}")
                            st.markdown(f"🎯 **แต้มที่ใช้:** {row.reward_point or '-'}")
                            st.markdown(f"📌 **สถานะ:** {row.status}")

                selected_rows = [row for row in rows if st.session_state.get(f"approve_req_{row.id}", False)]

                submit = ui.button("อนุมัติคำขอที่เลือก", key="add_point", variant="default")

                if submit:
                    if not selected_rows:
                        st.warning("⚠️ กรุณาเลือกคำขออย่างน้อย 1 รายการ")
                    else:
                        try:
                            for row in selected_rows:
                                conn.execute(text("""
                                    UPDATE kpigoalpoint.req_user_team
                                    SET status = 'approved',
                                        update_time = now()
                                    WHERE id = :id
                                """), {"id": row.id})

                            conn.commit()
                            st.success("✅ อนุมัติคำขอที่เลือกเรียบร้อยแล้ว")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ เกิดข้อผิดพลาดในการอนุมัติ: {e}")

        except Exception as e:
            st.error(f"❌ ไม่สามารถโหลดคำขอได้: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    
    elif selected_action == "History get point":
        st.title("📜 ประวัติการจัดการคำร้อง")
        st.write('------')

        conn = get_connection_app()

        # === ดึงคำร้องส่วนตัว ===
        query_personal = """
            SELECT 
                d.dept_name,
                u.full_name AS owner,
                f.message,
                f.upload_time,
                f.new_name,
                'ส่วนตัว' AS type
            FROM kpigoalpoint.file_messages_personal f
            JOIN kpigoalpoint.users u ON f.user_ref_id = u.user_id
            JOIN kpigoalpoint.departments d ON u.dept_id = d.id
            WHERE f.status = 'done'
        """

        # === ดึงคำร้องทีม ===
        query_team = """
            SELECT 
                d.dept_name,
                d.dept_name AS owner,
                f.message,
                f.upload_time,
                f.new_name,
                'ทีม' AS type
            FROM kpigoalpoint.file_messages_team f
            JOIN kpigoalpoint.departments d ON f.dept_ref_id = d.id
            WHERE f.status = 'done'
        """

        df_personal = pd.read_sql(query_personal, conn)
        df_team = pd.read_sql(query_team, conn)

        df_all = pd.concat([df_personal, df_team], ignore_index=True)
        df_all = df_all.rename(columns={
            "dept_name": "ทีม",
            "owner": "ผู้ร้องขอ",
            "message": "ข้อความ",
            "upload_time": "เวลาอัปโหลด",
            "new_name": "ชื่อไฟล์",
            "type": "ประเภท"
        })

        df_all = df_all.sort_values(by=["ทีม", "เวลาอัปโหลด"], ascending=[True, False])

        # === แสดงผลแยกตามทีม ===
        for team_name, group_df in df_all.groupby("ทีม"):
            st.markdown(f"### 🏢 ทีม: {team_name}")
            st.dataframe(
                group_df[["ประเภท", "ผู้ร้องขอ", "ข้อความ", "ชื่อไฟล์", "เวลาอัปโหลด"]],
                use_container_width=True
            )

    
    if selected_action == "History use point":
        
        st.title("📜 ประวัติการอนุมัติคำขอแลก Point")
        st.write('------')

        conn = get_connection_app()

        # --- ประวัติคำขอส่วนตัว ---
        query_user = """
            SELECT 
                d.dept_name,
                u.full_name AS owner,
                r.upload_time,
                rw.reward_name,
                rw.reward_point,
                'ส่วนตัว' AS type
            FROM kpigoalpoint.req_user_team r
            JOIN kpigoalpoint.users u ON r.requester_ref_id = u.user_id
            JOIN kpigoalpoint.departments d ON u.dept_id = d.id
            LEFT JOIN kpigoalpoint.reward rw ON r.reward_id = rw.id
            WHERE r.requester_type = 'user' AND r.status = 'approved'
        """

        # --- ประวัติคำขอทีม ---
        query_team = """
            SELECT 
                d.dept_name,
                d.dept_name AS owner,
                r.upload_time,
                rw.reward_name,
                rw.reward_point,
                'ทีม' AS type
            FROM kpigoalpoint.req_user_team r
            JOIN kpigoalpoint.departments d ON r.requester_ref_id::int = d.id
            LEFT JOIN kpigoalpoint.reward rw ON r.reward_id = rw.id
            WHERE r.requester_type = 'team' AND r.status = 'approved'
        """

        df_user = pd.read_sql(query_user, conn)
        df_team = pd.read_sql(query_team, conn)

        df_all = pd.concat([df_user, df_team], ignore_index=True)
        df_all = df_all.rename(columns={
            "dept_name": "ทีม",
            "owner": "ผู้ร้องขอ",
            "reward_name": "ของรางวัล",
            "reward_point": "แต้มที่ใช้",
            "upload_time": "เวลาอนุมัติ",
            "type": "ประเภท"
        })

        df_all = df_all.sort_values(by=["ทีม", "เวลาอนุมัติ"], ascending=[True, False])

        # === แสดงผลแยกตามทีม ===
        for team_name, group_df in df_all.groupby("ทีม"):
            st.markdown(f"### 🏢 ทีม: {team_name}")
            st.dataframe(
                group_df[["ประเภท", "ผู้ร้องขอ", "ของรางวัล", "แต้มที่ใช้", "เวลาอนุมัติ"]],
                use_container_width=True
            )

