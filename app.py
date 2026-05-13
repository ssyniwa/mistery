import streamlit as st
import google.generativeai as genai

# --- APIの設定 ---
# StreamlitのSecrets管理（公開時はここを使用）または直接入力
os_api_key = st.sidebar.text_input("Gemini API Key", type="password")
if os_api_key:
    genai.configure(api_key=os_api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- ゲーム管理用のセッション状態 ---
if "game_data" not in st.session_state:
    st.session_state.game_data = None  # 証言や嘘の正解を保持

# --- サイドバー：設定 ---
with st.sidebar:
    st.header("🏠 ホテル設定")
    event_info = st.text_area("本日のイベント情報", 
        "20:00-21:00：3階ホールにて大音量のジャズライブ\n20:30-21:30：中庭で花火打ち上げ")
    
    st.subheader("👥 容疑者設定")
    suspects_profile = []
    for i in range(1, 5):
        with st.expander(f"容疑者 {i}"):
            name = st.text_input("名前", value=f"人物{i}", key=f"n{i}")
            job = st.text_input("職業", value="教師", key=f"j{i}")
            suspects_profile.append(f"名前:{name}, 職業:{job}")

    if st.button("事件発生！（証言生成）") and os_api_key:
        # Geminiに証言を生成させるプロンプト
        prompt = f"""
        あなたはミステリーゲームの進行役です。
        以下の設定に基づき、4人の容疑者の前夜20:30の証言を生成してください。
        
        【ホテルのイベント】
        {event_info}
        
        【容疑者リスト】
        {", ".join(suspects_profile)}
        
        【ルール】
        1. 誰か一人が、イベント情報と矛盾する「嘘」をついています。
        2. 他の3人は真実を述べています。
        3. 探偵は最初は「全員の証言に矛盾はない」と勘違いしています。
        
        出力形式：
        容疑者名: 証言内容
        (最後に、誰が嘘つきで、どのイベントと矛盾しているかの正解を「正解：」の後に書いてください)
        """
        response = model.generate_content(prompt)
        st.session_state.game_data = response.text
        st.session_state.chat_history = []

# --- メイン画面 ---
st.title("🔎 Gemini×探偵アシスタント")

if st.session_state.game_data:
    # 証言の表示（正解部分は隠す）
    display_text = st.session_state.game_data.split("正解：")[0]
    st.info(display_text)
    
    st.subheader("🕵️‍♂️ 探偵の初期推理")
    st.warning("「ふむ、全員のアリバイは完璧だ。これは外部の犯行だろうか？」")

    # プレイヤーの指摘
    user_input = st.chat_input("探偵に矛盾を指摘してください")
    
    if user_input:
        # 指摘が正しいかGeminiに判定させる
        judge_prompt = f"""
        ゲームの正解データ: {st.session_state.game_data}
        プレイヤーの指摘: {user_input}
        
        プレイヤーの指摘が、嘘つきの矛盾を正しく突いているか判定してください。
        判定後、探偵になりきって、プレイヤーへの反応を返してください。
        正解なら「君の言う通りだ！〇〇の証言はおかしい！」、不正解なら「それはどうかな……？」というトーンで。
        """
        response = model.generate_content(judge_prompt)
        st.session_state.chat_history.append(("player", user_input))
        st.session_state.chat_history.append(("detective", response.text))

    # チャット表示
    for role, text in st.session_state.get("chat_history", []):
        with st.chat_message(role):
            st.write(text)
else:
    st.write("左側のサイドバーで設定を行い、「事件発生」ボタンを押してください。")