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
scope = ["https://www.googleapis.com/auth/sharedsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="One Page Economic Report - IBK ERI", layout="wide")

# 업로드하신 QR 코드 이미지의 Raw 링크 설정
QR_CODE_URL = "https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/QR_ibk_eri_bot.png"

# [메인 페이지] 화면 표시용 헤더
st.markdown(f"""
    <div style='display: flex; align-items: center; justify-content: flex-start; gap: 40px; margin-bottom: 25px; flex-wrap: wrap;'>
        <div style='display: flex; align-items: center; gap: 16px;'>
            <img src='https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/ibk_eri_oper.png' width='110'/>
            <h1 style='font-size:26pt; margin:0;'>One Page Economic Report - IBK ERI   (ver.2.1)</h1>
        </div>
        <div style='text-align: center; padding: 8px; border: 2px solid #007bff; border-radius: 8px; background-color: #f0f7ff; min-width: 140px;'>
            <img src='{QR_CODE_URL}' width='120' style='display: block; margin: 0 auto; border-radius: 4px;'/>
            <span style='font-size:9pt; color:#007bff; font-weight: bold; display: block; margin-top: 6px;'>모바일 실시간 봇</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>Made by curious@ibk.co.kr with ChatGPT / Version up with Gemini</div>", unsafe_allow_html=True)

if 'view_mode' not in st.session_state:
    st.session_state.view_mode = None

# 2. 데이터 로딩 및 전처리 함수
@st.cache_data(ttl=600)
def get_clean_data():
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet).dropna(how='all')
    df.columns = df.columns.str.strip()
    
    # 숫자형 데이터 변환 및 날짜 처리
    df['값'] = pd.to_numeric(df['값'], errors='coerce')
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
    
    # 중복 제거 및 유효 값 필터링
    df_clean = df.sort_values(['국가', '지표', '기준시점', '발표일'], ascending=[True, True, False, False])
    df_clean = df_clean.drop_duplicates(subset=['국가', '지표', '기준시점_text'], keep='first')
    df_clean = df_clean[df_clean['값'].notna()]
    
    # [추가] 일본의 경우 '단칸' 지표 제외 로직
    df_clean = df_clean[~((df_clean['국가'] == '일본') & (df_clean['지표'].str.contains('단칸', na=False)))]
    
    return df_clean

# 상단 버튼 (가로폭 조정 및 왼쪽 정렬)
col_btn1, col_btn2, col_spacer = st.columns([1, 1, 4])
with col_btn1:
    if st.button("📥 인쇄용 리포트 조회", use_container_width=True):
        st.session_state.view_mode = 'report'
with col_btn2:
    if st.button("📊 대시보드 시각화 조회", use_container_width=True):
        st.session_state.view_mode = 'dashboard'

# 3. 메인 로직 실행부
if st.session_state.view_mode:
    with st.spinner("⏳ 데이터를 처리 중입니다..."):
        try:
            df = get_clean_data()
            now = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")

            # 정렬 기준 정의
            country_order = ['한국', '미국', '중국', '일본', '유로존', '베트남', '인도', '인도네시아', '폴란드']
            indicator_order = [
                'GDP(연간)', 'GDP(분기)', '기준금리', '실업률', 'PCE', 'CPI', 'PPI', 
                '무역수지', '수출', '수입', '소매판매', '산업생산', '건설투자', '설비투자', '부동산투자', '실질임금'
            ]
            indicator_sort_dict = {ind: i for i, ind in enumerate(indicator_order)}

            # --- [MODE 1] 인쇄용 리포트 ---
            if st.session_state.view_mode == 'report':
                value_map = defaultdict(dict)
                meta = {}
                
                grouped_obj = df.groupby(['국가', '지표'])
                for (c_name, i_name), group in grouped_obj:
                    freq = group['빈도'].iloc[0]
                    n = 8 if i_name == 'GDP(분기)' else (4 if freq in ['연도', '분기'] else 12)
                    recent_data = group.sort_values('기준시점', ascending=False).head(n)
                    
                    key = (c_name, i_name)
                    meta[key] = (recent_data.iloc[0]['단위'], recent_data.iloc[0]['기준점'], freq)
                    for _, row in recent_data.iterrows():
                        val = row['값']
                        f_val = f"{float(val):,.2f}" if i_name == '기준금리' else f"{float(val):,.1f}"
                        value_map[key][row['기준시점_text']] = f_val

                omit_base = {'기준금리'}
                all_found_countries = df['국가'].unique()
                display_order = [c for c in country_order if c in all_found_countries] + [c for c in sorted(all_found_countries) if c not in country_order]
                
                color_map = {
                    '한국': '#f9f9f9', '미국': '#e6f0ff', '중국': '#ffe6e6', 
                    '일본': '#f3e6ff', '유로존': '#e6ffe6', 
                    '베트남': '#fff7e6', '인도': '#fff7e6', '인도네시아': '#fff7e6', '폴란드': '#fff7e6'
                }

                html = f'''
                <html><head><style>
                @page {{ size: A4 portrait; margin: 12mm 6mm 6mm 6mm; }}
                body {{ font-family: "Malgun Gothic"; font-size: 10pt; color: #000; -webkit-print-color-adjust: exact; }}
                
                /* [수정] 테이블 하단 여백 축소 (12px -> 6px) */
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 6px; page-break-inside: avoid; }}
                th, td {{ border: 1px solid black; padding: 2px; font-size: 8pt; text-align: center; color: #000; }}
                
                /* [수정] h3 타이틀의 상하 마진 축소 (위 아래 유격을 타이트하게 고정) */
                h3 {{ margin: 2px 0 6px 0; font-size: 15pt; font-weight: bold; border-left: 6px solid #222; padding-left: 12px; }}
                
                .print-button-container {{ text-align: left; margin-bottom: 25px; }}
                .print-button {{ padding: 8px 16px; font-weight: bold; cursor: pointer; border: 2px solid #333; background: #fff; border-radius: 4px; }}
                @media print {{ .print-button-container {{ display: none !important; }} }}
                </style></head><body>
                
                <div class="print-button-container">
                    <button class="print-button" onclick="window.print()">🖨️ 인쇄 또는 PDF 저장</button>
                </div>
                
                <!-- 인쇄용 고해상도 헤더 영역 -->
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 35px;">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <img src="https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/ibk_eri_oper.png" style="height:45px;" />
                        <div>
                            <div style="font-size:20pt; font-weight: bold; color:#000; letter-spacing: -0.5px;">One Page Economic Report - IBK ERI</div>
                            <div style="font-size:9pt; color:#444; margin-top: 4px;">기준일시: {now}</div>
                        </div>
                    </div>
                    <div style="text-align: center; min-width: 80px;">
                        <img src="{QR_CODE_URL}" style="height: 70px; width: 70px; display: block; margin: 0 auto; border: 1px solid #ccc; padding: 2px; background: #fff;" />
                        <span style="font-size: 7.5pt; color: #000; display: block; margin-top: 3px; font-weight: bold;">모바일 봇</span>
                    </div>
                </div>
                '''
                
                triggered_page_2 = False
                triggered_page_3 = False
                countries_printed = 0

                for country in display_order:
                    bg_color = color_map.get(country, '#ffffff')
                    country_keys = [k for k in value_map if k[0] == country]
                    if not country_keys: continue

                    if country in ['중국', '일본', '유로존']:
                        if not triggered_page_2 and countries_printed > 0:
                            html += '<div style="page-break-before: always;"></div>'
                            triggered_page_2 = True
                    
                    elif country not in ['한국', '미국', '중국', '일본', '유로존']:
                        if not triggered_page_3 and countries_printed > 0:
                            html += '<div style="page-break-before: always;"></div>'
                            triggered_page_3 = True

                    countries_printed += 1

                    # [수정] 박스 자체의 상하 패딩(12px -> 6px) 및 하단 외부 여백(30px -> 20px) 축소로 슬림화 조치
                    html += f'<div style="background-color:{bg_color}; padding: 6px 12px; margin-bottom:20px; border:1px solid #ddd; page-break-inside: avoid;">'
                    html += f'<h3>{country}</h3>'
                    
                    key_y, key_q = (country, 'GDP(연간)'), (country, 'GDP(분기)')
                    show_y = key_y in country_keys
                    show_q = key_q in country_keys
                    
                    if show_y or show_q:
                        p_y = sorted(value_map[key_y].keys(), reverse=True)[:4][::-1] if show_y else []
                        p_q = sorted(value_map[key_q].keys(), reverse=True)[:8][::-1] if show_q else []
                        html += '<table><tr>'
                        if p_y: html += f'<th colspan="{len(p_y)}"><b>GDP(연간)</b> ({meta[key_y][0]})</th>'
                        if p_q: html += f'<th colspan="{len(p_q)}"><b>GDP(분기)</b> ({meta[key_q][0]})</th>'
                        html += '</tr><tr>' + ''.join(f'<th style="white-space: nowrap;">{p}</th>' for p in p_y + p_q) + '</tr><tr>'
                        html += ''.join(f'<td>{value_map[key_y].get(p, "")}</td>' for p in p_y)
                        html += ''.join(f'<td>{value_map[key_q].get(p, "")}</td>' for p in p_q)
                        html += '</tr></table>'

                    other_keys = [k for k in country_keys if k[1] not in ['GDP(연간)', 'GDP(분기)']]
                    if other_keys:
                        all_p = sorted({p for k in other_keys for p in value_map[k]}, reverse=True)[:12][::-1]
                        html += '<table><tr><th style="width:110px;">지표명</th>' + ''.join(f'<th style="white-space: nowrap;">{p}</th>' for p in all_p) + '</tr>'
                        for k in sorted(other_keys, key=lambda x: indicator_sort_dict.get(x[1], 99)):
                            unit, base, _ = meta[k]
                            b_text = f", {base}" if k[1] not in omit_base and not pd.isna(base) and base != '-' else ""
                            html += f'<tr><td style="text-align:left; padding-left:5px;"><b>{k[1]}</b> <span style="font-size:7pt;">({unit}{b_text})</span></td>'
                            html += ''.join(f'<td>{value_map[k].get(p, "")}</td>' for p in all_p)
                            html += '</tr>'
                        html += '</table>'
                    html += '</div>'
                
                html += '</body></html>'
                components.html(html, height=1200, scrolling=True, width=1700)

            # --- [MODE 2] 대시보드 시각화 ---
            elif st.session_state.view_mode == 'dashboard':
                st.subheader("📊 경제 지표 시각화 대시보드")
                
                all_found_countries = df['국가'].unique()
                sorted_countries = [c for c in country_order if c in all_found_countries] + [c for c in sorted(all_found_countries) if c not in country_order]
                target_country = st.selectbox("조회할 국가를 선택하세요", sorted_countries)
                
                c_df = df[df['국가'] == target_country].copy()
                present_inds = c_df['지표'].unique()
                sorted_indicators = [i for i in indicator_order if i in present_inds] + [i for i in sorted(present_inds) if i not in indicator_order]
                
                default_selection = [i for i in ['GDP(연간)', 'GDP(분기)', '기준금리', 'CPI'] if i in sorted_indicators]
                selected_inds = st.multiselect("확인할 지표를 선택하세요", sorted_indicators, default=default_selection)
                
                if selected_inds:
                    cols = st.columns(2)
                    for i, ind in enumerate(selected_inds):
                        with cols[i % 2]:
                            ind_df = c_df[c_df['지표'] == ind].sort_values('기준시점').tail(12)
                            if not ind_df.empty:
                                st.write(f"**{ind} ({target_country})**")
                                st.vega_lite_chart(ind_df, {
                                    'mark': {'type': 'line', 'point': True, 'tooltip': True},
                                    'encoding': {
                                        'x': {'field': '기준시점_text', 'type': 'nominal', 'title': '기준시점', 'sort': None},
                                        'y': {
                                            'field': '값', 
                                            'type': 'quantitative', 
                                            'title': '수치',
                                            'axis': {'format': '.1f'},
                                            'scale': {'zero': False, 'padding': 20}
                                        },
                                        'color': {'value': '#007bff'}
                                    },
                                    'width': 'container',
                                    'height': 300
                                })
                else:
                    st.warning("표시할 지표 데이터가 없습니다.")

        except Exception as e:
            st.error("데이터 처리 중 오류 발생")
            st.exception(e)
else:
    st.info("👆 버튼을 눌러 조회 방식을 선택하세요.")
