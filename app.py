import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

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

            html = '''
            <html><head><style>
            @page { size: A4 portrait; margin: 5mm; }
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

            # [중략] 주요국 출력 생략 (그대로 유지됨)

            # ✅ 신흥국 GDP 표 - 1행 1열은 '국가', 2행 1열은 공란, 3~6행 1열에는 각 국가명
            html += f'<div style="background-color:{color_map["베트남"]}; padding:6px; margin-bottom:15px;"><h3>신흥국</h3>'

            gdp_annual = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(연간)'}
            gdp_quarter = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(분기)'}
            annual_periods = sorted({p for v in gdp_annual.values() for p in v}, reverse=True)[:4][::-1]
            quarter_periods = sorted({p for v in gdp_quarter.values() for p in v}, reverse=True)[:8][::-1]

            html += '<table>'
            html += f'<tr><th rowspan="2">국가</th>'
            html += f'<th colspan="{len(annual_periods)}">{format_label("GDP(연간)", "%", "전동비")}</th>'
            html += f'<th colspan="{len(quarter_periods)}">{format_label("GDP(분기)", "%", "전동비")}</th></tr>'
            html += '<tr>' + ''.join(f'<th>{p}</th>' for p in annual_periods + quarter_periods) + '</tr>'

            for i, country in enumerate(sorted(emerging, key=lambda x: country_order.get(x, 99))):
                html += f'<tr{" style=\"border-bottom:2px solid black;\"" if i == len(emerging)-1 else ""}>'
                html += f'<td>{country}</td>'
                html += ''.join(f'<td>{gdp_annual.get((country, "GDP(연간)"), {}).get(p, "")}</td>' for p in annual_periods)
                html += ''.join(f'<td>{gdp_quarter.get((country, "GDP(분기)"), {}).get(p, "")}</td>' for p in quarter_periods)
                html += '</tr>'
            html += '</table>'

            # [중략] 신흥국 기타 지표 표 출력 로직도 기존과 동일하게 이어짐...

            html += '</body></html>'
            components.html(html, height=1700, scrolling=True)

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
