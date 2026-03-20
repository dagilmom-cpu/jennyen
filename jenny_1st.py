import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 (럭셔리 배경 & 텍스트 스타일)
st.set_page_config(page_title="Jenny's VIP Global Academy", page_icon="🐆", layout="wide")
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
    /* 사이드바 하단 버튼 고정 스타일 */
    [data-testid="stSidebarNav"] + div { position: absolute; bottom: 20px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"🚨 Secrets Error: {e}"); st.stop()

# [3] 세션 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_exps" not in st.session_state: st.session_state.learned_exps = []
if "summary_mode" not in st.session_state: st.session_state.summary_mode = False

# [4] 입학 신청서
if "user_info" not in st.session_state:
    st.title("🐆 Welcome to Jenny's VIP Global Academy")
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Name", value="maykim")
        role = st.selectbox("Your Goal", [
            "소상공인 영어 배우기 (Hospitality English)",
            "미드로 영어 표현 배우기 (Sitcom Vibe)",
            "비지니스 영어 배우기 (Professional English)",
            "유창한 영어 배우기 (Fluency & Slang)",
            "토론 해보기 (Debating & Logic)",
            "영어 인터뷰 배우기 (Interview Prep)"
        ])
    with c2:
        level = st.select_slider("English Level", options=["Beginner", "Intermediate", "Advanced"])
        interest = st.text_area("Your Interests", placeholder="e.g. SATC, News, K-pop...")
    if st.button("Start! 🏄‍♀️"):
        if name and interest:
            st.session_state.user_info = {"name": name, "role": role, "level": level, "interest": interest}
            st.rerun()
    st.stop()

user = st.session_state.user_info

# [5] 사이드바 설정 (하단에 버튼 배치)
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Studio")
    v_speed = st.slider("🗣️ Voice Speed", 0.5, 2.0, 1.4, 0.1)
    st.divider()
    st.subheader("📚 Today's Expressions")
    for e in st.session_state.learned_exps: st.write(f"✨ {e}")
    
    st.markdown("<br><br>", unsafe_allow_html=True) # 공간 확보
    if st.button("🏁 수업 종료 및 요약하기"):
        st.session_state.summary_mode = True
        st.rerun()

# [요약 모드] 깔끔한 지침 적용
if st.session_state.summary_mode:
    st.balloons()
    st.title("🎓 Today's Lesson Recap")
    with st.spinner("Jenny is creating a clean summary... ✍️"):
        sum_res = client.chat.completions.create(
            messages=[{"role": "system", "content": "너는 깔끔한 요약봇이야. 지금까지의 대화 내용을 3줄의 평서문으로 요약하고, 가장 중요한 핵심 표현 3개를 '단어 - 뜻' 형식으로만 나열해줘. 한자 금지, 특수 태그([[ ]]) 금지, 오직 한글과 영어만 사용해."}] + 
                     [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            model="llama-3.3-70b-versatile",
        )
        st.success(f"Great work, {user['name']}!")
        st.info(sum_res.choices[0].message.content)
        if st.button("대화로 돌아가기"):
            st.session_state.summary_mode = False
            st.rerun()
    st.stop()

# [6] 난이도 가변형 지침
LEVEL_GUIDE = {
    "Beginner": "Use very simple, short sentences. Limit vocabulary. Keep it simple and clear.",
    "Intermediate": "Use standard conversational English with some idioms.",
    "Advanced": "Full native speed. Use complex structures and deep vocabulary."
}

JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 전문 영어 강사이고 ENFP 글로벌 전문가야.
[Level Rule] 레벨: {user['level']}. {LEVEL_GUIDE[user['level']]}
[Rules]
1. 이름이나 'Bestie', 'Partner' 등으로 불러줘.
2. 첫 인사만 한국어, 이후 100% 영어.
3. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
4. 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식.
5. **한자(Chinese characters)는 절대 금지.**"""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_b64"): st.audio(base64.b64decode(m["audio_b64"]), format="audio/mp3")

# [7] 대화 로직
prompt = st.chat_input(f"Hi {user['name']}! Ready?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is typing..."):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            
            # 표현 추출 (중복 제거)
            exps = re.findall(r'\[\[표현: (.*?)\]\]', ans)
            for e in exps:
                clean_e = re.sub(r'<.*?>', '', e)
                if clean_e not in st.session_state.learned_exps: st.session_state.learned_exps.append(clean_e)

            with st.chat_message("assistant"):
                display_ans = ans.replace("[[표현:", "⭐ **Exp**:").replace("]]", "")
                st.markdown(display_ans, unsafe_allow_html=True)
                
                v_text = re.sub(r'<.*?>|\[.*?\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', ans).strip()
                audio_b64 = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.45, "similarity_boost": 0.8}}
                    )
                    if v_res.status_code == 200:
                        audio_data = v_res.content
                        audio_b64 = base64.b64encode(audio_data).decode()
                        st.audio(audio_data, format="audio/mp3")
                        md = f"""<audio id="ja" class="hidden-audio" autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>
                            <script>var a=document.getElementById('ja'); a.playbackRate={v_speed}; a.play();</script>"""
                        st.markdown(md, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": ans, "display_content": display_ans, "audio_b64": audio_b64})
    except Exception as e:
        st.error(f"🚨 Error: {e}")
