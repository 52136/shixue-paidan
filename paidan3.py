import streamlit as st
import pandas as pd
import os

# ---------- 配置 ----------
EXCEL_FILE = "paiDan_data.xlsx"
ADMIN_PASSWORD = "admin123"

# ---------- 自动修复数据文件 ----------
def init_data():
    cols = ["派单员", "送心数量", "金额", "提交时间"]
    if not os.path.exists(EXCEL_FILE):
        pd.DataFrame(columns=cols).to_excel(EXCEL_FILE, index=False)
    else:
        try:
            df = pd.read_excel(EXCEL_FILE)
            if not all(c in df.columns for c in cols):
                pd.DataFrame(columns=cols).to_excel(EXCEL_FILE, index=False)
        except:
            pd.DataFrame(columns=cols).to_excel(EXCEL_FILE, index=False)

init_data()

# ---------- 页面 ----------
st.set_page_config(page_title="莳雪派单系统", layout="centered")
st.title("🌸 莳雪代肝派单")

option = st.sidebar.radio("选择功能", ["📝 员工填单", "📊 管理员统计"])

# ========== 员工填单 ==========
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
                df = pd.read_excel(EXCEL_FILE)
                new_row = pd.DataFrame({
                    "派单员": [employee.strip()],
                    "送心数量": [quantity],
                    "金额": [amount],
                    "提交时间": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_excel(EXCEL_FILE, index=False)
                st.success(f"✅ {employee} 的单子已提交！❤️{quantity}，¥{amount}")

# ========== 管理员统计 ==========
elif option == "📊 管理员统计":
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if not st.session_state.auth:
        pwd = st.text_input("请输入管理员密码", type="password")
        if pwd == ADMIN_PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.warning("请输入正确密码")
            st.stop()

    df = pd.read_excel(EXCEL_FILE)
    df["送心数量"] = pd.to_numeric(df["送心数量"], errors="coerce").fillna(0).astype(int)
    df["金额"] = pd.to_numeric(df["金额"], errors="coerce").fillna(0)

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
        for _, row in summary.iterrows():
            st.write(f"**{row['派单员']}**：❤️{row['总数量']} 颗，¥{row['总金额']}，共 {row['订单数']} 单")

        with st.expander("查看所有明细"):
            st.dataframe(df, use_container_width=True)

    # ---------- 删除功能 ----------
    st.subheader("🗑️ 删除记录")
    delete_option = st.radio("选择删除方式", ["删除全部记录", "按派单员删除"])

    if delete_option == "删除全部记录":
        with st.popover("⚠️ 确认删除全部数据"):
            st.warning("此操作不可恢复！")
            if st.button("✅ 确定删除", type="primary"):
                pd.DataFrame(columns=["派单员", "送心数量", "金额", "提交时间"]).to_excel(EXCEL_FILE, index=False)
                st.success("✅ 全部记录已删除")
                st.rerun()
            if st.button("❌ 取消"):
                st.rerun()
    else:
        df = pd.read_excel(EXCEL_FILE)
        if not df.empty and "派单员" in df.columns:
            employees = df["派单员"].unique().tolist()
            selected = st.selectbox("选择要删除的派单员", employees)
            with st.popover(f"⚠️ 确认删除 {selected}"):
                st.warning(f"将删除 {selected} 的所有记录，不可恢复！")
                if st.button("✅ 确定删除", type="primary"):
                    df = df[df["派单员"] != selected]
                    df.to_excel(EXCEL_FILE, index=False)
                    st.success(f"✅ {selected} 的所有记录已删除")
                    st.rerun()
                if st.button("❌ 取消"):
                    st.rerun()
        else:
            st.info("暂无数据")