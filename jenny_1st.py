import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# [1] 디자인 설정 (생략)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("<style>.stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; }</style>", unsafe_allow_html=True)

# 🔊 ElevenLabs 재생 함수 (속도감 개선)
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio id="jenny_voice" autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3") # 확인용 플레이어

st.title("🐆 제니쌤 영어 VIP")

# [2] API 설정
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    # 모델 자동 탐색
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    # 🧠 제니의 뇌에 '슬랭 데이터'와 '천천히 말하기' 주입
    JENNY_PROMPT = """너는 24세 재미교포 제니야. 힙한 MZ 영어쌤이지.
    1. '10Q'(Thank you), '143'(I love you), 'YEET' 같은 슬랭과 약어를 섞어서 힙하게 말해줘.
    2. 무조건 영어 한 줄 대화! (첫 인사만 한국어 가능)
    3. 말을 너무 빨리 하지 말고, 차근차근 언니에게 설명하듯 말해줘.
    4. 슬랭 사용 시 끝에 [Slang: 단어-뜻] 붙이기."""

    model = genai.GenerativeModel(model_name=st.session_state.model_path, system_instruction=JENNY_PROMPT)
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"설정 확인 필요: {e}"); st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 대화 로직
prompt = st.chat_input("Hi Jenny!")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 생각 중... 🥂"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                # 음성용 텍스트 필터링
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY}
                    
                    # ⭐ 속도와 감정을 조절하는 핵심 파트!
                    data = {
                        "text": v_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.8,        # 값이 높을수록 목소리가 차분하고 안정적이야 (0.0 ~ 1.0)
                            "similarity_boost": 0.8, # 제니의 원래 목소리 특징을 더 강하게!
                            "style": 0.0,            # 감정 과잉 방지
                            "use_speaker_boost": True
                        }
                    }
                    
                    v_res = requests.post(url, json=data, headers=headers)
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"에러: {e}")
