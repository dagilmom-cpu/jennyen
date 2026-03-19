import streamlit as st
import requests
import re
import base64

# [1] 디자인 (유지)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("""<style>
    .stApp { background-image: url("https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg"); background-size: cover; background-attachment: fixed; }
    html, body, [class*="css"], .stMarkdown, p, span, div { color: #000000 !important; font-weight: 900 !important; text-shadow: -2px -2px 0 #FFF, 2px -2px 0 #FFF, -2px 2px 0 #FFF, -2px 2px 0 #FFF !important; }
    .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: rgba(0, 0, 0, 0.95) !important; border: 2px solid #FFD700 !important; border-radius: 15px; }
    .stChatMessage[data-testid="stChatMessageAssistant"] p { color: #FFFFFF !important; text-shadow: none !important; }
</style>""", unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP")

# [2] API 설정 (공백/줄바꿈 완벽 제거 로직)
def clean_it(val): return str(val).strip().replace("\n", "").replace("\r", "")

# ⭐ 언니가 준 최신 키들을 여기에 '한 줄로' 정확히 넣으세요!
CLAUDE_KEY = clean_it("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")
ELEVEN_KEY = clean_it("sk_9665d7f430925bb8ef413175c17b94f9c74ea27f2d88b5f5")
VOICE_ID = "O7njSdfuJRf0H4s0EQeo"

if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

# [3] 입력창
prompt = st.chat_input("Hi Jenny!")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        with st.spinner("제니가 분석 중... 🥂"):
            # Claude 호출 (모델명: claude-sonnet-4-6)
            c_res = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": CLAUDE_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": "24세 재미교포 제니쌤. 한 줄 영어 대화.", "messages": st.session_state.messages},
                timeout=25
            ).json()

            if "content" in c_res:
                answer = c_res["content"][0]["text"]
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                    # 음성 생성 (영어만 추출)
                    v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', answer).strip()
                    if v_text:
                        v_res = requests.post(
                            f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                            headers={"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": ELEVEN_KEY},
                            json={"text": v_text, "model_id": "eleven_multilingual_v2"}
                        )
                        if v_res.status_code == 200:
                            # 🔊 '다시 듣기' 버튼과 '자동 재생'을 동시에!
                            st.audio(v_res.content, format="audio/mp3", autoplay=True)
                        else:
                            st.error(f"목소리 에러: {v_res.text}")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                st.error(f"Claude 에러: {c_res}")

    except Exception as e:
        st.error(f"시스템 오류: {e}")
