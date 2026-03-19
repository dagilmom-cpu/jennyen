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

# 🔊 소리 재생 필살기 (버튼 + 자동재생 혼합)
def play_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    # 1. 일단 자동 재생 시도
    md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(md, unsafe_allow_html=True)
    # 2. 혹시 안 들릴까봐 재생 바도 작게 보여주기
    st.audio(audio_bytes, format="audio/mp3")

st.title("🐆 제니쌤 영어 VIP (Gemini)")

# [2] API 설정
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)

    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    model = genai.GenerativeModel(
        model_name=st.session_state.model_path,
        system_instruction="너는 24세 재미교포 제니야. 힙한 MZ 영어쌤. 무조건 영어 한 줄 대화만 해. 슬랭 사용 시 [Slang: 단어-뜻]을 꼭 붙여줘."
    )

    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"설정 확인 필요: {e}")
    st.stop()

# 대화 로그 출력
if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 입력창 및 보이스 로직
prompt = st.chat_input("Hi Jenny!")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 녹음 중... 🎙️"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                # 소리 생성용 텍스트 가공 (영어만)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2"}
                    )
                    if v_res.status_code == 200:
                        play_voice(v_res.content)
                    else:
                        st.warning("목소리 엔진이 조금 피곤한가봐요!")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"제니가 말을 못해요: {e}")
