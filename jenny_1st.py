import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# [1] 디자인 (생략 가능하지만 제니의 자존심!)
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("<style>.stApp { background-image: url('https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg'); background-size: cover; }</style>", unsafe_allow_html=True)

st.title("🐆 제니쌤 영어 VIP")

# [2] API 설정 및 모델 자동 탐색 (404 방어막)
try:
    # Secrets 로딩
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    genai.configure(api_key=GOOGLE_KEY)

    # ⭐ 범인 검거 로직: 서버에 있는 모델 중 쓸 수 있는 걸 직접 찾기
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # gemini-1.5-flash 가 들어간 모델을 우선 찾고, 없으면 아무거나!
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    model = genai.GenerativeModel(
        model_name=st.session_state.model_path,
        system_instruction="너는 24세 재미교포 제니야. 힙한 MZ 영어쌤. 한 줄 영어 대화."
    )

    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"제니가 아직 잠들어 있어요... 원인: {e}")
    st.stop()

# [3] 대화창 (심플하게!)
if "msgs" not in st.session_state: st.session_state.msgs = []
for m in st.session_state.msgs:
    with st.chat_message(m["role"]): st.write(m["content"])

prompt = st.chat_input("Hi Jenny!")
if prompt:
    st.session_state.msgs.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        response = st.session_state.chat.send_message(prompt)
        answer = response.text
        with st.chat_message("assistant"): st.write(answer)
        st.session_state.msgs.append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"대화 도중 에러: {e}")
