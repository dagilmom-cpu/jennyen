import streamlit as st
import google.generativeai as genai
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 설정
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🏄‍♀️")
st.markdown("<style>.stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; }</style>", unsafe_allow_html=True)

def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

# [2] 첫 화면 입력 폼
if "user_info" not in st.session_state:
    with st.container():
        st.title("🐆 Welcome to Jenny's Surf House!")
        name = st.text_input("Name")
        level = st.select_slider("Level", options=["초급", "중급", "고급"])
        goal = st.text_area("Why English?")
        if st.button("Start! 🏄‍♀️"):
            if name and goal:
                st.session_state.user_info = {"name": name, "level": level, "goal": goal}
                st.rerun()
    st.stop()

# [3] 제니의 인격 설정
user = st.session_state.user_info
JENNY_PROMPT = f"""너는 24세 재미교포 제니야. ENFP 서퍼이자 영어쌤이지.
- 이름: {user['name']}, 레벨: {user['level']}, 목적: {user['goal']} 정보를 바탕으로 대화해줘.
- 첫 인사만 한국어, 이후엔 영어로만! 힙하게 대답해줘.
- 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어-뜻] 붙이기.
- 목소리 재생을 위해 영어 본문만 읽어줘."""

# [4] API 연결 (⭐ 429 에러 방지용 '1.5-flash' 강제 고정)
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    # 🚨 2.5 버전은 20회 제한이 있으므로, 한도가 큰 1.5 버전을 '직접' 명시합니다.
    # 만약 'models/gemini-1.5-flash'로도 404가 난다면 'gemini-1.5-flash'로 바꿔보세요.
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash', 
        system_instruction=JENNY_PROMPT
    )
    
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.messages = []

except Exception as e:
    st.error(f"Setup error: {e}"); st.stop()

# [5] 메인 대화 로직
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

prompt = st.chat_input(f"Hey {user['name']}! Let's talk!")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is surfing... 🏄‍♀️"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.9, "similarity_boost": 0.8}})
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        # 에러 메시지에 '429'가 있으면 모델 이름을 다시 체크하게 안내
        if "429" in str(e):
            st.error("앗, 구글이 또 20회 제한을 걸었네! 잠시 후 다시 시도하거나 키를 바꿔야 할 것 같아. 😭")
        else:
            st.error(f"Error: {e}")
