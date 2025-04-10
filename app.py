import streamlit as st
import pandas as pd
import io
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")

# 제목
st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 버튼 행
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("📥 데이터 조회 및 출력"):
        st.session_state["triggered"] = True

# 샘플 데이터 (미국 GDP)
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

# 조회되었을 때만 출력
if st.session_state.get("triggered", False):

    # 표 구성용 DataFrame (엑셀 저장용)
    df_dict = {"지표": [], "기준시점": [], "값": []}
    for i in range(2):
        for j, 시점 in enumerate(sample_data["값목록"][i]):
            df_dict["지표"].append(sample_data["지표"][i])
            df_dict["기준시점"].append(시점)
            df_dict["값"].append(sample_data["수치"][i][j])
    df_excel = pd.DataFrame(df_dict)

    # 엑셀 다운로드 버튼 (스타일 통일)
    with col2:
        output = io.BytesIO()
        today = datetime.today().strftime('%Y%m%d')
        filename = f"One Page Economy Report_{today}.xlsx"
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_excel.to_excel(writer, index=False, sheet_name="미국")
        st.download_button("📥 엑셀 다운로드", data=output.getvalue(),
                           file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # 인쇄 버튼
    with col3:
        if st.button("🖨️ 인쇄 또는 PDF 저장"):
            components.html("""<script>window.print()</script>""", height=0)

    # 표 HTML 출력
    html = """
    <style>
    @media print {
        .element-container button, .stDownloadButton { display: none !important; }
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin-bottom: 20px;
        font-family: 'Malgun Gothic';
        font-size: 10pt;
    }
    th, td {
        border: 1px solid black;
        padding: 6px;
        text-align: center;
    }
    th.label {
        text-align: left;
    }
    </style>
    <h3>미국</h3>
    <table><tr>
    """
    for i in range(2):  # 연간, 분기
        label = f"<b>{sample_data['지표'][i]}</b> <span style='font-weight:normal; font-size:8pt;'>({sample_data['단위'][i]}, {sample_data['기준점'][i]})</span>"
        html += f'<td><table><tr><th colspan="{len(sample_data["값목록"][i])}" class="label">{label}</th></tr>'
        html += '<tr>' + ''.join(f"<th>{p}</th>" for p in sample_data["값목록"][i]) + '</tr>'
        html += '<tr style="border-bottom:2px solid black;">' + ''.join(f"<td>{v}</td>" for v in sample_data["수치"][i]) + '</tr></table></td>'
    html += '</tr></table>'

    components.html(html, height=450, scrolling=True)

else:
    st.info("👆  상단   '📥 데이터 조회 및 출력'   버튼을  눌러주세요.")
