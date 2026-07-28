import streamlit as st
import pandas as pd
import os
import time
import shutil
from datetime import datetime

ADMIN_PASSWORD = "admin123"
TASKS_FILE = "tasks.xlsx"
CLAIMS_FILE = "claims.xlsx"
SCREENSHOT_DIR = "screenshots"

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# ---------- 初始化文件 ----------
def init_files():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=["任务ID", "派单员", "老板名", "总数量", "总金额", "创建时间", "状态", "截图路径"])
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
st.title("🌸 莳雪代肝派单")

menu = st.sidebar.radio("选择功能", ["📝 创建任务", "🙋 认领任务", "📊 管理员统计"])

# ---------- 创建任务 ----------
if menu == "📝 创建任务":
    st.subheader("📝 派单员创建任务")
    with st.form("create_task"):
        paidan_ren = st.text_input("派单员（你的名字）")
        boss = st.text_input("老板名（下单客户）")
        total_qty = st.number_input("总送心数量", min_value=1, step=1)
        total_amount = st.number_input("总提成金额（元）", min_value=0.0, step=0.01, format="%.2f")
        # ！！！上传截图入口在这里 ！！！
        screenshot = st.file_uploader("上传接龙截图（仅管理员可见）", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("✅ 创建任务")

        if submitted:
            if paidan_ren.strip() == "":
                st.error("请填写派单员姓名")
            elif boss.strip() == "":
                st.error("请填写老板名")
            elif total_qty > 0:
                screenshot_path = ""
                if screenshot is not None:
                    timestamp = int(time.time())
                    filename = f"{timestamp}_{screenshot.name}"
                    save_path = os.path.join(SCREENSHOT_DIR, filename)
                    with open(save_path, "wb") as f:
                        f.write(screenshot.getbuffer())
                    screenshot_path = save_path

                task_id = generate_task_id()
                tasks = load_tasks()
                new_row = pd.DataFrame({
                    "任务ID": [task_id],
                    "派单员": [paidan_ren.strip()],
                    "老板名": [boss.strip()],
                    "总数量": [total_qty],
                    "总金额": [total_amount],
                    "创建时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "状态": ["开放"],
                    "截图路径": [screenshot_path]
                })
                tasks = pd.concat([tasks, new_row], ignore_index=True)
                save_tasks(tasks)
                st.success(f"✅ {paidan_ren} 创建任务成功！老板: {boss}，总❤️: {total_qty}")

# ---------- 认领任务 ----------
elif menu == "🙋 认领任务":
    st.subheader("🙋 员工认领任务")
    tasks = load_tasks()
    if tasks.empty:
        st.info("暂无待认领的任务")
    else:
        open_tasks = tasks[tasks["状态"] == "开放"]
        if open_tasks.empty:
            st.info("当前没有开放任务")
        else:
            options = []
            for _, row in open_tasks.iterrows():
                task_id = row["任务ID"]
                remaining = get_remaining(task_id)
                if remaining > 0:
                    # 员工认领时只看到派单员和老板名，看不到截图
                    options.append(
                        f"{task_id} - {row['派单员']} - {row['老板名']} "
                        f"(总❤️{row['总数量']}，剩余{remaining})"
                    )
            if not options:
                st.info("所有开放任务已被认领完")
            else:
                selected = st.selectbox("选择任务", options)
                task_id = int(selected.split(" - ")[0])
                remaining = get_remaining(task_id)
                st.write(f"剩余可认领数量：**{remaining}**")

                with st.form("claim_form"):
                    claimant = st.text_input("你的昵称（认领人）")
                    claim_qty = st.number_input("认领数量（❤️）", min_value=1, max_value=remaining, step=1)
                    claimed = st.form_submit_button("🙋 认领")

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

                            new_remaining = get_remaining(task_id)
                            if new_remaining == 0:
                                tasks.loc[tasks["任务ID"] == task_id, "状态"] = "已满"
                                save_tasks(tasks)

                            st.success(f"✅ {claimant} 认领了 {claim_qty}❤️")

# ---------- 管理员统计 ----------
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

    claims = load_claims()
    tasks = load_tasks()

    if claims.empty:
        st.info("暂无认领记录")
    else:
        summary = claims.groupby("认领人").agg(
            总认领数量=("认领数量", "sum"),
            认领单数=("任务ID", "count")
        ).reset_index()
        summary = summary.sort_values("总认领数量", ascending=False)

        st.subheader("👤 员工排行榜")
        st.dataframe(summary, use_container_width=True)

        st.subheader("🏆 本月之星")
        for _, row in summary.iterrows():
            st.write(f"**{row['认领人']}**：❤️{row['总认领数量']} 颗，共 {row['认领单数']} 单")

        if not tasks.empty:
            paidan_summary = tasks.groupby("派单员").agg(
                创建任务数=("任务ID", "count"),
                总送心量=("总数量", "sum"),
                总金额=("总金额", "sum")
            ).reset_index()
            paidan_summary = paidan_summary.sort_values("总送心量", ascending=False)

            st.subheader("📋 派单员业绩")
            st.dataframe(paidan_summary, use_container_width=True)

        # 任务明细（只有管理员能看到截图）
        with st.expander("📋 任务明细（含截图）"):
            if not tasks.empty:
                for _, task in tasks.iterrows():
                    task_id = task["任务ID"]
                    st.write(f"**任务 {task_id}** | 派单员：{task['派单员']} | 老板：{task['老板名']} | 总❤️{task['总数量']} | 状态：{task['状态']}")
                    # 管理员可见截图
                    if pd.notna(task.get("截图路径", "")) and task["截图路径"] != "" and os.path.exists(task["截图路径"]):
                        st.image(task["截图路径"], caption="接龙截图", width=200)
                    task_claims = claims[claims["任务ID"] == task_id]
                    if not task_claims.empty:
                        st.dataframe(task_claims[["认领人", "认领数量", "认领时间"]], use_container_width=True)
                    else:
                        st.write("暂无认领")
                    st.write("---")

    st.subheader("🗑️ 数据管理")
    with st.expander("删除数据（谨慎操作）"):
        if st.button("⚠️ 删除所有任务和认领记录"):
            if os.path.exists(SCREENSHOT_DIR):
                shutil.rmtree(SCREENSHOT_DIR)
                os.makedirs(SCREENSHOT_DIR)
            if os.path.exists(TASKS_FILE):
                os.remove(TASKS_FILE)
            if os.path.exists(CLAIMS_FILE):
                os.remove(CLAIMS_FILE)
            init_files()
            st.success("✅ 所有数据已清空")
            st.rerun()
