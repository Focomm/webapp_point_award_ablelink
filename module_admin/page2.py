import streamlit as st
import streamlit_shadcn_ui as ui
from db import get_connection_app
import pandas as pd
import bcrypt


def admin_page2():
    st.title("👤 จัดการผู้ใช้งาน")

    action = ["เพิ่มผู้ใช้", "แก้ไขผู้ใช้", "ลบผู้ใช้"]
    
    
    st.sidebar.header("🔎 ตัวกรองข้อมูล")
    selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)

    st.markdown("---")

    if selected_dept == "เพิ่มผู้ใช้":
        st.subheader("เพิ่มผู้ใช้ใหม่")
        try:
            conn = get_connection_app()
            cur = conn.cursor()

            # ดึงข้อมูลแผนกสำหรับ dropdown
            dept_df = pd.read_sql("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name", conn)
            dept_options = dict(zip(dept_df['dept_name'], dept_df['id']))
            dept_selected = st.selectbox("แผนก", list(dept_options.keys()))
            dept_id = dept_options[dept_selected]

            # ฟอร์มกรอกข้อมูล
            user_id = st.text_input("User ID", key="user_id")
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("รหัสผ่าน", type="password", key="password")
            with col2:
                confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password", key="confirm_password")

            full_name = st.text_input("ชื่อ-นามสกุล", key="full_name")
            nickname = st.text_input("ชื่อเล่น", key="nickname")
            email = st.text_input("Email (ไม่จำเป็น)", placeholder="someone@example.com", key="email")
            phone = st.text_input("เบอร์โทร (ไม่จำเป็น)", key="phone")
            role = st.selectbox("บทบบาท", ["user", "admin"], key="role")
            role_position = st.text_input("ตำแหน่ง (ถ้ามี)", key="role_position")

            submit = st.button("✅ เพิ่มผู้ใช้")

            if submit:
                if not user_id or not full_name or not nickname:
                    st.warning("⚠️ กรุณากรอก user_id, ชื่อ-นามสกุล และชื่อเล่น")
                    return
                if not password or not confirm_password:
                    st.warning("⚠️ กรุณากรอกรหัสผ่านให้ครบ")
                    return
                if password != confirm_password:
                    st.warning("⚠️ รหัสผ่านไม่ตรงกัน")
                    return
                try:
                    # ตรวจสอบว่า user_id ซ้ำหรือไม่
                    cur.execute("SELECT 1 FROM kpigoalpoint.users WHERE user_id = %s", (user_id,))
                    if cur.fetchone():
                        st.warning("⚠️ User ID นี้มีอยู่แล้ว กรุณาใช้รหัสอื่น")
                        return
                    # เพิ่ม user
                    cur.execute("""
                        INSERT INTO kpigoalpoint.users (
                            user_id, full_name, nickname, email,
                            phone_number, role_onweb, role_position, dept_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, full_name, nickname, email or None,
                        phone or None, role, role_position or None, dept_id
                    ))
                    # hash password และเพิ่ม auth_credentials
                    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

                    cur.execute("""
                        INSERT INTO kpigoalpoint.auth_credentials (
                            user_id, hashed_password
                        ) VALUES (%s, %s)
                    """, (user_id, hashed_pw))
                    # เพิ่มค่าเริ่มต้น 0 ให้ personal_points
                    cur.execute("""
                        INSERT INTO kpigoalpoint.personal_points (
                            user_ref_id, point_value
                        ) VALUES (%s, %s)
                    """, (user_id, 0))
                    conn.commit()
                    st.success(f"✅ เพิ่มผู้ใช้ {user_id} และตั้งรหัสผ่านเรียบร้อยแล้ว")
                    # ล้างค่าใน session state
                    # st.session_state["user_id"] = ""
                    # st.session_state["full_name"] = ""
                    # st.session_state["nickname"] = ""
                    # st.session_state["email"] = ""
                    # st.session_state["phone"] = ""
                    # st.session_state["role_position"] = ""
                    # st.session_state["password"] = ""
                    # st.session_state["confirm_password"] = ""

                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ เกิดข้อผลพลาด: {e}")

        except Exception as e:
            st.error(f"❌ โหลดข้อมูลแผนกล้มเหว: {e}")


    elif selected_dept == "แก้ไขผู้ใช้":
        st.subheader("✏️ แก้ไขข้อมูลผู้ใช้")

        try:
            conn = get_connection_app()
            cur = conn.cursor()

            # ดึงรายชื่อ user ทั้งหมด
            user_df = pd.read_sql("SELECT user_id, full_name, nickname FROM kpigoalpoint.users ORDER BY full_name", conn)

            if user_df.empty:
                st.info("ยังไม่มีผู้ใช้ในระบบ")
            else:
                user_map = {
                    f"{row['full_name']} ({row['nickname']})": row['user_id']
                    for _, row in user_df.iterrows()
                }

                selected_display = st.selectbox("เลือกผู้ใช้ที่ต้องการแก้ไข", list(user_map.keys()))
                selected_user_id = user_map[selected_display]

                # ดึงข้อมูลผู้ใช้ที่เลือก
                cur.execute("""
                    SELECT full_name, nickname, email, phone_number, role_onweb, role_position, dept_id
                    FROM kpigoalpoint.users
                    WHERE user_id = %s
                """, (selected_user_id,))
                row = cur.fetchone()

                if row:
                    # ดึงข้อมูลแผนก
                    dept_df = pd.read_sql("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name", conn)
                    dept_options = dict(zip(dept_df['dept_name'], dept_df['id']))
                    dept_name_reverse = {v: k for k, v in dept_options.items()}

                    # ฟอร์มแก้ไข
                    full_name = st.text_input("ชื่อ-นามสกุล", value=row[0])
                    nickname = st.text_input("ชื่อเล่น", value=row[1])
                    email = st.text_input("Email", value=row[2] or "")
                    phone = st.text_input("เบอร์โทร", value=row[3] or "")
                    role = st.selectbox("บทบาท", ["user", "admin"], index=["user", "admin"].index(row[4]))
                    role_position = st.text_input("ตำแหน่ง (ถ้ามี)", value=row[5] or "")
                    dept_selected = st.selectbox("แผนก", list(dept_options.keys()), index=list(dept_options.values()).index(row[6]))
                    dept_id = dept_options[dept_selected]

                    if st.button("💾 บันทึกการเปลี่ยนแปลง"):
                        try:
                            cur.execute("""
                                UPDATE kpigoalpoint.users
                                SET full_name = %s,
                                    nickname = %s,
                                    email = %s,
                                    phone_number = %s,
                                    role_onweb = %s,
                                    role_position = %s,
                                    dept_id = %s,
                                    updated_at = NOW()
                                WHERE user_id = %s
                            """, (
                                full_name, nickname, email or None, phone or None,
                                role, role_position or None, dept_id, selected_user_id
                            ))
                            conn.commit()
                            st.success(f"✅ บันทึกการแก้ไขของ {selected_display} เรียบร้อยแล้ว")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ แก้ไขไม่สำเร็จ: {e}")
        except Exception as e:
            st.error(f"❌ โหลดข้อมูลผู้ใช้ล้มเหลว: {e}")


    elif selected_dept == "ลบผู้ใช้":
        st.subheader("🗑️ ลบผู้ใช้")
        try:
            conn = get_connection_app()
            cur = conn.cursor()
            # ดึงรายชื่อ user ทั้งหมด
            user_df = pd.read_sql("SELECT user_id, full_name, nickname FROM kpigoalpoint.users ORDER BY full_name", conn)
            if user_df.empty:
                st.info("ยังไม่มีผู้ใช้ในระบบ")
            else:
                # dropdown แสดงชื่อ
                user_map = {
                    f"{row['full_name']} ({row['nickname']})": row['user_id']
                    for _, row in user_df.iterrows()
                }
                selected_display = st.selectbox("เลือกผู้ใช้ที่ต้องการลบ", list(user_map.keys()))
                selected_user_id = user_map[selected_display]

                # ตรวจสอบว่ามีคะแนนที่มากกว่า 0 หรือไม่
                cur.execute("""
                    SELECT COALESCE(SUM(point_value), 0)
                    FROM kpigoalpoint.personal_points
                    WHERE user_ref_id = %s
                """, (selected_user_id,))
                point_total = cur.fetchone()[0]

                if point_total > 0:
                    st.warning("⚠️ ไม่สามารถลบผู้ใช้นี้ได้ เพราะมีข้อมูลคะแนนอยู่ในระบบ")
                else:
                    # Confirm 2 ขั้นตอน
                    confirm_1 = st.checkbox(f"คุณแน่ใจหรือไม่ว่าจะลบ '{selected_display}'?", key="confirm1")
                    submit = st.button("✅ ยืนยันการลบ", key="delete_user")

                    if submit:
                        if confirm_1:
                            try:
                                # ลบข้อมูลใน auth_credentials (ต้องลบก่อน เพราะมี foreign key)
                                cur.execute("DELETE FROM kpigoalpoint.auth_credentials WHERE user_id = %s", (selected_user_id,))
                                # ลบข้อมูลใน personal_points (กรณีมี point_value = 0 ก็ต้องลบ)
                                cur.execute("DELETE FROM kpigoalpoint.personal_points WHERE user_ref_id = %s", (selected_user_id,))
                                # ลบข้อมูลใน users
                                cur.execute("DELETE FROM kpigoalpoint.users WHERE user_id = %s", (selected_user_id,))
                                conn.commit()
                                st.success(f"✅ ลบผู้ใช้ {selected_display} เรียบร้อยแล้ว")
                            except Exception as e:
                                conn.rollback()
                                st.error(f"❌ ลบไม่สำเร็จ: {e}")
                        else:
                            st.warning("สติจ้า กรุณายืนยันการลบก่อน")
                    
        except Exception as e:
            st.error(f"❌ โหลดรายชื่อผู้ใช้ล้มเหลว: {e}")
