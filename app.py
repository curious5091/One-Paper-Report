import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
from datetime import datetime
from pytz import timezone

# 1. 인증 및 설정
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="One Page Economic Report - IBK ERI", layout="wide")

st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <img src='https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/ibk_eri_oper.png' width='100'/>
        <h1 style='font-size:24pt; margin:0;'>One Page Economic Report - IBK ERI</h1>
    </div>
""", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = None

# 2. 데이터 로딩 및 전처리 함수 (리포트와 대시보드 로직 통합)
@st.cache_data(ttl=600)
def get_clean_data():
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet).dropna(how='all')
    df.columns = df.columns.str.strip()
    
    # 날짜 변환
    df['기준시점'] = pd.to_datetime(df['기준시점'], format='%Y-%m', errors='coerce')
    df['발표일'] = pd.to_datetime(df['발표일'], errors='coerce')

    # 기준시점 텍스트 변환 함수
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

    # 핵심 로직: 동일 [국가, 지표, 기준시점] 내에서 가장 최근 [발표일] 데이터만 남기기
    df_clean = df.sort_values(['국가', '지표', '기준시점', '발표일'], ascending=[True, True, False, False])
    df_clean = df_clean.drop_duplicates(subset=['국가', '지표', '기준시점_text'], keep='first')
    
    return df_clean

# 상단 버튼
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📥 인쇄용 리포트 조회", use_container_width=True):
        st.session_state.view_mode = 'report'
with col_btn2:
    if st.button("📊 대시보드 시각화 조회", use_container_width=True):
        st.session_state.view_mode = 'dashboard'

if st.session_state.view_mode:
    with st.spinner("⏳ 데이터를 정제 중입니다..."):
        try:
            df = get_clean_data()
            now = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")

            # --- [MODE 1] 인쇄용 리포트 ---
            if st.session_state.view_mode == 'report':
                # 정제된 df에서 최근 n개 추출
                def extract_recent(group):
                    freq = group['빈도'].iloc[0]
                    if group.name[1] == 'GDP(분기)': n = 8
                    elif freq in ['연도', '분기']: n = 4
                    else: n = 12 
                    return group.sort_values('기준시점', ascending=False).head(n)

                grouped = df.groupby(['국가', '지표'], group_keys=False).apply(extract_recent).reset_index(drop=True)

                # (이하 기존 HTML 생성 로직과 동일)
                omit_base = {'기준금리'}
                sort_order = {'기준금리': 0, '실업률': 1, 'PCE': 2, 'CPI': 3, 'PPI': 4, '무역수지': 5, '수출': 6, '수입': 7, '소매판매': 8, '산업생산': 9}
                color_map = {'한국': '#f9f9f9', '미국': '#e6f0ff', '중국': '#ffe6e6', '일본': '#f3e6ff', '유로존': '#e6ffe6'}

                value_map = defaultdict(dict)
                meta = {}
                for _, row in grouped.iterrows():
                    key = (row['국가'], row['지표'])
                    meta[key] = (row['단위'], row['기준점'], row['빈도'])
                    val = row['값']
                    try:
                        f_val = f"{float(val):,.2f}" if row['지표'] == '기준금리' else f"{float(val):,.1f}"
                    except: f_val = ""
                    value_map[key][row['기준시점_text']] = f_val

                html = f'<html><head><style>@page {{ size: A4 portrait; margin: 5mm; }} body {{ font-family: "Malgun Gothic"; font-size: 10pt; }} table {{ border-collapse: collapse; width: 100%; margin-bottom: 8px; }} th, td {{ border: 1px solid black; padding: 2px; font-size: 8pt; text-align: center; }}</style></head><body><div style="text-align:center; font-size:13pt; font-weight: bold;">One Page Economic Report</div><div style="text-align:center; font-size:8.5pt; margin-bottom:10px;">기준일시: {now}</div>'
                
                for country in ['한국', '미국', '중국', '일본', '유로존']:
                    bg_color = color_map.get(country, '#ffffff')
                    html += f'<div style="background-color:{bg_color}; padding:6px; margin-bottom:10px;"><h3>{country}</h3>'
                    keys = [k for k in value_map if k[0] == country and k[1] not in ['GDP(연간)', 'GDP(분기)']]
                    if keys:
                        all_p = sorted({p for k in keys for p in value_map[k]}, reverse=True)[:12][::-1]
                        html += '<table><tr><th>지표명</th>' + ''.join(f'<th>{p}</th>' for p in all_p) + '</tr>'
                        for k in sorted(keys, key=lambda x: sort_order.get(x[1], 99)):
                            unit, base, _ = meta[k]
                            html += f'<tr><td><b>{k[1]}</b> ({unit})</td>' + ''.join(f'<td>{value_map[k].get(p, "")}</td>' for p in all_p) + '</tr>'
                        html += '</table>'
                    html += '</div>'
                html += '</body></html>'
                components.html(html, height=1000, scrolling=True, width=1700)

            # --- [MODE 2] 대시보드 시각화 ---
            elif st.session_state.view_mode == 'dashboard':
                st.subheader("📊 경제 지표 시각화 대시보드")
                # 이미 중복이 제거된 df를 사용하므로 안심하고 차트를 그립니다.
                target_country = st.selectbox("조회할 국가를 선택하세요", df['국가'].unique())
                c_df = df[df['국가'] == target_country].copy()
                
                all_inds = sorted(c_df['지표'].unique())
                selected_inds = st.multiselect("확인할 지표를 선택하세요", all_inds, default=[i for i in ['CPI', '산업생산', '기준금리'] if i in all_inds])
                
                if selected_inds:
                    cols = st.columns(2)
                    for i, ind in enumerate(selected_inds):
                        with cols[i % 2]:
                            # 기준시점순으로 정렬하여 차트 왜곡 방지
                            ind_df = c_df[c_df['지표'] == ind].sort_values('기준시점').tail(12)
                            if not ind_df.empty:
                                st.write(f"**{ind} ({target_country})**")
                                st.line_chart(data=ind_df, x='기준시점_text', y='값')
                else:
                    st.warning("지표를 선택해주세요.")

        except Exception as e:
            st.error("오류가 발생했습니다.")
            st.exception(e)
else:
    st.info("👆 버튼을 눌러 조회 방식을 선택하세요.")
