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

# 🔊 음성 재생 함수 (다시 듣기 지원)
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

st.title("🐆 제니쌤 영어 VIP (v1.3 Stable)")

# [2] API 설정
try:
    # 🚨 보안을 위해 Secrets에서 가져오는 구조를 유지합니다.
    # (Secrets 창에 AIzaSyBKZpR9gE6PVAgZHtWGCvZYolvYfyTu_Po 를 꼭 업데이트해주세요!)
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    # ⭐ 지침 수정: 슬랭 빈도 낮추기 + 천천히 말하기 강조
    JENNY_PROMPT = """너는 24세 재미교포 제니야. 힙하지만 다정한 MZ 영어쌤이지.
    1. 슬랭('10Q', 'YOLO' 등)은 대화 흐름상 꼭 필요할 때만 가끔씩 섞어줘. (너무 남발하지 마!)
    2. 슬랭을 쓰면 반드시 끝에 [Slang: 단어-한국어 뜻] 형식으로 붙여줘.
    3. 무조건 영어 한 줄 대화! (첫 인사만 한국어 가능)
    4. 음성 재생을 위해 본문에는 영어만 써줘.
    5. 아주 천천히, 언니가 영어를 잘 알아들을 수 있게 또박또박 말하는 스타일이야."""

    model = genai.GenerativeModel(model_name=st.session_state.model_path, system_instruction=JENNY_PROMPT)
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"설정 확인 필요: {e}"); st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 대화 및 보이스 로직
prompt = st.chat_input("Hi Jenny! 천천히 말해줘~ ☕")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 생각 중... 🥂"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY}
                    
                    # ⭐ 목소리 속도 늦추기 세팅 (Stability를 더 높여서 정적으로 만듭니다)
                    data = {
                        "text": v_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.95,        # 0.8 -> 0.95로 높여서 더 차분하게!
                            "similarity_boost": 0.85, # 제니 목소리 특성은 더 선명하게!
                            "style": 0.0,
                            "use_speaker_boost": True
                        }
                    }
                    
                    v_res = requests.post(url, json=data, headers=headers)
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"에러 발생: {e}")
