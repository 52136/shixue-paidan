import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

ADMIN_PASSWORD = "admin123"
TASKS_FILE = "tasks.xlsx"

def init_files():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=["派单员", "送心数量", "团抽金额", "提交时间"])
        df.to_excel(TASKS_FILE, index=False)

init_files()

def load_tasks():
    return pd.read_excel(TASKS_FILE)

def save_tasks(df):
    df.to_excel(TASKS_FILE, index=False)

def format_name(name):
    name = name.strip()
    if not name.startswith("莳雪_"):
        return f"莳雪_{name}"
    return name

st.set_page_config(page_title="莳雪代肝派单", layout="centered")
st.title("🌸 莳雪代肝派单")

menu = st.sidebar.radio("选择功能", ["📝 提交记录", "📊 管理员统计"])

# ========== 提交记录 ==========
if menu == "📝 提交记录":
    st.subheader("📝 派单员提交记录")
    with st.form("submit_form"):
        paidan_ren = st.text_input("派单员（你的名字）")
        heart_qty = st.number_input("送心数量（❤️）", min_value=1, step=1)
        amount = st.number_input("团抽金额（元）", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("✅ 提交")

        if submitted:
            if paidan_ren.strip() == "":
                st.error("请填写派单员姓名")
            elif heart_qty <= 0:
                st.error("送心数量必须大于0")
            else:
                paidan_ren = format_name(paidan_ren.strip())
                df = load_tasks()
                new_row = pd.DataFrame({
                    "派单员": [paidan_ren],
                    "送心数量": [heart_qty],
                    "团抽金额": [amount],
                    "提交时间": [datetime.now().strftime("%Y-%m-%d %H:%M")]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                save_tasks(df)
                st.success(f"✅ {paidan_ren} 提交成功！❤️{heart_qty}，团抽金额¥{amount}")

# ========== 管理员统计 ==========
elif menu == "📊 管理员统计":
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
    df = load_tasks()

    if df.empty:
        st.info("暂无数据")
    else:
        # 按派单员汇总
        summary = df.groupby("派单员").agg(
            总送心数量=("送心数量", "sum"),
            总团抽金额=("团抽金额", "sum"),
            提交次数=("送心数量", "count")
        ).reset_index()
        # 按团抽金额从高到低排名
        summary = summary.sort_values("总团抽金额", ascending=False)
        summary.insert(0, "排名", range(1, len(summary) + 1))

        st.subheader("📋 派单员业绩排名（按团抽金额）")
        st.dataframe(summary, use_container_width=True)

        # 全团总计
        total_hearts = df["送心数量"].sum()
        total_amount = df["团抽金额"].sum()
        col1, col2 = st.columns(2)
        col1.metric("全团总送心数", f"{total_hearts} ❤️")
        col2.metric("全团总团抽金额", f"¥{total_amount:.2f}")

        # 任务明细
        st.subheader("📋 所有记录明细")
        st.dataframe(df, use_container_width=True)

        # 删除功能（仅管理员）
        st.subheader("🗑️ 删除记录")
        delete_option = st.radio("选择删除方式", ["删除全部记录", "按派单员删除"])

        if delete_option == "删除全部记录":
            if st.button("⚠️ 确认删除全部数据"):
                df_empty = pd.DataFrame(columns=["派单员", "送心数量", "团抽金额", "提交时间"])
                save_tasks(df_empty)
                st.success("✅ 全部记录已删除")
                st.rerun()
        else:
            paidan_list = df["派单员"].unique().tolist()
            if paidan_list:
                selected = st.selectbox("选择要删除的派单员", paidan_list)
                if st.button(f"⚠️ 确认删除 {selected} 的所有记录"):
                    df = df[df["派单员"] != selected]
                    save_tasks(df)
                    st.success(f"✅ {selected} 的所有记录已删除")
                    st.rerun()
            else:
                st.info("暂无数据")
