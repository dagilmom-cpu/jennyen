import streamlit as st
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

# 🔊 소리 재생 함수 (가장 강력한 HTML5 오디오 주입 방식)
def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    # 팁: 브라우저 차단을 피하기 위해 ID와 강제 재생 스크립트를 포함했습니다.
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

st.title("🐆 제니쌤 영어 VIP")

# --- [2] API 설정 (언니의 최신 무적 키 직접 적용) ---
# Secrets에 넣으셨더라도 코드 실행 시 이 키들이 우선 적용되도록 세팅했습니다.
CLAUDE_API_KEY = "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".strip()
ELEVENLABS_API_KEY = "sk_9665d7f430925bb8ef413175c17b94f9c74ea27f2d88b5f5".strip()
VOICE_ID = "O7njSdfuJRf0H4s0EQeo"

# --- [3] 세션 상태 및 레벨 설정 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

level = st.selectbox("🎯 영어 레벨을 골라봐 언니!", ["초급", "중급", "원어민"])
level_map = {
    "초급": "아주 쉬운 영어",
    "중급": "일상 회화 영어",
    "원어민": "슬랭 포함 자연스러운 영어"
}

# 기존 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- [4] 입력창 ---
prompt = st.chat_input("Hi Jenny! (제니랑 수다 떨자! 💬)")

# --- [5] 메인 로직 (모델: claude-sonnet-4-6) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("제니가 힙한 문장을 생각 중... 🥂"):
            # 1. Claude API 호출
            claude_headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            claude_data = {
                "model": "claude-sonnet-4-6", # ⭐ 언니가 알려준 2026년 최신 모델!
                "max_tokens": 1024,
                "system": f"""너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지. 
                1. {level_map[level]} 수준으로 한 줄 영어 대화.
                2. 이름, 나이, 직업을 물어보고 기억해줘.
                3. 슬랭 사용 시 끝에 [Slang: 단어-뜻] 붙이기.
                4. 보이스 재생을 위해 영어 뒤에 한국어 설명을 배치해.""",
                "messages": st.session_state.messages
            }
            
            res = requests.post("https://api.anthropic.com/v1/messages", headers=claude_headers, json=claude_data, timeout=25).json()

            if "content" in res:
                answer = res["content"][0]["text"]
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                    # 2. 음성 생성 (영어 문장만 추출)
                    voice_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                    voice_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', voice_text).strip()
                    
                    if voice_text:
                        el_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                        el_headers = {
                            "Accept": "audio/mpeg", 
                            "Content-Type": "application/json", 
                            "xi-api-key": ELEVENLABS_API_KEY 
                        }
                        v_res = requests.post(el_url, headers=el_headers, json={"text": voice_text, "model_id": "eleven_multilingual_v2"})
                        
                        if v_res.status_code == 200:
                            autoplay_audio(v_res.content)
                        else:
                            st.warning(f"목소리 에러: {v_res.text}")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"제니 진단: {res.get('error', {}).get('message', '연결 확인!')}")

    except Exception as e:
        st.error(f"시스템 오류: {e}")
