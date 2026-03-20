import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 스타일 (럭셔리 하이라이트 스타일)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆", layout="wide")
st.markdown("""
    <style>
    .stApp { 
        background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: rgba(0, 0, 0, 0.85) !important; 
        border: 2px solid #FFD700 !important; border-radius: 15px; 
    }
    .highlight { background-color: #FFFF00; color: #000; padding: 2px 8px; border-radius: 5px; font-weight: bold; border: 1px solid #000; }
    /* 텍스트 가독성 */
    .stMarkdown p, .stMarkdown span { color: #000 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# 🔊 음성 재생 함수 (속도 조절 및 강제 재생 기능)
def play_eleven_voice(audio_bytes, speed=1.0):
    b64 = base64.b64encode(audio_bytes).decode()
    # 사용자가 클릭하지 않아도 재생될 확률을 높이기 위한 HTML5 설정
    audio_html = f"""
        <audio id="jenny_voice" autoplay controls style="width: 100%; margin-top: 10px;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById('jenny_voice');
            audio.playbackRate = {speed};
            audio.play().catch(e => console.log("Autoplay blocked. Please click the play button."));
        </script>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error("Secrets 설정을 확인해줘 언니! 😭"); st.stop()

# [3] 세션 상태 초기화 (대화 & 학습 리스트)
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_expressions" not in st.session_state: st.session_state.learned_expressions = []

# [4] 사이드바: 설정 및 학습 리스트 나열
with st.sidebar:
    st.title("🐆 Jenny's VIP Lounge")
    voice_speed = st.slider("🗣️ 제니 말하기 속도", 0.5, 1.5, 1.0, 0.1)
    
    st.divider()
    st.subheader("📚 Today's Key Expressions")
    if not st.session_state.learned_expressions:
        st.write("대화를 시작하면 표현들이 쌓여!")
    for idx, exp in enumerate(st.session_state.learned_expressions):
        st.markdown(f"**{idx+1}.** {exp}")

# [5] 메인 화면
if "user_info" not in st.session_state:
    st.title("🐆 Welcome back, Maykim!")
    if st.button("Start Lesson"):
        st.session_state.user_info = {"name": "maykim"}
        st.rerun()
    st.stop()

# 제니 지침 (세련되고 지적인 24세 서퍼 톤)
JENNY_SYSTEM = """
너는 24세 재미교포 제니야. 전문 영어 강사이자 심리학에 능통한 ENFP 서퍼지.
[톤 지침]
1. 세련되고 지적인 톤을 유지해. (너무 가볍지 않게!)
2. 첫 인사만 한국어, 이후 100% 영어.
3. 유용한 표현은 반드시 [[표현: 영어표현 - 뜻]] 형식으로 포함해줘.
4. 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어-뜻] 추가.
"""

# 대화 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.markdown(m["display_content"], unsafe_allow_html=True)

# [6] 메인 대화 로직
prompt = st.chat_input("Hey Jenny! Let's talk!")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is thinking... 🌊"):
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            answer = response.choices[0].message.content
            
            # 표현 추출 및 사이드바 저장
            new_exps = re.findall(r'\[\[표현: (.*?)\]\]', answer)
            for e in new_exps:
                if e not in st.session_state.learned_expressions:
                    st.session_state.learned_expressions.append(e)

            with st.chat_message("assistant"):
                # 본문 하이라이트 처리 (노란색 배경)
                display_answer = re.sub(r'\[\[표현: (.*?)\]\]', r'<span class="highlight">\1</span>', answer)
                st.markdown(display_answer, unsafe_allow_html=True)
                
                # 음성 생성용 텍스트 (한글/기호 제거)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer)
                v_text = re.sub(r'\[\[표현:.*?\]\]', '', v_text)
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={
                            "text": v_text,
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.8, "similarity_boost": 0.8} # 세련된 톤 고정
                        }
                    )
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content, speed=voice_speed)
            
            st.session_state.messages.append({"role": "assistant", "content": answer, "display_content": display_answer})
    except Exception as e:
        st.error(f"Error: {e}")
