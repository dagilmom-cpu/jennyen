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

def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    md = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(md, unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP")

# --- [2] API 설정 (코딩에 직접 키 입력 완료!) ---
CLAUDE_API_KEY = "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"
ELEVENLABS_API_KEY = "sk_6de3761d943fe084486efb94676a26daab9fc28640b57951"
VOICE_ID = "O7njSdfuJRf0H4s0EQeo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- [3] 입력창 (Win+H로 말해줘!) ---
prompt = st.chat_input("Hi Jenny! (제니랑 영어로 대화해요!)")

# --- [4] 대화 로직 (작동하는 모델명으로 수정) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("제니가 생각 중... 🥂"):
            claude_url = "https://api.anthropic.com/v1/messages"
            claude_headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            claude_data = {
                "model": "claude-3-5-sonnet-latest", # ⭐ 실제 작동하는 최신 모델명!
                "max_tokens": 1024,
                "system": """너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지. 
                1. 한 줄 영어 대화. (첫 인사만 한국어 가능)
                2. 이름, 나이, 직업을 물어보고 기억해줘.
                3. 슬랭 사용 시 끝에 [Slang: 단어-뜻] 붙이기.
                4. 보이스 재생 시 한국어는 빼고 오직 영어만 읽어줘.""",
                "messages": st.session_state.messages
            }
            
            response = requests.post(claude_url, headers=claude_headers, json=claude_data, timeout=15)
            res_json = response.json()

            if "content" in res_json:
                answer = res_json["content"][0]["text"]
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                    # 보이스 전용 텍스트 필터링 (영어만)
                    voice_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                    voice_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', voice_text).strip()
                    
                    if voice_text:
                        el_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                        el_headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVENLABS_API_KEY}
                        v_res = requests.post(el_url, headers=el_headers, json={"text": voice_text, "model_id": "eleven_multilingual_v2"})
                        if v_res.status_code == 200:
                            autoplay_audio(v_res.content)
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                # 에러 메시지 상세 출력
                st.error(f"제니의 긴급 진단: {res_json.get('error', {}).get('message', '연결 확인!')}")

    except Exception as e:
        st.error(f"시스템 오류: {e}")
