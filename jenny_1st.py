import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 (럭셔리 배경 & 세련된 스타일)
st.set_page_config(page_title="Jenny's English VIP", page_icon="🐆", layout="wide")
st.markdown("""
    <style>
    .stApp { 
        background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    .stChatMessage { background-color: rgba(255, 255, 255, 0.85) !important; border-radius: 15px; border: 2px solid #FFD700; }
    .korean { color: #FF1493 !important; font-weight: bold !important; } 
    p, span, div { color: #000 !important; font-weight: 800 !important; }
    .hidden-audio { display: none; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"⚠️ Secrets Check!: {e}"); st.stop()

# [3] 세션 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_exps" not in st.session_state: st.session_state.learned_exps = []

# [4] 입학 신청서
if "user_info" not in st.session_state:
    st.title("🐆 Welcome to Jenny's VIP English Lounge")
    st.subheader("Ready to catch a wave with native-speed English? 🌊")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Name", value="maykim")
        age = st.number_input("Age", min_value=0, max_value=100, value=25)
    with c2:
        gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Prefer not to say"])
        level = st.select_slider("English Level", options=["Beginner", "Intermediate", "Advanced"])
    goal = st.text_area("Your Goal", placeholder="What's your ultimate goal?")
    if st.button("Start Your Native Journey! 🏄‍♀️"):
        if name and goal:
            st.session_state.user_info = {"name": name, "age": age, "gender": gender, "level": level, "goal": goal}
            st.rerun()
    st.stop()

user = st.session_state.user_info

# [5] 사이드바 (말속도 기본값 상향)
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Studio")
    # 기본 속도를 1.4로 상향해서 더 원어민스럽게!
    v_speed = st.slider("🗣️ Voice Speed", 0.5, 2.0, 1.4, 0.1)
    st.divider()
    st.subheader("📚 Key Expressions")
    for e in st.session_state.learned_exps: st.write(f"✨ {e}")

JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 전문 영어 강사이고 ENFP 서퍼지.
사용자 이름: {user['name']}, 레벨: {user['level']}, 목적: {user['goal']}
[글로벌 지침]
1. 사용자를 '언니'라고 부르지 마. 이름이나 'Bestie', 'My friend' 등을 사용해.
2. 첫 인사만 한국어, 이후 100% 영어 대화.
3. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
4. 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식. 한글은 반드시 <span class='korean'> </span> 태그로 감싸줘."""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_b64"):
                st.audio(base64.b64decode(m["audio_b64"]), format="audio/mp3")

# [6] 대화 로직
prompt = st.chat_input(f"Hey {user['name']}! Let's talk like a pro! 🥂")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is catching a wave... 🌊"):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            
            exps = re.findall(r'\[\[표현: (.*?)\]\]', ans)
            for e in exps:
                clean_e = re.sub(r'<.*?>', '', e)
                if clean_e not in st.session_state.learned_exps: st.session_state.learned_exps.append(clean_e)

            with st.chat_message("assistant"):
                display_ans = ans.replace("[[표현:", "⭐ **Expression**:").replace("]]", "")
                st.markdown(display_ans, unsafe_allow_html=True)
                
                v_text = re.sub(r'<.*?>|\[.*?\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', ans).strip()
                audio_b64 = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={
                            "text": v_text, 
                            "model_id": "eleven_multilingual_v2", 
                            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8} # 경쾌함 극대화
                        }
                    )
                    if v_res.status_code == 200:
                        audio_data = v_res.content
                        audio_b64 = base64.b64encode(audio_data).decode()
                        
                        st.audio(audio_data, format="audio/mp3")
                        
                        md = f"""
                            <audio id="ja" class="hidden-audio" autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>
                            <script>var a=document.getElementById('ja'); a.playbackRate={v_speed}; a.play();</script>
                            """
                        st.markdown(md, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": ans, "display_content": display_ans, "audio_b64": audio_b64})
    except Exception as e:
        st.error(f"🚨 Error: {e}")
