import streamlit as st
from groq import Groq
import requests
import re
import base64

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

# [2] API 연결 (VOICE_ID 이름 유지)
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
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
        role = st.selectbox("Your Goal", ["소상공인 영어 배우기", "미드로 영어 표현 배우기", "비지니스 영어 배우기", "유창한 영어 배우기", "토론 해보기", "영어 인터뷰 배우기"])
    with c2:
        level = st.select_slider("Level", options=["Beginner", "Intermediate", "Advanced"])
        interest = st.text_area("Interests", placeholder="e.g. SATC, News, K-pop...")
    if st.button("Start! 🏄‍♀️"):
        if name and interest:
            st.session_state.user_info = {"name": name, "role": role, "level": level, "interest": interest}
            st.rerun()
    st.stop()

user = st.session_state.user_info

# [5] 사이드바 (오늘 배운 표현 리스트 추출 보강)
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

if st.session_state.summary_mode:
    st.balloons()
    sum_res = client.chat.completions.create(
        messages=[{"role": "system", "content": "3줄 요약 + 핵심표현 3개. **한자/일어/노르웨이어 금지**. 오직 한글과 영어만 사용."}] + 
                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        model="llama-3.3-70b-versatile",
    )
    # 한자/일어/기타 외국어 문자 강제 제거 필터
    clean_summary = re.sub(r'[一-龥ぁ-ゔァ-ヶー]', '', sum_res.choices[0].message.content)
    st.info(clean_summary)
    if st.button("Back"): st.session_state.summary_mode = False; st.rerun()
    st.stop()

# [6] 시스템 지침 (언어 제한 및 형식 고정)
JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. 레벨: {user['level']}.
1. **오직 영어와 한글만 사용해.** 노르웨이어, 한자, 일본어 절대 금지.
2. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>뜻</span>] 추가.
3. 표현은 반드시 [[표현: 영어 - <span class='korean'>뜻</span>]] 이 형식을 지켜줘.
4. 초보자(Beginner)라면 아주 짧고 쉬운 문장으로만 말해."""

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
        with st.spinner("Jenny is matching your vibe..."):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            raw_ans = res.choices[0].message.content
            # 외국어 문자 제거 필터
            ans = re.sub(r'[一-龥ぁ-ゔァ-ヶー]', '', raw_ans)
            
            # ⭐ [표현 추출 로직 업그레이드] - '영어: 영어' 같은 오타도 잡아냄
            exps = re.findall(r'\[\[표현:\s*(.*?)\s*\]\]', ans)
            for e in exps:
                # 불필요한 태그 제거 및 '영어 - 뜻' 형식으로 정제
                clean_e = re.sub(r'<.*?>|영어\s*[:|-]\s*', '', e).strip()
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
