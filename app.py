import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
import re

# 페이지 설정
st.set_page_config(layout="wide", page_title="SambaNova DeepSeek-V3.2 Builder")

# CSS: 아이패드 UI 최적화 및 버튼 스타일
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; height: 3.5em; font-weight: bold; border-radius: 12px; background-color: #007bff; color: white; }
    .stTextArea textarea { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 1. API 키 설정 (Streamlit Secrets)
try:
    API_KEY = st.secrets["SAMBANOVA_API_KEY"]
    client = OpenAI(api_key=API_KEY, base_url="https://api.sambanova.ai/v1")
except Exception:
    st.error("❌ API Key 설정 필요: Streamlit Cloud Secrets에 SAMBANOVA_API_KEY를 입력하세요.")
    st.stop()

# 2. 모델 목록 가져오기 및 DeepSeek-V3.2를 기본으로 설정
@st.cache_data(ttl=3600)
def get_models():
    try:
        models = client.models.list()
        model_list = [model.id for model in models.data]
        
        # 사용자가 요청한 DeepSeek-V3.2를 최상단으로 설정
        target_model = "DeepSeek-V3.2"
        if target_model in model_list:
            model_list.remove(target_model)
            model_list.insert(0, target_model)
        else:
            # 리스트에 없을 경우를 대비해 수동으로라도 맨 앞에 추가
            model_list.insert(0, target_model)
            
        return model_list
    except:
        # API 오류 시 수동 목록 (스크린샷 기준)
        return ["DeepSeek-V3.2", "DeepSeek-V3.1", "Llama-4-Maverick-17B-128E-Instruct"]

# 사이드바
with st.sidebar:
    st.title("⚙️ 모델 설정")
    available_models = get_models()
    # DeepSeek-V3.2가 index 0에 오도록 처리됨
    selected_model = st.selectbox("사용할 모델", available_models, index=0)
    st.divider()
    st.info("아이패드 사용 시 '팝업 차단'을 해제해야 새 탭 미리보기가 작동합니다.")

# 코드 추출 함수
def extract_html_code(text):
    pattern = r"```(?:html)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

# 메인 UI
st.title("🚀 DeepSeek-V3.2 Web Designer")
st.write(f"현재 선택된 모델: **{selected_model}**")

if "html_code" not in st.session_state:
    st.session_state.html_code = ""

# 입력창
prompt = st.text_area("어떤 웹 페이지를 만들까요?", 
                    placeholder="예: 실시간으로 움직이는 멋진 3D 배경의 타이머 웹사이트", 
                    height=130)

if st.button("AI 디자인 시작하기 ✨"):
    if prompt:
        with st.spinner(f"{selected_model} 모델이 코드를 생성 중..."):
            try:
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": "You are a professional web developer. Create a single-file HTML/CSS/JS solution. Output ONLY the code inside markdown blocks."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                st.session_state.html_code = extract_html_code(response.choices[0].message.content)
            except Exception as e:
                st.error(f"오류 발생: {e}")
    else:
        st.warning("프롬프트를 입력하세요.")

# 결과 표시 섹션
if st.session_state.html_code:
    tab_preview, tab_code = st.tabs(["🖥️ Full Preview", "📝 Source Code"])

    with tab_preview:
        # --- 아이패드용 새 탭 열기 (JS 방식) ---
        escaped_code = st.session_state.html_code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        
        js_button = f"""
            <script>
            function openNewWindow() {{
                var win = window.open('', '_blank');
                if (win) {{
                    win.document.write(`{escaped_code}`);
                    win.document.close();
                }} else {{
                    alert('팝업 차단됨! 설정에서 팝업을 허용해주세요.');
                }}
            }}
            </script>
            <button onclick="openNewWindow()" style="
                width: 100%; padding: 20px; background-color: #28a745; color: white; 
                border: none; border-radius: 12px; font-size: 18px; font-weight: bold; 
                cursor: pointer; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.15);
            ">
                🌐 새 탭에서 전체 화면으로 실행 (V3.2 결과물)
            </button>
        """
        components.html(js_button, height=100)
        
        # 앱 내 간이 미리보기
        components.html(st.session_state.html_code, height=700, scrolling=True)

    with tab_code:
        st.subheader("HTML 소스 코드")
        st.code(st.session_state.html_code, language="html", line_numbers=True)
        st.download_button("index.html 다운로드", st.session_state.html_code, file_name="index.html")
