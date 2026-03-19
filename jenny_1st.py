import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# --- [1] 럭셔리 호피 디자인 (제니쌤 시그니처) ---
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

# 🔊 사운드 자동 재생 함수
def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP (Gemini)")

# --- [2] API 및 학습 지침 설정 ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"]
VOICE_ID = st.secrets["VOICE_ID"]

genai.configure(api_key=GOOGLE_API_KEY)

# ⭐ 제니의 뇌에 "최신 트렌드"와 "슬랭" 지침을 박제!
JENNY_INSTRUCTION = """
너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지.
1. 지금 미국 인스타, 트위터(X)에서 가장 핫한 신조어와 밈(Meme)을 적극적으로 사용해줘.
2. 대화 중간중간 최신 팝컬처나 뉴스 이야기를 섞어서 진짜 현지인처럼 말해.
3. 무조건 영어 한 줄 대화! (첫 인사만 한국어 가능)
4. 슬랭이나 약어 사용 시 끝에 [Slang: 단어-뜻] 붙이기.
5. 보이스 재생을 위해 한국어는 빼고 오직 영어만 읽어줘.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=JENNY_INSTRUCTION
)

# 세션 관리 (대화 기억)
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 로그 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# --- [3] 메인 대화 로직 ---
prompt = st.chat_input("Hi Jenny! 오늘 미국에서 뭐가 핫해? 🔥")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        with st.spinner("제니가 인스타 확인 중... 🥂"):
            # 제미나이 답변 생성
            response = st.session_state.chat_session.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                
                # ElevenLabs 음성 생성 (영어만)
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
