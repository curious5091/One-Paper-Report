# ... (중략: 데이터 처리 및 주요국 출력 부분은 동일)

# ✅ 신흥국 GDP 표 - 1행 1열 '국가', 2행 1열은 '-', 3~6행은 국가명
html += f'<div style="background-color:{color_map["베트남"]}; padding:6px; margin-bottom:15px;"><h3>신흥국</h3>'

gdp_annual = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(연간)'}
gdp_quarter = {k: v for k, v in value_map.items() if k[0] in emerging and k[1] == 'GDP(분기)'}
annual_periods = sorted({p for v in gdp_annual.values() for p in v}, reverse=True)[:4][::-1]
quarter_periods = sorted({p for v in gdp_quarter.values() for p in v}, reverse=True)[:8][::-1]

html += '<table>'

# ▶ 1행: 국가 + 지표명
html += f'<tr><th>국가</th>'
html += f'<th colspan="{len(annual_periods)}">{format_label("GDP(연간)", "%", "전동비")}</th>'
html += f'<th colspan="{len(quarter_periods)}">{format_label("GDP(분기)", "%", "전동비")}</th></tr>'

# ▶ 2행: '-' + 시점
html += '<tr><th>-</th>'
html += ''.join(f'<th>{p}</th>' for p in annual_periods + quarter_periods)
html += '</tr>'

# ▶ 3~6행: 국가별 수치
for i, country in enumerate(sorted(emerging, key=lambda x: country_order.get(x, 99))):
    html += f'<tr{" style=\"border-bottom:2px solid black;\"" if i == len(emerging)-1 else ""}>'
    html += f'<td>{country}</td>'
    html += ''.join(f'<td>{gdp_annual.get((country, "GDP(연간)"), {}).get(p, "")}</td>' for p in annual_periods)
    html += ''.join(f'<td>{gdp_quarter.get((country, "GDP(분기)"), {}).get(p, "")}</td>' for p in quarter_periods)
    html += '</tr>'

html += '</table>'
