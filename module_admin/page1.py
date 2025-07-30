import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
from db import get_connection_readonly


def admin_page1():
    st.title(f"🛠️ Hello Admin")
    try:
        conn = get_connection_readonly()

        # ดึงข้อมูล users + departments
        users_df = pd.read_sql("""
            SELECT u.user_id, u.full_name, u.nickname, u.dept_id,
                   d.id AS dept_real_id, d.dept_name, d.point_dpmt
            FROM kpigoalpoint.users u
            JOIN kpigoalpoint.departments d ON u.dept_id = d.id
        """, conn)

        # ดึงข้อมูลคะแนนจาก personal_points
        points_df = pd.read_sql("""
            SELECT user_ref_id, SUM(point_value)::int AS point_value
            FROM kpigoalpoint.personal_points
            GROUP BY user_ref_id
        """, conn)

        # JOIN รวมคะแนนเข้ากับ users
        df = users_df.merge(points_df, left_on='user_id', right_on='user_ref_id', how='left')
        df['point_value'] = df['point_value'].fillna(0).astype(int)

        # ตัวเลือก dropdown
        all_depts = ['ทั้งหมด'] + sorted(df['dept_name'].unique().tolist())
        all_nicks = ['ทั้งหมด'] + sorted(df['nickname'].unique().tolist())

        # Sidebar filter
        st.sidebar.header("🔎 ตัวกรองข้อมูล")
        selected_dept = st.sidebar.selectbox("เลือกแผนก", all_depts)
        selected_nick = st.sidebar.selectbox("เลือกพนักงาน", all_nicks)

        filtered_df = df.copy()

        # กรองตามพนักงานก่อน (ถ้าเลือก)
        if selected_nick != 'ทั้งหมด':
            filtered_df = filtered_df[filtered_df['nickname'] == selected_nick]
            # auto sync แผนกด้วย
            selected_dept = filtered_df['dept_name'].iloc[0] if not filtered_df.empty else selected_dept

        # กรองตามแผนก (ถ้าเลือก)
        if selected_dept != 'ทั้งหมด':
            filtered_df = filtered_df[filtered_df['dept_name'] == selected_dept]

        # รวมคะแนน
        total_point = filtered_df['point_value'].sum()
        total_dpmt = filtered_df['point_dpmt'].iloc[0] if not filtered_df.empty else 0

        # แสดงผล
        st.markdown("### คะแนนรวม")
        col1, col2 = st.columns(2)
        
        
        with col1:
            ui.metric_card(title="Personal Point", content=int(total_point), description="test", key="card1")
        with col2:
            ui.metric_card(title="Team Point", content=int(total_dpmt), description="test", key="card2")

        st.markdown("### 👥 รายชื่อพนักงาน")
        st.dataframe(
            filtered_df[['full_name', 'nickname', 'dept_name', 'point_value']],
            use_container_width=True
        )

    except Exception as e:
        st.error(f"❌ โหลดข้อมูลล้มเหลว: {e}")
