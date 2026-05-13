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
            # 抽出テキストの正規化：連続する空白を1つにまとめ、前後の空白を削除
            page_text = page.extract_text()
            full_text += page_text + "\n"
        
        # 「4. 事件の真相」を区切りにする（数字とキーワードで柔軟に検索）
        split_pattern = r"[4４][.\s・]*事件の真相"
        parts = re.split(split_pattern, full_text)
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

# --- 2. 構造化表示用関数 ---
def display_game_screen(text):
    # 見出しを「数字 + キーワード」で柔軟に検索するパターン
    p1 = re.search(r"[1１][.\s・]*ホテルの基本情報", text)
    p2 = re.search(r"[2２][.\s・]*容疑者たちの証言", text)
    p3 = re.search(r"[3３][.\s・]*探偵の初期推理", text)

    # どこかのセクションが見つからない場合のフォールバック
    if not p1 or not p2 or not p3:
        st.error("一部の見出しを自動特定できませんでした。")
        with st.expander("PDFから抽出された生のテキストを確認する"):
            st.text(text)
        # 失敗しても止まらずに全文を表示する
        st.info("解析に失敗したため、そのまま表示します：")
        st.write(text)
        return

    # --- セクション1: ホテルの基本情報 ---
    st.markdown("### 🏨 現場データ：スケジュール")
    sec1_raw = text[p1.end():p2.start()].strip()
    
    table_data = []
    for line in sec1_raw.split("\n"):
        # 時刻(HH:MM)が含まれる行を抽出
        time_match = re.search(r"(\d{1,2}:\d{2}\s*[-ー～〜]\s*\d{1,2}:\d{2})", line)
        if time_match:
            time_str = time_match.group(1)
            remaining = line.replace(time_str, "").strip()
            # 最初の空白で分割
            parts = re.split(r'\s+', remaining, maxsplit=1)
            event_name = parts[0] if len(parts) > 0 else "不明"
            detail = parts[1] if len(parts) > 1 else ""
            table_data.append([time_str, event_name, detail])
    
    if table_data:
        st.table(pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"]))
    else:
        st.info(sec1_raw) # 解析失敗時はそのまま表示 [cite: 20, 21, 22, 23]

    # --- セクション2: 容疑者の証言 ---
    st.markdown("### 🗣️ 容疑者の証言")
    sec2_raw = text[p2.end():p3.start()].strip()
    # 「・」または改行で分割
    suspect_blocks = re.split(r'[・·\n]', sec2_raw)
    
    for block in suspect_blocks:
        if len(block.strip()) < 5: continue 
        
        if "：" in block: name, quote = block.split("：", 1)
        elif ":" in block: name, quote = block.split(":", 1)
        else: name, quote = "関係者", block
            
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{name.strip()}**")
            st.write(quote.strip()) [cite: 24, 25, 26, 27, 28]

    # --- セクション3: 探偵の推理 ---
    st.markdown("### 🕵️‍♂️ 探偵の初期推理")
    sec3_raw = text[p3.end():].strip()
    with st.chat_message("assistant", avatar="🕵️"):
        st.write(sec3_raw) [cite: 30]
# --- 以下メイン処理 (変更なし) ---
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