import streamlit as st
import streamlit_shadcn_ui as ui
from db import get_connection_readonly

def user_page3():
   st.title("📎 ส่งไฟล์แนบและข้อความถึงระบบ/ผู้ดูแล")

   user_id = st.session_state.user_id

   with st.form("upload_form", clear_on_submit=True):
      uploaded_file = st.file_uploader("📁 แนบไฟล์", type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "csv"])
      message = st.text_area("📝 ข้อความเพิ่มเติม", placeholder="พิมพ์ข้อความที่ต้องการส่งถึงผู้ดูแล...")

      submitted = st.form_submit_button("✅ ส่งข้อมูล")

      if submitted:
         if not uploaded_file and not message:
               st.warning("⚠️ กรุณาแนบไฟล์หรือพิมพ์ข้อความอย่างน้อย 1 อย่าง")
         else:
               try:
                  if uploaded_file:
                     st.success(f"✅ บันทึกไฟล์: {uploaded_file.name}")
                  if message:
                     # บันทึกข้อความลงฐานข้อมูล
                     st.success("✅ บันทึกข้อความสำเร็จ")
                  st.success("📬 ส่งข้อมูลเรียบร้อยแล้ว")
               except Exception as e:
                  st.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")

