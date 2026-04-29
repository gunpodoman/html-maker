import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re

# 페이지 전체 화면 사용 및 제목 설정
st.set_page_config(layout="wide", page_title="DeepSeek HTML Generator")

# CSS로 UI 스타일 살짝 조정
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.title("⚙️ 설정")
    api_key = st.text_input("SambaNova API Key를 입력하세요", type="password")
    st.info("SambaNova Cloud에서 발급받은 API 키가 필요합니다.")
    model_id = "DeepSeek-V3"

# 코드 추출 함수
def extract_code(text):
    # ```html ... ``` 블록 찾기
    code_match = re.search(r"```html\n(.*?)```", text, re.DOTALL)
    if code_match:
        return code_match.group(1)
    # 블록이 없으면 ``` ... ``` 전체 찾기
    code_match = re.search(r"```\n(.*?)```", text, re.DOTALL)
    if code_match:
        return code_match.group(1)
    return text # 아무것도 없으면 전체 반환

# 메인 화면
st.title("🎨 DeepSeek-V3 실시간 웹 디자이너")
st.write("프롬프트를 입력하면 HTML/CSS/JS 코드를 짜고 바로 옆에서 실행해줍니다.")

# 세션 상태 초기화 (결과 유지용)
if "code" not in st.session_state:
    st.session_state.code = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f0f2f5; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>여기에 결과가 표시됩니다.</h1>
</body>
</html>"""

# 입력창
user_prompt = st.text_area("어떤 웹 기능을 만들까요?", placeholder="예: 무지개색으로 변하는 버튼이 있는 계산기 만들어줘", height=100)

if st.button("코드 생성 및 실행 ✨"):
    if not api_key:
        st.error("API 키를 입력해주세요!")
    elif not user_prompt:
        st.warning("내용을 입력해주세요!")
    else:
        try:
            with st.spinner("SambaNova DeepSeek가 코드를 작성 중입니다..."):
                client = OpenAI(
                    base_url="https://api.sambanova.ai/v1",
                    api_key=api_key
                )
                
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are a professional web developer. Create a single, complete HTML file including CSS and JavaScript. Only provide the code block."},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1
                )
                
                raw_content = response.choices[0].message.content
                st.session_state.code = extract_code(raw_content)
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")

# 2분할 레이아웃
col_code, col_preview = st.columns(2)

with col_code:
    st.subheader("📝 생성된 코드")
    st.code(st.session_state.code, language="html", line_numbers=True)
    st.download_button("코드 다운로드", st.session_state.code, file_name="index.html", mime="text/html")

with col_preview:
    st.subheader("👀 실시간 미리보기")
    # iframe 형태로 HTML 실행
    components.html(st.session_state.code, height=600, scrolling=True)
