import streamlit as st
import pandas as pd
import os
import time
import sqlitecloud
from datetime import datetime

# ！！！只改这一行：把引号里的内容换成你的 SQLite Cloud 连接字符串 ！！！
DB_URL = "sqlitecloud://sqlitecloud://cta9jweevz.g6.sqlite.cloud:8860/auth.sqlitecloud?apikey=PPxxbJGFDvSf8CxjJr5Db5EvOBifx0ybZZOCB6kP35c"

ADMIN_PASSWORD = "admin123"
SCREENSHOT_DIR = "screenshots"

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)


def get_connection():
    return sqlitecloud.connect(DB_URL)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paidan_ren TEXT,
            songxin_shuliang INTEGER,
            ticheng_jine REAL,
            tijiao_shijian TEXT,
            jietu_lujing TEXT
        )
    """)
    conn.commit()
    conn.close()


def load_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY id DESC", conn)
    conn.close()
    df.rename(columns={
        "paidan_ren": "派单员",
        "songxin_shuliang": "送心数量",
        "ticheng_jine": "提交提成金额",
        "tijiao_shijian": "提交时间",
        "jietu_lujing": "截图路径"
    }, inplace=True)
    return df


def save_order(paidan_ren, songxin_shuliang, ticheng_jine, tijiao_shijian, jietu_lujing):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (paidan_ren, songxin_shuliang, ticheng_jine, tijiao_shijian, jietu_lujing)
        VALUES (?, ?, ?, ?, ?)
    """, (paidan_ren, songxin_shuliang, ticheng_jine, tijiao_shijian, jietu_lujing))
    conn.commit()
    conn.close()


def delete_all_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders")
    conn.commit()
    conn.close()


def delete_by_paidanren(paidan_ren):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE paidan_ren = ?", (paidan_ren,))
    conn.commit()
    conn.close()


def get_all_paidanren():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT paidan_ren FROM orders")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


st.set_page_config(page_title="莳雪代肝派单", layout="centered")
st.title("🌸 莳雪代肝派单")

init_db()

option = st.sidebar.radio("选择功能", ["📝 派单员填单", "📊 管理员统计"])


if option == "📝 派单员填单":
    st.subheader("📝 提交新单")
    with st.form("submit_form"):
        paidan_ren = st.text_input("派单员（请填写完整昵称）")
        songxin_shuliang = st.number_input("送心数量（❤️）", min_value=1, step=1)
        ticheng_jine = st.number_input("提交提成金额（元）", min_value=0.0, step=0.01, format="%.2f")
        screenshot = st.file_uploader("上传接龙截图（可选）", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("✅ 提交")

        if submitted:
            if paidan_ren.strip() == "":
                st.error("请填写派单员姓名")
            elif songxin_shuliang > 0 and ticheng_jine >= 0:
                jietu_lujing = ""
                if screenshot is not None:
                    timestamp = int(time.time())
                    filename = f"{timestamp}_{screenshot.name}"
                    save_path = os.path.join(SCREENSHOT_DIR, filename)
                    with open(save_path, "wb") as f:
                        f.write(screenshot.getbuffer())
                    jietu_lujing = save_path

                tijiao_shijian = datetime.now().strftime("%Y-%m-%d %H:%M")
                save_order(paidan_ren.strip(), songxin_shuliang, ticheng_jine, tijiao_shijian, jietu_lujing)
                st.success(f"✅ {paidan_ren} 的单子已提交！❤️{songxin_shuliang}，提成¥{ticheng_jine}")
            else:
                st.error("数量和金额必须大于0")


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
    df = load_data()

    if df.empty:
        st.info("暂无数据，快去填单吧")
    else:
        summary = df.groupby("派单员").agg(
            总送心数量=("送心数量", "sum"),
            总提成金额=("提交提成金额", "sum"),
            订单数=("送心数量", "count")
        ).reset_index()
        summary = summary.sort_values("总送心数量", ascending=False)

        st.dataframe(summary, use_container_width=True)

        st.subheader("🏆 本月之星")
        for _, row in summary.iterrows():
            st.write(f"**{row['派单员']}**：❤️{row['总送心数量']} 颗，¥{row['总提成金额']}，共 {row['订单数']} 单")

        with st.expander("查看所有明细"):
            st.dataframe(df.drop(columns=["截图路径"], errors="ignore"), use_container_width=True)

            if "截图路径" in df.columns and not df["截图路径"].isnull().all():
                st.subheader("📸 上传的截图")
                for _, row in df.iterrows():
                    if pd.notna(row["截图路径"]) and row["截图路径"] != "" and os.path.exists(row["截图路径"]):
                        st.image(row["截图路径"], caption=f"{row['派单员']} - {row['提交时间']}", width=200)

    st.subheader("🗑️ 删除记录")
    delete_option = st.radio("选择删除方式", ["删除全部记录", "按派单员删除"])

    if delete_option == "删除全部记录":
        if st.button("⚠️ 确认删除全部数据"):
            if os.path.exists(SCREENSHOT_DIR):
                import shutil
                shutil.rmtree(SCREENSHOT_DIR)
                os.makedirs(SCREENSHOT_DIR)
            delete_all_data()
            st.success("✅ 全部记录已删除")
            st.rerun()
    else:
        paidanren_list = get_all_paidanren()
        if paidanren_list:
            selected = st.selectbox("选择要删除的派单员", paidanren_list)
            if st.button(f"⚠️ 确认删除 {selected} 的所有记录"):
                df_del = load_data()
                for _, row in df_del[df_del["派单员"] == selected].iterrows():
                    if pd.notna(row["截图路径"]) and row["截图路径"] != "" and os.path.exists(row["截图路径"]):
                        os.remove(row["截图路径"])
                delete_by_paidanren(selected)
                st.success(f"✅ {selected} 的所有记录已删除")
                st.rerun()
        else:
            st.info("暂无数据")
