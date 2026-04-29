import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re
import json
import os

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="AI Self-Modifying Chat")

# 저장 폴더 설정
SAVE_DIR = "chat_sessions"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 2. 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [] # 대화 내용
if "dynamic_css" not in st.session_state:
    st.session_state.dynamic_css = "" # 앱에 주입될 CSS
if "dynamic_js" not in st.session_state:
    st.session_state.dynamic_js = "" # 앱에 주입될 JS (고래 등 애니메이션)

# 3. API 설정
try:
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    client = OpenAI(api_key=API_KEY, base_url="https://api.sambanova.ai/v1")
except:
    st.error("Streamlit Secrets에 SAMBANOVA_API_KEY를 설정해주세요.")
    st.stop()

# 4. 스타일 및 스크립트 주입 함수
def apply_custom_style():
    # CSS 주입
    st.markdown(f"<style>{st.session_state.dynamic_css}</style>", unsafe_allow_html=True)
    # JS 주입 (고래 날아다니기 등 애니메이션 처리용)
    if st.session_state.dynamic_js:
        components.html(f"<script>{st.session_state.dynamic_js}</script>", height=0)

# 5. 저장/불러오기 기능
def save_chat(name):
    data = {
        "messages": st.session_state.messages,
        "css": st.session_state.dynamic_css,
        "js": st.session_state.dynamic_js
    }
    with open(os.path.join(SAVE_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_chat(name):
    path = os.path.join(SAVE_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.messages = data["messages"]
            st.session_state.dynamic_css = data["css"]
            st.session_state.dynamic_js = data["js"]
            return True
    return False

# 6. 사이드바 (저장/불러오기)
with st.sidebar:
    st.title("💾 저장소")
    save_name = st.text_input("현재 상태 저장 이름")
    if st.button("서버에 저장"):
        if save_name:
            save_chat(save_name)
            st.success("저장 완료!")
    
    st.divider()
    
    files = [f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    selected_file = st.selectbox("불러오기", ["선택 안 함"] + files)
    if st.button("로드하기"):
        if selected_file != "선택 안 함":
            if load_chat(selected_file):
                st.rerun()

    if st.button("🗑️ 모든 초기화"):
        st.session_state.messages = []
        st.session_state.dynamic_css = ""
        st.session_state.dynamic_js = ""
        st.rerun()

# 7. 메인 채팅 UI
st.title("🌈 Magic UI AI Chat")
st.caption("DeepSeek-V3.2가 대화 내용에 맞춰 앱의 UI를 실시간으로 변경합니다.")

# 현재까지의 스타일 적용
apply_custom_style()

# 채팅 내역 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 채팅 입력
if prompt := st.chat_input("메시지를 입력하세요 (예: 배경에 고래가 날라다니게 해줘)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중..."):
            system_prompt = f"""You are a UI magician.
            - If user asks for visual changes (rainbow text, animations, colors), provide CSS/JS code.
            - CSS selector info:
              - App background: `.stApp`
              - Chat messages: `[data-testid="stChatMessage"]`
              - Chat text: `[data-testid="stChatMessageContent"] p`
              - Chat input: `[data-testid="stChatInput"] textarea`
            - Format for styling: Wrap CSS in [CSS] tags and JS in [JS] tags.
            - If it's a normal conversation, just talk naturally.
            - ALWAYS include the updated styling code if the user requested a change.
            - CURRENT CSS: {st.session_state.dynamic_css}
            """
            
            response = client.chat.completions.create(
                model="DeepSeek-V3.2",
                messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages[-10:],
                temperature=0.3
            )
            
            full_res = response.choices[0].message.content
            
            # 스타일 추출
            css_match = re.search(r"\[CSS\](.*?)\[/CSS\]", full_res, re.DOTALL)
            js_match = re.search(r"\[JS\](.*?)\[/JS\]", full_res, re.DOTALL)
            
            clean_res = re.sub(r"\[CSS\].*?\[/CSS\]", "", full_res, flags=re.DOTALL)
            clean_res = re.sub(r"\[JS\].*?\[/JS\]", "", clean_res, flags=re.DOTALL)
            
            if css_match:
                st.session_state.dynamic_css = css_match.group(1).strip()
            if js_match:
                st.session_state.dynamic_js = js_match.group(1).strip()
            
            st.markdown(clean_res)
            st.session_state.messages.append({"role": "assistant", "content": clean_res})
            
            # 스타일 변경 사항이 있으면 즉시 리런해서 반영
            if css_match or js_match:
                st.rerun()
