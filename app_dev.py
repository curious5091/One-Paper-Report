import streamlit as st
import pandas as pd
 
 # 페이지 설정
 st.set_page_config(layout="wide")
 
 # 타이틀
 st.markdown("<h1 style='text-align: center;'>Dev Page</h1>", unsafe_allow_html=True)
 st.markdown("<div style='text-align: center; font-size:10pt;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)
 st.markdown("<br>", unsafe_allow_html=True)
 
 # 7개 버튼 영역 생성
 cols = st.columns(6)
 cols = st.columns(7)
 
 with cols[0]:
     run_button_1 = st.button("📊 경제지표 조회 / 출력", key="btn1")
 @@ -19,30 +19,30 @@
     run_button_2 = st.button("🌎 중기지표 조회 / 출력", key="btn2")
 
 # 나머지 컬럼은 비워둠 (추후 버튼 추가용)
 for i in range(2, 6):
 for i in range(2, 7):
     with cols[i]:
         st.markdown("&nbsp;", unsafe_allow_html=True)
 
 # 임시 데이터
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
 
 # 버튼 클릭 시 표 출력
 if run_button_1:
     st.markdown("#### 📊 경제지표")
     st.dataframe(temp_data_1, use_container_width=True)
 
 elif run_button_2:
     st.markdown("#### 🌎 중기지표")
     st.dataframe(temp_data_2, use_container_width=True)
