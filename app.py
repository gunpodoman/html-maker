import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re

# 페이지 설정
st.set_page_config(layout="wide", page_title="SambaNova AI Code Builder")

# 스타일 설정
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #007BFF; color: white; height: 3em; }
    iframe { border: 1px solid #ddd; border-radius: 8px; background: white; }
    </style>
    """, unsafe_allow_html=True)

# 1. API 키 설정 (Streamlit Secrets 사용)
# 배포 시 Streamlit Cloud 설정에서 SAMBANOVA_API_KEY를 추가해야 합니다.
try:
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    BASE_URL = "https://api.sambanova.ai/v1"
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
except Exception:
    st.error("❌ API Key가 설정되지 않았습니다. Streamlit Cloud의 Secrets 설정에서 SAMBANOVA_API_KEY를 추가해주세요.")
    st.stop()

# 2. 사용 가능한 모델 목록 가져오기
@st.cache_data(ttl=3600) # 모델 목록은 1시간 동안 캐싱
def get_models():
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except Exception as e:
        st.sidebar.error(f"모델 목록을 불러오지 못했습니다: {e}")
        return ["DeepSeek-V3", "Meta-Llama-3.1-405B-Instruct", "Meta-Llama-3.1-70B-Instruct"]

# 사이드바 구성
with st.sidebar:
    st.title("🤖 모델 설정")
    available_models = get_models()
    selected_model = st.selectbox("사용할 모델을 선택하세요", available_models, index=0)
    st.divider()
    st.info("이 앱은 SambaNova API를 사용하여 실시간 HTML 코드를 생성합니다.")

# 코드 추출 정규식 함수
def extract_html_code(text):
    # ```html ... ``` 또는 ``` ... ``` 블록 추출
    pattern = r"```(?:html)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

# 메인 UI
st.title("🚀 AI Real-time HTML Designer")

if "html_code" not in st.session_state:
    st.session_state.html_code = """
    <div style="display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <h2 style="color:#888;">왼쪽에 프롬프트를 입력하고 버튼을 눌러보세요!</h2>
    </div>
    """

# 프롬프트 입력창
prompt = st.text_area("어떤 웹 페이지를 만들고 싶나요?", placeholder="예: 깔끔한 다크모드 대시보드, 애니메이션이 있는 시계 등", height=150)

if st.button("코드 생성 및 실행"):
    if prompt:
        with st.spinner(f"{selected_model} 모델이 코드를 생성 중..."):
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a master web developer. Create a single-file HTML/CSS/JS solution. Output ONLY the code inside markdown code blocks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                raw_content = response.choices[0].message.content
                st.session_state.html_code = extract_html_code(raw_content)
            except Exception as e:
                st.error(f"API 호출 중 오류 발생: {e}")
    else:
        st.warning("프롬프트를 입력해주세요.")

# 화면 분할 (코드창 4 : 미리보기 6 비율)
col_code, col_preview = st.columns([4, 6])

with col_code:
    st.subheader("📄 Generated Code")
    st.code(st.session_state.html_code, language="html", line_numbers=True)
    st.download_button("index.html 다운로드", st.session_state.html_code, file_name="index.html")

with col_preview:
    st.subheader("💻 Live Preview")
    # iframe 생성
    components.html(st.session_state.html_code, height=700, scrolling=True)
