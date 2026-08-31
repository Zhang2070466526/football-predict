"""Streamlit 前端 —— 三个 Tab：RAG 问答 / 比赛预测 / 统计。"""
from __future__ import annotations

import httpx

import streamlit as st

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="football-predict", layout="wide")
st.title("⚽ football-predict")


tab_qa, tab_predict, tab_stats = st.tabs(["RAG 问答", "比赛预测", "统计分析"])

with tab_qa:
    st.subheader("用自然语言查询足球数据")
    question = st.text_input("问题", placeholder="例如：上赛季谁夺冠了？")
    if st.button("提问", key="qa"):
        if not question.strip():
            st.warning("请输入问题")
        else:
            try:
                r = httpx.post(f"{API}/api/chat", json={"question": question}, timeout=60).json()
                st.markdown(r["answer"])
                with st.expander("检索来源"):
                    for s in r.get("sources", []):
                        st.caption(f"[{s['score']:.3f}] {s['content'][:120]}...")
            except Exception as exc:
                st.error(f"调用失败：{exc}")

with tab_predict:
    st.subheader("比赛结果预测")
    c1, c2 = st.columns(2)
    home = c1.text_input("主队", key="home")
    away = c2.text_input("客队", key="away")
    if st.button("预测", key="predict"):
        if not home or not away:
            st.warning("请输入主队和客队")
        else:
            try:
                r = httpx.post(f"{API}/api/predict", json={"home_team": home, "away_team": away}, timeout=60).json()
                st.metric("预测", r.get("prediction", "—"))
                st.write(f"主胜 {r.get('home_win_prob')} / 平 {r.get('draw_prob')} / 客胜 {r.get('away_win_prob')}")
            except Exception as exc:
                st.error(f"调用失败：{exc}")

with tab_stats:
    st.subheader("球队统计")
    team = st.text_input("球队名", key="team")
    if st.button("查询统计", key="stats"):
        if not team:
            st.warning("请输入球队名")
        else:
            try:
                r = httpx.get(f"{API}/api/stats", params={"team": team}, timeout=60).json()
                st.json(r)
            except Exception as exc:
                st.error(f"调用失败：{exc}")
