import streamlit as st
import pandas as pd
import io
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="샘플 - IBK ERI One Page", layout="wide")

st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 미국 샘플 경제지표</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 샘플 데이터
sample_data = {
    "지표": ["GDP(연간)", "GDP(분기)"],
    "단위": ["%", "%"],
    "기준점": ["전년대비", "전기대비"],
    "값목록": [
        ["2020", "2021", "2022", "2023"],
        ["2023 Q1", "Q2", "Q3", "Q4", "2024 Q1", "Q2", "Q3", "Q4"]
    ],
    "수치": [
        ["-3.5", "5.7", "2.1", "2.5"],
        ["1.6", "2.2", "3.0", "3.2", "1.8", "2.0", "2.1", "2.3"]
    ]
}

# 버튼 컨테이너
btn_col1, btn_col2 = st.columns(2)

with btn_col1:
    if st.button("📥 데이터 조회 및 출력", use_container_width=True):
        st.session_state['show'] = True

if 'show' in st.session_state and st.session_state['show']:

    # 버튼 행
    btns = """
    <div style="display:flex; justify-content:right; gap:12px; margin-bottom:10px;">
        <form method="get">
            <button formaction="#" style="padding:6px 12px; font-size:10pt; font-weight:bold; border: 2px solid #333; cursor:pointer;">
                📥 엑셀 다운로드
            </button>
        </form>
        <button onclick="window.print()" style="padding:6px 12px; font-size:10pt; font-weight:bold; border: 2px solid #333; cursor:pointer;">
            🖨️ 인쇄 또는 PDF 저장
        </button>
    </div>
    """
    st.markdown(btns, unsafe_allow_html=True)

    # HTML 테이블 생성
    html = '''
    <html><head><style>
    body {
      font-family: 'Malgun Gothic';
      font-size: 10pt;
      color: #000;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 20px;
    }
    th, td {
      border: 1px solid black;
      padding: 6px;
      text-align: center;
    }
    th.label {
      text-align: left;
      background-color: #f0f0f0;
    }
    td.label {
      text-align: left;
    }
    </style></head><body>
    <h3>미국</h3>
    <table><tr>
    '''
    for i in range(2):  # 연간 + 분기
        label = f"<b>{sample_data['지표'][i]}</b> <span style='font-weight:normal; font-size:8pt;'>({sample_data['단위'][i]}, {sample_data['기준점'][i]})</span>"
        html += f'<td><table><tr><th colspan="{len(sample_data["값목록"][i])}" class="label">{label}</th></tr>'
        html += '<tr>' + ''.join(f"<th>{p}</th>" for p in sample_data["값목록"][i]) + '</tr>'
        html += '<tr>' + ''.join(f"<td>{v}</td>" for v in sample_data["수치"][i]) + '</tr></table></td>'
    html += '</tr></table></body></html>'

    components.html(html, height=400, scrolling=True)

    # 엑셀 다운로드 - 진짜 저장
    df_dict = {
        "지표": [],
        "기준시점": [],
        "값": []
    }
    for i in range(2):
        for j in range(len(sample_data["값목록"][i])):
            df_dict["지표"].append(sample_data["지표"][i])
            df_dict["기준시점"].append(sample_data["값목록"][i][j])
            df_dict["값"].append(sample_data["수치"][i][j])
    df_excel = pd.DataFrame(df_dict)
    output = io.BytesIO()
    today = datetime.today().strftime('%Y%m%d')
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False, sheet_name="미국")
    st.download_button(
        label="📥 엑셀 다운로드 (실제)",
        data=output.getvalue(),
        file_name=f"One Page Economy Report_{today}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
