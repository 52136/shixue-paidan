import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

ADMIN_PASSWORD = "shixue0201"
TASKS_FILE = "tasks.xlsx"
CLAIMS_FILE = "claims.xlsx"
SCREENSHOT_DIR = "screenshots"

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

def init_files():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=["任务ID", "派单员", "老板名", "总数量", "总金额", "创建时间", "状态", "截图路径"])
        df.to_excel(TASKS_FILE, index=False)
    if not os.path.exists(CLAIMS_FILE):
        df = pd.DataFrame(columns=["任务ID", "认领人", "认领数量", "认领时间", "状态"])
        df.to_excel(CLAIMS_FILE, index=False)

init_files()

def load_tasks():
    return pd.read_excel(TASKS_FILE)

def save_tasks(df):
    df.to_excel(TASKS_FILE, index=False)

def load_claims():
    return pd.read_excel(CLAIMS_FILE)

def save_claims(df):
    df.to_excel(CLAIMS_FILE, index=False)

def generate_task_id():
    return int(time.time())

def format_name(name):
    name = name.strip()
    if not name.startswith("莳雪_"):
        return f"莳雪_{name}"
    return name


st.set_page_config(page_title="莳雪代肝派单", layout="centered")
st.title("🌸 莳雪代肝派单")

menu = st.sidebar.radio("选择功能", ["📝 创建任务", "🙋 认领任务", "✅ 认领审核", "📊 管理员统计"])


# ========== 创建任务 ==========
if menu == "📝 创建任务":
    st.subheader("📝 派单员创建任务")
    with st.form("create_task"):
        paidan_ren = st.text_input("派单员（你的名字）")
        boss = st.text_input("老板名（下单客户）")
        total_qty = st.number_input("总送心数量", min_value=1, step=1)
        total_amount = st.number_input("总提成金额（元）", min_value=0.0, step=0.01, format="%.2f")
        screenshot = st.file_uploader("上传接龙截图（可选）", type=["png", "jpg", "jpeg"])
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
                new_task = pd.DataFrame({
                    "任务ID": [task_id],
                    "派单员": [paidan_ren.strip()],
                    "老板名": [boss.strip()],
                    "总数量": [total_qty],
                    "总金额": [total_amount],
                    "创建时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "状态": ["开放"],
                    "截图路径": [screenshot_path]
                })
                tasks = pd.concat([tasks, new_task], ignore_index=True)
                save_tasks(tasks)
                st.success(f"✅ 任务创建成功！老板：{boss}，总❤️：{total_qty}，任务ID：{task_id}")


# ========== 认领任务 ==========
elif menu == "🙋 认领任务":
    st.subheader("🙋 员工认领任务")
    tasks = load_tasks()
    claims = load_claims()
    
    if tasks.empty:
        st.info("暂无任务")
    else:
        open_tasks = tasks[tasks["状态"] == "开放"]
        if open_tasks.empty:
            st.info("当前没有开放任务")
        else:
            options = []
            for _, row in open_tasks.iterrows():
                task_id = row["任务ID"]
                task_claims = claims[claims["任务ID"] == task_id]
                approved_claims = task_claims[task_claims["状态"] == "已通过"]
                claimed_total = approved_claims["认领数量"].sum() if not approved_claims.empty else 0
                remaining = row["总数量"] - claimed_total
                if remaining > 0:
                    options.append(f"{task_id} - {row['派单员']} - {row['老板名']} (剩余{remaining}❤️)")
            
            if not options:
                st.info("所有任务已认领完毕")
            else:
                selected = st.selectbox("选择任务", options)
                task_id = int(selected.split(" - ")[0])
                tasks_row = tasks[tasks["任务ID"] == task_id].iloc[0]
                task_claims = claims[claims["任务ID"] == task_id]
                approved_claims = task_claims[task_claims["状态"] == "已通过"]
                claimed_total = approved_claims["认领数量"].sum() if not approved_claims.empty else 0
                remaining = tasks_row["总数量"] - claimed_total
                
                st.write(f"**老板**：{tasks_row['老板名']}")
                st.write(f"**总❤️**：{tasks_row['总数量']} | **已认领**：{claimed_total} | **剩余**：{remaining}")
                
                if not task_claims.empty:
                    with st.expander("查看已认领人员"):
                        st.dataframe(task_claims[["认领人", "认领数量", "认领时间", "状态"]], use_container_width=True)
                
                with st.form(f"claim_form_{task_id}"):
                    claimant = st.text_input("你的昵称（认领人）")
                    claim_qty = st.number_input("认领数量（❤️）", min_value=1, max_value=remaining, step=1)
                    claimed = st.form_submit_button("🙋 认领")

                    if claimed:
                        if claimant.strip() == "":
                            st.error("请填写你的昵称")
                        else:
                            claimant = format_name(claimant.strip())
                            new_claim = pd.DataFrame({
                                "任务ID": [task_id],
                                "认领人": [claimant],
                                "认领数量": [claim_qty],
                                "认领时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                                "状态": ["待确认"]
                            })
                            claims = load_claims()
                            claims = pd.concat([claims, new_claim], ignore_index=True)
                            save_claims(claims)
                            st.success(f"✅ {claimant} 已提交认领申请，等待管理员确认")
                            st.rerun()


