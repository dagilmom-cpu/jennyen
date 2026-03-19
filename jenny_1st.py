import streamlit as st
import requests
import re
import base64

# --- [1] 디자인 & 설정 ---
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("""
    <style>
    .stApp { background-image: url("https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg"); background-size: cover; background-attachment: fixed; }
    html, body, [class*="css"], .stMarkdown, p, span, div { color: #000000 !important; font-weight: 900 !important; text-shadow: -2px -2px 0 #FFF, 2px -2px 0 #FFF, -2px 2px 0 #FFF, -2px 2px 0 #FFF !important; }
    .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: rgba(0, 0, 0, 0.95) !important; border: 2px solid #FFD700 !important; border-radius: 15px; }
    .stChatMessage[data-testid="stChatMessageAssistant"] p { color: #FFFFFF !important; text-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

def autoplay_audio(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    md = f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(md, unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP")

# --- [2] API 설정 (강력한 인증 방어) ---
def get_clean_key(name):
    # Secrets에서 키를 가져와 앞뒤 공백과 줄바꿈을 완벽히 제거합니다.
    val = st.secrets.get(name, "")
    return str(val).strip().replace("\n", "").replace("\r", "")

CLAUDE_API_KEY = get_clean_key("CLAUDE_API_KEY")
ELEVENLABS_API_KEY = get_clean_key("ELEVENLABS_API_KEY")
VOICE_ID = get_clean_key("VOICE_ID")

if not CLAUDE_API_KEY or not ELEVENLABS_API_KEY:
    st.warning("Secrets 설정에서 API 키 입력을 확인해줘 언니! 🔓")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- [3] 입력창 ---
prompt = st.chat_input("Hi Jenny! (새로운 열쇠로 대화하자!)")

# --- [4] 대화 로직 (모델: claude-sonnet-4-6) ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("제니가 새 목소리를 준비 중... 🥂"):
            # 1. Claude 대화 요청
            c_headers = {"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            c_data = {
                "model": "claude-sonnet-4-6", 
                "max_tokens": 1024, 
                "system": "너는 24세 재미교포 제니야. 힙하고 친절한 MZ 선생님이지. 한 줄 영어 대화만 해. 슬랭 사용 시 [Slang: 단어-뜻] 붙여줘. 한국어는 보이스용 텍스트에서 제외할 수 있게 영어 뒤에 배치해.", 
                "messages": st.session_state.messages
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=c_headers, json=c_data, timeout=20).json()

            if "content" in res:
                answer = res["content"][0]["text"]
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                    # 2. 음성 생성 (새로운 키 사용)
                    # 영어 문장만 골라내기 (정규식)
                    v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                    v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                    
                    if v_text:
                        el_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                        el_headers = {
                            "Accept": "audio/mpeg", 
                            "Content-Type": "application/json", 
                            "xi-api-key": ELEVENLABS_API_KEY 
                        }
                        v_res = requests.post(el_url, headers=el_headers, json={"text": v_text, "model_id": "eleven_multilingual_v2"})
                        
                        if v_res.status_code == 200:
                            autoplay_audio(v_res.content)
                        else:
                            st.warning(f"목소리 에러: {v_res.text}")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"제니 진단: {res.get('error', {}).get('message', '연결 확인!')}")
    except Exception as e:
        st.error(f"오류 발생: {e}")
