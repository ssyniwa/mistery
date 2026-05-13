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
            # 改行や空白を正規化しつつ読み込み
            full_text += page.extract_text() + "\n"
        
        # 「4. 事件の真相」以降は正解データとして切り離す
        parts = full_text.split("4. 事件の真相")
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

# --- 2. 構造化表示用関数 ---
def display_game_screen(text):
    # セクション分割用キーワード
    sec1_marker = "1. ホテルの基本情報"
    sec2_marker = "2. 容疑者たちの証言"
    sec3_marker = "3. 探偵の初期推理"

    # --- セクション1: ホテルの基本情報（表形式） ---
    if sec1_marker in text:
        st.markdown("### 🏨 現場データ：スケジュール")
        # セクション1と2の間を抜き出し
        sec1_raw = text.split(sec1_marker)[1].split(sec2_marker)[0].strip()
        
        # 時刻(HH:MM-HH:MM)を起点に行を解析
        table_data = []
        lines = sec1_raw.split("\n")
        for line in lines:
            line = line.strip()
            # 時刻のパターンを探す
            match = re.search(r"(\d{1,2}:\d{2}\s*[-ー～]\s*\d{1,2}:\d{2})", line)
            if match:
                time_str = match.group(1)
                # 時刻以降の部分を分割
                remaining = line.replace(time_str, "").strip()
                # 最初のスペースで「イベント名」と「詳細」に分ける
                parts = re.split(r'\s+', remaining, maxsplit=1)
                event_name = parts[0] if len(parts) > 0 else "不明"
                detail = parts[1] if len(parts) > 1 else ""
                table_data.append([time_str, event_name, detail])
        
        if table_data:
            df = pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"])
            st.table(df) # 明確な枠線のある表を表示
        else:
            st.info("表データが見つかりませんでした。直近のテキストを表示します：")
            st.code(sec1_raw)

    # --- セクション2: 容疑者の証言（吹き出し形式） ---
    if sec2_marker in text:
        st.markdown("### 🗣️ 容疑者の証言")
        sec2_raw = text.split(sec2_marker)[1].split(sec3_marker)[0].strip()
        
        # 「・」または「容疑者」という言葉で始まるブロックを分割
        suspect_blocks = re.split(r'\n(?=・|容疑者)', sec2_raw)
        
        for block in suspect_blocks:
            clean_block = block.strip().replace("・", "")
            if not clean_block: continue
            
            # 名前と発言の区切り（： または :）
            if "：" in clean_block:
                name, quote = clean_block.split("：", 1)
            elif ":" in clean_block:
                name, quote = clean_block.split(":", 1)
            else:
                name, quote = "関係者", clean_block
                
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{name.strip()}**")
                st.write(quote.strip())

    # --- セクション3: 探偵の推理（探偵の吹き出し） ---
    if sec3_marker in text:
        st.markdown("### 🕵️‍♂️ 探偵の初期推理")
        sec3_raw = text.split(sec3_marker)[1].strip()
        with st.chat_message("assistant", avatar="🕵️"):
            st.write(sec3_raw)

# --- 3. メインアプリ構成 ---
st.set_page_config(page_title="探偵アシスタント：WEBミステリー", layout="wide")
st.title("🔎 探偵アシスタント：碧水の館 事件簿")

with st.sidebar:
    st.header("🗂 事件ファイル選択")
    scenario_pdfs = [f for f in os.listdir(".") if f.endswith(".pdf") and f.startswith("scenario")]
    
    if scenario_pdfs:
        selected_pdf = st.selectbox("調査する事件を選択", scenario_pdfs)
        if st.button("捜査を開始する"):
            display_txt, answer_txt = extract_case_files(selected_pdf)
            st.session_state.current_scenario = display_txt
            st.session_state.answer_key = answer_txt
            st.session_state.chat_history = []
            
            # 画像対応
            base_name = selected_pdf.replace(".pdf", "")
            st.session_state.current_image = next((f"{base_name}{ext}" for ext in [".png", ".jpg"] if os.path.exists(f"{base_name}{ext}")), None)

if "current_scenario" in st.session_state:
    if st.session_state.current_image:
        st.image(st.session_state.current_image, use_container_width=True)
    
    display_game_screen(st.session_state.current_scenario)

    st.divider()
    st.subheader("💡 矛盾の指摘")
    
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("例：容疑者Aは静かだと言ったが、花火の音がしているはずだ")
    
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