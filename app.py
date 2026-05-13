import streamlit as st
from pypdf import PdfReader
import os

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
    """テキストをセクションごとに整形して表示する"""
    
    # セクションごとに分割（PDFの見出しに合わせて調整）
    sections = {
        "基本情報": "1. ホテルの基本情報",
        "容疑者の証言": "2. 容疑者たちの証言",
        "探偵の推理": "3. 探偵の初期推理"
    }

    # --- 1. ホテルの基本情報 ---
    if sections["基本情報"] in text:
        st.markdown("#### 🏨 現場検証データ")
        content = text.split(sections["基本情報"])[1].split(sections["容疑者の証言"])[0]
        with st.container(border=True):
            st.markdown(content.strip().replace("\n", "  \n"))

    # --- 2. 容疑者の証言（カード型で横に並べる） ---
    st.markdown("### 🗣️ 容疑者の証言")
    if sections["容疑者の証言"] in text:
        testimony_part = text.split(sections["容疑者の証言"])[1].split(sections["探偵の推理"])[0]
        # 「容疑者A」「容疑者B」などで分割してカード化
        cols = st.columns(2) # 2列で表示
        
        # 簡易的な分割（実際の内容に合わせて微調整が必要）
        suspects_raw = testimony_part.split("・")
        for idx, s in enumerate(suspects_raw):
            if len(s.strip()) > 5:
                with cols[idx % 2]:
                    st.chat_message("user").write(s.strip())

    # --- 3. 探偵の推理 ---
    if sections["探偵の推理"] in text:
        st.markdown("#### 🕵️‍♂️ 探偵の現時点の結論")
        detective_part = text.split(sections["探偵の推理"])[1]
        st.warning(f"探偵「{detective_part.strip()}」")

# --- メインアプリ構成 ---

st.set_page_config(page_title="探偵アシスタント：事件簿", layout="wide")
st.title("🔎 探偵アシスタント：Web版")

# 1. シナリオ選択（サイドバー）
with st.sidebar:
    st.header("🗂 事件ファイル選択")
    all_files = os.listdir(".")
    scenario_pdfs = [f for f in all_files if f.endswith(".pdf") and f.startswith("scenario")]
    
    selected_pdf = st.selectbox("調査する事件を選んでください", scenario_pdfs)
    
    if st.button("捜査を開始する"):
        # データの抽出
        display_txt, answer_txt = extract_text_from_pdf(selected_pdf)
        st.session_state.current_scenario = display_txt
        st.session_state.answer_key = answer_txt
        st.session_state.chat_history = []
        # 画像パスの特定（JPGとPNGの両方に対応）
        base_name = selected_pdf.replace(".pdf", "")
        img_path_jpg = f"{base_name}.jpg"
        img_path_png = f"{base_name}.png"

        if os.path.exists(img_path_jpg):
            st.session_state.current_image = img_path_jpg
        elif os.path.exists(img_path_png):
            st.session_state.current_image = img_path_png
        else:
            st.session_state.current_image = None
# 2. メイン画面の表示
if "current_scenario" in st.session_state:
    
    # 画像があれば表示
    if st.session_state.current_image:
        st.image(st.session_state.current_image, caption="現場写真・見取り図", use_container_width=True)
    
    # 構造化テキストの表示
    display_structured_scenario(st.session_state.current_scenario)

    st.divider()

    # 3. チャット・推理指摘パート
    st.subheader("💡 矛盾を指摘して探偵を導こう")
    
    # チャット履歴表示
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    user_input = st.chat_input("（例：容疑者Aの証言は花火の音と矛盾している）")

    if user_input:
        # プレイヤーのメッセージを履歴に追加
        st.session_state.chat_history.append(("human", user_input))
        
        # 判定ロジック（正解PDFに含まれる容疑者名とキーワードで簡易チェック）
        # 正解データ（answer_key）に「容疑者A」があり、入力に「A」が含まれるか
        is_correct = False
        target_suspect = ""
        
        for name in ["A", "B", "C", "D"]:
            if f"容疑者{name}" in st.session_state.answer_key:
                target_suspect = name
                break
        
        if target_suspect in user_input and ("矛盾" in user_input or "嘘" in user_input or "おかしい" in user_input):
            is_correct = True

        if is_correct:
            ans = f"「なるほど！{target_suspect}の証言は確かに不自然だ。君の指摘で目が覚めたよ！」"
            st.balloons()
        else:
            ans = "「うーむ、一理あるようだが……まだ決定的とは言えないな。別の視点はないか？」"
        
        st.session_state.chat_history.append(("assistant", ans))
        st.rerun() # 画面を更新して最新のチャットを表示

else:
    st.info("サイドバーから事件ファイルを選択して「捜査を開始」してください。")