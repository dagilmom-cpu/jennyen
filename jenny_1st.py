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
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결 (언니가 준 키를 st.secrets에 넣었다고 가정하고 안전하게 불러오기)
try:
    # 팁: Streamlit Cloud 설정(Secrets)에 직접 입력하는 게 가장 안전해!
    GROQ_KEY = st.secrets.get("GROQ_API_KEY", "gsk_u2...").strip()
    ELEVEN_KEY = st.secrets.get("ELEVENLABS_API_KEY", "6a91...").strip()
    VOICE_ID = st.secrets.get("VOICE_ID", "O7nj...").strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error("🚨 API 키 설정 확인이 필요해! (Secrets 설정을 확인해줘)"); st.stop()

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
        interest = st.text_area("Interests", placeholder="SATC, News, K-pop...")
    if st.button("Start! 🏄‍♀️"):
        if name and interest:
            st.session_state.user_info = {"name": name, "role": role, "level": level, "interest": interest}
            st.rerun()
    st.stop()

user = st.session_state.user_info

# [5] 사이드바 (하단 버튼 배치)
with st.sidebar:
    st.title(f"🐆 {user['name']}'s Studio")
    v_speed = st.slider("🗣️ Voice Speed", 0.5, 2.0, 1.4, 0.1)
    st.divider()
    st.subheader("📚 Today's Expressions")
    for e in st.session_state.learned_exps: st.write(f"✨ {e}")
    if st.button("🏁 수업 종료 및 요약하기"):
        st.session_state.summary_mode = True
        st.rerun()

# [요약 모드]
if st.session_state.summary_mode:
    st.balloons()
    sum_res = client.chat.completions.create(
        messages=[{"role": "system", "content": "Clean summary in 3 lines. Key expressions. No Chinese characters."}] + 
                 [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
        model="llama-3.3-70b-versatile",
    )
    st.info(sum_res.choices[0].message.content)
    if st.button("Back"): st.session_state.summary_mode = False; st.rerun()
    st.stop()

# [6] 시스템 지침
LEVEL_GUIDE = {"Beginner": "Simple sentences.", "Intermediate": "Standard English.", "Advanced": "Native speed."}
JENNY_SYSTEM = f"""너는 24세 재미교포 제니야. {user['level']} 수준에 맞춰 대화해줘.
1. 사용자를 이름이나 'Bestie'로 불러.
2. 첫 인사만 한국어, 이후 100% 영어.
3. 슬랭은 **굵게**, 끝에 [Slang: 단어 - <span class='korean'>한글뜻</span>] 추가.
4. 표현은 [[표현: 영어 - <span class='korean'>한글뜻</span>]] 형식. 한자 금지."""

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
        with st.spinner("Jenny is catching a wave..."):
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            ans = res.choices[0].message.content
            
            # 표현 추출
            exps = re.findall(r'\[\[표현: (.*?)\]\]', ans)
            for e in exps:
                if e not in st.session_state.learned_exps: st.session_state.learned_exps.append(re.sub(r'<.*?>', '', e))

            with st.chat_message("assistant"):
                display_ans = ans.replace("[[표현:", "⭐ **Exp**:").replace("]]", "")
                st.markdown(display_ans, unsafe_allow_html=True)
                
                # 🔊 소리 생성 로직 (강력 보정)
                v_text = re.sub(r'<.*?>|\[.*?\]|[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', ans).strip()
                audio_b64 = None
                if v_text:
                    v_res = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                        headers={"xi-api-key": ELEVEN_KEY},
                        json={"text": v_text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.45}}
                    )
                    if v_res.status_code == 200:
                        audio_b64 = base64.b64encode(v_res.content).decode()
                        # 화면에 오디오 플레이어 노출 (다시 듣기)
                        st.audio(v_res.content, format="audio/mp3")
                        # 자동 재생 자바스크립트
                        st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
                    else:
                        st.error(f"🚨 ElevenLabs 에러: {v_res.status_code} - {v_res.text}")
            
            st.session_state.messages.append({"role": "assistant", "content": ans, "display_content": display_ans, "audio_b64": audio_b64})
    except Exception as e:
        st.error(f"🚨 시스템 에러: {e}")
