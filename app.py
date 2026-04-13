# --- [MODE 2] 대시보드 시각화 (Y축 최적화 버전) ---
            elif st.session_state.view_mode == 'dashboard':
                st.subheader("📊 경제 지표 시각화 대시보드")
                target_country = st.selectbox("조회할 국가를 선택하세요", sorted(df['국가'].unique()))
                c_df = df[df['국가'] == target_country].copy()
                all_inds = sorted(c_df['지표'].unique())
                selected_inds = st.multiselect("확인할 지표를 선택하세요", all_inds, default=[i for i in ['CPI', '산업생산', '기준금리'] if i in all_inds])
                
                if selected_inds:
                    cols = st.columns(2)
                    for i, ind in enumerate(selected_inds):
                        with cols[i % 2]:
                            ind_df = c_df[c_df['지표'] == ind].sort_values('기준시점').tail(12)
                            if not ind_df.empty:
                                st.write(f"**{ind} ({target_country})**")
                                
                                # Y축 최적화를 위해 Vega-Lite 차트 사용
                                # scale={'zero': False} 설정이 핵심입니다. (0부터 시작하지 않고 데이터 범위에 맞춤)
                                st.vega_lite_chart(ind_df, {
                                    'mark': {'type': 'line', 'point': True, 'tooltip': True},
                                    'encoding': {
                                        'x': {'field': '기준시점_text', 'type': 'nominal', 'title': '기준시점', 'sort': None},
                                        'y': {
                                            'field': '값', 
                                            'type': 'quantitative', 
                                            'title': '수치',
                                            'scale': {'zero': False, 'padding': 10} # 0을 강제하지 않고 여백을 줌
                                        },
                                        'color': {'value': '#007bff'}
                                    },
                                    'width': 'container',
                                    'height': 300
                                })
                else:
                    st.warning("지표를 선택해주세요.")
