import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ---------- 配置 ----------
# ⚠️ 把下面的地址换成你从 Supabase 复制的 "Connection string"！
DB_URL = "postgresql://postgres.xxxx:你的密码@aws-0-xxx.pooler.supabase.com:5432/postgres"
ADMIN_PASSWORD = "admin123"

# ---------- 连接数据库 ----------
@st.cache_resource
def init_engine():
    return create_engine(DB_URL)

engine = init_engine()

# ---------- 页面标题 ----------
st.set_page_config(page_title="莳雪派单系统", layout="centered")
st.title("🌸 莳雪代肝派单")

# ---------- 侧边栏选择功能 ----------
option = st.sidebar.radio("选择功能", ["📝 员工填单", "📊 管理员统计"])

# ========== 员工填单页 ==========
if option == "📝 员工填单":
    st.subheader("📝 提交新单")
    with st.form("submit_form"):
        employee = st.text_input("派单员（请填写完整昵称）")
        quantity = st.number_input("送心数量（❤️）", min_value=1, step=1)
        amount = st.number_input("金额（元）", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("✅ 提交")

        if submitted:
            if employee.strip() == "":
                st.error("请填写派单员姓名")
            else:
                with engine.connect() as conn:
                    conn.execute(
                        text(f"INSERT INTO orders (\"派单员\", \"送心数量\", \"金额\", \"提交时间\") VALUES ('{employee.strip()}', {quantity}, {amount}, '{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}')")
                    )
                    conn.commit()
                st.success(f"✅ {employee} 的单子已提交！❤️{quantity}，¥{amount}")

# ========== 管理员统计页 ==========
elif option == "📊 管理员统计":
    # ---------- 密码验证 ----------
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        pwd = st.text_input("请输入管理员密码", type="password")
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.success("验证通过")
            st.rerun()
        else:
            st.warning("请输入正确密码")
            st.stop()

    # ---------- 读取数据 ----------
    df = pd.read_sql("SELECT * FROM orders", engine)

    if df.empty:
        st.info("暂无数据，快去填单吧")
    else:
        summary = df.groupby("派单员").agg(
            总数量=("送心数量", "sum"),
            总金额=("金额", "sum"),
            订单数=("送心数量", "count")
        ).reset_index()
        summary = summary.sort_values("总数量", ascending=False)

        st.subheader("📊 全团统计报表")
        st.dataframe(summary, use_container_width=True)

        st.subheader("🏆 本月之星")
        for idx, row in summary.iterrows():
            st.write(f"**{row['派单员']}**：❤️{row['总数量']} 颗，¥{row['总金额']}，共 {row['订单数']} 单")

        with st.expander("查看所有明细"):
            st.dataframe(df, use_container_width=True)

    # ---------- 🗑️ 删除功能（带确认弹窗） ----------
    st.subheader("🗑️ 删除记录")
    delete_option = st.radio("选择删除方式", ["删除全部记录", "按派单员删除"])

    with engine.connect() as conn:
        if delete_option == "删除全部记录":
            with st.popover("⚠️ 确认删除全部数据"):
                st.warning("确定要删除全部数据吗？此操作不可恢复！")
                col1, col2 = st.columns(2)
                if col1.button("✅ 确定删除", type="primary"):
                    conn.execute(text("DELETE FROM orders;"))
                    conn.commit()
                    st.success("✅ 全部记录已删除")
                    st.rerun()
                if col2.button("❌ 取消"):
                    st.info("已取消操作")
                    st.rerun()
        else:
            df_check = pd.read_sql("SELECT DISTINCT \"派单员\" FROM orders", engine)
            if not df_check.empty:
                employees = df_check["派单员"].tolist()
                selected = st.selectbox("选择要删除的派单员", employees)
                with st.popover(f"⚠️ 确认删除 {selected} 的所有记录"):
                    st.warning(f"确定要删除 **{selected}** 的所有记录吗？此操作不可恢复！")
                    col1, col2 = st.columns(2)
                    if col1.button("✅ 确定删除", type="primary"):
                        conn.execute(text(f"DELETE FROM orders WHERE \"派单员\" = '{selected}';"))
                        conn.commit()
                        st.success(f"✅ {selected} 的所有记录已删除")
                        st.rerun()
                    if col2.button("❌ 取消"):
                        st.info("已取消操作")
                        st.rerun()
            else:
                st.info("暂无数据")