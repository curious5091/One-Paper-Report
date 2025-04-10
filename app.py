import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from collections import defaultdict
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# 구글 시트 인증
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

# 페이지 기본 설정
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 조회 버튼 + Streamlit 인쇄 버튼
col1, col2 = st.columns([1, 1])
with col1:
    run_button = st.button("📥 데이터 조회 및 출력")
with col2:
    if st.button("🖨️ 인쇄 또는 PDF 저장"):
        components.html("""
            <script>
            window.print();
            </script>
        """, height=0)

html = '''<html><head><style>
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

# 주요국 출력
for country in sorted(set(country_order) - emerging, key=lambda x: country_order[x]):
    bg_color = color_map.get(country, '#ffffff')
    html += f'<div style="background-color:{bg_color}; padding:6px; margin-bottom:15px;">'
    html += f'<h3 style="color:#000;">{country}</h3>'

    key_y, key_q = (country, 'GDP(연간)'), (country, 'GDP(분기)')
    if key_y in value_map or key_q in value_map:
        periods_y = sorted(value_map[key_y].keys(), reverse=True)[:4][::-1]
        periods_q = sorted(value_map[key_q].keys(), reverse=True)[:8][::-1]
        label_y = format_label('GDP(연간)', *meta[key_y][:2])
        label_q = format_label('GDP(분기)', *meta[key_q][:2])
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

# 신흥국 GDP 병합 표
html += f'<div style="background-color:{color_map["베트남"]}; padding:6px; margin-bottom:15px;"><h3>신흥국</h3>'
gdp_annual = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(연간)'}
gdp_quarter = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(분기)'}
annual_periods = sorted({p for v in gdp_annual.values() for p in v}, reverse=True)[:4][::-1]
quarter_periods = sorted({p for v in gdp_quarter.values() for p in v}, reverse=True)[:8][::-1]
html += '<table><tr><th>국가</th>'
html += f'<th colspan="{len(annual_periods)}">{format_label("GDP(연간)", "%", "전동비")}</th>'
html += f'<th colspan="{len(quarter_periods)}">{format_label("GDP(분기)", "%", "전동비")}</th></tr>'
html += '<tr>' + ''.join(f'<th>{p}</th>' for p in annual_periods + quarter_periods) + '</tr>'
for country in sorted(emerging, key=lambda x: country_order.get(x, 99)):
    html += '<tr style="border-bottom:2px solid black;"><td>' + country + '</td>'
    html += ''.join(f'<td>{gdp_annual.get((country, "GDP(연간)"), {}).get(p, "")}</td>' for p in annual_periods)
    html += ''.join(f'<td>{gdp_quarter.get((country, "GDP(분기)"), {}).get(p, "")}</td>' for p in quarter_periods)
    html += '</tr>'
html += '</table>'

# 신흥국 기타 지표 병합 표
g_keys = [k for k in value_map if k[0] in emerging and k[1] not in ['GDP(연간)', 'GDP(분기)']]
all_periods = sorted({p for k in g_keys for p in value_map[k]}, reverse=True)[:6][::-1]
html += '<table><tr><th>국가</th><th>지표명</th>' + ''.join(f'<th>{p}</th>' for p in all_periods) + '</tr>'
last_country = None
rowspan = defaultdict(int)
for k in g_keys:
    rowspan[k[0]] += 1
for i, k in enumerate(sorted(g_keys, key=lambda x: (country_order.get(x[0], 99), sort_order.get(x[1], 99)))):
    unit, base, _ = meta[k]
    html += f'<tr{" style=\"border-bottom:2px solid black;\"" if i == len(g_keys)-1 else ""}>'
    if k[0] != last_country:
        html += f'<td rowspan="{rowspan[k[0]]}">{k[0]}</td>'
        last_country = k[0]
    html += f'<td class="label">{format_label(k[1], unit, base)}</td>'
    for p in all_periods:
        html += f'<td>{value_map[k].get(p, "")}</td>'
    html += '</tr>'

html += '</body></html>'
components.html(html, height=1700, scrolling=True)
