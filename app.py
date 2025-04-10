import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# 인증 및 초기 설정
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")

# 상단 제목
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 초기 세션 상태 설정
if "all_selected" not in st.session_state:
    st.session_state.all_selected = True
if "selected_countries" not in st.session_state:
    st.session_state.selected_countries = set()

# 국가 정의
all_main = ["한국", "미국", "중국", "일본", "유로존", "신흥국"]
emerging = {"베트남", "폴란드", "인도네시아", "인도"}
all_countries = ["한국", "미국", "중국", "일본", "유로존"] + list(emerging)

# 버튼 스타일 함수
def render_button(label, selected):
    style = f"""
        display:inline-block;
        margin: 4px 6px 12px 0;
        padding: 6px 16px;
        font-size: 10pt;
        font-weight: bold;
        border: 2px solid #333;
        border-radius: 6px;
        background-color: {'#2c80ff' if selected else '#fff'};
        color: {'#fff' if selected else '#000'};
        cursor: pointer;
    """
    return f"<button style='{style}'>{label}</button>"

# 전체/국가 선택 버튼 UI
st.markdown("### 국가 선택")
col_container = st.container()
with col_container:
    # 전체 보기 버튼
    col_all, col_each = st.columns([1, 5])
    with col_all:
        if st.button("전체 보기", key="전체보기"):
            st.session_state.all_selected = True
            st.session_state.selected_countries = set()
    with col_each:
        st.markdown("<div style='display:flex; flex-wrap:wrap;'>", unsafe_allow_html=True)
        for country in all_main:
            is_selected = country in st.session_state.selected_countries
            if st.button(country, key=f"선택_{country}"):
                st.session_state.all_selected = False
                if is_selected:
                    st.session_state.selected_countries.remove(country)
                else:
                    st.session_state.selected_countries.add(country)
            st.markdown(render_button(country, is_selected), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# 출력 국가 결정
if st.session_state.all_selected or not st.session_state.selected_countries:
    selected = all_countries
    selected_emerging = emerging
else:
    selected = []
    selected_emerging = set()
    for c in st.session_state.selected_countries:
        if c == "신흥국":
            selected_emerging = emerging
        else:
            selected.append(c)

# 조회 버튼
run_button = st.button("📥 데이터 조회 및 출력")

# --- 데이터 처리 및 출력 ---
if run_button:
    with st.spinner("⏳ 데이터 로딩 중입니다. 잠시만 기다려주세요..."):
        try:
            sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
            worksheet = sheet.worksheet("Database")
            df = get_as_dataframe(worksheet).dropna(how='all')
            df.columns = df.columns.str.strip()
            df = df[df['샘플구분'] == 'N']
            df['기준시점'] = pd.to_datetime(df['기준시점'], format='%Y-%m', errors='coerce')
            df['발표일'] = pd.to_datetime(df['발표일'], errors='coerce')

            def format_period(row):
                d = row['기준시점']
                if pd.isnull(d): return ""
                if row['지표'] == 'GDP(분기)' or row['빈도'] == '분기':
                    q = (d.month - 1) // 3 + 1
                    return f"{d.year} Q{q}"
                elif row['지표'] == 'GDP(연간)' or row['빈도'] == '연도':
                    return f"{d.year}"
                return d.strftime('%Y-%m')

            df['기준시점_text'] = df.apply(format_period, axis=1)
            df_sorted = df.sort_values(['국가', '지표', '기준시점', '발표일'], ascending=[True, True, False, False])
            df_deduped = df_sorted.drop_duplicates(subset=['국가', '지표', '기준시점_text'], keep='first')

            def extract_recent(group):
                freq = group['빈도'].iloc[0]
                n = 8 if group['지표'].iloc[0] == 'GDP(분기)' else (4 if freq in ['연도', '분기'] else 6)
                return group.sort_values('기준시점', ascending=False).head(n)

            grouped = df_deduped.groupby(['국가', '지표'], group_keys=False).apply(extract_recent).reset_index(drop=True)

            # value_map 및 출력 전처리 이후 표 렌더링 (기존 html 구조 유지)
            # 필요한 경우 이어서 전체 html 출력부도 제공 가능

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
