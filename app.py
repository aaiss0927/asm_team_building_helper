import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from supabase import create_client, Client
from postgrest.exceptions import APIError
import json
import os
from dotenv import load_dotenv

# 1. 환경 설정
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_TOKEN = os.getenv("SECRET_TOKEN")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="소마 17기 팀 빌딩 헬퍼", layout="wide")
if 'page' not in st.session_state: st.session_state.page = 'home'

# MBTI 리스트 정의
MBTI_LIST = [
    "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"
]

# 2. 유틸리티
def get_unit_vector(scores):
    vec = np.array(scores)
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist() if norm > 0 else vec.tolist()

def create_radar_chart(my_scores, partner_scores, partner_name):
    categories = ["Speed", "Ownership", "Arch", "Reliability", "Candor", "Doc", "DeepDive", "Risk", "Market", "Commit"]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=my_scores, theta=categories, fill='toself', name='나', line_color='rgb(31, 119, 180)'))
    fig.add_trace(go.Scatterpolar(r=partner_scores, theta=categories, fill='toself', name=partner_name, line_color='rgb(255, 127, 14)'))
    fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            title=f"나 vs {partner_name}",
            margin=dict(l=40, r=40, t=60, b=40), # 왼쪽(l) 여백을 주어 잘림 방지
            height=350, # 차트 높이를 살짝 줄여서 2*5 배열 최적화
        )
    return fig

# 3. 페이지 렌더링
def show_home():
    st.markdown("<h1 style='text-align: center;'>🚀 SOMA 17기 팀 빌딩 헬퍼</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>합격을 진심으로 축하합니다!</p>", unsafe_allow_html=True)
    _, center_col, _ = st.columns([2, 1, 2])
    with center_col:
        try:
            st.image("logo.png", use_container_width=True)
        except:
            pass
    st.write("---")
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("📊 설문 하기", use_container_width=True): 
            st.session_state.page = 'survey'; st.rerun()
    with c2: 
        if st.button("🔍 팀원 매칭", use_container_width=True): 
            st.session_state.page = 'match'; st.rerun()

def show_survey():
    if st.button("🔙 홈으로"): st.session_state.page = 'home'; st.rerun()
    st.header("📝 성향 및 목표 등록")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1: name = st.text_input("이름")
        with c2: notion_url = st.text_input("노션 주소 (자기소개 페이지 전체화면 후 주소 복사)")
        with c3: access_token = st.text_input("인증 번호 (안내 및 수요조사 링크 뒷 4자리)", type="password")
            
        c4, c5, c6 = st.columns(3)
        with c4: role = st.selectbox("주력 역할", ["ios", "android", "FE", "BE", "AI", "PM"])
        with c5: position = st.radio("선호 포지션", ["팀원", "팀장"], horizontal=True)
        with c6: goal = st.radio("최종 목표", ["창업", "취업"], horizontal=True)
        
        # MBTI 추가
        mbti = st.selectbox("나의 MBTI", MBTI_LIST)
    
    st.write("---")
    st.subheader("💡 기술 협업 성향 (1: 전혀 아니다 ~ 5: 매우 그렇다)")
    
    questions = [
        "나는 완벽한 설계보다 빠르게 작동하는 MVP를 만들어 피드백을 받는 것을 선호한다. (Speed)",
        "나는 프로젝트의 전반적인 수행에 관여하기 보다, 특정 모듈이나 기술 스택을 책임지고 주도하는 것을 즐긴다. (Ownership)",
        "나는 코드를 작성하기 전, 전체적인 시스템 아키텍처와 데이터 흐름을 설계하는 데 공을 들인다. (Architecture)",
        "나는 기능 구현만큼이나 테스트 코드 작성과 예외 처리를 통한 시스템 안정성을 중시한다. (Reliability)",
        "나는 팀원과의 갈등 상황에서 기술적 근거를 바탕으로 한 직설적이고 투명한 피드백을 선호한다. (Candor)",
        "나는 구두 소통보다 노션이나 위키를 통한 비동기적 문서화 기록을 협업의 핵심이라고 생각한다. (Documentation)",
        "나는 새로운 기술 도입 시 공식 문서나 논문을 통해 내부 동작 원리를 파헤치는 것을 즐긴다. (Deep Dive)",
        "나는 팀에 도움이 된다면 다소 생소하고 난이도 높은 최신 기술 도입에 도전하고 싶다. (Risk Taker)",
        "나의 프로젝트 지향점은 기술적 화려함보다 실제 유저의 문제를 해결하고 가치를 창출하는 것에 가깝다. (Market-Driven)",
        "나는 소마 연수 기간 동안 오프라인 연수 센터에 상주하며 전념할 계획이다. (Commitment)"
    ]
    
    scores = []
    for i, q in enumerate(questions):
        q_col, a_col = st.columns([3, 2])
        with q_col: st.write(f"**{i+1}. {q}**")
        with a_col: 
            score = st.radio(f"score_{i}", [1, 2, 3, 4, 5], index=2, horizontal=True, label_visibility="collapsed")
            scores.append(score)
    
    if st.button("🚀 설문 완료", use_container_width=True):
            if access_token != SECRET_TOKEN: 
                st.error("인증 번호 오류")
            elif not notion_url or not name: 
                st.warning("필수 항목 누락")
            else:
                embedding = get_unit_vector(scores)
                try:
                    # 1. 데이터 삽입 시도
                    supabase.table("survey_responses").insert({
                        "name": name, "notion_url": notion_url, "role": role,
                        "user_position": position, "goal": goal, "mbti": mbti, 
                        "scores": scores, "embedding": embedding
                    }).execute()
                    
                    # 2. 성공 시 메시지 출력 후 페이지 이동
                    st.success("✅ 등록되었습니다! 매칭 화면으로 이동합니다.")
                    st.session_state.page = 'match'
                    st.rerun() # 여기서 실행 흐름이 끊기고 페이지가 전환됨
                    
                except Exception as e:
                    # 3. 에러 발생 시에만 이 블록이 실행됨
                    # 중복 등록(Unique Violation) 에러인 경우를 분기
                    if "23505" in str(e) or "already exists" in str(e).lower():
                        st.error("❗ 이미 등록된 주소입니다. '팀원 매칭' 메뉴에서 바로 조회해 보세요.")
                    else:
                        st.error(f"❌ 등록 중 오류 발생: {e}")
