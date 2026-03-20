import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 (럭셔리 배경 & 한글 핑크색 강제 스타일)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆", layout="wide")
st.markdown("""
    <style>
    .stApp { 
        background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    .stChatMessage { background-color: rgba(255, 255, 255, 0.8) !important; border-radius: 15px; border: 2px solid #FFD700; }
    /* 한글 텍스트 전용 스타일 */
    .korean { color: #FF1493 !important; font-weight: bold !important; }
    p, span, div { color: #000 !important; font-weight: 800 !important; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"⚠️ Secrets 설정 확인!: {e}"); st.stop()

# [3] 세션 상태 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_exps" not in st.session_state: st.session_state.learned_exps = []

# [4] 입학 신청서 (옵션 선택 화면 - 완벽 복구!)
if "user_info" not in st.session_state:
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

# [5] 사이드바 & 지침
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Room")
    voice_speed = st.slider("🗣️ 제니 말하기 속도", 0.5, 1.5, 1.0, 0.1)
    st.divider()
    st.subheader("📚 Today's Expressions")
    for e in st.session_state.learned_exps:
        st.write(f"✅ {e}")

# 제니의 지침 (한글 색상 입히는 태그 포함)
JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 전문 영어 강사이고 ENFP 서퍼지.
사용자 이름: {user['name']}, 레벨: {user['level']}, 목적: {user['goal']}
[규칙]
1. 첫 인사만 한국어, 이후 100% 영어 대화.
2. 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
3. 유용한 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식으로 문장 끝에 포함.
* 반드시 한글 뜻은 <span class='korean'> </span> 태그로 감싸서 분홍색으로 만들어줘."""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio"):
                st.audio(m["audio"], format="audio/mp3")

# [6] 메인 대화 로직
prompt = st.chat_input(f"Hey {user['name']}! Ready to slay? 🥂")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is catching a wave..."):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            
            # 표현 추출 (태그 제거 후 저장)
            exps = re.findall(r'\[\[표현: (.*?)\]\]', ans)
            for e in exps:
                clean_e = re.sub(r'<.*?>', '', e)
                if clean_e not in st.session_state.learned_exps: st.session_state.learned_exps.append(clean_e)

            with st.chat_message("assistant"):
                # 한글 색상 적용을 위해 markdown 대신 HTML 허용
                display_ans = ans.replace("[[표현:", "⭐ **Expression**:").replace("]]", "")
                st.markdown(display_ans, unsafe_allow_html=True)
                
                # 음성 생성용 텍스트 (태그 및 한글 제거)
                v_text = re.sub(r'<.*?>|\[.*?\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', ans).strip()
                audio_data = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.8}}
                    )
                    if v_res.status_code == 200:
                        audio_data = v_res.content
                        st.audio(audio_data, format="audio/mp3")
                    else:
                        st.error(f"🚨 소리 에러: {v_res.status_code}")
            
            st.session_state.messages.append({"role": "assistant", "content": ans, "display_content": display_ans, "audio": audio_data})
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
