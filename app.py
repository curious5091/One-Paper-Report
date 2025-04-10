import streamlit as st
import streamlit.components.v1 as components
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
from collections import defaultdict

# --- 기본 설정 ---
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# --- 국가 목록 정의 ---
main_countries = ["한국", "미국", "중국", "일본", "유로존", "신흥국"]
emerging = ["베트남", "폴란드", "인도네시아", "인도"]
all_countries = ["한국", "미국", "중국", "일본", "유로존"] + emerging

# --- 커스텀 국가 선택 UI ---
selected = components.html(f"""
<div id=\"selector\">
  <div style=\"margin-bottom:10px;\"><b>국가 선택</b></div>
  <button class=\"toggle\" data-name=\"전체 보기\">전체 보기</button>
  {"".join(f'<button class="toggle" data-name="{c}">{c}</button>' for c in main_countries)}
</div>

<script>
  const buttons = document.querySelectorAll(".toggle");
  let selected = [];

  function updateStreamlit() {{
    const message = selected.includes("전체 보기") 
      ? {all_countries}
      : selected.includes("신흥국") 
        ? selected.filter(x => x !== "전체 보기").concat({emerging}) 
        : selected;
    Streamlit.setComponentValue([...new Set(message)]);
  }}

  buttons.forEach(btn => {{
    btn.onclick = () => {{
      const name = btn.dataset.name;
      if (name === "전체 보기") {{
        selected = ["전체 보기"];
        buttons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
      }} else {{
        const idx = selected.indexOf(name);
        if (idx > -1) {{
          selected.splice(idx, 1);
          btn.classList.remove("active");
        }} else {{
          selected = selected.filter(x => x !== "전체 보기");
          selected.push(name);
          btn.classList.add("active");
        }}
        buttons.forEach(b => {{
          if (b.dataset.name === "전체 보기") b.classList.remove("active");
        }});
      }}
      updateStreamlit();
    }};
  }});

  // 기본 전체 보기 선택
  document.querySelector('button[data-name="전체 보기"]').click();
</script>

<style>
  #selector button {{
    margin: 4px 6px 12px 0;
    padding: 6px 16px;
    font-size: 10pt;
    font-weight: bold;
    border: 2px solid #333;
    border-radius: 6px;
    background-color: #fff;
    color: #000;
    cursor: pointer;
  }}
  #selector button.active {{
    background-color: #2c80ff;
    color: #fff;
  }}
</style>
""", height=180, key="country_selector", default=[])

# --- 조회 버튼 ---
run_button = st.button("데이터 조회 및 출력")

if run_button:
    if not selected:
        st.warning("1개 이상의 국가를 선택해주세요.")
        st.stop()

    # --- 인증 및 데이터 로딩 ---
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
    worksheet = sheet.worksheet("Database")
    df = get_as_dataframe(worksheet).dropna(how='all')
    df.columns = df.columns.str.strip()
    df = df[df['샘플구분'] == 'N']
    df['기준시점'] = pd.to_datetime(df['기준시점'], format='%Y-%m', errors='coerce')
    df['발표일'] = pd.to_datetime(df['발표일'], errors='coerce')

    # --- 기준시점 텍스트 생성 ---
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

    # --- 최신 데이터 추출 ---
    def extract_recent(group):
        freq = group['빈도'].iloc[0]
        n = 8 if group['지표'].iloc[0] == 'GDP(분기)' else (4 if freq in ['연도', '분기'] else 6)
        return group.sort_values('기준시점', ascending=False).head(n)

    grouped = df_deduped.groupby(['국가', '지표'], group_keys=False).apply(extract_recent).reset_index(drop=True)

    # --- 지표 처리 ---
    omit_base = {'기준금리', '실업률'}
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
        if row['국가'] not in selected:
            continue
        key = (row['국가'], row['지표'])
        meta[key] = (row['단위'], row['기준점'], row['빈도'])
        value_map[key][row['기준시점_text']] = format_value(row['값'], row['지표'])

    # --- 표 생성 (샘플 형식) ---
    html = '''
    <html><head><style>
    @page { size: A4; margin: 5mm; }
    body { font-family: 'Malgun Gothic'; font-size: 10pt; color: #000; -webkit-print-color-adjust: exact; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 10px; page-break-inside: avoid; }
    th, td { border: 1px solid black; padding: 4px; font-size: 9pt; text-align: center; color: #000; }
    th:first-child, td:first-child { border-left: none; }
    th:last-child, td:last-child { border-right: none; }
    tr:first-child th { border-top: 2px solid black; border-bottom: 2px solid black; }
    @media print { .print-button { display: none !important; } }
    </style></head><body>
    <div class="print-button" style="text-align:right; margin: 10px 0;">
      <button onclick="window.print()" style="padding:6px 12px; font-size:10pt; cursor:pointer; border: 2px solid #333; font-weight:bold;">인쇄 또는 PDF 저장</button>
    </div>
    '''

    html += '<p style="margin-top:20px;">선택된 국가 수: ' + str(len(selected)) + '</p>'
    html += '</body></html>'
    components.html(html, height=1800, scrolling=True)
else:
    st.info("👆  상단 \"데이터 조회 및 출력\" 버튼을 눌러주세요.")