def show_match():
    if st.button("🔙 홈으로"): st.session_state.page = 'home'; st.rerun()
    st.header("🔍 팀원 매칭")
    search_url = st.text_input("나의 노션 주소를 입력하세요.")
    
    if search_url:
        try:
            res = supabase.table("survey_responses").select("*").eq("notion_url", search_url).single().execute()
            my = res.data
            # Top 30 넉넉히 호출 (필터링 고려)
            matches = supabase.rpc("match_users", {"query_embedding": my['embedding'], "match_threshold": 0.5, "match_count": 30}).execute()
            
            if matches.data:
                df = pd.DataFrame(matches.data)
                df = df[df['notion_url'] != search_url]
                
                # 필터링 섹션 (MBTI 추가)
                st.write("---")
                st.subheader("🎯 맞춤 필터링")
                f1, f2, f3, f4 = st.columns(4)
                with f1: r_f = st.multiselect("역할", ["ios", "android", "FE", "BE", "AI", "PM"], default=["ios", "android", "FE", "BE", "AI", "PM"])
                with f2: p_f = st.multiselect("포지션", ["팀원", "팀장"], default=["팀원", "팀장"])
                with f3: g_f = st.multiselect("목표", ["창업", "취업"], default=["창업", "취업"])
                with f4: m_f = st.multiselect("MBTI", MBTI_LIST, default=MBTI_LIST) # MBTI 필터
                
                # 필터링 적용
                df_f = df[df['role'].isin(r_f) & df['user_position'].isin(p_f) & df['goal'].isin(g_f) & df['mbti'].isin(m_f)]
                
                if not df_f.empty:
                    st.dataframe(df_f[['name', 'role', 'user_position', 'goal', 'mbti', 'similarity', 'notion_url']].head(10), hide_index=True, use_container_width=True)
                    
                    st.subheader("📊 방사형 차트 비교 (Top 10)")
                    my_s = my['scores'] if isinstance(my['scores'], list) else json.loads(my['scores'])
                    
                    # 2*5 Radar Chart 레이아웃 구현
                    # st.columns(5)를 두 번 호출하여 2*5 그리드 생성
                    top_10 = df_f.head(10)
                    for i in range(2): # Row
                        cols = st.columns(5)
                        for j in range(5): # Column
                            idx = i * 5 + j
                            if idx < len(top_10):
                                row = top_10.iloc[idx]
                                p_s = row['scores'] if isinstance(row['scores'], list) else json.loads(row['scores'])
                                with cols[j]:
                                    st.plotly_chart(create_radar_chart(my_s, p_s, row['name']), use_container_width=True)
                            else:
                                with cols[j]: st.write("") # 빈 칸 처리
                                
                else: st.write("조건에 맞는 팀원이 없습니다.")
        except APIError: st.error("먼저 설문을 완료해주세요.")

if st.session_state.page == 'home': show_home()
elif st.session_state.page == 'survey': show_survey()
elif st.session_state.page == 'match': show_match()