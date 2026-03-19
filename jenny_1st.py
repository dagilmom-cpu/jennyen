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

# 🔊 음성 재생 함수 (다시 듣기 지원)
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio id="jenny_voice" autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)
    st.audio(audio_bytes, format="audio/mp3")

# [2] 첫 화면: 세련된 사용자 정보 입력 폼
if "user_info" not in st.session_state:
    with st.container():
        st.title("🐆 Welcome to Jenny's Surf House!")
        st.subheader("제니쌤이랑 수다 떨기 전에 통성명부터 할까? ✨")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name", placeholder="언니 이름이 뭐야?")
            age = st.number_input("Age", min_value=0, max_value=100, value=25)
        with col2:
            gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Secret"])
            level = st.select_slider("English Level", options=["초급", "중급", "고급"])
        
        goal = st.text_area("Why English?", placeholder="영어를 공부하려는 목적이 뭐야? (예: 일상 회화, 여행, 비즈니스 등)")
        
        if st.button("Start Surfing with Jenny! 🏄‍♀️"):
            if name and goal:
                st.session_state.user_info = {
                    "name": name, "age": age, "gender": gender, "level": level, "goal": goal
                }
                st.rerun()
            else:
                st.warning("이름이랑 목적은 꼭 알려줘야 제니가 맞춤형으로 가르쳐주지! 😉")
    st.stop()

# [3] 제니의 인격 및 지침 설정 (언니의 모든 주문 반영)
today_date = datetime.now().strftime("%Y-%m-%d")
user = st.session_state.user_info

JENNY_PROMPT = f"""
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
7. 대화 내용을 기억해서 다음 수업 때 복습할 수 있게 해줘.
"""

# [4] API 연결 (404 에러 자동 방어 시스템)
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)
    
    # 모델 자동 탐색 필살기
    if "model_path" not in st.session_state:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
        st.session_state.model_path = target

    model = genai.GenerativeModel(
        model_name=st.session_state.model_path, 
        system_instruction=JENNY_PROMPT
    )
    
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])
        st.session_state.messages = []

except Exception as e:
    st.error(f"Jenny is getting ready: {e}")
    st.stop()

# 대화 로그 출력
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [5] 메인 대화 로직
prompt = st.chat_input(f"Hey {user['name']}! 제니랑 수다 떨 준비 됐어? 🥂")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is thinking... 🏄‍♀️"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                # 음성용 텍스트 가공 (한국어 및 슬랭 설명 제거)
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={
                            "text": v_text, 
                            "model_id": "eleven_multilingual_v2", 
                            "voice_settings": {"stability": 0.9, "similarity_boost": 0.8}
                        }
                    )
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Something went wrong: {e}")

# [6] 사이드바: 수업 종료 및 요약 버튼
if st.sidebar.button("🏁 오늘 수업 끝 (요약하기)"):
    with st.sidebar:
        summary_res = st.session_state.chat.send_message("지금까지 대화 내용 중 중요 표현 3가지만 요약해주고 퀴즈 정답 확인해줘!")
        st.success("Today's Key Expressions")
        st.write(summary_res.text)
