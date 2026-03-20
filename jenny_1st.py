import streamlit as st
from groq import Groq
import requests
import re
import base64

# [1] 디자인 (럭셔리 스타일)
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

# [2] API 연결 (GitHub Secrets 이름과 100% 동기화)
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_KEY"].strip() # 스크린샷의 VOICE_KEY와 맞춤!
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error(f"🚨 Secrets 설정 확인 필요: {e}"); st.stop()

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
    if st.button("Unlock Your Potential! 🏄‍♀️"):
        if name and interest:
            st.session_state.user_info = {"name": name, "role": role, "level": level, "interest": interest}
            st.rerun()
    st.stop()

user = st.session_state.user_info

# [5] 사이드바 & 수업 종료
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Studio")
    v_speed = st.slider("🗣️ Voice Speed", 0.5, 2.0, 1.4, 0.1)
    if st.button("🏁 수업 종료 및 요약하기"):
        st.session_state.summary_mode = True
        st.rerun()
    st.divider()
    st.subheader("📚 Today's Expressions")
    for e in list(dict.fromkeys(st.session_state.learned_exps)):
        st.write(f"✨ {e}")

# [요약 모드] 외국어 차단 필터 적용
if st.session_state.summary_mode:
    st.balloons()
    sum_res = client.chat.completions.create(
        messages=[{"role": "system", "content": "3줄 요약 + 핵심표현 3개. 한자(Chinese)나 일본어 절대 금지. 오직 한글과 영어만 사용."}] + 
                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        model="llama-3.3-70b-versatile",
    )
    # 한자/일어 강제 제거
    clean_summary = re.sub(r'[一-龥ぁ-ゔァ-ヶー]', '', sum_res.choices[0].message.content)
    st.info(clean_summary)
    if st.button("돌아가기"): st.session_state.summary_mode = False; st.rerun()
    st.stop()

# [6] 시스템 지침 (강력 언어 제한)
LEVEL_GUIDE = {"Beginner": "Short/Simple.", "Intermediate": "Standard.", "Advanced": "Native Speed."}
JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 레벨: {user['level']}.
1. 오직 영어와 한글(Korean Alphabet)만 사용해.
2. 한자(Chinese)와 일본어(Japanese)를 1%도 섞지 마. 발견되면 즉시 삭제해.
3. '언니'라 부르지 마. 이름이나 'Bestie' 사용.
4. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
5. 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식. 한글 뜻은 <span class='korean'> </span> 태그 필수."""

# 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_b64"): st.audio(base64.b64decode(m["audio_b64"]), format="audio/mp3")

# [7] 대화 로직
prompt = st.chat_input(f"Hi {user['name']}!")
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
            raw_ans = res.choices[0].message.content
            # ⭐ [한자/일본어 강제 제거 필터]
            ans = re.sub(r'[一-龥ぁ-ゔァ-ヶー]', '', raw_ans)
            
            exps = re.findall(r'\[\[표현:\s*(.*?)\s*\]\]', ans)
            for e in exps:
                clean_e = re.sub(r'<.*?>', '', e).strip()
                if clean_e and clean_e not in st.session_state.learned_exps:
                    st.session_state.learned_exps.append(clean_e)

            with st.chat_message("assistant"):
                display_ans = ans.replace("[[표현:", "⭐ **Exp**:").replace("]]", "")
                st.markdown(display_ans, unsafe_allow_html=True)
                
                v_text = re.sub(r'<.*?>|\[.*?\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', ans).strip()
                audio_b64 = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.45}}
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
