import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# --- [1] 럭셔리 호피 디자인 설정 ---
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

# 🔊 강력한 오디오 재생 함수
def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
        <audio id="jenny_voice" autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById('jenny_voice');
            audio.play().catch(e => console.log("Autoplay blocked: " + e));
        </script>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP (Gemini)")

# --- [2] API 설정 (언니의 새로운 키들 반영) ---
# 구글 키와 일레븐랩스 키를 깨끗하게 정리해서 넣었습니다.
GOOGLE_API_KEY = "AIzaSyBV_nrgqg7UJC-VBHBeuBw_Zxp0U7ybv-w".strip()
ELEVEN_KEY = "sk_9665d7f430925bb8ef413175c17b94f9c74ea27f2d88b5f5".strip()
VOICE_ID = "O7njSdfuJRf0H4s0EQeo"

# Gemini 모델 설정 (가장 빠르고 저렴한 Flash 모델)
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

if "messages" not in st.session_state:
    st.session_state.messages = []

# 제니의 핵심 학습 지침
JENNY_SYSTEM_PROMPT = """너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지. 
1. 한 줄 영어 대화만 해. (첫 인사만 한국어 가능)
2. 상대방의 이름, 나이, 직업을 물어보고 대화 중에 기억해서 불러줘.
3. 힙한 슬랭 사용 시 끝에 [Slang: 단어-뜻] 붙이기.
4. 보이스 재생을 위해 영어 뒤에 한국어 설명을 배치해."""

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- [3] 입력창 ---
prompt = st.chat_input("Hi Jenny! (공짜니까 마음껏 수다 떨자 🥂)")

# --- [4] 메인 로직 (Gemini + ElevenLabs) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("제니가 빛의 속도로 생각 중... 🥂"):
            # 1. Gemini 대화 요청 (이전 대화 내역 포함)
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat = model.start_chat(history=history)
            
            # 지침 주입하여 메시지 전송
            full_prompt = f"{JENNY_SYSTEM_PROMPT}\n\nUser: {prompt}"
            response = chat.send_message(full_prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.markdown(answer)
                
                # 2. 음성 생성 (영어만 추출)
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
        st.error(f"시스템 오류 발생: {e}")
