import streamlit as st
import streamlit_shadcn_ui as ui
from db import get_connection_app
from sqlalchemy import text
import pandas as pd
import bcrypt

def admin_page2():
    st.title("👤 จัดการผู้ใช้งาน")

    action = ["เพิ่มผู้ใช้", "แก้ไขผู้ใช้", "ลบผู้ใช้"]
    st.sidebar.header("การดำเนินการ")
    selected_dept = st.sidebar.selectbox("เลือกการจัดการ", action)
    st.markdown("---")

    conn = get_connection_app()

    if selected_dept == "เพิ่มผู้ใช้":
        st.subheader("เพิ่มผู้ใช้ใหม่")
        try:
            dept_df = pd.read_sql(text("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name"), conn)
            dept_options = dict(zip(dept_df['dept_name'], dept_df['id']))
            dept_selected = st.selectbox("เลือกแผนก", list(dept_options.keys()))
            dept_id = dept_options[dept_selected]
            st.write('------')

            user_id = st.text_input("User ID")
            col1, col2 = st.columns(2)
            with col1:
                password = st.text_input("รหัสผ่าน", type="password")
            with col2:
                confirm_password = st.text_input("ยืนยันรหัสผ่าน", type="password")

            full_name = st.text_input("ชื่อ-นามสกุล")
            nickname = st.text_input("ชื่อเล่น")
            email = st.text_input("Email (ไม่จำเป็น)", placeholder="someone@example.com")
            phone = st.text_input("เบอร์โทร (ไม่จำเป็น)")
            role = st.selectbox("บทบบาท", ["user", "admin"])
            role_position = st.text_input("ตำแหน่ง (ถ้ามี)")

            add_user_button = ui.button(
                text="เพิ่มผู้ใช้",
                key="add_user_button",
                variant="default"  # ทำให้ปุ่มเป็นสีแดง
            )

            if add_user_button:
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
                    # ตรวจสอบซ้ำ
                    result = conn.execute(text("SELECT 1 FROM kpigoalpoint.users WHERE user_id = :uid"), {"uid": user_id})
                    if result.first():
                        st.warning("⚠️ User ID นี้มีอยู่แล้ว กรุณาใช้รหัสอื่น")
                        return

                    # เริ่ม transaction
                    conn.execute(text("""
                        INSERT INTO kpigoalpoint.users (
                            user_id, full_name, nickname, email,
                            phone_number, role_onweb, role_position, dept_id
                        ) VALUES (
                            :user_id, :full_name, :nickname, :email,
                            :phone, :role, :role_position, :dept_id
                        )
                    """), {
                        "user_id": user_id,
                        "full_name": full_name,
                        "nickname": nickname,
                        "email": email or None,
                        "phone": phone or None,
                        "role": role,
                        "role_position": role_position or None,
                        "dept_id": dept_id
                    })

                    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                    conn.execute(text("""
                        INSERT INTO kpigoalpoint.auth_credentials (user_id, hashed_password)
                        VALUES (:uid, :hashed)
                    """), {"uid": user_id, "hashed": hashed_pw})

                    conn.execute(text("""
                        INSERT INTO kpigoalpoint.personal_points (user_ref_id, point_value)
                        VALUES (:uid, 0)
                    """), {"uid": user_id})

                    conn.commit()
                    st.success(f"✅ เพิ่มผู้ใช้ {user_id} และตั้งรหัสผ่านเรียบร้อยแล้ว")

                except Exception as e:
                    conn.rollback()
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")

        except Exception as e:
            st.error(f"❌ โหลดข้อมูลแผนกล้มเหลว: {e}")

    elif selected_dept == "แก้ไขผู้ใช้":
        st.subheader("✏️ แก้ไขข้อมูลผู้ใช้")
        try:
            user_df = pd.read_sql(text("SELECT user_id, full_name, nickname FROM kpigoalpoint.users ORDER BY full_name"), conn)

            if user_df.empty:
                st.info("ยังไม่มีผู้ใช้ในระบบ")
                return        
            user_map = {f"{row['full_name']} ({row['nickname']})": row['user_id'] for _, row in user_df.iterrows()}
            selected_display = st.selectbox("เลือกผู้ใช้ที่ต้องการแก้ไข", list(user_map.keys()))
            selected_user_id = user_map[selected_display]

            result = conn.execute(text("""
                SELECT full_name, nickname, email, phone_number, role_onweb, role_position, dept_id
                FROM kpigoalpoint.users WHERE user_id = :uid
            """), {"uid": selected_user_id})
            row = result.fetchone()

            if row:
                dept_df = pd.read_sql(text("SELECT id, dept_name FROM kpigoalpoint.departments ORDER BY dept_name"), conn)
                dept_options = dict(zip(dept_df['dept_name'], dept_df['id']))
                
                st.write('------')

                full_name = st.text_input("ชื่อ-นามสกุล", value=row[0])
                nickname = st.text_input("ชื่อเล่น", value=row[1])
                email = st.text_input("Email", value=row[2] or "")
                phone = st.text_input("เบอร์โทร", value=row[3] or "")
                role = st.selectbox("บทบาท", ["user", "admin"], index=["user", "admin"].index(row[4]))
                role_position = st.text_input("ตำแหน่ง (ถ้ามี)", value=row[5] or "")
                dept_selected = st.selectbox("แผนก", list(dept_options.keys()), index=list(dept_options.values()).index(row[6]))
                dept_id = dept_options[dept_selected]

                save_edit = ui.button(
                    text="บันทึกการเปลี่ยนแปลง",
                    key="save_edit",
                    variant="default"  # ทำให้ปุ่มเป็นสีแดง
                )

                if save_edit:
                    try:
                        conn.execute(text("""
                            UPDATE kpigoalpoint.users SET
                                full_name = :fn,
                                nickname = :nn,
                                email = :em,
                                phone_number = :ph,
                                role_onweb = :ro,
                                role_position = :rp,
                                dept_id = :dp,
                                updated_at = NOW()
                            WHERE user_id = :uid
                        """), {
                            "fn": full_name, "nn": nickname, "em": email or None,
                            "ph": phone or None, "ro": role, "rp": role_position or None,
                            "dp": dept_id, "uid": selected_user_id
                        })
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
            user_df = pd.read_sql(text("SELECT user_id, full_name, nickname FROM kpigoalpoint.users ORDER BY full_name"), conn)

            if user_df.empty:
                st.info("ยังไม่มีผู้ใช้ในระบบ")
                return

            user_map = {f"{row['full_name']} ({row['nickname']})": row['user_id'] for _, row in user_df.iterrows()}
            selected_display = st.selectbox("เลือกผู้ใช้ที่ต้องการลบ", list(user_map.keys()))
            selected_user_id = user_map[selected_display]

            result = conn.execute(text("""
                SELECT COALESCE(SUM(point_value), 0) AS total
                FROM kpigoalpoint.personal_points
                WHERE user_ref_id = :uid
            """), {"uid": selected_user_id})
            point_total = result.scalar()

            if point_total > 0:
                st.warning("⚠️ ไม่สามารถลบผู้ใช้นี้ได้ เพราะมีข้อมูลคะแนนอยู่ในระบบ")
            else:
                confirm_1 = st.checkbox(f"คุณแน่ใจหรือไม่ว่าจะลบ '{selected_display}'?", key="confirm1")

                confirm_delete = ui.button("ยืนยันการลบ", key="delete_user", variant="destructive")

                if confirm_delete:
                    if confirm_1:
                        try:
                            conn.execute(text("DELETE FROM kpigoalpoint.auth_credentials WHERE user_id = :uid"), {"uid": selected_user_id})
                            conn.execute(text("DELETE FROM kpigoalpoint.personal_points WHERE user_ref_id = :uid"), {"uid": selected_user_id})
                            conn.execute(text("DELETE FROM kpigoalpoint.users WHERE user_id = :uid"), {"uid": selected_user_id})
                            conn.commit()
                            st.success(f"✅ ลบผู้ใช้ {selected_display} เรียบร้อยแล้ว")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"❌ ลบไม่สำเร็จ: {e}")
                    elif not confirm_1:
                        st.warning("สติจ้า กรุณายืนยันการลบก่อน")
        except Exception as e:
            st.error(f"❌ โหลดรายชื่อผู้ใช้ล้มเหลว: {e}")
