import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re
import json
import os

# 1. 페이지 설정 및 초기화
st.set_page_config(layout="wide", page_title="DeepSeek-V3.2 AI Live Architect")

# 저장 폴더 설정
SAVE_DIR = "saved_designs"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [] # 채팅 내역
if "current_code" not in st.session_state:
    st.session_state.current_code = "" # 현재 HTML 코드
if "current_save_name" not in st.session_state:
    st.session_state.current_save_name = ""

# 2. API 설정
try:
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    client = OpenAI(api_key=API_KEY, base_url="https://api.sambanova.ai/v1")
except:
    st.error("API Key 설정이 필요합니다 (Streamlit Secrets)")
    st.stop()

# 3. 주요 함수들
def extract_code(text):
    pattern = r"```(?:html)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else text

def save_design(name, code, history):
    filename = os.path.join(SAVE_DIR, f"{name}.json")
    data = {"code": code, "history": history}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_design(name):
    filename = os.path.join(SAVE_DIR, f"{name}.json")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# 4. 사이드바 (저장/불러오기/초기화)
with st.sidebar:
    st.title("📂 저장 및 불러오기")
    
    # 저장하기
    save_name = st.text_input("디자인 이름", value=st.session_state.current_save_name)
    if st.button("💾 서버에 저장"):
        if save_name and st.session_state.current_code:
            save_design(save_name, st.session_state.current_code, st.session_state.messages)
            st.success(f"'{save_name}' 저장 완료!")
            st.rerun()
        else:
            st.warning("이름과 코드가 필요합니다.")

    st.divider()

    # 불러오기
    saved_files = [f.replace(".json", "") for f in os.listdir(SAVE_DIR) if f.endswith(".json")]
    selected_load = st.selectbox("불러올 디자인 선택", ["선택 안 함"] + saved_files)
    if st.button("📂 불러오기"):
        if selected_load != "선택 안 함":
            data = load_design(selected_load)
            if data:
                st.session_state.current_code = data["code"]
                st.session_state.messages = data["history"]
                st.session_state.current_save_name = selected_load
                st.success("로드 성공!")
                st.rerun()

    st.divider()
    
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = []
        st.session_state.current_code = ""
        st.session_state.current_save_name = ""
        st.rerun()

# 5. 메인 레이아웃 (왼쪽: 채팅 / 오른쪽: 프리뷰)
col_chat, col_preview = st.columns([4, 6])

with col_chat:
    st.subheader("💬 AI Designer Chat")
    
    # 채팅 내역 표시
    chat_container = st.container(height=500)
    for message in st.session_state.messages:
        with chat_container.chat_message(message["role"]):
            st.markdown(message["content"])

    # 채팅 입력
    if prompt := st.chat_input("디자인 수정을 요청하세요..."):
        # 1. 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)

        # 2. AI 응답 생성
        with chat_container.chat_message("assistant"):
            with st.spinner("생각 중..."):
                # 이전 코드를 포함하여 시스템 프롬프트 작성
                system_msg = f"""You are a professional web designer. 
                CURRENT_CODE:
                {st.session_state.current_code}
                
                Instruction:
                1. Modify the CURRENT_CODE based on user request.
                2. ALWAYS return the FULL complete HTML/CSS/JS code in a markdown block.
                3. Briefly explain what you changed before the code block."""
                
                messages = [{"role": "system", "content": system_msg}] + st.session_state.messages[-5:] # 최근 5대화 유지
                
                response = client.chat.completions.create(
                    model="DeepSeek-V3.2",
                    messages=messages,
                    temperature=0.1
                )
                
                full_response = response.choices[0].message.content
                st.markdown(full_response)
                
                # 코드 추출 및 상태 업데이트
                new_code = extract_code(full_response)
                if new_code:
                    st.session_state.current_code = new_code
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.rerun()

with col_preview:
    st.subheader("💻 Live Design Preview")
    
    if st.session_state.current_code:
        # 아이패드용 새 탭 열기 자바스크립트
        escaped_code = st.session_state.current_code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        js_button = f"""
            <script>
            function openInNewTab() {{
                var win = window.open('', '_blank');
                win.document.write(`{escaped_code}`);
                win.document.close();
            }}
            </script>
            <button onclick="openInNewTab()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">
                🌐 전체 화면으로 보기 (새 탭)
            </button>
        """
        components.html(js_button, height=80)
        
        # 앱 내 프리뷰
        components.html(st.session_state.current_code, height=750, scrolling=True)
    else:
        st.info("채팅으로 원하는 웹사이트 디자인을 말해보세요!")
