import streamlit as st
import pandas as pd
import os

# ---------- 配置 ----------
EXCEL_FILE = "paiDan_data.xlsx"
ADMIN_PASSWORD = "admin123"

# ---------- 初始化数据文件 ----------
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["派单员", "送心数量", "金额", "提交时间"])
    df.to_excel(EXCEL_FILE, index=False)

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
            elif quantity > 0 and amount >= 0:
                new_row = pd.DataFrame({
                    "派单员": [employee.strip()],
                    "送心数量": [quantity],
                    "金额": [amount],
                    "提交时间": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")]
                })
                existing = pd.read_excel(EXCEL_FILE)
                updated = pd.concat([existing, new_row], ignore_index=True)
                updated.to_excel(EXCEL_FILE, index=False)
                st.success(f"✅ {employee} 的单子已提交！❤️{quantity}，¥{amount}")
            else:
                st.error("数量和金额必须大于0")

# ========== 管理员统计页 ==========
elif option == "📊 管理员统计":
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
    
    st.subheader("📊 全团统计报表")
    df = pd.read_excel(EXCEL_FILE)
    
    if df.empty:
        st.info("暂无数据，快去填单吧")
    else:
        summary = df.groupby("派单员").agg(
            总数量=("送心数量", "sum"),
            总金额=("金额", "sum"),
            订单数=("送心数量", "count")
        ).reset_index()
        summary = summary.sort_values("总数量", ascending=False)
        
        st.dataframe(summary, use_container_width=True)
        
        st.subheader("🏆 本月之星")
        for idx, row in summary.iterrows():
            st.write(f"**{row['派单员']}**：❤️{row['总数量']} 颗，¥{row['总金额']}，共 {row['订单数']} 单")
        
        with st.expander("查看所有明细"):
            st.dataframe(df, use_container_width=True)