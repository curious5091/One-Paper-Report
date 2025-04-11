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

# 인증 및 설정
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="One Page Economy Report - IBK ERI", layout="wide")

# APK 다운로드 링크 및 QR 코드 생성
apk_url = "https://github.com/curious5091/One-Paper-Report/releases/download/ver.1.0/IBK_ERI_OPER.apk"
buffer = BytesIO()
qrcode.make(apk_url).save(buffer, format="PNG")
qr_b64 = base64.b64encode(buffer.getvalue()).decode()

# 사용자 인터페이스 버튼 배치 및 QR 팝업
st.markdown(f"""
<style>
.button-container {{
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}}
.button-container a button,
.button-container button {{
    padding: 0.5rem 1.2rem;
    font-size: 14px;
    font-weight: bold;
    border: 2px solid #333;
    background-color: white;
    cursor: pointer;
}}
#qrModal {{
    display: none;
    position: fixed;
    z-index: 9999;
    left: 0; top: 0;
    width: 100%; height: 100%;
    background-color: rgba(0,0,0,0.6);
}}
#qrContent {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    background-color: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    text-align: center;
}}
#qrContent img {{
    width: 200px;
    height: auto;
}}
#closeBtn {{
    position: absolute;
    top: 10px; right: 14px;
    font-size: 18px;
    cursor: pointer;
    color: #333;
}}
</style>

<div class="button-container">
    <form action="" method="post">
        <button name="run" type="submit">📥 데이터 조회 및 출력</button>
    </form>
    <a href="{apk_url}" download>
        <button>📱 Android 앱 설치</button>
    </a>
    <button onclick="document.getElementById('qrModal').style.display='block'">📷 QR코드 보기</button>
</div>

<div id="qrModal">
  <div id="qrContent">
    <div id="closeBtn" onclick="document.getElementById('qrModal').style.display='none'">❌</div>
    <img src="data:image/png;base64,{qr_b64}" alt="QR 코드" />
    <p style="margin-top: 10px; font-size: 12px;">휴대폰 카메라로 스캔하여 설치하세요</p>
  </div>
</div>

<script>
document.addEventListener("click", function(event) {{
  const modal = document.getElementById('qrModal');
  if (event.target == modal) modal.style.display = "none";
}});
</script>
""", unsafe_allow_html=True)

run_button = st.session_state.get("run")

st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 One Page Economy Report - IBK ERI</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

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

            # value_map 구성 및 시각화 HTML 출력
            omit_base = {'기준금리'}
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

            from app_util_html import generate_full_html
            html = generate_full_html(value_map, meta, now, sort_order, country_order, color_map, emerging)
            components.html(html, height=1800, scrolling=True)

            value_map = defaultdict(dict)
            for _, row in grouped.iterrows():
                key = (row['국가'], row['지표'])
                value_map[key][row['기준시점_text']] = row['값']

            html = "<h3>데이터 시각화</h3>"
            html += "<table style='width:100%; border-collapse:collapse;'>"
            html += "<tr><th style='border:1px solid black;'>국가</th><th style='border:1px solid black;'>지표</th><th style='border:1px solid black;'>기준시점</th><th style='border:1px solid black;'>값</th></tr>"
            for key, val_dict in value_map.items():
                for 기준, 값 in val_dict.items():
                    html += f"<tr><td style='border:1px solid black;'>{key[0]}</td><td style='border:1px solid black;'>{key[1]}</td><td style='border:1px solid black;'>{기준}</td><td style='border:1px solid black;'>{값}</td></tr>"
            html += "</table>"
            components.html(html, height=600, scrolling=True)

        except Exception as e:
            st.error("❌ 오류가 발생했습니다.")
            st.exception(e)
else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
