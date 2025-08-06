import streamlit as st
import streamlit_shadcn_ui as ui
import os
import shutil
import datetime
import pandas as pd   

from sqlalchemy import text
from db import get_connection_app

def admin_page4():
    action = ["REQ get personal point", "REQ get team point",  "REQ use personal point", "REQ use team point", "History"]

    st.sidebar.header("🔎 ตัวกรองข้อมูล")
    selected_action = st.sidebar.selectbox("เลือกการจัดการ", action)

    if selected_action == "REQ get personal point":
        st.title("📥 Request Get Personal Point")
        st.write('------')

        conn = get_connection_app()
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
            st.info("✅ ยังไม่มีคำร้องขอใหม่")
        else:
            for row in rows:
                col1, col2 = st.columns([1, 12])  # 1 = checkbox, 12 = expander

                with col1:
                    st.checkbox("เลือก", key=f"select_{row.id}", label_visibility="collapsed")

                with col2:
                    with st.expander(f"📨 จาก {row.full_name} ({row.nickname}) เวลา {row.upload_time.strftime('%Y-%m-%d %H:%M')}"):
                        st.markdown(f"**ข้อความคำร้อง:**\n\n{row.message}")

                        if row.kpi_name:
                            st.markdown(f"📌 **KPI ที่เกี่ยวข้อง:** {row.kpi_name}")
                            st.markdown(f"🎯 **จำนวน Point ที่ขอ:** {row.point_value}")
                        else:
                            st.markdown("📌 ไม่มีข้อมูล KPI ที่เกี่ยวข้อง")

                        if row.original_name and row.new_name and row.path:
                            try:
                                file_path = f"{row.path}/{row.new_name}"
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()

                                st.download_button(
                                    label=f"⬇️ ดาวน์โหลดไฟล์แนบ: {row.original_name}",
                                    data=file_bytes,
                                    file_name=row.original_name,
                                    mime=row.file_type
                                )
                            except Exception as e:
                                st.warning(f"ไม่สามารถโหลดไฟล์ได้: {e}")
                        else:
                            st.markdown("📭 ไม่มีไฟล์แนบ")
                            
            # เก็บคำร้องที่ถูกเลือก
            selected_rows = [row for row in rows if st.session_state.get(f"select_{row.id}", False)]

            if st.button("📤 Submit คำร้องที่เลือก"):
                if not selected_rows:
                    st.warning("⚠️ กรุณาเลือกคำร้องอย่างน้อย 1 รายการ")
                else:
                    for row in selected_rows:
                        try:
                            # ✅ ตรวจสอบว่ามี point และ user
                            if not row.user_ref_id or row.point_value is None:
                                st.warning(f"❗ ข้อมูลผู้ใช้หรือ point ว่าง: {row.full_name}")
                                continue

                            # ✅ พยายาม UPDATE คะแนน (ห้าม INSERT ถ้าไม่มี)
                            result = conn.execute(text("""
                                UPDATE kpigoalpoint.personal_points
                                SET point_value = point_value + :add_point
                                WHERE user_ref_id = :user_id
                            """), {
                                "add_point": row.point_value or 0,
                                "user_id": row.user_ref_id
                            })

                            if result.rowcount == 0:
                                st.error(f"❌ ไม่พบข้อมูลคะแนนเดิมของ {row.full_name} ในตาราง personal_points (user_ref_id: {row.user_ref_id})")
                                continue

                            # ✅ ตรวจสอบว่ามีไฟล์จริง (ทั้งข้อมูลครบและไฟล์มีจริงใน disk)
                            if row.path and row.new_name and row.original_name:
                                old_path = os.path.join(row.path, row.new_name)
                                if os.path.exists(old_path):
                                    now = datetime.datetime.now()
                                    year = str(now.year)
                                    month = str(now.month).zfill(2)
                                    save_dir = os.path.join("uploads", "personal", "done", year, month)
                                    os.makedirs(save_dir, exist_ok=True)

                                    file_ext = os.path.splitext(row.original_name)[-1]
                                    full_filename = row.new_name + file_ext
                                    new_path = os.path.join(save_dir, full_filename)

                                    shutil.move(old_path, new_path)

                                    # ✅ อัปเดตสถานะ + path เฉพาะกรณีไฟล์มีอยู่จริง
                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_personal
                                        SET status = 'done',
                                            new_name = :new_name,
                                            path = :path,
                                            updated_at = NOW()
                                        WHERE id = :id
                                    """), {
                                        "new_name": full_filename,
                                        "path": save_dir,
                                        "id": row.id
                                    })
                                else:
                                    # ❗ กรณีข้อมูลดูเหมือนมีไฟล์แต่ไฟล์หาย → ไม่อัป path
                                    st.warning(f"❗ ไม่พบไฟล์แนบของ {row.full_name} ที่ {old_path} — อัปเดตสถานะเป็น done อย่างเดียว")
                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_personal
                                        SET status = 'done',
                                            updated_at = NOW()
                                        WHERE id = :id
                                    """), {"id": row.id})
                            else:
                                # ✅ ไม่มีข้อมูลไฟล์เลย → อัปเดตสถานะอย่างเดียว
                                conn.execute(text("""
                                    UPDATE kpigoalpoint.file_messages_personal
                                    SET status = 'done',
                                        updated_at = NOW()
                                    WHERE id = :id
                                """), {"id": row.id})

                            st.success(f"✅ อัปเดตคำร้องของ {row.full_name} สำเร็จแล้ว")

                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาดกับคำร้องของ {row.full_name}: {e}")

                    conn.commit()
                    
    elif selected_action == "REQ get team point":
        st.title("📥 Request Get Team Point")
        st.write('------')

        conn = get_connection_app()
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
            st.info("✅ ยังไม่มีคำร้องขอใหม่")
        else:
            for row in rows:
                col1, col2 = st.columns([1, 12])

                with col1:
                    st.checkbox("เลือก", key=f"select_team_{row.id}", label_visibility="collapsed")

                with col2:
                    with st.expander(f"📨 จากแผนก {row.dept_name} เวลา {row.upload_time.strftime('%Y-%m-%d %H:%M')}"):
                        st.markdown(f"**ข้อความคำร้อง:**\n\n{row.message}")

                        if row.kpi_name:
                            st.markdown(f"📌 **KPI ที่เกี่ยวข้อง:** {row.kpi_name}")
                            st.markdown(f"🎯 **จำนวน Point ที่ขอ:** {row.point_value}")
                        else:
                            st.markdown("📌 ไม่มีข้อมูล KPI ที่เกี่ยวข้อง")

                        if row.original_name and row.new_name and row.path:
                            try:
                                file_path = f"{row.path}/{row.new_name}"
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()

                                st.download_button(
                                    label=f"⬇️ ดาวน์โหลดไฟล์แนบ: {row.original_name}",
                                    data=file_bytes,
                                    file_name=row.original_name,
                                    mime=row.file_type
                                )
                            except Exception as e:
                                st.warning(f"ไม่สามารถโหลดไฟล์ได้: {e}")
                        else:
                            st.markdown("📭 ไม่มีไฟล์แนบ")

            selected_rows = [row for row in rows if st.session_state.get(f"select_team_{row.id}", False)]

            if st.button("📤 Submit คำร้องที่เลือก"):
                if not selected_rows:
                    st.warning("⚠️ กรุณาเลือกคำร้องอย่างน้อย 1 รายการ")
                else:
                    for row in selected_rows:
                        try:
                            if row.point_value is None or not row.dept_ref_id:
                                st.warning(f"❗ ข้อมูลแผนกหรือ point ว่าง: {row.dept_name}")
                                continue

                            result = conn.execute(text("""
                                UPDATE kpigoalpoint.departments
                                SET point_dpmt = point_dpmt + :add_point
                                WHERE id = :dept_ref_id
                            """), {
                                "add_point": row.point_value,
                                "dept_ref_id": row.dept_ref_id
                            })

                            if result.rowcount == 0:
                                st.error(f"❌ ไม่พบข้อมูลคะแนนของ {row.dept_name} ใน team_points")
                                continue

                            if row.path and row.new_name and row.original_name:
                                old_path = os.path.join(row.path, row.new_name)
                                if os.path.exists(old_path):
                                    now = datetime.datetime.now()
                                    year = str(now.year)
                                    month = str(now.month).zfill(2)
                                    save_dir = os.path.join("uploads", "team", "done", year, month)
                                    os.makedirs(save_dir, exist_ok=True)

                                    file_ext = os.path.splitext(row.original_name)[-1]
                                    full_filename = row.new_name + file_ext
                                    new_path = os.path.join(save_dir, full_filename)

                                    shutil.move(old_path, new_path)

                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_team
                                        SET status = 'done',
                                            new_name = :new_name,
                                            path = :path,
                                            updated_at = NOW()
                                        WHERE id = :id
                                    """), {
                                        "new_name": full_filename,
                                        "path": save_dir,
                                        "id": row.id
                                    })
                                else:
                                    st.warning(f"❗ ไม่พบไฟล์แนบของ {row.dept_name} ที่ {old_path} — อัปเดตสถานะเป็น done อย่างเดียว")
                                    conn.execute(text("""
                                        UPDATE kpigoalpoint.file_messages_team
                                        SET status = 'done',
                                            updated_at = NOW()
                                        WHERE id = :id
                                    """), {"id": row.id})
                            else:
                                conn.execute(text("""
                                    UPDATE kpigoalpoint.file_messages_team
                                    SET status = 'done',
                                        updated_at = NOW()
                                    WHERE id = :id
                                """), {"id": row.id})

                            st.success(f"✅ อัปเดตคำร้องของแผนก {row.dept_name} สำเร็จแล้ว")

                        except Exception as e:
                            st.error(f"❌ เกิดข้อผิดพลาดกับคำร้องของแผนก {row.dept_name}: {e}")

                    conn.commit()
    
    elif selected_action == "History":
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

        

