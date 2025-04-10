import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
import io
from datetime import datetime

scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 2])
with col1:
    run_button = st.button("📥 데이터 조회 및 출력")
with col2:
    download_slot = st.empty()

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

            # 엑셀 다운로드 버튼
            output = io.BytesIO()
            today = datetime.today().strftime('%Y%m%d')
            excel_filename = f"One Page Economy Report_{today}.xlsx"
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                grouped.to_excel(writer, index=False, sheet_name='경제지표')
            download_slot.download_button(
                label="📥 엑셀 다운로드",
                data=output.getvalue(),
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # 인쇄 버튼도 조회 후에 표시
            st.markdown("""
            <div class="print-button" style="text-align:right; margin: 10px 0;">
              <button onclick="window.print()" style="padding:6px 12px; font-size:10pt; cursor:pointer; border: 2px solid #333; font-weight:bold;">🖨️ 인쇄 또는 PDF 저장</button>
            </div>
            """, unsafe_allow_html=True)

            # 표 생성 영역 (테스트용)
            html = '''
            <html><head><style>
            @page { size: A4 landscape; margin: 5mm; }
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
            '''

            html += '<h3 style="color:#000;">📌 표 예시 영역 (데이터 정상 조회됨)</h3>'
            html += '<table><tr><th>국가</th><th>지표</th><th>기준시점</th><th>값</th></tr>'
            for _, row in grouped.head(10).iterrows():
                html += f"<tr><td>{row['국가']}</td><td>{row['지표']}</td><td>{row['기준시점_text']}</td><td>{row['값']}</td></tr>"
            html += '</table></body></html>'

            # 결과 출력
            components.html(html, height=600, scrolling=True)

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
