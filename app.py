import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re
import base64

# 페이지 설정
st.set_page_config(layout="wide", page_title="SambaNova AI Web Builder")

# 스타일 설정 (버튼 디자인 등)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3em; font-weight: bold; }
    .preview-button {
        display: inline-block;
        padding: 0.5em 1em;
        color: white;
        background-color: #28a745;
        text-decoration: none;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        margin-top: 10px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. API 키 설정 (Streamlit Secrets)
try:
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    client = OpenAI(api_key=API_KEY, base_url="https://api.sambanova.ai/v1")
except Exception:
    st.error("❌ API Key를 확인해주세요. (Streamlit Secrets 설정 필요)")
    st.stop()

# 2. 모델 목록 가져오기
@st.cache_data(ttl=3600)
def get_models():
    try:
        models = client.models.list()
        return [model.id for model in models.data]
    except:
        return ["DeepSeek-V3", "DeepSeek-R1"]

# 사이드바
with st.sidebar:
    st.title("🤖 모델 설정")
    available_models = get_models()
    selected_model = st.selectbox("모델 선택", available_models, index=0)
    st.divider()
    st.write("아이패드 배포용 버전")

# 코드 추출 함수
def extract_html_code(text):
    pattern = r"```(?:html)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

# 세션 상태 초기화
if "html_code" not in st.session_state:
    st.session_state.html_code = ""

st.title("🚀 AI HTML Full-Screen Builder")

# 입력 영역
prompt = st.text_area("어떤 웹사이트를 만들까요?", placeholder="예: 화려한 네온 사인이 들어간 3D 타이머 웹사이트 만들어줘", height=150)

if st.button("코드 생성하기 ✨"):
    if prompt:
        with st.spinner("AI가 코드를 작성 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a master web developer. Create a single-file HTML/CSS/JS solution. Include all dependencies in the file. Output ONLY the code inside markdown code blocks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                st.session_state.html_code = extract_html_code(response.choices[0].message.content)
            except Exception as e:
                st.error(f"오류 발생: {e}")
    else:
        st.warning("프롬프트를 입력하세요.")

# 결과가 있을 때만 표시
if st.session_state.html_code:
    col_code, col_preview = st.columns([1, 1])

    with col_code:
        st.subheader("📄 Generated Code")
        st.code(st.session_state.html_code, language="html", line_numbers=True)
        st.download_button("index.html 다운로드", st.session_state.html_code, file_name="index.html")

    with col_preview:
        st.subheader("💻 Preview Options")
        
        # 1. 새 탭에서 열기 버튼 구현 (Base64 인코딩 사용)
        b64_code = base64.b64encode(st.session_state.html_code.encode()).decode()
        # 데이터 URI를 사용하여 새 탭에서 즉시 열기
        html_link = f'<a href="data:text/html;base64,{b64_code}" target="_blank" class="preview-button">🌐 새 탭에서 전체 화면으로 보기</a>'
        st.markdown(html_link, unsafe_allow_html=True)
        
        st.info("위 버튼을 누르면 새 창에서 디자인을 깨짐 없이 확인할 수 있습니다.")
        
        # 2. 작은 미리보기 (참고용)
        st.caption("간이 미리보기")
        components.html(st.session_state.html_code, height=400, scrolling=True)
