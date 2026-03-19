import streamlit as st
import requests
import re
import base64

# ---------------------------
# [1] 기본 설정 & 스타일
# ---------------------------
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")

st.markdown("""
<style>
.stApp {
    background-image: url("https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg");
    background-size: cover;
    background-attachment: fixed;
}
html, body, [class*="css"], .stMarkdown, p, span, div {
    color: #000000 !important;
    font-weight: 900 !important;
    text-shadow: -2px -2px 0 #FFF, 2px -2px 0 #FFF, -2px 2px 0 #FFF, 2px 2px 0 #FFF !important;
}
.stChatMessage[data-testid="stChatMessageAssistant"] {
    background-color: rgba(0, 0, 0, 0.95) !important;
    border: 2px solid #FFD700 !important;
    border-radius: 15px;
}
.stChatMessage[data-testid="stChatMessageAssistant"] p {
    color: #FFFFFF !important;
    text-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP")

# ---------------------------
# [2] API 키 안전 로딩
# ---------------------------
def get_clean_key(name):
    val = st.secrets.get(name, "")
    return str(val).strip().replace("\n", "").replace("\r", "")

CLAUDE_API_KEY = get_clean_key("CLAUDE_API_KEY")
ELEVENLABS_API_KEY = get_clean_key("ELEVENLABS_API_KEY")
VOICE_ID = get_clean_key("VOICE_ID")

if not CLAUDE_API_KEY or not ELEVENLABS_API_KEY:
    st.warning("Secrets에 API 키 넣어줘 🔐")
    st.stop()

# ---------------------------
# [3] 세션 상태
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

# ---------------------------
# [4] Claude 메시지 포맷 변환
# ---------------------------
def format_messages(messages):
    formatted = []
    for m in messages:
        formatted.append({
            "role": m["role"],
            "content": [{"type": "text", "text": m["content"]}]
        })
    return formatted

# ---------------------------
# [5] UI 옵션
# ---------------------------
level = st.selectbox("🎯 영어 레벨", ["초급", "중급", "원어민"])

level_map = {
    "초급": "아주 쉬운 영어",
    "중급": "일상 회화 영어",
    "원어민": "슬랭 포함 자연스러운 영어"
}

# ---------------------------
# [6] 기존 메시지 출력
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# [7] 입력창
# ---------------------------
prompt = st.chat_input("Hi Jenny! (말 걸어봐 💬)")

# ---------------------------
# [8] 메인 로직
# ---------------------------
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        with st.spinner("제니 생각중... 💭"):

            # Claude 요청
            c_headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            system_prompt = f"""
너는 24세 재미교포 제니야.
MZ 영어 선생님이고 힙하게 말해.
{level_map[level]} 수준으로 한 줄 영어만 말해.
슬랭 사용 시 [Slang: 단어-뜻] 붙여.
"""

            c_data = {
                "model": "claude-3-5-sonnet-latest",
                "max_tokens": 300,
                "system": system_prompt,
                "messages": format_messages(st.session_state.messages)
            }

            res = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=c_headers,
                json=c_data,
                timeout=40
            ).json()

            if "content" not in res:
                st.error("Claude 응답 오류 😢")
                st.stop()

            answer = res["content"][0]["text"]

        # ---------------------------
        # [9] 텍스트 먼저 출력 (UX 개선)
        # ---------------------------
        with st.chat_message("assistant"):
            st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

        # ---------------------------
        # [10] 음성 생성 (비동기 느낌)
        # ---------------------------
        v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()

        if v_text:
            with st.spinner("🎤 제니가 말하는 중..."):

                el_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                el_headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": ELEVENLABS_API_KEY
                }

                el_data = {
                    "text": v_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.4,
                        "similarity_boost": 0.8
                    }
                }

                v_res = requests.post(
                    el_url,
                    headers=el_headers,
                    json=el_data,
                    timeout=40
                )

                if v_res.status_code == 200:
                    audio_bytes = v_res.content
                    st.session_state.last_audio = audio_bytes

                    # 🔊 안정적인 재생 방식
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

                else:
                    st.warning("음성 생성 실패 😢")

    except Exception as e:
        st.error(f"시스템 오류: {e}")

# ---------------------------
# [11] 다시 듣기 버튼
# ---------------------------
if st.session_state.last_audio:
    if st.button("🔊 다시 들어보기"):
        st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)
