import streamlit as st

# ファイルからデータを読み込む関数
def load_case():
    with open("case_data.txt", "r", encoding="utf-8") as f:
        return f.read()

st.title("🔎 ミステリー：碧水の館殺人事件")

# シナリオデータの取得
case_text = load_case()

# --- 画面表示 ---
st.subheader("📌 現場の情報と証言")
st.text_area("事件ファイル", value=case_text, height=300)

# --- 推理パート ---
user_input = st.chat_input("矛盾している容疑者と、その理由を入力してください")

if user_input:
    # 簡易的な正誤判定（キーワードが含まれているか）
    if "A" in user_input and ("静か" in user_input or "花火" in user_input):
        st.success("🕵️‍♂️ 探偵「なるほど！容疑者Aは『静かだった』と言ったが、その時間は花火とジャズライブで騒がしかったはずだ！君の指摘通り、Aが犯人だ！」")
    else:
        st.error("🕵️‍♂️ 探偵「うーむ、その指摘には少し無理があるようだね。もう一度イベント情報と証言を読み直してみてくれないか？」")