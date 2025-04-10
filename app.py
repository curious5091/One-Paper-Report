import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# 인증
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

# 페이지 설정
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")

# 상단 제목
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 초기 상태 설정
if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = "전체 보기"
if "selected_custom" not in st.session_state:
    st.session_state.selected_custom = set()

# 국가 정의
main_countries = ["한국", "미국", "중국", "일본", "유로존", "신흥국"]
all_countries_full = ["한국", "미국", "중국", "일본", "유로존", "베트남", "폴란드", "인도네시아", "인도"]
emerging = {"베트남", "폴란드", "인도네시아", "인도"}

# 버튼 스타일 정의
def custom_button(label, selected=False):
    base_style = "padding:6px 12px; margin:4px 4px 8px 0; font-size:10pt; font-weight:bold; border:2px solid #444; border-radius:6px; cursor:pointer;"
    color = "#fff" if selected else "#000"
    background = "#2c80ff" if selected else "#fff"
    return f"<button style='{base_style} background-color:{background}; color:{color};' onclick='window.location.href=\"?{label}\"'>{label}</button>"

# 전체보기 버튼
st.markdown("#### 국가 선택")
col1, col2 = st.columns([1, 5])
with col1:
    clicked = st.button("전체 보기", help="모든 국가를 포함한 전체 보기", type="primary")
    if clicked:
        st.session_state.selected_mode = "전체 보기"
        st.session_state.selected_custom = set()

# 일부 선택 버튼
with col2:
    st.markdown("<div style='display:flex; flex-wrap:wrap;'>", unsafe_allow_html=True)
    for country in main_countries:
        if country == "신흥국":
            actual_countries = emerging
        else:
            actual_countries = {country}
        selected = actual_countries <= st.session_state.selected_custom
        if st.button(f"{country}", key=f"btn_{country}"):
            st.session_state.selected_mode = "일부 보기"
            if selected:
                st.session_state.selected_custom -= actual_countries
            else:
                st.session_state.selected_custom |= actual_countries
        style = "background-color:#2c80ff; color:white;" if selected else "background-color:white; color:black;"
        st.markdown(f"<span style='padding:6px 12px; margin:4px; font-size:10pt; font-weight:bold; border:2px solid #444; border-radius:6px; {style}'>{country}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 국가 리스트 정리
if st.session_state.selected_mode == "전체 보기" or not st.session_state.selected_custom:
    selected_countries = all_countries_full
    selected_emerging = emerging
else:
    selected_countries = []
    selected_emerging = set()
    for c in st.session_state.selected_custom:
        if c in emerging:
            selected_emerging.add(c)
        else:
            selected_countries.append(c)
    if "신흥국" in st.session_state.selected_custom:
        selected_emerging = emerging

# 조회 버튼
run_button = st.button("📥 데이터 조회 및 출력")

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

            omit_base = {'기준금리', '실업률'}
            sort_order = {
                '기준금리': 0, '실업률': 1, 'PCE': 2, 'CPI': 3, 'PPI': 4, '무역수지': 5, '수출': 6, '수입': 7,
                '소매판매': 8, '산업생산': 9, '설비투자': 10, '건설투자': 11, '부동산투자': 12, '실질임금': 13
            }
            country_order = {
                '한국': 0, '미국': 1, '중국': 2, '일본': 3, '유로존': 4,
                '베트남': 5, '폴란드': 6, '인도네시아': 7, '인도': 8
            }
            color_map = {
                '한국': '#f9f9f9', '미국': '#e6f0ff', '중국': '#ffe6e6',
                '일본': '#f3e6ff', '유로존': '#e6ffe6',
                '베트남': '#fff7e6', '폴란드': '#fff7e6', '인도네시아': '#fff7e6', '인도': '#fff7e6'
            }

            def format_value(val, 지표):
                try:
                    val = float(val)
                    return f"{val:,.2f}" if 지표 == '기준금리' else f"{val:,.1f}"
                except:
                    return ""

            def format_label(지표, 단위, 기준점):
                base = "" if 지표 in omit_base or 기준점 == '-' or pd.isna(기준점) else f", {기준점}"
                return f'<b>{지표}</b> <span style="font-weight:normal; font-size:8pt;">({단위}{base})</span>'

            value_map = defaultdict(dict)
            meta = {}
            for _, row in grouped.iterrows():
                if row['국가'] not in selected_countries and row['국가'] not in selected_emerging:
                    continue
                key = (row['국가'], row['지표'])
                meta[key] = (row['단위'], row['기준점'], row['빈도'])
                value_map[key][row['기준시점_text']] = format_value(row['값'], row['지표'])

            # ... (이후 테이블 출력 HTML 그대로 사용) ...
            # 필요하시면 이어서 테이블 출력 부분도 전체 제공드릴 수 있습니다

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
