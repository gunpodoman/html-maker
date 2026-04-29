import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re
import json
import os

# 1. 페이지 설정 (가장 먼저 실행)
st.set_page_config(layout="wide", page_title="AI Magic UI Chat")

# 저장 폴더 설정
SAVE_DIR = "chat_sessions"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 2. 세션 상태 초기화 (새로고침 시 데이터 보존을 위해 초기값 설정)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "dynamic_css" not in st.session_state:
    st.session_state.dynamic_css = ""
if "dynamic_js" not in st.session_state:
    st.session_state.dynamic_js = ""

# --- [중요] 스타일 주입부: 코드 최상단에서 매번 실행되어야 함 ---
def apply_styles():
    # CSS 주입 (배경, 글자색 등)
    if st.session_state.dynamic_css:
        st.markdown(f"<style>{st.session_state.dynamic_css}</style>", unsafe_allow_html=True)
    
    # JS 주입 (고래 애니메이션 등)
    if st.session_state.dynamic_js:
        # components.html은 iframe이므로, 배경 애니메이션을 위해 투명한 전체 화면 레이어로 설정
        components.html(f"""
            <script>
            {st.session_state.dynamic_js}
            </script>
        """, height=0, width=0)

# 3. 앱 시작 시 스타일 즉시 적용
apply_styles()

# 4. API 설정
try:
    # Streamlit Secrets에서 가져오기
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    client = OpenAI(api_key=API_KEY, base_url="https://api.sambanova.ai/v1")
except:
    st.error("API Key 설정이 필요합니다 (Streamlit Cloud Secrets)")
    st.stop()

# 5. 사이드바 (저장/불러오기)
with st.sidebar:
    st.title("💾 저장/로드")
    save_name = st.text_input("현재 테마 저장 이름")
    if st.button("서버에 저장"):
        if save_name:
            data = {"messages": st.session_state.messages, "css": st.session_state.dynamic_css, "js": st.session_state.dynamic_js}
            with open(os.path.join(SAVE_DIR, f"{save_name}.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.success("저장되었습니다!")

    st.divider()
    
    saved_files = [f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    selected_file = st.selectbox("불러오기", ["선택 안 함"] + saved_files)
    if st.button("로드하기"):
        if selected_file != "선택 안 함":
            with open(os.path.join(SAVE_DIR, f"{selected_file}.json"), "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.messages = data["messages"]
                st.session_state.dynamic_css = data["css"]
                st.session_state.dynamic_js = data["js"]
            st.rerun()

    if st.button("🗑️ 초기화"):
        st.session_state.messages = []
        st.session_state.dynamic_css = ""
        st.session_state.dynamic_js = ""
        st.rerun()

# 6. 채팅 화면 구성
st.title("🌈 AI UI Magic Chat")
st.write("디자인 수정을 요청하면 앱이 즉시 변합니다!")

# 대화 내용 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 채팅 입력창
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 사용자 메시지 저장 및 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("마법을 부리는 중..."):
            # 시스템 프롬프트: CSS 선택자를 정확히 알려줌
            system_msg = f"""You are a master of Streamlit UI.
            If the user asks for design changes, you MUST provide CSS or JS.
            
            Selectors:
            - Entire App: .stApp
            - Chat Message: [data-testid="stChatMessage"]
            - User Message: [data-testid="stChatMessage"]:nth-child(even)
            - Assistant Message: [data-testid="stChatMessage"]:nth-child(odd)
            - Chat Input Area: [data-testid="stChatInput"]
            - Text Color: p, h1, h2, h3, span
            
            Format:
            - CSS: Wrap in [CSS] ... [/CSS] tags.
            - JS: Wrap in [JS] ... [/JS] tags.
            
            Current CSS: {st.session_state.dynamic_css}
            
            Tell the user naturally what you changed, then include the tags.
            """
            
            response = client.chat.completions.create(
                model="DeepSeek-V3.2",
                messages=[{"role": "system", "content": system_msg}] + st.session_state.messages[-6:],
                temperature=0.2
            )
            
            full_content = response.choices[0].message.content
            
            # 스타일 데이터 파싱 및 업데이트
            new_css = re.search(r"\[CSS\](.*?)\[/CSS\]", full_content, re.DOTALL)
            new_js = re.search(r"\[JS\](.*?)\[/JS\]", full_content, re.DOTALL)
            
            # 텍스트 답변만 추출
            clean_text = re.sub(r"\[CSS\].*?\[/CSS\]", "", full_content, flags=re.DOTALL)
            clean_text = re.sub(r"\[JS\].*?\[/JS\]", "", clean_text, flags=re.DOTALL)
            
            if new_css:
                st.session_state.dynamic_css = new_css.group(1).strip()
            if new_js:
                st.session_state.dynamic_js = new_js.group(1).strip()
                
            st.markdown(clean_text)
            st.session_state.messages.append({"role": "assistant", "content": clean_text})
            
            # 스타일이 바뀌었으므로 즉시 리런하여 최상단 apply_styles() 호출
            if new_css or new_js:
                st.rerun()
