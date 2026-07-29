import streamlit as st
import pandas as pd
import os
import time
import re
from datetime import datetime

ADMIN_PASSWORD = "shixue0201"
TASKS_FILE = "tasks.xlsx"
CLAIMS_FILE = "claims.xlsx"

# ---------- 初始化 ----------
def init_files():
    if not os.path.exists(TASKS_FILE):
        df = pd.DataFrame(columns=["任务ID", "派单员", "老板名", "总数量", "总金额", "创建时间", "状态", "接龙原文"])
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

def generate_task_id():
    return int(time.time())

def format_name(name):
    """统一加前缀，支持多种写法"""
    name = name.strip()
    # 去除所有空格
    name_no_space = re.sub(r'\\s+', '', name)
    if name_no_space.startswith("莳雪"):
        # 已经是莳雪开头，提取后缀
        suffix = name_no_space[2:]  # 去掉"莳雪"
        if suffix.startswith("_"):
            suffix = suffix[1:]
        if suffix == "":
            return "莳雪"
        return f"莳雪_{suffix}"
    else:
        return f"莳雪_{name_no_space}"

# ---------- 接龙解析（支持多种格式） ----------
def parse_jielong(text):
    lines = text.strip().splitlines()
    lines = [l.strip() for l in lines if l.strip()]
    
    if len(lines) < 3:
        return None, None, None, []
    
    # 解析第一行：老板名板数量❤️
    first_line = lines[0]
    pattern1 = r'([\\u4e00-\\u9fa5]+)板(\\d+)❤️'
    match = re.search(pattern1, first_line)
    if not match:
        pattern2 = r'([\\u4e00-\\u9fa5]+).*?(\\d+)❤️'
        match = re.search(pattern2, first_line)
        if not match:
            return None, None, None, []
    
    boss_name = match.group(1).strip()
    total_qty = int(match.group(2))
    
    # 找到"送心员："那一行
    claim_start = -1
    for i, line in enumerate(lines):
        if "送心员" in line or "认领人" in line:
            claim_start = i + 1
            break
    
    if claim_start == -1 or claim_start >= len(lines):
        return None, None, None, []
    
    # 解析认领列表
    claims = []
    for line in lines[claim_start:]:
        # 匹配格式：数字. 任意内容 数字（最后一个数字作为数量）
        match = re.search(r'^\\s*\\d+\\.\\s*(.+?)\\s*(\\d+)\\s*$', line)
        if match:
            name_part = match.group(1).strip()
            qty = int(match.group(2))
            claimant = format_name(name_part)
            claims.append((claimant, qty))
        else:
            # 尝试更宽松的匹配：名字 + 数字（无序号）
            match2 = re.search(r'([\\u4e00-\\u9fa5\\s]+?)\\s*(\\d+)\\s*$', line)
            if match2:
                name_part = match2.group(1).strip()
                qty = int(match2.group(2))
                claimant = format_name(name_part)
                claims.append((claimant, qty))
    
    return boss_name, total_qty, 0.0, claims


# ---------- 页面 ----------
st.set_page_config(page_title="莳雪代肝派单", layout="centered")
st.title("🌸 莳雪代肝派单")

menu = st.sidebar.radio("选择功能", ["📝 创建任务", "🙋 认领任务", "📊 管理员统计"])


# ========== 创建任务 ==========
if menu == "📝 创建任务":
    st.subheader("📝 派单员创建任务")
    with st.form("create_task"):
        paidan_ren = st.text_input("派单员（你的名字）")
        total_amount = st.number_input("总提成金额（元）", min_value=0.0, step=0.01, format="%.2f")
        jielong_text = st.text_area(
            "📋 粘贴结单群接龙",
            height=250,
            placeholder="格式示例：\\nAA板10❤️\\n送心员：\\n1.小汐5\\n2.小六5",
            help="第一行：老板名板数量❤️\\n第二行：送心员：\\n后续行：数字.名字数量（数量必须为数字）"
        )
        submitted = st.form_submit_button("✅ 创建任务并自动审核")

        if submitted:
            if paidan_ren.strip() == "":
                st.error("请填写派单员姓名")
            elif jielong_text.strip() == "":
                st.error("请粘贴接龙内容")
            else:
                boss_name, total_qty, _, claims = parse_jielong(jielong_text)
                
                if boss_name is None:
                    st.error("⚠️ 接龙解析失败，请检查格式")
                    st.info("格式示例：\\nAA板10❤️\\n送心员：\\n1.小汐5\\n2.小六5")
                elif not claims:
                    st.error("⚠️ 未识别到认领人员，请检查每行是否包含数字数量")
                else:
                    total_claimed = sum([q for _, q in claims])
                    
                    if total_claimed != total_qty:
                        st.warning(f"⚠️ 认领总和（{total_claimed}）≠ 总数量（{total_qty}），状态为「待复核」")
                        status = "待复核"
                    else:
                        status = "已审核"
                        st.success(f"✅ 自动审核通过！{total_claimed} = {total_qty}")
                    
                    task_id = generate_task_id()
                    tasks = load_tasks()
                    new_task = pd.DataFrame({
                        "任务ID": [task_id],
                        "派单员": [paidan_ren.strip()],
                        "老板名": [boss_name],
                        "总数量": [total_qty],
                        "总金额": [total_amount],
                        "创建时间": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                        "状态": [status],
                        "接龙原文": [jielong_text]
                    })
                    tasks = pd.concat([tasks, new_task], ignore_index=True)
                    save_tasks(tasks)
                    
                    claims_df = load_claims()
                    for claimant, qty in claims:
                        new_claim = pd.DataFrame({
                            "任务ID": [task_id],
                            "认领人": [claimant],
                            "认领数量": [qty],
                            "认领时间": [datetime.now().strftime("%Y-%m-%d %H:%M")]
                        })
                        claims_df = pd.concat([claims_df, new_claim], ignore_index=True)
                    save_claims(claims_df)
                    
                    st.success(f"✅ 任务创建成功！共 {len(claims)} 人认领，总计 {total_claimed}❤️")
                    st.info(f"任务ID：{task_id}，状态：{status}")


