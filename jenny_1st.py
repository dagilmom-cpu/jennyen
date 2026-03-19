import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# [1] 디자인 설정
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("""
    <style>
    .stApp { 
        background-image: url("https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg"); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    html, body, [class*="css"], .stMarkdown, p, span, div { 
        color: #000000 !important; font-weight: 900 !important; 
        text-shadow: -2px -2px 0 #FFF, 2px -2px 0 #FFF, -2px 2px 0 #FFF, -2px 2px 0 #FFF !important; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: rgba(0, 0, 0, 0.95) !important; 
        border: 2px solid #FFD700 !important; border-radius: 15px; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] p { 
        color: #FFFFFF !important; text-shadow: none !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# 🔊 음성 재생 및 다시 듣기 함수
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

st.title("🐆 제니쌤 영어 VIP (Jenny_v1.2)")

# [2] API 설정 (🚨 절대 코딩에 키를 직접 적지 마세요!)
try:
    # Streamlit Secrets에서 가져오기
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    # 모델 자동 탐색 (404 방지)
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    # 제니 지침 (슬랭 한글 번역 포함)
    JENNY_PROMPT = """너는 24세 재미교포 제니야. 힙한 MZ 영어쌤이지.
    1. '10Q', '143', 'YEET', 'YOLO' 같은 슬랭을 섞어서 한 줄 영어로만 대답해.
    2. 슬랭을 쓰면 반드시 끝에 [Slang: 단어-한국어 뜻] 형식으로 붙여줘. (뜻은 한국어로!)
    3. 말은 차분하고 또박또박하게 해줘. (ElevenLabs 속도 조절용)
    4. 음성 재생을 위해 대답 본문에는 한국어를 섞지 마 (대괄호 안에서만 한국어 허용)."""

    model = genai.GenerativeModel(model_name=st.session_state.model_path, system_instruction=JENNY_PROMPT)
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"⚠️ 설정 에러: Secrets 창에 새 키를 넣었는지 확인해줘 언니! ({e})")
    st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 대화 로직
prompt = st.chat_input("Hi Jenny! I'm back! 🔥")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 메시지 작성 중... 🥂"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                # 음성용 텍스트 필터링
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                
                if v_text:
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY}
                    data = {
                        "text": v_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.8, "similarity_boost": 0.8}
                    }
                    v_res = requests.post(url, json=data, headers=headers)
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"제니 긴급 상황: {e}")
