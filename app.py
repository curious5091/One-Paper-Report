import streamlit as st
import gspread
from gspread_dataframe import get_as_dataframe
import pandas as pd
from google.oauth2.service_account import Credentials

# ✅ secrets에서 인증 정보 가져오기
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

st.set_page_config(page_title="국가별 경제지표 조회", layout="wide")
st.title("📊 국가별 경제지표 A4 표 출력 뷰어")

if st.button("📥 데이터 조회 및 표 출력"):
    with st.spinner("⏳ 데이터 로딩 중입니다..."):

        try:
            sheet = gc.open_by_key("1OSzr7Kb0CrfFSXaD60BLoPknJDo28kC1B_L6CgxxMOw")
            worksheet = sheet.worksheet("Database")
            df = get_as_dataframe(worksheet)
            df = df.dropna(how='all')
            df.columns = df.columns.str.strip()

            st.success("✅ 데이터 조회 성공!")
            st.dataframe(df.head(10))

        except Exception as e:
            st.error("❌ 오류 발생")
            st.exception(e)

else:
    st.info("좌측 상단 '📥 데이터 조회 및 표 출력' 버튼을 눌러주세요.")
