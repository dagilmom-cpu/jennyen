import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 스타일 (럭셔리 핑크 골드 레오파드)
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
    .stMarkdown p, .stMarkdown span { color: #000 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error("Secrets 설정을 확인해줘 언니! 😭"); st.stop()

# [3] 세션 상태 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_expressions" not in st.session_state: st.session_state.learned_expressions = []

# [4] 입학 신청서 (옵션 선택 화면 복구!)
if "user_info" not in st.session_state:
    with st.container():
        st.title("🐆 Welcome to Jenny's VIP Surf House!")
        st.subheader("제니쌤이랑 1:1 밀착 영어 수다 시작해볼까? 🥂")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", value="maykim")
            age = st.number_input("Age", min_value=0, max_value=100, value=25)
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Secret"])
            level = st.select_slider("English Level", options=["초급", "중급", "고급"])
        
        goal = st.text_area("Why English?", placeholder="영어를 배우려는 목적이 뭐야? (예: 여행, 비즈니스 등)")
        
        if st.button("Start Surfing with Jenny! 🏄‍♀️"):
            if name and goal:
                st.session_state.user_info = {"name": name, "age": age, "gender": gender, "level": level, "goal": goal}
                st.rerun()
            else:
                st.warning("이름이랑 목적은 꼭 알려줘야지! 😉")
    st.stop()

user = st.session_state.user_info

# [5] 사이드바: 설정 및 학습 리스트
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Lounge")
    voice_speed = st.slider("🗣️ 제니 말하기 속도", 0.5, 1.5, 1.0, 0.1)
    st.divider()
    st.subheader("📚 Today's Key Expressions")
    for idx, exp in enumerate(st.session_state.learned_expressions):
        st.markdown(f"**{idx+1}.** {exp}")

# 제니 지침 (세련된 전문 강사 톤)
JENNY_SYSTEM = f"""
너는 24세 재미교포 제니야. 전문 영어 강사이자 심리학에 능통한 ENFP 서퍼지.
사용자 이름: {user['name']}, 레벨: {user['level']}, 목적: {user['goal']}
[지침]
1. 세련되고 지적인 톤을 유지해.
2. 첫 인사만 한국어, 이후 100% 영어.
3. 유용한 표현은 반드시 [[표현: 영어표현 - 뜻]] 형식으로 포함해줘.
4. 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어-뜻] 추가.
"""

# 대화 로그 출력 (다시 듣기 오디오 바 포함)
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): 
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_base64"):
                audio_html = f'<audio controls style="width: 100%;"><source src="data:audio/mp3;base64,{m["audio_base64"]}" type="audio/mp3"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)

# [6] 메인 대화 로직
prompt = st.chat_input(f"Hey {user['name']}! Ready to slay? 🥂")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is catching a wave... 🌊"):
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            answer = response.choices[0].message.content
            
            # 표현 추출
            new_exps = re.findall(r'\[\[표현: (.*?)\]\]', answer)
            for e in new_exps:
                if e not in st.session_state.learned_expressions:
                    st.session_state.learned_expressions.append(e)

            with st.chat_message("assistant"):
                display_answer = re.sub(r'\[\[표현: (.*?)\]\]', r'<span class="highlight">\1</span>', answer)
                st.markdown(display_answer, unsafe_allow_html=True)
                
                v_text = re.sub(r'\[Slang:.*?\]', '', answer)
                v_text = re.sub(r'\[\[표현:.*?\]\]', '', v_text)
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                audio_b64 = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={
                            "text": v_text,
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.8, "similarity_boost": 0.8}
                        }
                    )
                    if v_res.status_code == 200:
                        audio_b64 = base64.b64encode(v_res.content).decode()
                        # 자동 재생 + 시각적 오디오 플레이어
                        audio_html = f"""
                            <audio id="jenny_voice" autoplay="true" controls style="width: 100%;">
                                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                            </audio>
                            <script>document.getElementById('jenny_voice').playbackRate = {voice_speed};</script>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer, 
                "display_content": display_answer,
                "audio_base64": audio_b64
            })
    except Exception as e:
        st.error(f"Error: {e}")
