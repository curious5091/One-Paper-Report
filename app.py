import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from google.auth import default
from collections import defaultdict
import streamlit.components.v1 as components

st.set_page_config(page_title="국가별 경제지표 조회", layout="wide")
st.title("📊 국가별 경제지표 A4 표 출력 뷰어")

if st.button("📥 데이터 조회 및 표 출력"):

    creds, _ = default()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet)
    df = df.dropna(how='all')
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

    html = """<html>
<head>
  <style>
    body { font-family: 'Malgun Gothic'; font-size: 10pt; color: #000; }
    h3 { color: #000; }
  </style>
</head>
<body>
  <h3>✅ 데이터가 성공적으로 로딩되었습니다!</h3>
  <p>이곳에 향후 A4 표 형태 HTML 출력이 삽입될 예정입니다.</p>
</body>
</html>"""

    components.html(html, height=400, scrolling=True)

else:
    st.info("좌측 상단 '📥 데이터 조회 및 표 출력' 버튼을 눌러주세요.")