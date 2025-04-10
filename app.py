
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from google.auth.transport.requests import AuthorizedSession
from google.auth import default
from collections import defaultdict
import datetime
from st_aggrid import AgGrid
import streamlit.components.v1 as components

st.set_page_config(page_title="국가별 경제지표 조회", layout="wide")

st.title("📊 국가별 경제지표 A4 출력 뷰어")

# 조회 버튼
if st.button("📥 데이터 조회 및 표 출력"):

    # 구글 인증
    creds, _ = default()
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet)
    df = df.dropna(how='all')
    df.columns = df.columns.str.strip()
    df = df[df['샘플구분'] == 'N']

    # 기준시점 가공
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

    # 최신값만 추출
    df_sorted = df.sort_values(['국가', '지표', '기준시점', '발표일'], ascending=[True, True, False, False])
    df_deduped = df_sorted.drop_duplicates(subset=['국가', '지표', '기준시점_text'], keep='first')
    def extract_recent(group):
        freq = group['빈도'].iloc[0]
        n = 8 if group['지표'].iloc[0] == 'GDP(분기)' else (4 if freq in ['연도', '분기'] else 6)
        return group.sort_values('기준시점', ascending=False).head(n)
    grouped = df_deduped.groupby(['국가', '지표'], group_keys=False).apply(extract_recent).reset_index(drop=True)

    # 여기서는 HTML 생성만 테스트용 간단히 출력
    html = "<h4>✅ 데이터 로딩 완료! (여기에는 A4 출력용 HTML 표가 들어갈 예정)</h4>"
    html += f"<p>총 {len(grouped)}개의 지표 항목이 준비되었습니다.</p>"

    components.html(html, height=200, scrolling=True)
else:
    st.info("좌측 상단 '📥 데이터 조회 및 표 출력' 버튼을 눌러주세요.")
