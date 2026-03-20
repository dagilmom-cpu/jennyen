import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 (럭셔리 스타일 & 한글 핑크색)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆", layout="wide")
st.markdown("""
    <style>
    .stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; background-attachment: fixed; }
    .stChatMessage[data-testid="stChatMessageAssistant"] { background-color: rgba(0, 0, 0, 0.85) !important; border: 2px solid #FFD700 !important; border-radius: 15px; }
    .highlight { background-color: #FFFF00; color: #000; padding: 2px 5px; border-radius: 5px; font-weight: bold; }
    .korean-text { color: #FF69B4 !important; font-weight: bold; }
    .stMarkdown p, .stMarkdown span { color: #000 !important; font-weight: 700 !important; }
    audio { width: 100%; height: 45px; margin-top: 10px; border: 2px solid #FFD700; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결 및 에러 체크
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"⚠️ Secrets 설정 오류 (키 이름을 확인해줘!): {e}"); st.stop()

# [3] 세션 상태
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_expressions" not in st.session_state: st.session_state.learned_expressions = []

# [4] 입학 신청서
if "user_info" not in st.session_state:
    st.title("🐆 Welcome to Jenny's VIP Surf House!")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name", value="maykim")
        age = st.number_input("Age", min_value=0, max_value=100, value=25)
    with col2:
        gender = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Secret"])
        level = st.select_slider("English Level", options=["초급", "중급", "고급"])
    goal = st.text_area("Goal", placeholder="목적을 적어줘!")
    if st.button("Start! 🏄‍♀️"):
        if name and goal:
            st.session_state.user_info = {"name": name, "age": age, "level": level, "goal": goal}
            st.rerun()
    st.stop()

# [5] 사이드바
with st.sidebar:
    st.title(f"🐆 {st.session_state.user_info['name']}'s Lounge")
    voice_speed = st.slider("🗣️ 제니 말하기 속도", 0.5, 1.5, 1.0, 0.1)
    st.divider()
    st.subheader("📚 Today's Expressions")
    for exp in st.session_state.learned_expressions:
        st.markdown(f"✅ {exp}")

JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 전문 영어 강사이고 ENFP 서퍼지.
1. 첫 인사만 한국어, 이후 100% 영어. 
2. 슬랭은 **굵게** 표시하고 [Slang: 단어 - <span class='korean-text'>한글뜻</span>] 추가.
3. 유용한 표현은 [[표현: 영어 - <span class='korean-text'>한글뜻</span>]] 형식."""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_b64"):
                st.markdown(f'<audio controls><source src="data:audio/mp3;base64,{m["audio_b64"]}" type="audio/mp3"></audio>', unsafe_allow_html=True)

# [6] 대화 & 일레븐랩스 강제 호출 로직
prompt = st.chat_input("Message Jenny...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is catching a wave..."):
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            answer = response.choices[0].message.content
            
            # 표현 리스트 업데이트
            new_exps = re.findall(r'\[\[표현: (.*?)\]\]', answer)
            for e in new_exps:
                if e not in st.session_state.learned_expressions: st.session_state.learned_expressions.append(e)

            with st.chat_message("assistant"):
                display_answer = re.sub(r'\[\[표현: (.*?)\]\]', r'<span class="highlight">\1</span>', answer)
                st.markdown(display_answer, unsafe_allow_html=True)
                
                # 🔊 일레븐랩스 목소리 생성 (영어만 추출)
                v_text = re.sub(r'\[Slang:.*?\]|\[\[표현:.*?\]\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', answer).strip()
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
                        # HTML5 플레이어로 확실하게 재생
                        st.markdown(f'''
                            <audio id="v" autoplay controls style="width:100%">
                                <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                            </audio>
                            <script>document.getElementById("v").playbackRate={voice_speed}</script>
                        ''', unsafe_allow_html=True)
                    else:
                        # 🚨 일레븐랩스 호출 실패 시 에러 원인 출력
                        st.error(f"🚨 ElevenLabs 목소리 생성 실패! (코드: {v_res.status_code})")
                        st.json(v_res.json()) # 에러 내용 보여주기
                else:
                    st.warning("⚠️ 읽어줄 영어가 없네!")
            
            st.session_state.messages.append({"role": "assistant", "content": answer, "display_content": display_answer, "audio_b64": audio_b64})
    except Exception as e:
        st.error(f"🚨 시스템 에러: {e}")