# ========== 认领审核 ==========
elif menu == "✅ 认领审核":
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

    st.subheader("✅ 认领审核")
    claims = load_claims()
    tasks = load_tasks()
    
    pending_claims = claims[claims["状态"] == "待确认"]
    
    if pending_claims.empty:
        st.info("暂无待审核的认领")
    else:
        for _, claim in pending_claims.iterrows():
            task_id = claim["任务ID"]
            task = tasks[tasks["任务ID"] == task_id]
            if task.empty:
                continue
            task_row = task.iloc[0]
            
            with st.container():
                st.markdown(f"### 🆔 认领申请")
                st.write(f"**任务ID**：{task_id}")
                st.write(f"**派单员**：{task_row['派单员']}")
                st.write(f"**老板**：{task_row['老板名']}")
                st.write(f"**总❤️**：{task_row['总数量']}")
                st.write(f"**认领人**：{claim['认领人']}")
                st.write(f"**认领数量**：{claim['认领数量']}❤️")
                st.write(f"**申请时间**：{claim['认领时间']}")
                
                if pd.notna(task_row.get("截图路径", "")) and task_row["截图路径"] != "" and os.path.exists(task_row["截图路径"]):
                    st.image(task_row["截图路径"], caption="接龙截图", width=300)
                else:
                    st.caption("无截图")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"✅ 通过", key=f"approve_{claim['认领人']}_{task_id}"):
                        claims.loc[(claims["任务ID"] == task_id) & (claims["认领人"] == claim["认领人"]), "状态"] = "已通过"
                        save_claims(claims)
                        task_claims = claims[claims["任务ID"] == task_id]
                        approved_claims = task_claims[task_claims["状态"] == "已通过"]
                        claimed_total = approved_claims["认领数量"].sum() if not approved_claims.empty else 0
                        if claimed_total >= task_row["总数量"]:
                            tasks.loc[tasks["任务ID"] == task_id, "状态"] = "已满"
                            save_tasks(tasks)
                        st.success(f"✅ {claim['认领人']} 的认领已通过")
                        st.rerun()
                with col_btn2:
                    if st.button(f"❌ 驳回", key=f"reject_{claim['认领人']}_{task_id}"):
                        claims = claims[~((claims["任务ID"] == task_id) & (claims["认领人"] == claim["认领人"]))]
                        save_claims(claims)
                        st.warning(f"❌ {claim['认领人']} 的认领已驳回")
                        st.rerun()
                st.write("---")


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
    tasks = load_tasks()
    claims = load_claims()
    
    approved_claims = claims[claims["状态"] == "已通过"]

    if tasks.empty and claims.empty:
        st.info("暂无数据")
    else:
        if not approved_claims.empty:
            summary = approved_claims.groupby("认领人").agg(
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

        st.subheader("📋 任务明细")
        
        if tasks.empty:
            st.info("暂无任务")
        else:
            for _, task in tasks.iterrows():
                task_id = task["任务ID"]
                task_claims = claims[claims["任务ID"] == task_id]
                
                with st.container():
                    st.markdown(f"### 🆔 任务 {task_id}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("派单员", task["派单员"])
                    col2.metric("老板", task["老板名"])
                    col3.metric("总❤️", task["总数量"])
                    col4.metric("状态", task["状态"])
                    
                    st.write(f"**创建时间**：{task['创建时间']}")
                    
                    if pd.notna(task.get("截图路径", "")) and task["截图路径"] != "" and os.path.exists(task["截图路径"]):
                        with st.expander("📸 查看截图"):
                            st.image(task["截图路径"], caption="接龙截图", width=300)
                    
                    with st.expander("查看认领明细"):
                        if not task_claims.empty:
                            st.dataframe(task_claims[["认领人", "认领数量", "认领时间", "状态"]], use_container_width=True)
                        else:
                            st.write("暂无认领")
                    
                    st.markdown("**🗑️ 管理操作**")
                    col_del1, col_del2, col_del3 = st.columns(3)
                    
                    with col_del1:
                        if st.button(f"删除整个任务", key=f"del_task_{task_id}"):
                            tasks = tasks[tasks["任务ID"] != task_id]
                            save_tasks(tasks)
                            claims = claims[claims["任务ID"] != task_id]
                            save_claims(claims)
                            st.success(f"✅ 任务 {task_id} 已删除")
                            st.rerun()
                    
                    if not task_claims.empty:
                        with col_del2:
                            claim_options = [f"{row['认领人']}（{row['认领数量']}❤️）" for _, row in task_claims.iterrows()]
                            selected_claim = st.selectbox(
                                f"选择要删除的认领",
                                claim_options,
                                key=f"select_{task_id}"
                            )
                            if st.button(f"删除该认领", key=f"del_claim_{task_id}"):
                                claimant = selected_claim.split("（")[0]
                                claims = claims[~((claims["任务ID"] == task_id) & (claims["认领人"] == claimant))]
                                save_claims(claims)
                                st.success(f"✅ 已删除 {claimant} 的认领记录")
                                st.rerun()
                    
                    with col_del3:
                        if st.button(f"重置为开放", key=f"reset_{task_id}"):
                            tasks.loc[tasks["任务ID"] == task_id, "状态"] = "开放"
                            save_tasks(tasks)
                            st.success(f"✅ 任务 {task_id} 已重置为开放")
                            st.rerun()
                    
                    st.write("---")
        
        st.subheader("⚠️ 数据管理")
        with st.expander("删除全部数据（谨慎操作）"):
            if st.button("🗑️ 删除所有任务和认领记录"):
                if os.path.exists(TASKS_FILE):
                    os.remove(TASKS_FILE)
                if os.path.exists(CLAIMS_FILE):
                    os.remove(CLAIMS_FILE)
                init_files()
                st.success("✅ 所有数据已清空")
                st.rerun()
