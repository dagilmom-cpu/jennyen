import streamlit as st
import google.generativeai as genai
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 설정
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("<style>.stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; }</style>", unsafe_allow_html=True)

def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

st.title("🐆 제니쌤 영어 VIP (v1.5 Real-time)")

# [2] API 및 실시간 지침 설정
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    # ⭐ 오늘 날짜 반영 및 실시간 검색 권한 부여
    today_date = datetime.now().strftime("%Y년 %m월 %d일")
    
    JENNY_PROMPT = f"""너는 24세 재미교포 제니야. 오늘은 {today_date}이야.
    1. 너는 실시간 인터넷 정보를 검색할 수 있는 능력이 있어. 2026년 현재의 트렌드를 반영해줘.
    2. 미국 20대들이 실제로 쓰는 자연스러운 구어체와 슬랭(slay, rizz, bffr, no cap 등)을 적절히 섞어줘.
    3. 무조건 영어 한 줄 대화! 슬랭 사용 시 끝에 [Slang: 단어-한국어 뜻] 붙이기.
    4. 음성 재생을 위해 본문에는 영어만 써줘.
    5. 천천히, 하지만 아주 힙하게 말해주는 다정한 언니 모드야."""

    model = genai.GenerativeModel(model_name=st.session_state.model_path, system_instruction=JENNY_PROMPT)
    if "chat" not in st.session_state:
        # 대화 시작할 때 날짜를 한 번 더 인지시킴
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"설정 확인 필요: {e}"); st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 대화 로직
prompt = st.chat_input("Hi Jenny! What's the tea today? ☕")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 실시간 정보 확인 중... 🥂"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY}
                    data = {
                        "text": v_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.85, "similarity_boost": 0.8}
                    }
                    v_res = requests.post(url, json=data, headers=headers)
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"제니 긴급 상황: {e}")
