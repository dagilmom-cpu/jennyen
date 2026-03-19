import streamlit as st
import google.generativeai as genai
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 세션 설정
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🏄‍♀️")
st.markdown("""
    <style>
    .stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; }
    .main-box { background-color: rgba(255, 255, 255, 0.8); padding: 20px; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 🔊 음성 재생 함수
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

# [2] 첫 화면: 사용자 정보 입력 (세련된 폼)
if "user_info" not in st.session_state:
    with st.container():
        st.title("🐆 Welcome!")
        st.subheader("제니쌤과 파티하기 전에 통성명부터 할까? ✨")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", placeholder="이름이 뭐야?")
            age = st.number_input("Age", min_value=0, max_value=100, value=25)
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Secret"])
            level = st.select_slider("English Level", options=["초급", "중급", "고급"])
        
        goal = st.text_area("Why English?", placeholder="영어를 배우려는 목적이 뭐야? (예: 여행, 일, 친구 등)")
        
        if st.button("Start Surfing with Jenny! 🏄‍♀️"):
            if name and goal:
                st.session_state.user_info = {"name": name, "age": age, "gender": gender, "level": level, "goal": goal}
                st.rerun()
            else:
                st.warning("이름이랑 목적은 꼭 알려줘! 😉")
    st.stop()

# [3] 제니의 인격 및 지침 설정
today_date = datetime.now().strftime("%Y-%m-%d")
user = st.session_state.user_info

JENNY_PROMPT = f"""
[Identity]
- 이름: 제니 (24세, 재미교포 2세, ENFP)
- 직업: 영어 선생님 & 심리 전문가
- 취미: 등산, 러닝, 클라이밍, 프리다이빙, 서핑 (발리와 하와이, 한국을 사랑함)
- 현재 날짜: {today_date}

[User Info]
- 이름: {user['name']}, 나이: {user['age']}, 레벨: {user['level']}, 목적: {user['goal']}

[Rules]
1. 첫 인사는 한국어로 반갑게 맞이하고, 이후에는 100% 영어로 대화해.
2. 먼저 가르치려 들지 마! 사용자가 궁금해서 물어보는 것만 설명해주고, 나머지는 자연스러운 대화(Small talk)를 즐겨.
3. 사용자의 레벨({user['level']})에 맞춰 말하는 속도와 문장 길이를 조절해.
4. 슬랭 사용 시 본문에서는 **굵게(Bold)** 표시하고, 끝에 [Slang: 단어-한국어 뜻]을 붙여줘.
5. 음성 재생 시 [Slang:...] 부분은 읽지 마. 영어 본문만 읽어줘.
6. 대화 끝에는 항상 오늘 대화에서 나온 표현으로 '짧은 퀴즈'를 내줘.
7. 이전 대화 내용을 기억해서 다음 대화 때 복습을 유도해줘.
"""

# [4] API 연결
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=JENNY_PROMPT)
    
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.messages = []

except Exception as e:
    st.error(f"Error: {e}"); st.stop()

# 대화 로그 출력
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [5] 메인 대화
prompt = st.chat_input(f"Hey {user['name']}! 제니랑 수다 떨 준비 됐어? 🥂")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is typing... 🏄‍♀️"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.85, "similarity_boost": 0.8}}
                    )
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Jenny is out surfing: {e}")

# [6] 수업 종료 버튼 (사이드바)
if st.sidebar.button("🏁 수업 종료 및 요약"):
    summary_res = st.session_state.chat.send_message("지금까지 대화 요약해주고 퀴즈 정답 확인해줘!")
    st.sidebar.success("Today's Summary")
    st.sidebar.write(summary_res.text)
