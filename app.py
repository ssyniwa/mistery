import streamlit as st
from pypdf import PdfReader
import os
import pandas as pd
import re

# --- 1. PDF解析・抽出用関数 ---
def extract_case_files(file_path):
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            # 各ページのテキストを取得し、正規化（余計な改行を整理）
            page_text = page.extract_text()
            full_text += page_text + "\n"
        
        # 「4.」を境に前半（問題）と後半（正解）に分ける
        parts = re.split(r"4\.\s*事件の真相", full_text)
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

# --- 2. 構造化表示用関数 ---
def display_game_screen(text):
    # 正規表現で見出しの位置を特定（1., 2., 3. の形式を柔軟に探す）
    # セクションごとに分割
    s1 = re.search(r"1\.\s*ホテルの基本情報", text)
    s2 = re.search(r"2\.\s*容疑者たちの証言", text)
    s3 = re.search(r"3\.\s*探偵の初期推理", text)

    if not s1 or not s2 or not s3:
        st.error("PDF内の見出し（1.〜3.）が見つかりません。見出しの形式を確認してください。")
        with st.expander("PDFから抽出された生テキストを表示"):
            st.text(text)
        return

    # --- セクション1: ホテルの基本情報（表形式） ---
    st.markdown("### 🏨 現場データ：スケジュール")
    sec1_raw = text[s1.end():s2.start()].strip()
    
    # 時刻(HH:MM-HH:MM)を起点に表を作成
    table_data = []
    for line in sec1_raw.split("\n"):
        line = line.strip()
        match = re.search(r"(\d{1,2}:\d{2}\s*[-ー～]\s*\d{1,2}:\d{2})", line)
        if match:
            time_str = match.group(1)
            remaining = line.replace(time_str, "").strip()
            parts = re.split(r'\s+', remaining, maxsplit=1)
            event_name = parts[0] if len(parts) > 0 else "不明"
            detail = parts[1] if len(parts) > 1 else ""
            table_data.append([time_str, event_name, detail])
    
    if table_data:
        st.table(pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"]))
    else:
        st.info("表の自動解析に失敗したため、テキストを表示します：")
        st.code(sec1_raw)

    # --- セクション2: 容疑者の証言（吹き出し形式） ---
    st.markdown("### 🗣️ 容疑者の証言")
    sec2_raw = text[s2.end():s3.start()].strip()
    
    # 容疑者ごとの発言を分割（・ または 容疑者 で始まる行）
    suspect_blocks = re.split(r'\n(?=・|容疑者)', sec2_raw)
    for block in suspect_blocks:
        clean_block = block.strip().replace("・", "")
        if not clean_block: continue
        
        if "：" in clean_block: name, quote = clean_block.split("：", 1)
        elif ":" in clean_block: name, quote = clean_block.split(":", 1)
        else: name, quote = "関係者", clean_block
            
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{name.strip()}**")
            st.write(quote.strip())

    # --- セクション3: 探偵の推理（吹き出し） ---
    st.markdown("### 🕵️‍♂️ 探偵の初期推理")
    sec3_raw = text[s3.end():].strip()
    with st.chat_message("assistant", avatar="🕵️"):
        st.write(sec3_raw)

# --- メイン処理（サイドバー・チャットなど） ---
st.set_page_config(layout="wide")
st.title("🔎 探偵アシスタント")

scenario_pdfs = [f for f in os.listdir(".") if f.endswith(".pdf")]
selected_pdf = st.sidebar.selectbox("事件ファイル", scenario_pdfs)

if st.sidebar.button("捜査開始"):
    display_txt, answer_txt = extract_case_files(selected_pdf)
    st.session_state.current_scenario = display_txt
    st.session_state.answer_key = answer_txt
    st.session_state.chat_history = []
    st.session_state.current_image = selected_pdf.replace(".pdf", ".png") if os.path.exists(selected_pdf.replace(".pdf", ".png")) else None

if "current_scenario" in st.session_state:
    if st.session_state.current_image:
        st.image(st.session_state.current_image, use_container_width=True)
    display_game_screen(st.session_state.current_scenario)
    
    st.divider()
    user_input = st.chat_input("矛盾を指摘してください")
    if user_input:
        st.session_state.chat_history.append(("human", user_input))
        # 判定ロジック
        is_correct = False
        target = ""
        # answer_keyから「嘘つき: 容疑者X」を探す
        match = re.search(r"嘘つき:\s*容疑者([A-D])", st.session_state.answer_key)
        if match:
            target = match.group(1)
        
        if target and target in user_input and any(kw in user_input for kw in ["矛盾", "嘘", "おかしい", "静か"]):
            ans = f"「なるほど！{target}の証言は現場の状況と明らかに食い違っている。君の指摘通りだ！」"
            st.balloons()
        else:
            ans = "「……一理あるが、まだ決定的とは言えないな。別の視点はないか？」"
            
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun()