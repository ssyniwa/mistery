import streamlit as st
from pypdf import PdfReader
import os
import pandas as pd

# --- ユーティリティ関数 ---

def extract_text_from_pdf(file_path):
    """PDFからテキストを抽出し、表示用（項目1-3）と正解用に分割する"""
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        
        # 「4. 事件の真相」で分割
        parts = full_text.split("4. 事件の真相")
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDFの読み込みに失敗しました: {e}")
        return None, None

def display_structured_scenario(text):
    """テキストを構造化して表示する（表形式 ＆ 吹き出し）"""
    
    sec1_title = "1. ホテルの基本情報"
    sec2_title = "2. 容疑者たちの証言"
    sec3_title = "3. 探偵の初期推理"

    # --- 1. ホテルの基本情報（表形式に変換） ---
    if sec1_title in text:
        st.markdown("#### 🏨 現場検証データ（イベントスケジュール）")
        content = text.split(sec1_title)[1].split(sec2_title)[0].strip()
        
        # テキスト内の「時刻」「内容」などの改行を簡易的にリスト化して表にする
        lines = [line.strip() for line in content.split("\n") if ":" in line]
        if lines:
            data = [line.split("：") if "：" in line else line.split(":") for line in lines]
            df = pd.DataFrame(data, columns=["項目/時刻", "詳細"])
            st.table(df) # 表形式で表示
        else:
            st.info(content)

    # --- 2. 容疑者の証言（吹き出し形式） ---
    if sec2_title in text:
        st.markdown("#### 🗣️ 容疑者の証言")
        testimony_part = text.split(sec2_title)[1].split(sec3_title)[0]
        
        # 容疑者ごとに分割（「・」や「容疑者」というキーワードで区切る）
        suspects = testimony_part.split("・")
        for s in suspects:
            clean_s = s.strip()
            if clean_s:
                # 名前とセリフを分ける（例 容疑者A: 「〜〜」）
                if "：" in clean_s:
                    name, quote = clean_s.split("：", 1)
                elif ":" in clean_s:
                    name, quote = clean_s.split(":", 1)
                else:
                    name, quote = "容疑者", clean_s
                
                with st.chat_message("user", avatar="👤"):
                    st.markdown(f"**{name}**")
                    st.write(quote)

    # --- 3. 探偵の推理 ---
    if sec3_title in text:
        st.markdown("#### 🕵️‍♂️ 探偵の現時点の結論")
        detective_part = text.split(sec3_title)[1]
        with st.chat_message("assistant", avatar="🕵️"):
            st.write(f"「{detective_part.strip()}」")

# --- メインアプリ構成 ---

st.set_page_config(page_title="探偵アシスタント：事件簿", layout="wide")
st.title("🔎 探偵アシスタント：Web版")

with st.sidebar:
    st.header("🗂 事件ファイル選択")
    scenario_pdfs = [f for f in os.listdir(".") if f.endswith(".pdf") and f.startswith("scenario")]
    selected_pdf = st.selectbox("調査する事件を選んでください", scenario_pdfs)
    
    if st.button("捜査を開始する"):
        display_txt, answer_txt = extract_text_from_pdf(selected_pdf)
        st.session_state.current_scenario = display_txt
        st.session_state.answer_key = answer_txt
        st.session_state.chat_history = []
        
        # 画像対応（JPG / PNG 両対応）
        base_name = selected_pdf.replace(".pdf", "")
        img_jpg, img_png = f"{base_name}.jpg", f"{base_name}.png"
        if os.path.exists(img_jpg):
            st.session_state.current_image = img_jpg
        elif os.path.exists(img_png):
            st.session_state.current_image = img_png
        else:
            st.session_state.current_image = None

if "current_scenario" in st.session_state:
    if st.session_state.current_image:
        st.image(st.session_state.current_image, caption="現場写真・見取り図", use_container_width=True)
    
    display_structured_scenario(st.session_state.current_scenario)

    st.divider()
    st.subheader("💡 矛盾を指摘して探偵を導こう")
    
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("例：容疑者Aの証言は花火の音と矛盾している")

    if user_input:
        st.session_state.chat_history.append(("human", user_input))
        
        is_correct = False
        target_suspect = ""
        for name in ["A", "B", "C", "D"]:
            if f"容疑者{name}" in st.session_state.answer_key:
                target_suspect = name
                break
        
        if target_suspect and (target_suspect in user_input) and any(kw in user_input for kw in ["矛盾", "嘘", "おかしい", "静か"]):
            ans = f"「なるほど！{target_suspect}の証言は確かに不自然だ。君の指摘で目が覚めたよ！」"
            st.balloons()
        else:
            ans = "「うーむ、一理あるようだが……まだ決定的とは言えないな。別の視点はないか？」"
        
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun()
else:
    st.info("サイドバーから事件ファイルを選択して「捜査を開始」してください。")