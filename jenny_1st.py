import streamlit as st
from groq import Groq
import requests
import re
import base64
from datetime import datetime

# [1] 디자인 및 스타일 (럭셔리 하이라이트 스타일)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆", layout="wide")
st.markdown("""
    <style>
    .stApp { 
        background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: rgba(0, 0, 0, 0.85) !important; 
        border: 2px solid #FFD700 !important; border-radius: 15px; 
    }
    .highlight { background-color: #FFFF00; color: #000; padding: 2px 8px; border-radius: 5px; font-weight: bold; border: 1px solid #000; }
    .stMarkdown p, .stMarkdown span { color: #000 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# [2] API 연결
try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()
    client = Groq(api_key=GROQ_KEY)
except Exception as e:
    st.error("Secrets 설정을 확인해줘 언니! 😭"); st.stop()

# [3] 세션 상태 초기화
if "messages" not in st.session_state: st.session_state.messages = []
if "learned_expressions" not in st.session_state: st.session_state.learned_expressions = []

# [4] 사이드바: 설정 및 학습 리스트
with st.sidebar:
    st.title("🐆 Jenny's VIP Lounge")
    # 속도 조절 (ElevenLabs API에서 직접 조절하는 게 아니라 재생 시 속도감 있게 들리도록 설정)
    voice_speed = st.slider("🗣️ 제니 말하기 속도 (재생 바에서 조절 가능)", 0.5, 1.5, 1.0, 0.1)
    
    st.divider()
    st.subheader("📚 Today's Key Expressions")
    for idx, exp in enumerate(st.session_state.learned_expressions):
        st.markdown(f"**{idx+1}.** {exp}")

# [5] 메인 화면
if "user_info" not in st.session_state:
    st.title("🐆 Welcome back, Maykim!")
    if st.button("Start Lesson"):
        st.session_state.user_info = {"name": "maykim"}
        st.rerun()
    st.stop()

# 제니 지침 (세련된 전문 강사 톤)
JENNY_SYSTEM = """
너는 24세 재미교포 제니야. 전문 영어 강사이자 심리학에 능통한 ENFP 서퍼지.
[지침]
1. 세련되고 지적인 톤을 유지해.
2. 첫 인사만 한국어, 이후 100% 영어.
3. 유용한 표현은 반드시 [[표현: 영어표현 - 뜻]] 형식으로 포함해줘.
4. 슬랭은 **굵게** 표시하고 끝에 [Slang: 단어-뜻] 추가.
"""

# 대화 로그 출력
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): 
            st.markdown(m["display_content"], unsafe_allow_html=True)
            if m.get("audio_content"):
                st.audio(m["audio_content"], format="audio/mp3")

# [6] 메인 대화 로직
prompt = st.chat_input("Hey Jenny! Let's talk!")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "display_content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("Jenny is thinking... 🌊"):
            response = client.chat.completions.create(
                messages=[{"role": "system", "content": JENNY_SYSTEM}] + 
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                model="llama-3.3-70b-versatile",
            )
            answer = response.choices[0].message.content
            
            # 표현 추출
            new_exps = re.findall(r'\[\[표현: (.*?)\]\]', answer)
            for e in new_exps:
                if e not in st.session_state.learned_expressions:
                    st.session_state.learned_expressions.append(e)

            with st.chat_message("assistant"):
                display_answer = re.sub(r'\[\[표현: (.*?)\]\]', r'<span class="highlight">\1</span>', answer)
                st.markdown(display_answer, unsafe_allow_html=True)
                
                # 음성 생성용 텍스트 정제
                v_text = re.sub(r'\[Slang:.*?\]', '', answer)
                v_text = re.sub(r'\[\[표현:.*?\]\]', '', v_text)
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                audio_bytes = None
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
                        audio_bytes = v_res.content
                        # 확실하게 눈에 보이는 오디오 플레이어 추가!
                        st.audio(audio_bytes, format="audio/mp3")
            
            # 메시지 저장 시 오디오 데이터도 함께 저장 (나중에 다시 들을 수 있게)
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer, 
                "display_content": display_answer,
                "audio_content": audio_bytes
            })
    except Exception as e:
        st.error(f"Error: {e}")
