import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# 제목
st.markdown("<h1 style='text-align: center;'>IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size:10pt;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 버튼 2개 배치
col1, col2 = st.columns([1, 1])
with col1:
    run_button_db = st.button("📊 전체 데이터 조회", key="btn_db")
with col2:
    run_button_global = st.button("🌎 해외 데이터 조회", key="btn_global")

# 임시 데이터 예시
temp_data_1 = pd.DataFrame({
    '지표': ['GDP', 'CPI', 'PPI'],
    '2024 Q4': [25000, 3.2, 1.8],
    '2024 Q3': [24500, 3.4, 2.0],
    '2024 Q2': [24000, 3.6, 2.3],
})

temp_data_2 = pd.DataFrame({
    '지표': ['GDP', '실업률', '무역수지'],
    '2024 Q4': [13500, 5.1, -600],
    '2024 Q3': [13000, 5.0, -550],
    '2024 Q2': [12800, 5.2, -580],
})

# 버튼 누를 때마다 임시 표 렌더링
if run_button_db:
    st.markdown("#### 📊 전체 데이터")
    st.dataframe(temp_data_1, use_container_width=True)

elif run_button_global:
    st.markdown("#### 🌎 해외 데이터")
    st.dataframe(temp_data_2, use_container_width=True)

# 출력 안내 문구 및 버튼
if run_button_db or run_button_global:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("👆  상단   '📊 전체 데이터 조회' 또는 '🌎 해외 데이터 조회' 버튼을  눌러주세요.", unsafe_allow_html=True)
    
    today_str = datetime.today().strftime("%Y%m%d")
    file_name = f"One Page Economy Report_{today_str}.xlsx"

    col3, col4, col5 = st.columns([1.2, 0.1, 1])
    with col3:
        st.download_button(label="📥 엑셀 다운로드", data=b'', file_name=file_name, key="excel")
    with col5:
        st.markdown("<button onclick='window.print()'>🖨️ 인쇄 또는 PDF 저장</button>", unsafe_allow_html=True)
