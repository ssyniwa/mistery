import streamlit as st
from pypdf import PdfReader
import os
import pandas as pd
import re

# --- 1. PDF解析・抽出用関数 ---
def extract_case_files(file_path):
    """PDFからテキストを抽出し、表示用と正解用に分割する"""
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        
        # 「4. 事件の真相」という見出しで表示用と正解用を切り分ける
        parts = full_text.split("4. 事件の真相")
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDF読み込みエラー: {e}")
        return None, None

# --- 2. 構造化表示用関数 ---
def display_game_screen(text):
    """テキストを解析して『表』と『吹き出し』に加工して表示する[cite: 1, 2]"""
    
    # セクション分割用キーワード
    sec1_marker = "1. ホテルの基本情報"
    sec2_marker = "2. 容疑者たちの証言"
    sec3_marker = "3. 探偵の初期推理"

    # --- セクション1: ホテルの基本情報（表形式） ---
    if sec1_marker in text:
        st.markdown("### 🏨 現場データ：イベントスケジュール")
        # セクション1と2の間を抜き出す
        sec1_raw = text.split(sec1_marker)[1].split(sec2_marker)[0].strip()
        
        # 正規表現で「時刻(00:00-00:00) イベント名 詳細」のパターンを抽出
        # パターン: (時刻) (次の単語) (残りの行)
        table_pattern = re.findall(r"(\d{1,2}:\d{2}.*?\d{1,2}:\d{2})\s+([^\n\s]+)\s+([^\n]+)", sec1_raw)
        
        if table_pattern:
            df = pd.DataFrame(table_pattern, columns=["時刻", "イベント名", "詳細内容"])
            st.table(df) # 枠線付きの表として表示[cite: 1]
        else:
            st.info(sec1_raw) # 抽出失敗時はテキスト表示

    # --- セクション2: 容疑者の証言（吹き出し形式） ---
    if sec2_marker in text:
        st.markdown("### 🗣️ 容疑者の証言")
        sec2_raw = text.split(sec2_marker)[1].split(sec3_marker)[0].strip()
        
        # 容疑者ごとの発言を分割（「・容疑者X：」の形式を想定）
        suspect_lines = re.findall(r"(容疑者[A-D].*?[:：].*?)(?=容疑者[A-D]|$)", sec2_raw.replace("\n", " "))
        
        if suspect_lines:
            for line in suspect_lines:
                # 名前と発言を分離
                if "：" in line: name, quote = line.split("：", 1)
                elif ":" in line: name, quote = line.split(":", 1)
                else: name, quote = "関係者", line
                
                with st.chat_message("user", avatar="👤"): # ユーザー側吹き出し[cite: 1]
                    st.markdown(f"**{name.strip()}**")
                    st.write(quote.strip())
        else:
            st.write(sec2_raw)

    # --- セクション3: 探偵の推理（探偵の吹き出し） ---
    if sec3_marker in text:
        st.markdown("### 🕵️‍♂️ 探偵の現状の推理")
        sec3_raw = text.split(sec3_marker)[1].strip()
        with st.chat_message("assistant", avatar="🕵️"): # 探偵側吹き出し[cite: 2]
            st.write(sec3_raw)

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