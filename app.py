import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re
import json
import os
import base64
from datetime import datetime

# ==========================================
# 1. 고도화된 페이지 구성 및 테마 엔진
# ==========================================
st.set_page_config(
    page_title="DeepSeek-V3.2 UI Architect",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 저장소 경로 설정
SESSIONS_DIR = "stored_sessions"
if not os.path.exists(SESSIONS_DIR):
    os.makedirs(SESSIONS_DIR)

# 세션 상태 초기화 (강력한 데이터 무결성 보장)
STATE_KEYS = {
    "messages": [],
    "dynamic_css": "",
    "dynamic_js": "",
    "current_session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
    "last_ai_response": "",
    "system_status": "Ready",
    "theme_intensity": 0.8
}

for key, value in STATE_KEYS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. 강력한 스타일/스크립트 주입 시스템 (Magic Engine)
# ==========================================
def inject_magic_engine():
    """
    아이패드와 브라우저의 CSS 우선순위를 강제로 점유하고 
    자바스크립트 애니메이션 레이어를 생성합니다.
    """
    # 기본 레이아웃 최적화 CSS
    base_css = """
    <style>
    /* 기본 스트림릿 패딩 제거 및 캔버스 확보 */
    .block-container { padding-top: 2rem !important; padding-bottom: 0rem !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
    
    /* AI가 주입하는 동적 CSS 적용 영역 */
    """ + st.session_state.dynamic_css + """
    </style>
    """
    st.markdown(base_css, unsafe_allow_html=True)

    # 자바스크립트 엔진 (고래 날아다니기, 배경 파티클 등 처리)
    if st.session_state.dynamic_js:
        # 이 부분은 전체 화면 뒤에서 돌아가는 캔버스 레이어를 생성할 수 있도록 iFrame으로 삽입
        components.html(f"""
            <script>
            try {{
                {st.session_state.dynamic_js}
            }} catch (e) {{
                console.error("AI JS Error: ", e);
            }}
            </script>
        """, height=0, width=0)

# 최상단 실행
inject_magic_engine()

# ==========================================
# 3. SambaNova & DeepSeek API 컨트롤러
# ==========================================
class DeepSeekController:
    def __init__(self):
        try:
            self.api_key = st.secrets["SAMBANOVA_API_KEY"]
            self.client = OpenAI(api_key=self.api_key, base_url="https://api.sambanova.ai/v1")
        except:
            st.error("❌ SAMBANOVA_API_KEY가 설정되지 않았습니다. Secrets 설정을 확인하세요.")
            st.stop()

    def get_system_prompt(self):
        # AI에게 앱의 모든 구조를 학습시키는 마스터 프롬프트
        return f"""You are 'Aether', a sentient UI Architect. You exist within a Streamlit application.
Your goal is to modify your own existence (the UI) based on the user's emotions and requests.

TECHNICAL SPECIFICATIONS:
- You control the CSS. Target strictly:
  - Global Background: .stApp
  - Chat Container: [data-testid="stChatMessage"]
  - User Message Bubbles: [data-testid="stChatMessage"]:has([aria-label="user"])
  - Assistant Message Bubbles: [data-testid="stChatMessage"]:has([aria-label="assistant"])
  - Text Elements: p, h1, h2, h3, span, div
  - Input Box: [data-testid="stChatInput"] textarea
- IMPORTANT: Use !important on EVERY CSS rule to override Streamlit defaults.
- For animations (like flying whales, falling stars), use [JS] tags to write pure Vanilla JavaScript.
- Current CSS State: {st.session_state.dynamic_css}

FORMATTING RULES:
1. Normal talk: Explain what you're doing.
2. Styling: Wrap CSS in [CSS] ... [/CSS] blocks.
3. Animation: Wrap JS in [JS] ... [/JS] blocks.
Example: [CSS] .stApp {{ background: red !important; }} [/CSS]
"""

    def generate_response(self, user_input):
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        # 대화 맥락 유지 (최근 10개)
        messages.extend(st.session_state.messages[-10:])
        messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model="DeepSeek-V3.2",
                messages=messages,
                temperature=0.4, # 창의성과 정확성 사이의 균형
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ API Error: {str(e)}"

# ==========================================
# 4. 데이터 지속성 (저장/불러오기) 모듈
# ==========================================
def save_current_session(name):
    filepath = os.path.join(SESSIONS_DIR, f"{name}.json")
    payload = {
        "messages": st.session_state.messages,
        "dynamic_css": st.session_state.dynamic_css,
        "dynamic_js": st.session_state.dynamic_js,
        "timestamp": datetime.now().isoformat()
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

def load_session(name):
    filepath = os.path.join(SESSIONS_DIR, f"{name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state.messages = data["messages"]
            st.session_state.dynamic_css = data["dynamic_css"]
            st.session_state.dynamic_js = data["dynamic_js"]
            return True
    return False

# ==========================================
# 5. 메인 UI 레이아웃
# ==========================================
controller = DeepSeekController()

with st.sidebar:
    st.title("🧪 Core Settings")
    st.status(f"System: {st.session_state.system_status}")
    
    with st.expander("💾 Session Management", expanded=True):
        session_name = st.text_input("Session Name", placeholder="My Cool UI")
        if st.button("💾 Save State", use_container_width=True):
            if session_name:
                save_current_session(session_name)
                st.toast("Current UI state saved to server!")
        
        saved_sessions = [f.replace(".json", "") for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
        selected = st.selectbox("Load Session", ["None"] + saved_sessions)
        if st.button("📂 Restore Session", use_container_width=True):
            if selected != "None":
                if load_session(selected):
                    st.rerun()

    st.divider()
    if st.button("🗑️ Full System Reset", type="primary", use_container_width=True):
        for key in STATE_KEYS:
            st.session_state[key] = STATE_KEYS[key]
        st.rerun()

# --- 메인 채팅 인터페이스 ---
st.title("🔮 The Magic Architect")
st.info("I am DeepSeek-V3.2. I can see your words and change my world accordingly.")

# 채팅 메시지 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 입력 엔진
if prompt := st.chat_input("채팅창을 무지개색으로 빛나게 해줘, 혹은 배경에 고래를 띄워줘..."):
    # 1. 사용자 입력 기록
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI 응답 및 UI 수정
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        with st.spinner("Modifying Reality..."):
            full_response = controller.generate_response(prompt)
            
            # 정규표현식을 이용한 고성능 파싱
            css_content = re.search(r"\[CSS\](.*?)\[/CSS\]", full_response, re.DOTALL)
            js_content = re.search(r"\[JS\](.*?)\[/JS\]", full_response, re.DOTALL)
            
            # 텍스트 답변 정제 (코드 태그 제거)
            display_text = re.sub(r"\[CSS\].*?\[/CSS\]", "", full_response, flags=re.DOTALL)
            display_text = re.sub(r"\[JS\].*?\[/JS\]", "", display_text, flags=re.DOTALL)
            
            # 상태 업데이트
            if css_content:
                st.session_state.dynamic_css = css_content.group(1).strip()
            if js_content:
                st.session_state.dynamic_js = js_content.group(1).strip()
            
            response_placeholder.markdown(display_text)
            st.session_state.messages.append({"role": "assistant", "content": display_text})
            
            # 디자인 변경 사항이 있다면 즉시 리런하여 Magic Engine 가동
            if css_content or js_content:
                st.rerun()

# ==========================================
# 6. 하단 디버그 및 툴팁 (옵션)
# ==========================================
if st.checkbox("Show System Code"):
    with st.expander("현재 주입된 CSS 코드 보기"):
        st.code(st.session_state.dynamic_css, language="css")
    with st.expander("현재 주입된 JS 코드 보기"):
        st.code(st.session_state.dynamic_js, language="javascript")
