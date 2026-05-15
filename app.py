import streamlit as st
import json
import os
import pandas as pd

def load_scenario(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

st.set_page_config(layout="wide")
st.title("🔎 ポンコツ探偵を導け！アシスタントの事件簿")

# サイドバー：JSONファイル選択
scenario_files = [f for f in os.listdir(".") if f.endswith(".json")]

with st.sidebar:
    st.header("🗂 事件ファイル選択")
    selected_file = st.selectbox("調査する事件を選択", scenario_files)
    if st.button("捜査を開始する"):
        data = load_scenario(selected_file)
        st.session_state.current_data = data
        st.session_state.chat_history = []

# メインコンテンツ
if "current_data" in st.session_state:
    data = st.session_state.current_data

    # 1. 画像表示
    if os.path.exists(data["image"]):
        st.image(data["image"], use_container_width=True)

    # 2. 基本情報（表形式）
    st.markdown("### 🏨 現場データ：スケジュール")
    df = pd.DataFrame(data["basic_info"])
    df.columns = ["時刻", "イベント名", "詳細内容"]
    st.table(df)

    # 3. 容疑者の証言（吹き出し）
    st.markdown("### 🗣️ 容疑者の証言")
    for t in data["testimonies"]:
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{t['name']} ({t['profile']})**")
            st.write(t["text"])

    # 4. 探偵の推理
    st.markdown("### 🕵️‍♂️ 探偵の初期推理")
    with st.chat_message("assistant", avatar="🕵️"):
        st.write(data["detective_inference"])

    st.divider()

    # 5. 指摘・判定パート
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("矛盾を指摘してください")
    if user_input:
        st.session_state.chat_history.append(("human", user_input))
        
        # 判定
        culprit = data["answer"]["culprit"]
        if culprit in user_input and any(kw in user_input for kw in ["矛盾", "嘘", "おかしい", "静か", "湖", "景色", "霧", "場所","冷たい","室温","10度","デスクワーク","潮位","潮流","サーフィン","写真","時刻","レンズキャップ","這いつくばる","停電"]):
            response = f"「素晴らしい！{culprit}の証言の矛盾を見抜いたね。君の指摘通りだ！」"
            st.balloons()
        else:
            response = "「……まだ決定的とは言えないな。もう一度資料を読み直してみよう。」"
        
        st.session_state.chat_history.append(("assistant", response))
        st.rerun()