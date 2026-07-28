import streamlit as st
import pandas as pd
import os
import time
import shutil
from datetime import datetime

ADMIN_PASSWORD = "admin123"
TASKS_FILE = "tasks.xlsx"
CLAIMS_FILE = "claims.xlsx"

# ---------- 初始化文件 ----------
def init_files():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=["任务ID", "老板名", "总数量", "总金额", "创建时间", "状态"])
        df.to_excel(TASKS_FILE, index=False)
    if not os.path.exists(CLAIMS_FILE):
        df = pd.DataFrame(columns=["任务ID", "认领人", "认领数量", "认领时间"])
        df.to_excel(CLAIMS_FILE, index=False)

init_files()

# ---------- 辅助函数 ----------
def load_tasks():
    return pd.read_excel(TASKS_FILE)

def save_tasks(df):
    df.to_excel(TASKS_FILE, index=False)

def load_claims():
    return pd.read_excel(CLAIMS_FILE)

def save_claims(df):
    df.to_excel(CLAIMS_FILE, index=False)

def get_claimed_sum(task_id):
    claims = load_claims()
    claimed = claims[claims["任务ID"] == task_id]["认领数量"].sum()
    return claimed if not claims.empty else 0

def get_remaining(task_id):
    tasks = load_tasks()
    task = tasks[tasks["任务ID"] == task_id]
    if task.empty:
        return 0
    total = task.iloc[0]["总数量"]
    claimed = get_claimed_sum(task_id)
    return total - claimed

def generate_task_id():
    return int(time.time())

# ---------- 页面 ----------
st.set_page_config(page_title="莳雪代肝派单", layout="centered")
st.title("?? 莳雪代肝派单")

menu = st.sidebar.radio("选择功能", ["?? 创建任务", "?? 认领任务", "?? 管理员统计"])

# ---------- 创建任务 ----------
if menu == "?? 创建任务":
    st.subheader("?? 派单员创建任务")
    with st.form("create_task"):
        boss = st.text_input("老板名（下单客户）")
        total_qty = st.number_input("总送心数量", min_value=1, step=1)
        total_amount = st.number_input("总提成金额（元）", min_value=0.0, step=0.01, format="%.2f")
        submitted = st.form_submit_button("? 创建任务")

        if submitted:
            if boss.strip() == "":
                st.error("请填写老板名")
            elif total_qty > 0:
                task_id = generate_task_id()
                tasks = load_tasks()
                new_row = pd.DataFrame({
                    "任务ID": [task_id],
                    "老板名": [boss.strip()],
                    "总数量": [total_qty],
                    "总金额": [total_amount],
                    "创建时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "状态": ["开放"]
                })
                tasks = pd.concat([tasks, new_row], ignore_index=True)
                save_tasks(tasks)
                st.success(f"? 任务已创建！任务ID: {task_id}，老板: {boss}，总??: {total_qty}")

# ---------- 认领任务 ----------
elif menu == "?? 认领任务":
    st.subheader("?? 员工认领任务")
    tasks = load_tasks()
    if tasks.empty:
        st.info("暂无待认领的任务")
    else:
        # 过滤出开放的任务
        open_tasks = tasks[tasks["状态"] == "开放"]
        if open_tasks.empty:
            st.info("当前没有开放任务")
        else:
            # 构建显示选项
            options = []
            for _, row in open_tasks.iterrows():
                task_id = row["任务ID"]
                remaining = get_remaining(task_id)
                if remaining > 0:
                    options.append(f"{task_id} - {row['老板名']} (总??{row['总数量']}，剩余{remaining})")
            if not options:
                st.info("所有开放任务已被认领完")
            else:
                selected = st.selectbox("选择任务", options)
                task_id = int(selected.split(" - ")[0])
                remaining = get_remaining(task_id)
                st.write(f"剩余可认领数量：**{remaining}**")

                with st.form("claim_form"):
                    claimant = st.text_input("你的昵称（认领人）")
                    claim_qty = st.number_input("认领数量（??）", min_value=1, max_value=remaining, step=1)
                    claimed = st.form_submit_button("?? 认领")

                    if claimed:
                        if claimant.strip() == "":
                            st.error("请填写你的昵称")
                        elif claim_qty > remaining:
                            st.error(f"不能超过剩余数量 {remaining}")
                        else:
                            claims = load_claims()
                            new_claim = pd.DataFrame({
                                "任务ID": [task_id],
                                "认领人": [claimant.strip()],
                                "认领数量": [claim_qty],
                                "认领时间": [datetime.now().strftime("%Y-%m-%d %H:%M")]
                            })
                            claims = pd.concat([claims, new_claim], ignore_index=True)
                            save_claims(claims)

                            # 检查任务是否已满
                            new_remaining = get_remaining(task_id)
                            if new_remaining == 0:
                                tasks.loc[tasks["任务ID"] == task_id, "状态"] = "已满"
                                save_tasks(tasks)

                            st.success(f"? {claimant} 认领了 {claim_qty}??")

# ---------- 管理员统计 ----------
elif menu == "?? 管理员统计":
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

    st.subheader("?? 全团统计报表")

    claims = load_claims()
    if claims.empty:
        st.info("暂无认领记录")
    else:
        # 按认领人汇总
        summary = claims.groupby("认领人").agg(
            总认领数量=("认领数量", "sum"),
            认领单数=("任务ID", "count")
        ).reset_index()
        summary = summary.sort_values("总认领数量", ascending=False)

        st.dataframe(summary, use_container_width=True)

        st.subheader("?? 本月之星")
        for _, row in summary.iterrows():
            st.write(f"**{row['认领人']}**：??{row['总认领数量']} 颗，共 {row['认领单数']} 单")

        # 查看每个任务的明细
        with st.expander("?? 任务明细"):
            tasks = load_tasks()
            if not tasks.empty:
                for _, task in tasks.iterrows():
                    task_id = task["任务ID"]
                    st.write(f"**任务 {task_id} - 老板：{task['老板名']}**，总??{task['总数量']}，总金额￥{task['总金额']}")
                    task_claims = claims[claims["任务ID"] == task_id]
                    if not task_claims.empty:
                        st.dataframe(task_claims[["认领人", "认领数量", "认领时间"]], use_container_width=True)
                    else:
                        st.write("暂无认领")
                    st.write("---")

    # ---------- 删除功能（仅限管理员） ----------
    st.subheader("??? 数据管理")
    with st.expander("删除数据（谨慎操作）"):
        if st.button("?? 删除所有任务和认领记录"):
            if os.path.exists(TASKS_FILE):
                os.remove(TASKS_FILE)
            if os.path.exists(CLAIMS_FILE):
                os.remove(CLAIMS_FILE)
            init_files()
            st.success("? 所有数据已清空")
            st.rerun()
