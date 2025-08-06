import streamlit as st
import streamlit_shadcn_ui as ui
import os
import pandas as pd

from datetime import datetime
from sqlalchemy import create_engine, text
from db import get_connection_app


def user_page3():

   user_id = st.session_state.user_id

   action = ["ขอ Point ส่วนตัว", "ขอ Point ทีม", "ประวัติขอการ Point"]
   st.sidebar.header("🔎 ตัวกรองข้อมูล")
   select_option = st.sidebar.selectbox("เลือกการจัดการ", action)

   if select_option == "ขอ Point ส่วนตัว":
      st.title("📎 ส่งไฟล์แนบและข้อความถึงระบบ/ผู้ดูแล")

      conn_kpi = get_connection_app()
      kpi_query = text("""
         SELECT id, kpi_name
         FROM kpigoalpoint.kpi_personal
         WHERE user_ref_id = :user_id
      """)
      kpi_result = conn_kpi.execute(kpi_query, {"user_id": str(user_id)})
      kpi_list = kpi_result.fetchall()
      conn_kpi.close()

      if not kpi_list:
         st.warning("⚠️ ยังไม่มี KPI สำหรับบัญชีนี้ กรุณาเพิ่ม KPI ก่อนส่งคำขอ")
         selected_kpi_id = None
      else:
         kpi_dict = {f"{row.kpi_name} (ID: {row.id})": row.id for row in kpi_list}
         selected_kpi_name = st.selectbox("🎯 เลือก KPI ที่เกี่ยวข้อง", list(kpi_dict.keys()))
         selected_kpi_id = kpi_dict[selected_kpi_name]
         
         st.write('------')

         with st.form("upload_form", clear_on_submit=True):
            uploaded_file = st.file_uploader("📁 แนบไฟล์", type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "csv"])
            message = st.text_area("📝 ข้อความเพิ่มเติม", placeholder="พิมพ์ข้อความที่ต้องการส่งถึงผู้ดูแล...")
            status = "onprocess"
            submitted = st.form_submit_button("✅ ส่งข้อมูล")

         if submitted:
            if not uploaded_file and not message:
                  st.warning("⚠️ กรุณาแนบไฟล์หรือพิมพ์ข้อความอย่างน้อย 1 อย่าง")
                  st.stop()

            try:
                  now = datetime.now()
                  year = str(now.year)
                  month = str(now.month).zfill(2)

                  if uploaded_file:
                     original_name = uploaded_file.name
                     file_type = uploaded_file.type
                     relative_path = f"uploads/personal/examine/{year}/{month}"
                  else:
                     original_name = None
                     file_type = None
                     relative_path = None

                  conn = get_connection_app()
                  with conn.begin():
                     result = conn.execute(text("""
                        INSERT INTO kpigoalpoint.file_messages_personal (
                              user_ref_id, original_name, file_type, path, message, status, kpi_id
                        ) VALUES (
                              :user_ref_id, :original_name, :file_type, :path, :message, :status, :kpi_id
                        ) RETURNING id
                     """), {
                        "user_ref_id": str(user_id),
                        "original_name": original_name,
                        "file_type": file_type,
                        "path": relative_path,
                        "message": message,
                        "status": status,
                        "kpi_id": selected_kpi_id
                     })

                     inserted_id = result.scalar()
                     new_name = str(inserted_id)

                     if uploaded_file:
                        save_dir = os.path.join("uploads", "personal", "examine", year, month)
                        os.makedirs(save_dir, exist_ok=True)

                        file_ext = os.path.splitext(original_name)[-1]
                        full_filename = new_name + file_ext
                        save_path = os.path.join(save_dir, full_filename)

                        with open(save_path, "wb") as f:
                              f.write(uploaded_file.read())

                        conn.execute(text("""
                              UPDATE kpigoalpoint.file_messages_personal
                              SET new_name = :new_name
                              WHERE id = :id
                        """), {
                              "new_name": full_filename,
                              "id": inserted_id
                        })

                  conn.close()

                  if uploaded_file:
                     st.success(f"✅ บันทึกไฟล์: {original_name} → สำเร็จ")
                  if message:
                     st.success("✅ บันทึกข้อความสำเร็จ")
                  st.success("📬 ส่งข้อมูลเรียบร้อยแล้ว")

            except Exception as e:
                  st.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")


   elif select_option == "ขอ Point ทีม":
      st.title("📎 ส่งไฟล์แนบและข้อความถึงระบบ/ผู้ดูแล (ทีม)")

      conn = get_connection_app()
      dept_query = text("""
         SELECT dept_id FROM kpigoalpoint.users WHERE user_id = :user_id
      """)
      dept_result = conn.execute(dept_query, {"user_id": str(user_id)}).fetchone()
      conn.close()

      if not dept_result:
         st.error("❌ ไม่พบข้อมูลแผนกของผู้ใช้")
         st.stop()

      dept_ref_id = dept_result.dept_id

      conn_kpi = get_connection_app()
      kpi_query = text("""
         SELECT id, kpi_name
         FROM kpigoalpoint.kpi_team
         WHERE dept_ref_id = :dept_ref_id
      """)
      kpi_result = conn_kpi.execute(kpi_query, {"dept_ref_id": str(dept_ref_id)})
      kpi_list = kpi_result.fetchall()
      conn_kpi.close()

      if not kpi_list:
         st.warning("⚠️ ยังไม่มี KPI สำหรับทีมนี้ กรุณาเพิ่ม KPI ก่อนส่งคำขอ")
         selected_kpi_id = None
      else:
         kpi_dict = {f"{row.kpi_name} (ID: {row.id})": row.id for row in kpi_list}
         selected_kpi_name = st.selectbox("🎯 เลือก KPI ทีมที่เกี่ยวข้อง", list(kpi_dict.keys()))
         selected_kpi_id = kpi_dict[selected_kpi_name]

         st.write('------')

         with st.form("upload_form_team", clear_on_submit=True):
            uploaded_file = st.file_uploader("📁 แนบไฟล์", type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "csv"])
            message = st.text_area("📝 ข้อความเพิ่มเติม", placeholder="พิมพ์ข้อความที่ต้องการส่งถึงผู้ดูแล...")
            status = "onprocess"
            submitted = st.form_submit_button("✅ ส่งข้อมูล")

         if submitted:
            if not uploaded_file and not message:
                  st.warning("⚠️ กรุณาแนบไฟล์หรือพิมพ์ข้อความอย่างน้อย 1 อย่าง")
                  st.stop()

            try:
                  now = datetime.now()
                  year = str(now.year)
                  month = str(now.month).zfill(2)

                  if uploaded_file:
                     original_name = uploaded_file.name
                     file_type = uploaded_file.type
                     relative_path = f"uploads/team/examine/{year}/{month}"
                  else:
                     original_name = None
                     file_type = None
                     relative_path = None

                  conn = get_connection_app()
                  with conn.begin():
                     result = conn.execute(text("""
                        INSERT INTO kpigoalpoint.file_messages_team (
                              dept_ref_id, original_name, file_type, path, message, status, kpi_id
                        ) VALUES (
                              :dept_ref_id, :original_name, :file_type, :path, :message, :status, :kpi_id
                        ) RETURNING id
                     """), {
                        "dept_ref_id": str(dept_ref_id),
                        "original_name": original_name,
                        "file_type": file_type,
                        "path": relative_path,
                        "message": message,
                        "status": status,
                        "kpi_id": selected_kpi_id
                     })

                     inserted_id = result.scalar()
                     new_name = str(inserted_id)

                     if uploaded_file:
                        save_dir = os.path.join("uploads", "team", "examine", year, month)
                        os.makedirs(save_dir, exist_ok=True)

                        file_ext = os.path.splitext(original_name)[-1]
                        full_filename = new_name + file_ext
                        save_path = os.path.join(save_dir, full_filename)

                        with open(save_path, "wb") as f:
                              f.write(uploaded_file.read())

                        conn.execute(text("""
                              UPDATE kpigoalpoint.file_messages_team
                              SET new_name = :new_name
                              WHERE id = :id
                        """), {
                              "new_name": full_filename,
                              "id": inserted_id
                        })

                  conn.close()

                  if uploaded_file:
                     st.success(f"✅ บันทึกไฟล์: {original_name} → สำเร็จ")
                  if message:
                     st.success("✅ บันทึกข้อความสำเร็จ")
                  st.success("📬 ส่งข้อมูลเรียบร้อยแล้ว")

            except Exception as e:
                  st.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")


   elif select_option == "ประวัติขอการ Point":
      st.title("📜 ประวัติการขอ Point")

      try:
         conn = get_connection_app()
         query = text("""
               SELECT 
                  fm.original_name, 
                  fm.message, 
                  fm.upload_time, 
                  fm.status,
                  kp.kpi_name
               FROM kpigoalpoint.file_messages_personal fm
               LEFT JOIN kpigoalpoint.kpi_personal kp ON fm.kpi_id = kp.id
               WHERE fm.user_ref_id = :user_id
               ORDER BY fm.upload_time DESC
         """)
         result = conn.execute(query, {"user_id": str(user_id)})
         df = pd.DataFrame(result.fetchall(), columns=["ไฟล์", "ข้อความ", "เวลา", "สถานะ", "KPI ร้องขอ"])

         if df.empty:
               st.info("🔍 ยังไม่มีรายการคำขอจากคุณ")
         else:
               st.dataframe(df, use_container_width=True)

         conn.close()

      except Exception as e:
         st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
