# ✅ html_generator.py : A4용 경제지표 표 생성 렌더링 함수

def render_all_html(df):
    """
    전달받은 df를 HTML 테이블 형식으로 변환하여 반환
    (Streamlit에서 인쇄 및 PDF 저장용으로 렌더링에 사용)
    """
    import pandas as pd

    # 날짜 형식이 datetime이면 문자열로 변환
    if '기준시점' in df.columns and pd.api.types.is_datetime64_any_dtype(df['기준시점']):
        df['기준시점'] = df['기준시점'].dt.strftime('%Y-%m-%d')

    html_table = df.to_html(
        index=False,
        justify='center',
        border=1,
        escape=False,
        classes='dataframe'
    )

    html = f'''
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            .dataframe {{
                border-collapse: collapse;
                width: 100%;
                font-size: 12px;
            }}
            .dataframe th, .dataframe td {{
                border: 1px solid black;
                padding: 5px;
                text-align: center;
            }}
            .dataframe th {{
                background-color: #f2f2f2;
            }}
            @media print {{
                @page {{ size: A4 portrait; margin: 20mm; }}
                body {{ zoom: 85%; }}
            }}
        </style>
    </head>
    <body>
        {html_table}
    </body>
    </html>
    '''
    return html
