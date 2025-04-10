# 전체 app.py 코드 시작

import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
import io
from datetime import datetime

# 인증
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

# 페이지 설정
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 버튼
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    run_button = st.button("📥 데이터 조회 및 출력")
with col2:
    download_slot = st.empty()
with col3:
    st.markdown(\"\"\"
    <div class="print-button" style="text-align:right;">
        <button onclick="window.print()" style="padding:6px 12px; font-size:10pt; cursor:pointer; border: 2px solid #333; font-weight:bold;">🖨️ 인쇄 또는 PDF 저장</button>
    </div>
    \"\"\", unsafe_allow_html=True)

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

            # 엑셀 다운로드
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

            # 이후 HTML 표 출력은 이 자리에 표 생성 코드를 삽입해 확장 가능
            st.success("✅ 데이터 로딩 완료 — 표 출력 준비됨.")

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")