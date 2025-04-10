import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# Google Sheets 인증
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 데이터가 이미 로딩된 상태인지 확인
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False

run_button = st.button("📥 데이터 조회 및 출력")

# 데이터가 로드되지 않은 경우에만 로딩
if run_button or st.session_state.data_loaded:
    with st.spinner("⏳ 데이터 로딩 중입니다. 잠시만 기다려주세요..."):
        try:
            # 데이터를 처음 불러오는 부분
            if not st.session_state.data_loaded:
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
                emerging = {'베트남', '폴란드', '인도네시아', '인도'}
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
                    key = (row['국가'], row['지표'])
                    meta[key] = (row['단위'], row['기준점'], row['빈도'])
                    value_map[key][row['기준시점_text']] = format_value(row['값'], row['지표'])

                # 데이터가 로딩되었음을 표시
                st.session_state.data_loaded = True

            # ✅ 다중 드롭박스 (국가 카테고리 선택)
            category_selection = st.multiselect("국가 카테고리를 선택하세요", 
                                               ["한국", "미국", "중국", "일본", "유로존", "신흥국"], 
                                               default=["한국", "미국", "중국", "일본", "유로존", "신흥국"])

            # 신흥국을 선택하면 신흥국 관련 데이터만 출력
            countries_to_display = []
            if "신흥국" in category_selection:
                countries_to_display += ['베트남', '폴란드', '인도네시아', '인도']
            
            # 선택된 국가들에 대해 출력
            for country in category_selection:
                if country != "신흥국":
                    countries_to_display.append(country)

            html = '''
            <html><head><style>
            @page { size: A4; margin: 5mm; }
            body {
              font-family: 'Malgun Gothic';
              font-size: 10pt;
              color: #000;
              -webkit-print-color-adjust: exact;
            }
            table {
              border-collapse: collapse;
              width: 100%;
              margin-bottom: 10px;
              page-break-inside: avoid;
            }
            th, td {
              border: 1px solid black;
              padding: 4px;
              font-size: 9pt;
              text-align: center;
              color: #000;
            }
            th:first-child, td:first-child { border-left: none; }
            th:last-child, td:last-child { border-right: none; }
            tr:first-child th { border-top: 2px solid black; border-bottom: 2px solid black; }
            @media print {
              .print-button { display: none !important; }
            }
            </style></head><body>

            <div class="print-button" style="text-align:right; margin: 10px 0;">
              <button onclick="window.print()" style="padding:6px 12px; font-size:10pt; cursor:pointer; border: 2px solid #333; font-weight:bold;">🖨️ 인쇄 또는 PDF 저장</button>
              <p style="font-size:8pt; color:#555; text-align:right; margin-top:6px;">
                👉 이 버튼을 누르면 출력창이 열리며, PDF로 저장하거나 프린터로 바로 인쇄할 수 있습니다.
              </p>
            </div>
            '''

            # 선택된 카테고리(주요국 또는 신흥국)에 해당하는 국가 데이터만 출력
            for country in countries_to_display:
                bg_color = color_map.get(country, '#ffffff') if country != "신흥국" else "#f3f3f3"  # 신흥국은 색상 적용 X
                html += f'<div style="background-color:{bg_color}; padding:6px; margin-bottom:15px;">'
                html += f'<h3 style="color:#000;">{country}</h3>'

                key_y, key_q = (country, 'GDP(연간)'), (country, 'GDP(분기)')
                if key_y in value_map or key_q in value_map:
                    periods_y = sorted(value_map[key_y].keys(), reverse=True)[:4][::-1]
                    periods_q = sorted(value_map[key_q].keys(), reverse=True)[:8][::-1]
                    label_y = format_label('GDP(연간)', *meta.get(key_y, ('%', '', ''))[:2])
                    label_q = format_label('GDP(분기)', *meta.get(key_q, ('%', '', ''))[:2])
                    html += '<table><tr>'
                    html += f'<th colspan="{len(periods_y)}">{label_y}</th>'
                    html += f'<th colspan="{len(periods_q)}">{label_q}</th></tr>'
                    html += '<tr>' + ''.join(f'<th>{p}</th>' for p in periods_y + periods_q) + '</tr>'
                    html += '<tr style="border-bottom:2px solid black;">'
                    html += ''.join(f'<td>{value_map[key_y].get(p, "")}</td>' for p in periods_y)
                    html += ''.join(f'<td>{value_map[key_q].get(p, "")}</td>' for p in periods_q)
                    html += '</tr></table>'

                keys6 = [k for k in value_map if k[0] == country and k[1] not in ['GDP(연간)', 'GDP(분기)'] and len(value_map[k]) == 6]
                if keys6:
                    all_periods = sorted({p for k in keys6 for p in value_map[k]}, reverse=True)[:6][::-1]
                    html += '<table><tr><th class="label">지표명</th>' + ''.join(f'<th>{p}</th>' for p in all_periods) + '</tr>'
                    for i, k in enumerate(sorted(keys6, key=lambda x: sort_order.get(x[1], 99))):
                        unit, base, _ = meta[k]
                        row_style = ' style="border-bottom:2px solid black;"' if i == len(keys6)-1 else ''
                        html += f'<tr{row_style}><td class="label">{format_label(k[1], unit, base)}</td>'
                        for p in all_periods:
                            html += f'<td>{value_map[k].get(p, "")}</td>'
                        html += '</tr>'
                    html += '</table>'
                html += '</div>'

            html += '</body></html>'
            components.html(html, height=1800, scrolling=True)

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)
else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
