import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 스타일 설정 (럭셔리 스타일 + 학습 리스트 하이라이트)
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
    .highlight { background-color: #FFFF00; color: #000; padding: 2px 5px; border-radius: 3px; font-weight: bold; }
    .expression-list { background-color: rgba(255, 255, 255, 0.9); padding: 15px; border-radius: 10px; border-left: 5px solid #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# 🔊 음성 재생 함수 (속도 조절 및 세련된 톤 설정)
def play_eleven_voice(audio_bytes, speed=1.0):
    b64 = base64.b64encode(audio_bytes).decode()
    # HTML5 오디오 태그를 사용하여 속도(playbackRate) 조절
    audio_html = f"""
        <audio id="jenny_voice" autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById('jenny_voice');
            audio.playbackRate = {speed};
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
    st.error("Secrets 설정에서 API 키들을 확인해줘 언니! 😭"); st.stop()

# [3] 세션 상태 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_expressions" not in st.session_state: st.session_state.learned_expressions = []

# [4] 사이드바: 설정 및 학습 리스트
with st.sidebar:
    st.title("⚙️ Jenny's Settings")
    voice_speed = st.slider("🗣️ 말하기 속도", 0.5, 1.5, 1.0, 0.1)
    
    st.divider()
    st.title("📚 Today's Expressions")
    st.info("대화 중 배운 표현들이 여기에 나열돼!")
    for idx, exp in enumerate(st.session_state.learned_expressions):
        st.markdown(f"{idx+1}. <span class='highlight'>{exp}</span>", unsafe_allow_html=True)

# [5] 메인 화면 & 인격 설정
if "user_info" not in st.session_state:
    st.title("🐆 Welcome back, Sis!")
    name = st.text_input("Name", value="maykim")
    if st.button("Start"):
        st.session_state.user_info = {"name": name}
        st.rerun()
    st.stop()

user = st.session_state.user_info
JENNY_SYSTEM = f"""
너는 24세 재미교포 제니야. 전문 영어 강사이자 ENFP 서퍼지. 심리학에 능통해. 
[지침]
1. 첫 인사만 한국어, 이후 100% 영어 대화. 
2. 세련되고 전문적인 톤을 유지하되 찐친처럼 다정하게.
3. 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어-뜻] 추가.
4. 새로운 유용한 표현은 반드시 [[표현: 영어표현 - 뜻]] 형식으로 문장 끝에 포함해줘.
"""

# 대화 로그
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.write(m["content"])

# [6] 대화 실행
prompt = st.chat_input("메시지를 입력해줘!")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is typing..."):
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + st.session_state.messages,
                model="llama-3.3-70b-versatile",
            )
            answer = response.choices[0].message.content
            
            # 표현 추출 및 사이드바 저장
            new_exps = re.findall(r'\[\[표현: (.*?)\]\]', answer)
            for e in new_exps:
                if e not in st.session_state.learned_expressions:
                    st.session_state.learned_expressions.append(e)

            with st.chat_message("assistant"):
                # 하이라이트 시각화
                display_answer = re.sub(r'\[\[표현: (.*?)\]\]', r'<span class="highlight">\1</span>', answer)
                st.markdown(display_answer, unsafe_allow_html=True)
                
                # 음성 생성 (한글 제외)
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
                            "voice_settings": {
                                "stability": 0.75, # 수치가 높을수록 차분하고 세련된 톤
                                "similarity_boost": 0.8
                            }
                        }
                    )
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content, speed=voice_speed)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Error: {e}")
