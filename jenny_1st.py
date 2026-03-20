import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인
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

# [4] 입학 신청서 (난이도 선택 포함)
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

# [5] 사이드바 & 수업 종료
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Studio")
    v_speed = st.slider("🗣️ Voice Speed", 0.5, 2.0, 1.4, 0.1)
    if st.button("🏁 수업 종료 (요약)"): st.session_state.summary_mode = True
    st.divider()
    st.subheader("📚 Today's Expressions")
    for e in st.session_state.learned_exps: st.write(f"✨ {e}")

# 요약 로직
if st.session_state.summary_mode:
    st.balloons()
    sum_res = client.chat.completions.create(
        messages=[{"role": "system", "content": "오늘 대화 3줄 요약 + 핵심표현 3개. 한자 금지. 한글 뜻은 분홍색으로."}] + 
                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        model="llama-3.3-70b-versatile",
    )
    st.success("Today's Recap:")
    st.markdown(sum_res.choices[0].message.content)
    if st.button("Back"): st.session_state.summary_mode = False; st.rerun()
    st.stop()

# [6] [학습 핵심] 난이도 가변형 지침
LEVEL_GUIDE = {
    "Beginner": "Use very simple, short sentences. Use basic vocabulary. Speak slowly in your mind. Keep your responses brief.",
    "Intermediate": "Use standard conversational English. Mix some common idioms.",
    "Advanced": "Speak like a native. Use complex structures, advanced slang, and professional terms. Be as chatty as you want!"
}

JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 전문 영어 강사이고 ENFP 글로벌 전문가야.
[Level-Specific Rule]
- 사용자의 레벨은 '{user['level']}'이야. {LEVEL_GUIDE[user['level']]} 이 규칙을 반드시 지켜줘.

[Instructions]
1. '언니'라 부르지 마. 이름이나 'Bestie', 'Partner' 등을 써.
2. 첫 인사만 한국어, 이후 100% 영어.
3. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
4. 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식. 한글은 <span class='korean'> </span>로 감싸줘.
5. **CRITICAL: 한자(Chinese characters)는 100% 금지야. 절대 쓰지 마.**"""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_b64"): st.audio(base64.b64decode(m["audio_b64"]), format="audio/mp3")

# [7] 대화 로직
prompt = st.chat_input(f"Hi {user['name']}! Let's start!")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is matching your level... 🌊"):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            
            # 표현 추출
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
