"""Streamlit 前端 —— 数据总览 / 智能预测 / 球员阵容 / 统计分析。"""
from __future__ import annotations

import httpx
import pandas as pd
import streamlit as st

API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="足球预测分析",
    page_icon=":material/sports_soccer:",
    layout="wide",
)

# 收紧页面留白，让内容尽量占满屏幕（去掉 Streamlit 默认的大块顶部空白）
st.markdown(
    """
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 1rem; }
        h1 { font-size: 1.5rem; margin-bottom: 0.2rem; }
        div[data-testid="stVerticalBlock"] > div:has(> .stTabs) { margin-top: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("足球预测分析")
st.caption("500 彩票网足彩数据 · 采集 → 存储 → 预测 → 统计")


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_matches() -> list[dict]:
    """从后端拉取全部比赛（含赔率），失败返回空列表。"""
    try:
        return httpx.get(f"{API}/api/matches", timeout=30).json()["matches"]
    except Exception:
        return []


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_table() -> list[dict]:
    """从后端拉取积分榜，失败返回空列表。"""
    try:
        return httpx.get(f"{API}/api/table", timeout=30).json()["table"]
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_teams() -> list[str]:
    """从后端拉取全部球队名，失败返回空列表。"""
    try:
        return httpx.get(f"{API}/api/teams", timeout=30).json()["teams"]
    except Exception:
        return []


@st.cache_data(ttl=60, show_spinner=False)
def _fetch_players(team: str) -> list[dict]:
    """从后端拉取某队球员名单，失败返回空列表。"""
    try:
        return httpx.get(f"{API}/api/players", params={"team": team}, timeout=30).json()["players"]
    except Exception:
        return []


def _fmt_half(row: pd.Series) -> str:
    """半场比分格式化，缺失返回空串。"""
    h, a = row.get("home_halftime"), row.get("away_halftime")
    if pd.isna(h) or pd.isna(a):
        return ""
    return f"{int(h)}-{int(a)}"


def _matches_df(matches: list[dict]) -> pd.DataFrame:
    """把比赛记录整理成带中文表头的展示用 DataFrame。"""
    df = pd.DataFrame(matches)
    if df.empty:
        return df
    # 全场比分、半场比分、总进球
    df["比分"] = df["home_goals"].astype(str) + "-" + df["away_goals"].astype(str)
    df["半场"] = df.apply(_fmt_half, axis=1)
    df["总进球"] = df["home_goals"] + df["away_goals"]
    df = df.rename(columns={
        "date": "日期",
        "league": "联赛",
        "home_team": "主队",
        "away_team": "客队",
        "home_win": "主胜赔率",
        "draw": "平局赔率",
        "away_win": "客胜赔率",
    })
    return df[["日期", "联赛", "主队", "客队", "半场", "比分", "总进球", "主胜赔率", "平局赔率", "客胜赔率"]]


def _upcoming_df(upcoming: list[dict]) -> pd.DataFrame:
    """未来赛事（未开赛）的展示用 DataFrame，无比分，只列赔率。"""
    df = pd.DataFrame(upcoming)
    if df.empty:
        return df
    df = df.rename(columns={
        "date": "日期",
        "league": "联赛",
        "home_team": "主队",
        "away_team": "客队",
        "home_win": "主胜赔率",
        "draw": "平局赔率",
        "away_win": "客胜赔率",
    })
    return df[["日期", "联赛", "主队", "客队", "主胜赔率", "平局赔率", "客胜赔率"]]


def _table_df(table: list[dict]) -> pd.DataFrame:
    """把积分榜整理成带中文表头的展示用 DataFrame。"""
    df = pd.DataFrame(table)
    if df.empty:
        return df
    df.insert(0, "排名", range(1, len(df) + 1))
    df = df.rename(columns={
        "team": "球队",
        "league": "联赛",
        "played": "场次",
        "wins": "胜",
        "draws": "平",
        "losses": "负",
        "scored": "进球",
        "conceded": "失球",
        "goal_diff": "净胜球",
        "points": "积分",
        "avg_scored": "场均进球",
        "avg_conceded": "场均失球",
    })
    return df[["排名", "球队", "联赛", "场次", "胜", "平", "负", "进球", "失球", "净胜球", "积分", "场均进球", "场均失球"]]


def _players_df(players: list[dict]) -> pd.DataFrame:
    """把球员名单整理成带中文表头的展示用 DataFrame。"""
    df = pd.DataFrame(players)
    if df.empty:
        return df
    df = df.rename(columns={
        "name": "姓名",
        "number": "号码",
        "position": "位置",
        "nationality": "国籍",
        "age": "年龄",
        "height": "身高",
        "weight": "体重",
        "market_value": "身价",
        "appearances": "出场",
        "goals": "进球",
        "assists": "助攻",
    })
    cols = [c for c in ["姓名", "号码", "位置", "国籍", "年龄", "身高", "体重", "出场", "进球", "助攻", "身价"] if c in df.columns]
    return df[cols]


tab_overview, tab_agent, tab_players, tab_stats = st.tabs(
    ["数据总览", "智能预测", "球员阵容", "统计分析"]
)

# ── 数据总览：打开即自动加载全部数据 ──
with tab_overview:
    matches = _fetch_matches()
    table = _fetch_table()
    upcoming = [m for m in matches if m.get("status") == "未开赛"]
    finished = [m for m in matches if m.get("status") != "未开赛"]

    # 指标行
    with st.container(horizontal=True):
        st.metric("已完赛", len(finished), border=True)
        st.metric("未来赛事", len(upcoming), border=True)
        st.metric("球队数", len(table), border=True)

    odds_config = {
        "主胜赔率": st.column_config.NumberColumn(format="%.2f"),
        "平局赔率": st.column_config.NumberColumn(format="%.2f"),
        "客胜赔率": st.column_config.NumberColumn(format="%.2f"),
    }

    # 未来赛事（未开赛）
    with st.container(border=True):
        st.subheader("未来赛事")
        udf = _upcoming_df(upcoming)
        if not udf.empty:
            st.dataframe(udf, hide_index=True, column_config=odds_config)
        else:
            st.caption("暂无未开赛赛事")

    # 已完赛
    with st.container(border=True):
        st.subheader("已完赛")
        df = _matches_df(finished)
        if not df.empty:
            st.dataframe(df, hide_index=True, column_config=odds_config)
        else:
            st.caption("暂无数据，请先运行采集脚本 scripts/crawl_500.py")

    # 积分榜
    with st.container(border=True):
        st.subheader("球队积分榜")
        leagues = sorted({t.get("league") for t in table if t.get("league")})
        league_filter = st.selectbox("筛选联赛", ["全部"] + leagues, key="league_filter")
        if league_filter != "全部":
            table = [t for t in table if t.get("league") == league_filter]
        tdf = _table_df(table)
        if not tdf.empty:
            st.dataframe(tdf, hide_index=True)
        else:
            st.caption("暂无积分榜数据")


with tab_agent:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 标题 + 清空按钮
    c_title, c_clear = st.columns([6, 1])
    c_title.subheader(":material/sports_soccer: 智能预测")
    if c_clear.button("清空", key="clear_chat", disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.rerun()

    # 欢迎卡片：无历史时展示可点击的示例问题
    pending = None
    if not st.session_state.messages:
        with st.container(border=True):
            st.markdown("**试试这样问**（点击直接提问，回答后还能继续追问）")
            cols = st.columns(2)
            examples = [
                "预测皇马 vs 巴萨谁赢？",
                "曼城让阿森纳 1 球谁赢？",
                "列出未来几天的比赛",
                "皇马最近状态怎么样？",
            ]
            for i, ex in enumerate(examples):
                if cols[i % 2].button(ex, key=f"ex_{i}"):
                    pending = ex

    # 历史对话
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # 输入框（紧跟对话之后，非固定底部；用 form 支持回车发送 + 自动清空）
    with st.form("chat_form", clear_on_submit=True, border=False):
        c_input, c_btn = st.columns([5, 1])
        user_input = c_input.text_input(
            "输入问题", key="chat_q", label_visibility="collapsed", placeholder="问我预测问题…"
        )
        submitted = c_btn.form_submit_button("发送", width="stretch")

    q = pending or (user_input if submitted else None)
    if q:
        # 历史 = 当前问题之前的所有消息
        history = list(st.session_state.messages)
        st.session_state.messages.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("分析中..."):
                try:
                    r = httpx.post(f"{API}/api/agent", json={"question": q, "history": history}, timeout=180).json()
                    answer = r.get("answer", "（无回答）")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    st.error(f"调用失败：{exc}")


with tab_players:
    st.subheader("球员阵容")
    teams = _fetch_teams()
    if not teams:
        st.caption("暂无球队数据，请先采集比赛")
    else:
        team = st.selectbox("选择球队", teams, key="team_select")
        players = _fetch_players(team)
        with st.container(border=True):
            pdf = _players_df(players)
            if not pdf.empty:
                st.caption(f"{team} 共 {len(pdf)} 名球员")
                st.dataframe(pdf, hide_index=True)
            else:
                st.caption("该队暂无球员数据，可运行 scripts/crawl_players.py 采集")


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
