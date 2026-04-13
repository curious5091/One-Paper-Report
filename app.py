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

# 헤더 부분
st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 20px;'>
        <img src='https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/ibk_eri_oper.png' width='100'/>
        <h1 style='font-size:24pt; margin:0;'>One Page Economic Report - IBK ERI</h1>
    </div>
""", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 2. 세션 상태 초기화 (화면 전환 관리)
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = None

# 3. 상단 버튼 배치
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("📥 인쇄용 리포트 조회", use_container_width=True):
        st.session_state.view_mode = 'report'
with col_btn2:
    if st.button("📊 대시보드 시각화 조회", use_container_width=True):
        st.session_state.view_mode = 'dashboard'

# 4. 데이터 로딩 및 전처리 함수 (공통 사용)
@st.cache_data(ttl=600)  # 10분간 캐시 유지
def load_and_process_data():
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet).dropna(how='all')
    df.columns = df.columns.str.strip()
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
    return df

# 실행 로직
if st.session_state.view_mode:
    with st.spinner("⏳ 데이터를 불러오는 중입니다..."):
        try:
            df = load_and_process_data()
            now = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")

            # --- [MODE 1] 인쇄용 리포트 (기존 HTML 방식) ---
            if st.session_state.view_mode == 'report':
                df_sorted = df.sort_values(['국가', '지표', '기준시점', '발표일'], ascending=[True, True, False, False])
                df_deduped = df_sorted.drop_duplicates(subset=['국가', '지표', '기준시점_text'], keep='first')

                def extract_recent(group):
                    freq = group['빈도'].iloc[0]
                    # 월간 자료 12개월 출력을 위해 n 설정 수정
                    if group.name[1] == 'GDP(분기)': n = 8
                    elif freq in ['연도', '분기']: n = 4
                    else: n = 12 
                    res = group.sort_values('기준시점', ascending=False).head(n).copy()
                    res['국가'] = group.name[0]
                    res['지표'] = group.name[1]
                    return res

                grouped = df_deduped.groupby(['국가', '지표'], group_keys=False).apply(extract_recent).reset_index(drop=True)

                # HTML 생성을 위한 설정값들
                omit_base = {'기준금리'}
                sort_order = {'기준금리': 0, '실업률': 1, 'PCE': 2, 'CPI': 3, 'PPI': 4, '무역수지': 5, '수출': 6, '수입': 7, '소매판매': 8, '산업생산': 9}
                country_order = {'한국': 0, '미국': 1, '중국': 2, '일본': 3, '유로존': 4}
                emerging = {'베트남', '폴란드', '인도네시아', '인도'}
                color_map = {'한국': '#f9f9f9', '미국': '#e6f0ff', '중국': '#ffe6e6', '일본': '#f3e6ff', '유로존': '#e6ffe6', '베트남': '#fff7e6'}

                def format_value(val, 지표):
                    try:
                        val = float(val)
                        return f"{val:,.2f}" if 지표 == '기준금리' else f"{val:,.1f}"
                    except: return ""

                def format_label(지표, 단위, 기준점):
                    base = "" if 지표 in omit_base or 기준점 == '-' or pd.isna(기준점) else f", {기준점}"
                    return f'<b>{지표}</b> <span style="font-weight:normal; font-size:8pt;">({단위}{base})</span>'

                value_map = defaultdict(dict)
                meta = {}
                for _, row in grouped.iterrows():
                    key = (row['국가'], row['지표'])
                    meta[key] = (row['단위'], row['기준점'], row['빈도'])
                    value_map[key][row['기준시점_text']] = format_value(row['값'], row['지표'])

                # HTML 코드 생성 (기존 로직 유지, all_periods 슬라이싱 12로 반영)
                html = f'''
                <html><head><style>
                @page {{ size: A4 portrait; margin: 5mm; }}
                body {{ font-family: 'Malgun Gothic'; font-size: 10pt; color: #000; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 8px; page-break-inside: avoid; }}
                th, td {{ border: 1px solid black; padding: 2px; font-size: 8pt; text-align: center; }}
                .page-break {{ page-break-before: always; }}
                </style></head><body>
                <div style="text-align:center; font-size:13pt; font-weight: bold;">One Page Economic Report</div>
                <div style="text-align:center; font-size:8.5pt; margin-bottom:10px;">기준일시: {now}</div>
                '''
                
                # 주요국 출력 루프 (예시로 한국/미국/중국만 포함, 필요시 기존 코드 루프 전체 복사)
                for country in ['한국', '미국', '중국']:
                    bg_color = color_map.get(country, '#ffffff')
                    html += f'<div style="background-color:{bg_color}; padding:6px; margin-bottom:10px; border:1px solid #ccc;">'
                    html += f'<h3>{country}</h3>'
                    keys6 = [k for k in value_map if k[0] == country and k[1] not in ['GDP(연간)', 'GDP(분기)']]
                    if keys6:
                        # 12개월치 출력 반영
                        all_periods = sorted({p for k in keys6 for p in value_map[k]}, reverse=True)[:12][::-1]
                        html += '<table><tr><th>지표명</th>' + ''.join(f'<th>{p}</th>' for p in all_periods) + '</tr>'
                        for k in sorted(keys6, key=lambda x: sort_order.get(x[1], 99)):
                            unit, base, _ = meta[k]
                            html += f'<tr><td>{format_label(k[1], unit, base)}</td>'
                            for p in all_periods:
                                html += f'<td>{value_map[k].get(p, "")}</td>'
                            html += '</tr>'
                        html += '</table>'
                    html += '</div>'
                
                html += '</body></html>'
                components.html(html, height=1000, scrolling=True, width=1700)

            # --- [MODE 2] 대시보드 시각화 (신규 차트 방식) ---
            elif st.session_state.view_mode == 'dashboard':
                st.subheader("📊 경제 지표 시각화 대시보드")
                
                # 국가 선택
                target_country = st.selectbox("조회할 국가를 선택하세요", df['국가'].unique())
                
                # 데이터 필터링
                c_df = df[df['국가'] == target_country].copy()
                
                # 주요 지표 멀티 셀렉트
                all_inds = c_df['지표'].unique()
                selected_inds = st.multiselect("확인할 지표를 선택하세요", all_inds, default=[i for i in ['CPI', '산업생산', '기준금리', '실업률'] if i in all_inds])
                
                if selected_inds:
                    # 차트 레이아웃 (2열 구성)
                    cols = st.columns(2)
                    for i, ind in enumerate(selected_inds):
                        with cols[i % 2]:
                            ind_df = c_df[c_df['지표'] == ind].sort_values('기준시점').tail(12)
                            if not ind_df.empty:
                                st.write(f"**{ind} ({target_country}) - 최근 12개 시점**")
                                # 차트 그리기
                                st.line_chart(data=ind_df, x='기준시점_text', y='값')
                else:
                    st.warning("지표를 하나 이상 선택해주세요.")

        except Exception as e:
            st.error("데이터 처리 중 오류가 발생했습니다.")
            st.exception(e)
else:
    st.info("👆 상단 버튼을 눌러 **인쇄용 리포트** 또는 **대시보드**를 조회해 보세요.")
