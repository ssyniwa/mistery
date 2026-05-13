import streamlit as st
from pypdf import PdfReader
import os

def extract_text_from_pdf(file_path):
    """PDFからテキストを抽出し、項目1, 2, 3の部分を抜き出す"""
    reader = PdfReader(file_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    
    # 「4. 事件の真相」より前の部分（項目1, 2, 3）のみを取得
    display_content = full_text.split("4. 事件の真相")[0]
    # 正解データ（判定用）として後半を取得
    answer_content = full_text.split("4. 事件の真相")[-1] if "4. 事件の真相" in full_text else ""
    
    return display_content, answer_content

st.title("🔎 探偵アシスタント：事件ファイル選択")

# 1. シナリオファイルの選択
# フォルダ内のPDFファイルをリストアップ（仮にscenarioで始まるファイル）
scenario_files = [f for f in os.listdir(".") if f.endswith(".pdf") and "scenario" in f]

if not scenario_files:
    st.error("シナリオファイル（PDF）が見つかりません。")
else:
    selected_file = st.selectbox("調査する事件を選択してください", scenario_files)

    if st.button("捜査開始"):
        # PDFから内容を抽出してセッションに保存
        display_text, answer_text = extract_text_from_pdf(selected_file)
        st.session_state.current_scenario = display_text
        st.session_state.answer_key = answer_text
        st.session_state.chat_history = []

# 2. 画面表示（項目1, 2, 3の内容）
if "current_scenario" in st.session_state:
    st.divider()
    st.markdown("### 📋 事件記録（項目1〜3）")
    # PDFのテキストを整形して表示
    st.info(st.session_state.current_scenario)

    # 3. 正誤判定パート
    st.subheader("🕵️‍♂️ 推理の修正")
    user_input = st.chat_input("容疑者の嘘を指摘してください")

    if user_input:
        # 簡易判定：正解データ（answer_key）に含まれるキーワードと照合
        # 例：正解データに「容疑者A」とあれば、入力に「A」が含まれるか確認
        is_correct = False
        # PDF内の正解セクションから嘘つきの名前を特定するロジック（簡易版）
        if "容疑者A" in st.session_state.answer_key and "A" in user_input:
            is_correct = True
        elif "容疑者B" in st.session_state.answer_key and "B" in user_input:
            is_correct = True
        elif "容疑者C" in st.session_state.answer_key and "C" in user_input:
            is_correct = True
        elif "容疑者D" in st.session_state.answer_key and "D" in user_input:
            is_correct = True

        if is_correct:
            response = "「素晴らしい！まさにその通りだ。私の推理が間違っていたよ。」"
            st.balloons()
        else:
            response = "「うーむ、それは決定的な矛盾とは言えないようだ。もう一度よく資料を読んでみてくれ。」"
        
        st.session_state.chat_history.append(("player", user_input))
        st.session_state.chat_history.append(("detective", response))

    # チャット履歴表示
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)