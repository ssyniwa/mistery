import streamlit as st
from pypdf import PdfReader
import os
import pandas as pd
import re

# --- ユーティリティ関数 ---

def extract_text_from_pdf(file_path):
    """PDFからテキストを抽出し、表示用（項目1-3）と正解用に分割する"""
    try:
        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()
        
        parts = full_text.split("4. 事件の真相")
        display_content = parts[0]
        answer_content = parts[1] if len(parts) > 1 else ""
        return display_content, answer_content
    except Exception as e:
        st.error(f"PDFの読み込みに失敗しました: {e}")
        return None, None

def display_structured_scenario(text):
    """テキストを構造化して表示（3列の表 ＆ 吹き出し）"""
    
    sec1_title = "1. ホテルの基本情報"
    sec2_title = "2. 容疑者たちの証言"
    sec3_title = "3. 探偵の初期推理"

    # --- 1. ホテルの基本情報（3列の正確な表形式） ---
    if sec1_title in text:
        st.markdown("#### 🏨 ホテル・イベントスケジュール")
        content = text.split(sec1_title)[1].split(sec2_title)[0].strip()
        
        # 時刻(00:00-00:00)をキーにして行を分割する試み
        # PDFのテキスト構造に合わせ、正規表現で「時刻」「イベント」「詳細」を抽出
        lines = content.split("\n")
        table_data = []
        for line in lines:
            # 例: "20:30-20:50 花火 中庭から打ち上げ..." を分割
            match = re.match(r"(\d{1,2}:\d{2}\s*[-ー～]\s*\d{1,2}:\d{2})\s+([^\s]+)\s+(.*)", line.strip())
            if match:
                table_data.append(match.groups())
        
        if table_data:
            df = pd.DataFrame(table_data, columns=["時刻", "イベント名", "詳細内容"])
            st.dataframe(df, use_container_width=True, hide_index=True) # インデックスなしで表示
        else:
            # フォーマットが合わない場合はそのまま表示
            st.info(content)

    # --- 2. 容疑者の証言（アイコン付き吹き出し） ---
    if sec2_title in text:
        st.markdown("#### 🗣️ 容疑者の証言")
        testimony_part = text.split(sec2_title)[1].split(sec3_title)[0]
        
        # 箇条書き（・）で分割
        suspects = testimony_part.split("・")
        for s in suspects:
            clean_s = s.strip()
            if not clean_s: continue
            
            # 「容疑者A（職業/年齢）: セリフ」の形式を想定
            if "：" in clean_s:
                name_info, quote = clean_s.split("：", 1)
            elif ":" in clean_s:
                name_info, quote = clean_s.split(":", 1)
            else:
                name_info, quote = "関係者", clean_s
            
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{name_info.strip()}**")
                st.write(quote.strip())

    # --- 3. 探偵の推理 ---
    if sec3_title in text:
        st.markdown("#### 🕵️‍♂️ 探偵の現時点の結論")
        detective_part = text.split(sec3_title)[1]
        with st.chat_message("assistant", avatar="🕵️"):
            st.write(f"「{detective_part.strip()}」")

# --- メインアプリ構成 ---

st.set_page_config(page_title="探偵アシスタント：WEBミステリー", layout="wide")
st.title("🔎 探偵アシスタント：碧水の館事件簿")

with st.sidebar:
    st.header("🗂 事件ファイル選択")
    scenario_pdfs = [f for f in os.listdir(".") if f.endswith(".pdf") and f.startswith("scenario")]
    selected_pdf = st.selectbox("調査する事件を選んでください", scenario_pdfs)
    
    if st.button("捜査を開始する"):
        display_txt, answer_txt = extract_text_from_pdf(selected_pdf)
        st.session_state.current_scenario = display_txt
        st.session_state.answer_key = answer_txt
        st.session_state.chat_history = []
        
        base_name = selected_pdf.replace(".pdf", "")
        # PNGとJPGの優先チェック
        img_candidates = [f"{base_name}.png", f"{base_name}.jpg"]
        st.session_state.current_image = next((img for img in img_candidates if os.path.exists(img)), None)

if "current_scenario" in st.session_state:
    # 画像表示
    if st.session_state.current_image:
        st.image(st.session_state.current_image, caption="現場資料：見取り図・写真", use_container_width=True)
    
    # 構造化された表示を実行
    display_structured_scenario(st.session_state.current_scenario)

    st.divider()
    st.subheader("💡 矛盾を指摘して探偵を導こう")
    
    # チャット履歴
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("容疑者の嘘を指摘してください...")

    if user_input:
        st.session_state.chat_history.append(("human", user_input))
        
        # 判定
        is_correct = False
        target_suspect = ""
        for name in ["A", "B", "C", "D"]:
            if f"容疑者{name}" in st.session_state.answer_key:
                target_suspect = name
                break
        
        # 正解条件：正しい容疑者のアルファベットが含まれ、かつ矛盾を示唆する言葉がある
        keywords = ["矛盾", "嘘", "おかしい", "静か", "音", "聞こえ"]
        if target_suspect and (target_suspect in user_input) and any(kw in user_input for kw in keywords):
            ans = f"「なるほど！{target_suspect}の証言は現場の状況と明らかに食い違っている。君の指摘のおかげで真実が見えてきたよ！」"
            st.balloons()
        else:
            ans = "「……一理あるかもしれないが、まだ決定的な証拠とは言えないようだ。もう一度資料を精査してみよう。」"
        
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun()
else:
    st.info("サイドバーから事件ファイルを選択して「捜査を開始」してください。")