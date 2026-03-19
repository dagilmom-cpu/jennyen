import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# --- [1] 디자인 설정 ---
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

def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP (Gemini)")

# --- [2] API 및 모델 설정 ---
try:
    # Secrets에서 키 가져오기
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_API_KEY)

    JENNY_INSTRUCTION = """
    너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지.
    1. 미국 인스타, 트위터(X)의 최신 신조어와 밈을 사용해.
    2. 무조건 영어 한 줄 대화! (첫 인사만 한국어 가능)
    3. 슬랭 사용 시 끝에 [Slang: 단어-뜻] 붙이기.
    4. 보이스 재생을 위해 한국어는 빼고 오직 영어만 읽어줘.
    """

    # ⭐ 모델명을 가장 표준적인 'gemini-1.5-flash'로 설정
    # 만약 계속 404가 나면 'models/gemini-1.5-flash'로 자동 시도하도록 예외 처리 포함
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=JENNY_INSTRUCTION
        )
        # 테스트 호출로 모델 존재 확인
        model.generate_content("test") 
    except:
        model = genai.GenerativeModel(
            model_name='models/gemini-1.5-flash',
            system_instruction=JENNY_INSTRUCTION
        )

    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])
    if "messages" not in st.session_state:
        st.session_state.messages = []

except Exception as e:
    st.error(f"설정 에러: Secrets를 확인해줘 언니! ({e})")
    st.stop()

# 대화 로그 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- [3] 메인 대화 로직 ---
prompt = st.chat_input("Hi Jenny! 오늘 분위기 어때? 🔥")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        with st.spinner("제니가 생각 중... 🥂"):
            response = st.session_state.chat_session.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                
                # ElevenLabs 음성 생성
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2"}
                    )
                    if v_res.status_code == 200:
                        autoplay_audio(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"제니 긴급 상황: {e}")