# ========== 认领任务 ==========
elif menu == "🙋 认领任务":
    st.subheader("🙋 员工认领任务")
    
    tasks = load_tasks()
    claims = load_claims()
    
    if tasks.empty:
        st.info("暂无任务")
    else:
        for _, task in tasks.iterrows():
            task_id = task["任务ID"]
            task_claims = claims[claims["任务ID"] == task_id]
            claimed_total = task_claims["认领数量"].sum() if not task_claims.empty else 0
            
            with st.container():
                st.markdown(f"### 📌 任务 {task_id}")
                col1, col2, col3 = st.columns(3)
                col1.metric("派单员", task["派单员"])
                col2.metric("老板", task["老板名"])
                col3.metric("状态", task["状态"])
                
                st.write(f"**总❤️**：{task['总数量']} | **已认领**：{claimed_total} | **剩余**：{task['总数量'] - claimed_total}")
                
                if not task_claims.empty:
                    with st.expander("查看已认领人员"):
                        st.dataframe(task_claims[["认领人", "认领数量", "认领时间"]], use_container_width=True)
                
                remaining = task['总数量'] - claimed_total
                if remaining > 0 and task['状态'] != "已满":
                    with st.form(f"claim_form_{task_id}"):
                        claimant = st.text_input("你的昵称", key=f"name_{task_id}")
                        claim_qty = st.number_input("认领数量（❤️）", min_value=1, max_value=remaining, step=1, key=f"qty_{task_id}")
                        if st.form_submit_button("🙋 认领"):
                            if claimant.strip() == "":
                                st.error("请填写你的昵称")
                            else:
                                claimant = format_name(claimant.strip())
                                new_claim = pd.DataFrame({
                                    "任务ID": [task_id],
                                    "认领人": [claimant],
                                    "认领数量": [claim_qty],
                                    "认领时间": [datetime.now().strftime("%Y-%m-%d %H:%M")]
                                })
                                claims = load_claims()
                                claims = pd.concat([claims, new_claim], ignore_index=True)
                                save_claims(claims)
                                
                                new_claimed_total = claims[claims["任务ID"] == task_id]["认领数量"].sum()
                                if new_claimed_total >= task['总数量']:
                                    tasks.loc[tasks["任务ID"] == task_id, "状态"] = "已满"
                                    save_tasks(tasks)
                                st.success(f"✅ {claimant} 认领了 {claim_qty}❤️")
                                st.rerun()
                else:
                    st.info("✅ 该任务已认领完毕")
                
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

    if tasks.empty and claims.empty:
        st.info("暂无数据")
    else:
        # 员工排行榜
        if not claims.empty:
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

        # 派单员业绩
        if not tasks.empty:
            paidan_summary = tasks.groupby("派单员").agg(
                创建任务数=("任务ID", "count"),
                总送心量=("总数量", "sum"),
                总金额=("总金额", "sum")
            ).reset_index()
            paidan_summary = paidan_summary.sort_values("总送心量", ascending=False)

            st.subheader("📋 派单员业绩")
            st.dataframe(paidan_summary, use_container_width=True)

        # 任务明细 + 删除
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
                    
                    with st.expander("📋 查看接龙原文"):
                        st.text(task["接龙原文"])
                    
                    with st.expander("查看认领明细"):
                        if not task_claims.empty:
                            st.dataframe(task_claims[["认领人", "认领数量", "认领时间"]], use_container_width=True)
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
        
        # 全部删除
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
