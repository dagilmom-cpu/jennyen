import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 스타일 설정 (언니의 럭셔리 레오파드 취향 저격)
st.set_page_config(page_title="제니쌤 영어 VIP (Groq)", page_icon="🐆")
st.markdown("""
    <style>
    .stApp { 
        background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: rgba(0, 0, 0, 0.9) !important; 
        border: 2px solid #FFD700 !important; border-radius: 15px; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] p { color: #FFFFFF !important; }
    html, body, [class*="css"], .stMarkdown, p, span, div { 
        color: #000000 !important; font-weight: 800 !important; 
        text-shadow: -1px -1px 0 #FFF, 1px -1px 0 #FFF, -1px 1px 0 #FFF, 1px 1px 0 #FFF !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# 🔊 음성 재생 함수 (ElevenLabs 연동)
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

# [2] API 연결 (Groq & ElevenLabs)
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error("Secrets 설정에서 'GROQ_API_KEY'를 확인해줘 언니! 😭")
    st.stop()

# [3] 첫 화면: 입학 신청서 (이름/나이/성별/레벨)
if "user_info" not in st.session_state:
    with st.container():
        st.title("🐆 Welcome to Jenny's Surf House!")
        st.subheader("Groq 엔진으로 더 빨라진 제니쌤이랑 수다 떨자! ✨")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", placeholder="언니 이름이 뭐야?")
            age = st.number_input("Age", min_value=0, max_value=100, value=25)
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Secret"])
            level = st.select_slider("English Level", options=["초급", "중급", "고급"])
        
        goal = st.text_area("Why English?", placeholder="영어를 공부하려는 목적이 뭐야? (예: 여행, 일 등)")
        
        if st.button("Start Surfing with Jenny! 🏄‍♀️"):
            if name and goal:
                st.session_state.user_info = {"name": name, "age": age, "gender": gender, "level": level, "goal": goal}
                st.rerun()
            else:
                st.warning("이름이랑 목적은 꼭 알려줘야 제니가 맞춤형으로 가르쳐주지! 😉")
    st.stop()

# [4] 제니의 인격 설정 (ENFP 서퍼 제니)
user = st.session_state.user_info
today_date = datetime.now().strftime("%Y-%m-%d")

JENNY_SYSTEM = f"""
너는 24세 재미교포 제니야. 현재 영어 선생님으로 일하고 있어. ENFP이고 심리학을 잘 알아서 사람의 마음을 잘 캐치해.
취미는 등산, 러닝, 클라이밍, 프리다이빙, 서핑이야. 발리와 하와이, 한국을 사랑해. 오늘은 {today_date}이야.

[User Information]
- 이름: {user['name']}, 나이: {user['age']}, 레벨: {user['level']}, 목적: {user['goal']}
이 정보를 바탕으로 대화해줘.

[Rules]
1. 첫 인사만 한국어로 반갑게 하고, 나머지는 영어로만 대화해.
2. 먼저 가르치려 들지 마! 내가 궁금해서 물어보는 것만 힙하게 설명해주고, 나머지는 자연스러운 대화를 즐겨줘.
3. 사용자의 레벨({user['level']})에 맞춰 말하는 속도와 양을 조절해줘.
4. 슬랭 사용 시 본문에서는 **굵게(Bold)** 표시하고, 끝에 [Slang: 단어-한국어 뜻]을 붙여줘. 
5. 음성 재생 시 [Slang:...] 부분의 한국어 뜻은 절대 읽지 마. 영어 본문만 읽어줘.
6. 대화 끝에는 항상 오늘 배운 내용을 복습할 수 있는 짧은 퀴즈를 내줘.
"""

# 대화 내역 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.write(m["content"])

# [5] 메인 대화 로직 (Groq 엔진 호출)
prompt = st.chat_input(f"Hey {user['name']}! Ready to slay? 🥂")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is catching a wave... 🏄‍♀️"):
            # Groq 호출 (가장 똑똑하고 넉넉한 Llama3-70b 모델 사용)
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + st.session_state.messages,
                model="llama3-70b-8192", # 아주 똑똑한 대형 모델!
                temperature=0.8,
            )
            answer = response.choices[0].message.content
            
            with st.chat_message("assistant"):
                st.write(answer)
                # 보이스 필터링 (한글 제거 및 슬랭 뜻 제거)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.8, "similarity_boost": 0.8}}
                    )
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Something went wrong with Groq: {e}")

# [6] 사이드바 요약 버튼
if st.sidebar.button("🏁 오늘 수업 끝 (요약하기)"):
    st.sidebar.success(f"Great job today, {user['name']}! ✨")
    # 요약 기능도 Groq로 처리
    summary_req = client.chat.completions.create(
        messages=[{"role": "system", "content": "대화 내용을 3줄로 요약하고 오늘 배운 핵심 단어 3개를 정리해줘."}] + st.session_state.messages,
        model="model="llama-3.3-70b-versatile", # 요약은 가벼운 모델로 빠르게!
    )
    st.sidebar.write(summary_req.choices[0].message.content)
