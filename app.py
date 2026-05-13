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
            # 抽出時に1行に繋がってしまう問題に対応するため改行を明示
            full_text += page.extract_text() + "\n"
        
        # 「4. 事件の真相」で分割
        parts = re.split(r"4\.\s*事件の真相", full_text)
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

# --- 2. 構造化表示用関数 ---
def display_game_screen(text):
    # 見出しの開始位置を正規表現で検索（行頭でなくても見つける設定）
    m1 = re.search(r"1\.\s*ホテルの基本情報", text)
    m2 = re.search(r"2\.\s*容疑者たちの証言", text)
    m3 = re.search(r"3\.\s*探偵の初期推理", text)

    if not m1 or not m2 or not m3:
        st.error("見出しの特定に失敗しました。PDFの構成を確認してください。")
        with st.expander("PDFから抽出された生テキストを表示"):
            st.text(text)
        return

    # --- セクション1: ホテルの基本情報 ---
    st.markdown("### 🏨 現場データ：スケジュール")
    # m1の終わりからm2の始まりまでを抽出
    sec1_raw = text[m1.end():m2.start()].strip()
    
    table_data = []
    # 時刻(HH:MM-HH:MM)が含まれる行を抽出
    for line in sec1_raw.split("\n"):
        time_match = re.search(r"(\d{1,2}:\d{2}\s*[-ー～]\s*\d{1,2}:\d{2})", line)
        if time_match:
            time_str = time_match.group(1)
            # 時刻を除いた部分を「イベント名」と「詳細」に分割
            remaining = line.replace(time_str, "").strip()
            parts = re.split(r'\s+', remaining, maxsplit=1)
            event_name = parts[0] if len(parts) > 0 else "不明"
            detail = parts[1] if len(parts) > 1 else ""
            table_data.append([time_str, event_name, detail])
    
    if table_data:
        st.table(pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"]))
    else:
        st.info(sec1_raw)

    # --- セクション2: 容疑者の証言 ---
    st.markdown("### 🗣️ 容疑者の証言")
    # m2の終わりからm3の始まりまでを抽出
    sec2_raw = text[m2.end():m3.start()].strip()
    # 記号「・」や「·」で分割（半角・全角の両方に対応）
    suspect_blocks = re.split(r'[・·]', sec2_raw)
    
    for block in suspect_blocks:
        if len(block.strip()) < 5: continue # 短すぎるゴミを除外
        
        # 名前と発言を分離
        if "：" in block: name, quote = block.split("：", 1)
        elif ":" in block: name, quote = block.split(":", 1)
        else: name, quote = "関係者", block
            
        with st.chat_message("user", avatar="👤"):
            st.markdown(f"**{name.strip()}**")
            st.write(quote.strip())

    # --- セクション3: 探偵の推理 ---
    st.markdown("### 🕵️‍♂️ 探偵の初期推理")
    # m3の終わりから最後まで
    sec3_raw = text[m3.end():].strip()
    with st.chat_message("assistant", avatar="🕵️"):
        st.write(sec3_raw)

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