import streamlit as st
from pypdf import PdfReader
import os
import pandas as pd
import re

def extract_case_files(file_path):
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        parts = full_text.split("4. 事件の真相")
        return parts[0], parts[1] if len(parts) > 1 else ""
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

def display_game_screen(text):
    sec1_marker = "1. ホテルの基本情報"
    sec2_marker = "2. 容疑者たちの証言"
    sec3_marker = "3. 探偵の初期推理"

    # --- セクション1: ホテルの基本情報（表形式） ---
    if sec1_marker in text:
        st.markdown("### 🏨 現場データ：イベントスケジュール")
        sec1_raw = text.split(sec1_marker)[1].split(sec2_marker)[0].strip()
        
        # 時刻を起点にしてデータを分割するロジック
        time_pattern = r"(\d{1,2}:\d{2}\s*[-ー～]\s*\d{1,2}:\d{2})"
        lines = sec1_raw.split("\n")
        table_data = []
        
        for line in lines:
            # 時刻が含まれている行を探す
            times = re.findall(time_pattern, line)
            if times:
                time_str = times[0]
                # 時刻以降のテキストを「イベント」と「詳細」に分ける（最初の空白で分割）
                remaining = line.replace(time_str, "").strip()
                parts = re.split(r'\s+', remaining, maxsplit=1)
                
                event_name = parts[0] if len(parts) > 0 else ""
                detail = parts[1] if len(parts) > 1 else ""
                table_data.append([time_str, event_name, detail])
        
        if table_data:
            df = pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"])
            st.table(df) # 枠線ありの表を表示
        else:
            st.info("表の解析を試みましたが、直接テキストを表示します：")
            st.text(sec1_raw)

    # --- セクション2 & 3 は以前の吹き出しロジックを維持 ---
    if sec2_marker in text:
        st.markdown("### 🗣️ 容疑者の証言")
        sec2_raw = text.split(sec2_marker)[1].split(sec3_marker)[0].strip()
        suspect_lines = re.findall(r"(容疑者[A-D].*?[:：].*?)(?=・容疑者[A-D]|$)", sec2_raw.replace("\n", " "))
        for line in suspect_lines:
            if "：" in line: name, quote = line.split("：", 1)
            elif ":" in line: name, quote = line.split(":", 1)
            else: name, quote = "容疑者", line
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{name.strip()}**")
                st.write(quote.strip())

    if sec3_marker in text:
        st.markdown("### 🕵️‍♂️ 探偵の推理")
        sec3_raw = text.split(sec3_marker)[1].strip()
        with st.chat_message("assistant", avatar="🕵️"):
            st.write(sec3_raw)

# --- 以下、メイン処理（画像・チャット判定等）は前回と同様 ---

# --- 3. メインアプリ構成 ---
st.set_page_config(page_title="ミステリー探偵アシスタント", layout="wide")
st.title("🔎 探偵アシスタント：碧水の館 事件簿")

# サイドバー: ファイル選択
with st.sidebar:
    st.header("🗂 事件ファイル選択")
    scenario_pdfs = [f for f in os.listdir(".") if f.endswith(".pdf") and f.startswith("scenario")]
    
    if not scenario_pdfs:
        st.warning("PDFファイル（scenario_*.pdf）を配置してください。")
    else:
        selected_pdf = st.selectbox("調査する事件を選択", scenario_pdfs)
        
        if st.button("捜査を開始する"):
            # データ抽出とセッション保存
            display_txt, answer_txt = extract_case_files(selected_pdf)
            st.session_state.current_scenario = display_txt
            st.session_state.answer_key = answer_txt
            st.session_state.chat_history = []
            
            # 画像対応（PNG優先、なければJPG）[cite: 1]
            base_name = selected_pdf.replace(".pdf", "")
            if os.path.exists(f"{base_name}.png"):
                st.session_state.current_image = f"{base_name}.png"
            elif os.path.exists(f"{base_name}.jpg"):
                st.session_state.current_image = f"{base_name}.jpg"
            else:
                st.session_state.current_image = None

# メインコンテンツ表示
if "current_scenario" in st.session_state:
    # 現場写真（画像）の表示
    if st.session_state.current_image:
        st.image(st.session_state.current_image, caption="【現場資料】", use_container_width=True)
    
    # 構造化されたゲーム画面の表示
    display_game_screen(st.session_state.current_scenario)

    st.divider()
    
    # 推理指摘パート
    st.subheader("💡 矛盾の指摘")
    
    # 過去のやり取りを表示
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("例：容疑者Aは花火の音が静かだったと言っているが、イベント情報と矛盾する")
    
    if user_input:
        st.session_state.chat_history.append(("human", user_input))
        
        # 正解判定（キーワードチェック）[cite: 1, 2]
        target_suspect = ""
        for name in ["A", "B", "C", "D"]:
            if f"容疑者{name}" in st.session_state.answer_key:
                target_suspect = name
                break
        
        keywords = ["矛盾", "嘘", "おかしい", "静か", "音", "聞こえ"]
        if target_suspect and (target_suspect in user_input) and any(kw in user_input for kw in keywords):
            response = f"「なるほど！{target_suspect}の証言は現場のスケジュールと明らかに食い違っている。君のおかげで事件が解決したよ！」"
            st.balloons()
        else:
            response = "「……一理あるが、まだ決定的な矛盾とは言えないようだ。もう一度資料を読み直してみよう。」"
            
        st.session_state.chat_history.append(("assistant", response))
        st.rerun()
else:
    st.info("サイドバーから事件ファイルを選び、「捜査を開始する」をクリックしてください。")