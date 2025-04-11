import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components
from datetime import datetime
from pytz import timezone
import base64
import qrcode
from io import BytesIO

# APK 다운로드 링크 및 QR 코드 생성
apk_url = "https://github.com/curious5091/One-Paper-Report/releases/download/ver.1.0/IBK_ERI_OPER.apk"
buffer = BytesIO()
qrcode.make(apk_url).save(buffer, format="PNG")
qr_b64 = base64.b64encode(buffer.getvalue()).decode()

# 인증 및 설정
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="One Page Economy Report - IBK ERI", layout="wide")

# 상단 제목
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 One Page Economy Report - IBK ERI</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 버튼 영역
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    run_button = st.button("📥 데이터 조회 및 출력")
with col2:
    st.markdown(f'<a href="{apk_url}" download><button style="width:100%; padding:0.5rem 1.2rem; font-size:14px;">📱 Android 앱 설치</button></a>', unsafe_allow_html=True)
with col3:
    st.markdown('<button onclick="document.getElementById(\'qrModal\').style.display=\'block\'" style="width:100%; padding:0.5rem 1.2rem; font-size:14px;">📷 QR코드 보기</button>', unsafe_allow_html=True)

# QR 모달 HTML
st.markdown(f"""
<div id="qrModal" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; background-color:rgba(0,0,0,0.6);">
  <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); background-color:white; padding:20px; border-radius:12px; text-align:center;">
    <div onclick="document.getElementById('qrModal').style.display='none'" style="position:absolute; top:10px; right:14px; font-size:18px; cursor:pointer;">❌</div>
    <img src="data:image/png;base64,{qr_b64}" style="width:200px; height:auto;" />
    <p style="margin-top: 10px; font-size: 12px;">QR코드를 스캔하여 앱을 설치하세요</p>
  </div>
</div>
<script>
window.addEventListener("click", function(event) {{
  var modal = document.getElementById("qrModal");
  if (event.target === modal) {{
    modal.style.display = "none";
  }}
}});
</script>
""", unsafe_allow_html=True)

if run_button:
    with st.spinner("⏳ 데이터 로딩 중입니다. 잠시만 기다려주세요..."):
        try:
            now = datetime.now(timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M")
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

            st.dataframe(grouped)

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)
else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
