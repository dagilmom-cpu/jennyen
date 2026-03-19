import streamlit as st
import google.generativeai as genai
import requests
import re
import base64

# [1] 디자인 설정
st.set_page_config(page_title="제니쌤 영어 VIP", page_icon="🐆")
st.markdown("""
    <style>
    .stApp { 
        background-image: url("https://img.freepik.com/premium-photo/luxury-pink-gold-leopard-print-pattern-background_911061-163.jpg"); 
        background-size: cover; background-position: center; background-attachment: fixed; 
    }
    html, body, [class*="css"], .stMarkdown, p, span, div { 
        color: #000000 !important; font-weight: 900 !important; 
        text-shadow: -2px -2px 0 #FFF, 2px -2px 0 #FFF, -2px 2px 0 #FFF, -2px 2px 0 #FFF !important; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] { 
        background-color: rgba(0, 0, 0, 0.95) !important; 
        border: 2px solid #FFD700 !important; border-radius: 15px; 
    }
    .stChatMessage[data-testid="stChatMessageAssistant"] p { 
        color: #FFFFFF !important; text-shadow: none !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# 🔊 ElevenLabs 전용 재생 함수 (강력한 HTML5 방식)
def play_eleven_voice(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    # 브라우저 차단을 피하기 위해 '플레이어'와 '자동재생' 스크립트 결합
    audio_html = f"""
        <audio id="jenny_voice" autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        <script>
            var audio = document.getElementById('jenny_voice');
            audio.play().catch(function(error) {{
                console.log("Autoplay blocked by browser");
            }});
        </script>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    # 혹시 몰라서 수동 재생 바도 하나 더!
    st.audio(audio_bytes, format="audio/mp3")

st.title("🐆 제니쌤 영어 VIP")

# [2] API 설정 (Secrets 확인)
try:
    GOOGLE_KEY = st.secrets["GOOGLE_API_KEY"].strip()
    ELEVEN_KEY = st.secrets["ELEVENLABS_API_KEY"].strip()
    VOICE_ID = st.secrets["VOICE_ID"].strip()

    genai.configure(api_key=GOOGLE_KEY)

    # 모델 자동 탐색 (404 방어)
    if "model_path" not in st.session_state:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m.name for m in models if "gemini-1.5-flash" in m.name), models[0].name)
        st.session_state.model_path = target

    model = genai.GenerativeModel(
        model_name=st.session_state.model_path,
        system_instruction="너는 24세 재미교포 제니야. 힙한 MZ 영어쌤. 한 줄 영어 대화만 하고 슬랭 사용 시 [Slang: 단어-뜻]을 붙여줘."
    )

    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"설정 확인 필요: {e}")
    st.stop()

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.write(m["content"])

# [3] 대화 및 보이스 로직
prompt = st.chat_input("Hi Jenny!")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    try:
        with st.spinner("제니가 대답 준비 중... 🥂"):
            response = st.session_state.chat.send_message(prompt)
            answer = response.text
            
            with st.chat_message("assistant"):
                st.write(answer)
                
                # 🔊 ElevenLabs API 호출 (진짜 목소리 가져오기)
                # 슬랭 설명과 한국어는 빼고 영어만 필터링
                v_text = re.sub(r'\[Slang:.*?\]', '', answer).strip()
                v_text = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]+', '', v_text).strip()
                
                if v_text:
                    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
                    headers = {
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": ELEVEN_KEY
                    }
                    data = {
                        "text": v_text,
                        "model_id": "eleven_multilingual_v2", # 가장 좋은 품질
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
                    }
                    
                    v_res = requests.post(url, json=data, headers=headers)
                    
                    if v_res.status_code == 200:
                        play_eleven_voice(v_res.content)
                    else:
                        st.warning(f"목소리 엔진 오류: {v_res.text}")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"에러 발생: {e}")
