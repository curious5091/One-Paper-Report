# IBK ERI One Page Economy Report

![One Page Report Thumbnail](https://raw.githubusercontent.com/curious5091/One-Paper-Report/main/thumbnail.png)

Streamlit 기반의 경제 지표 시각화 대시보드입니다.

👉 [앱 실행하기](https://oper-ibkeri.streamlit.app)

---

## 🧾 주요 기능

- 📊 한국, 미국, 중국, 일본, 유로존 및 신흥국(베트남, 폴란드, 인도네시아, 인도) 포함
- 🧮 GDP(연간/분기), CPI, 실업률 등 주요 지표 시각화
- 🖨️ A4 사이즈로 인쇄 가능한 HTML 테이블 레이아웃 제공
- 📤 PDF 저장 기능 지원

---

## ⚙️ 사용 기술

- [Streamlit](https://streamlit.io/)
- Google Sheets API (서비스 계정 연동)
- Pandas / Plotly / OpenPyXL
- HTML + CSS 커스터마이징
- PDF 내보내기 기능 포함

---

## 🧪 실행 방법

```bash
git clone https://github.com/curious5091/One-Paper-Report.git
cd One-Paper-Report
streamlit run app.py
