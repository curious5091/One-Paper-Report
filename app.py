import streamlit as st
import streamlit.components.v1 as components

# 페이지 설정
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")

st.markdown("<h1 style='font-size:24pt; margin-bottom:0pt;'>📊 IBK ERI One Page Economy Report</h1>", unsafe_allow_html=True)
st.markdown("<div style='font-size:10pt; color:#555; margin-bottom:20px;'>made by curious@ibk.co.kr with ChatGPT</div>", unsafe_allow_html=True)

# 국가 목록
main_countries = ["한국", "미국", "중국", "일본", "유로존", "신흥국"]
all_countries = ["한국", "미국", "중국", "일본", "유로존", "베트남", "폴란드", "인도네시아", "인도"]
emerging = ["베트남", "폴란드", "인도네시아", "인도"]

# 버튼 UI 출력 (HTML + CSS + JS)
components.html(f"""
<div id="selector">
  <div style="margin-bottom:10px;"><b>국가 선택</b></div>
  <button class="toggle" data-name="전체 보기">전체 보기</button>
  {"".join(f'<button class="toggle" data-name="{c}">{c}</button>' for c in main_countries)}
</div>

<script>
  const buttons = document.querySelectorAll(".toggle");
  let selected = [];

  function updateStreamlit() {{
    const message = selected.includes("전체 보기") ? {all_countries} : selected.includes("신흥국") ? selected.filter(x => x !== "전체 보기").concat({emerging}) : selected;
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
""", height=180)

# Streamlit 컴포넌트 값 수신
selected_countries = st.experimental_get_query_params().get("component_value", [])

if selected_countries:
    st.write("✅ 선택된 국가:", selected_countries)
    # 여기에 데이터 필터링 및 출력 로직을 연결하세요
else:
    st.info("👆 상단 버튼을 클릭해 국가를 선택하세요.")
