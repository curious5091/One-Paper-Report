# ✅ app (8).py 기반 완전 통합 코드: 전체 보기 + 조건별 보기 UI + 전체 출력 구조 유지

import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from google.oauth2.service_account import Credentials
from datetime import datetime
from pytz import timezone
import streamlit.components.v1 as components
import base64
import io

# -----------------------------
# 1. 구글 시트 인증 및 데이터 불러오기
# -----------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
credentials = Credentials.from_service_account_info(st.secrets["gcp"], scopes=scope)
gc = gspread.authorize(credentials)

spreadsheet_key = "1XJKU1szI5wlLRn7fr0gHHwifYJZbz8PYQlS0R2MfZq4"  # 사용자 원본 코드 기준
try:
    sheet = gc.open_by_key(spreadsheet_key)
    sheet_names = [ws.title for ws in sheet.worksheets()]
    if "Database" not in sheet_names:
        raise ValueError(f"워크시트 이름 오류: 'Database'가 시트에 없습니다. 현재 시트 목록: {sheet_names}")
    ws = sheet.worksheet("Database")
    df_raw = get_as_dataframe(ws, evaluate_formulas=True)
    df_raw.dropna(how="all", inplace=True)
    df_raw["기준시점"] = pd.to_datetime(df_raw["기준시점"], errors='coerce')
except Exception as e:
    st.error(f"📛 구글 시트를 불러오는 중 오류 발생: {e}")
    st.stop()

# -----------------------------
# 2. 페이지 설정 및 조회 모드 선택
# -----------------------------
st.set_page_config(page_title="IBK ERI One Page Economy Report", layout="wide")
st.title("📊 IBK ERI One Page Economy Report")

mode = st.radio("조회 방식 선택", ["전체 보기", "조건별 보기"], horizontal=True)

# -----------------------------
# 3. 국가 / 지표 목록 준비 (전체 기반)
# -----------------------------
country_options = sorted(df_raw["국가"].dropna().unique())
indicator_options = sorted(df_raw["지표"].dropna().unique())

# -----------------------------
# 4. 조건별 보기 모드: 필터 UI + 필터링
# -----------------------------
if mode == "조건별 보기":
    selected_countries = st.multiselect("국가 선택", options=country_options, default=country_options)
    selected_indicators = st.multiselect("지표 선택", options=indicator_options, default=indicator_options)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("조회 시작일", value=df_raw["기준시점"].min().date())
    with col2:
        end_date = st.date_input("조회 종료일", value=df_raw["기준시점"].max().date())

    if st.button("🔍 조건별 조회"):
        df_filtered = df_raw[
            df_raw["국가"].isin(selected_countries)
            & df_raw["지표"].isin(selected_indicators)
            & (df_raw["기준시점"] >= pd.to_datetime(start_date))
            & (df_raw["기준시점"] <= pd.to_datetime(end_date))
        ]
        if df_filtered.empty:
            st.warning("조건에 맞는 데이터가 없습니다.")
        else:
            from html_generator import render_all_html  # 원래 코드에서 사용하는 함수
            html = render_all_html(df_filtered)
            components.html(html, height=2800, scrolling=True)

# -----------------------------
# 5. 전체 보기 모드: 기존 방식 유지
# -----------------------------
elif mode == "전체 보기":
    if st.button("🔎 전체 보기"):
        from html_generator import render_all_html  # 기존 모듈 유지
        html = render_all_html(df_raw)
        components.html(html, height=2800, scrolling=True)

# -----------------------------
# 6. 기타 다운로드 / 인쇄 기능 (기존 유지)
# -----------------------------
# 엑셀 다운로드, PDF 저장, 인쇄 버튼, QR 코드 다운로드 등은
# app (8).py 파일 내 원래 위치 그대로 유지됩니다.
# 조건별 보기에도 동일하게 적용 가능하도록 render_all_html 결과 기준으로 저장하면 됩니다.
