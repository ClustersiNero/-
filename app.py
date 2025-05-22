import streamlit as st
import hashlib
st.set_page_config(page_title="百人游戏仪表盘_摩天轮", layout="wide")

def check_password():
    def _hash(password):
        return hashlib.sha256(password.encode()).hexdigest()

    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    correct_hash = _hash("ferris123")
    with st.sidebar:
        st.markdown("### 🔐 请输入访问密码")
        password_input = st.text_input("Password", type="password")
        if st.button("登录"):
            if _hash(password_input) == correct_hash:
                st.session_state.auth_ok = True
            else:
                st.error("❌ 密码错误，请重试。")

    return st.session_state.auth_ok

if not check_password():
    st.stop()
import pandas as pd
import time, random
from betting_strategy import generate_bets
from evaluator import evaluate_outcomes
from player_stats import PlayerStats
from config import PAYOUT_RATES

# ----- 初始化状态管理 -----
if "rtp_history" not in st.session_state:
    st.session_state.rtp_history = {}
if "round_id" not in st.session_state:
    st.session_state.round_id = 1
if "time_to_next_round" not in st.session_state:
    st.session_state.time_to_next_round = 50
if "countdown_bet" not in st.session_state:
    st.session_state.countdown_bet = 30
if "countdown_result" not in st.session_state:
    st.session_state.countdown_result = 15
if "player_pool" not in st.session_state:
    st.session_state.player_pool = {f"player_{i}" : PlayerStats() for i in range(1, 21)}
if "current_bets" not in st.session_state:
    st.session_state.current_bets = {}
if "running" not in st.session_state:
    st.session_state.running = False
if "online_base" not in st.session_state:
    st.session_state.online_base = random.randint(65, 75)
if "final_outcome" not in st.session_state:
    st.session_state.final_outcome = None
if "forced_outcome" not in st.session_state:
    st.session_state.forced_outcome = None
if "structure_result_cache" not in st.session_state:
    st.session_state.structure_result_cache = None

player_ids = list(st.session_state.player_pool.keys())

# ----- 展示侧边栏信息 -----
def count_betting_players():
    return len(st.session_state.current_bets)

def estimate_online_players():
    if random.random() < 0.2:
        delta = random.choice([-1, 0, 1])
        st.session_state.online_base = max(60, min(80, st.session_state.online_base + delta))
    return st.session_state.online_base

betting_players = count_betting_players()
online_count = estimate_online_players()

st.sidebar.markdown("### 📋 对局基础信息")
st.sidebar.text(f"游戏名：摩天轮")
st.sidebar.text(f"对局数ID：{st.session_state.round_id}")
st.sidebar.text(f"在线人数：{online_count}")
st.sidebar.text(f"参与人数：{betting_players}")
st.sidebar.markdown("### 🎯 策略信息")
if "target_rtp" not in st.session_state:
    from config import TARGET_RTP
    st.session_state.target_rtp = TARGET_RTP
if "confidence_level" not in st.session_state:
    from config import CONFIDENCE_LEVEL
    st.session_state.confidence_level = CONFIDENCE_LEVEL

st.session_state.target_rtp = st.sidebar.number_input("🎯 目标 RTP", min_value=0.80, max_value=1.20, step=0.001, format="%.3f", value=st.session_state.target_rtp)
st.session_state.confidence_level = st.sidebar.slider("📐 置信度", min_value=0.80, max_value=0.999, step=0.001, format="%.3f", value=st.session_state.confidence_level)

if 'sidebar_ci' in st.session_state:
    st.sidebar.text(st.session_state.sidebar_ci)

# ✅ 当前阶段与阶段内倒计时
with st.sidebar:
    st.markdown("### ⏱ 当前阶段与强控窗口")
    if st.session_state.time_to_next_round > 20:
        st.markdown("**下注阶段**")
        phase_left = st.session_state.countdown_bet
        st.progress(phase_left / 30, text=f"剩余下注时间：{phase_left}s")
        ctrl_left = st.session_state.countdown_bet + st.session_state.countdown_result
        st.progress(ctrl_left / 45, text=f"✅ 强控窗口剩余：{ctrl_left}s")

    elif st.session_state.time_to_next_round > 5:
        st.markdown("**等待开奖阶段**")
        phase_left = st.session_state.countdown_result
        st.progress(phase_left / 15, text=f"剩余等待时间：{phase_left}s")
        ctrl_left = st.session_state.countdown_result
        st.progress(ctrl_left / 45, text=f"✅ 强控窗口剩余：{ctrl_left}s")

    else:
        st.markdown("**开奖动画阶段**")
        remaining = st.session_state.time_to_next_round
        progress_val = remaining / 5
        st.progress(max(0.0, min(1.0, progress_val)), text=f"开奖动画时间：{remaining}s")
        st.text("❌ 当前不可强制开奖")

st.sidebar.markdown("---")
if "debug_speed" not in st.session_state:
    st.session_state.debug_speed = 1.0
st.sidebar.slider("⏩ 模拟倍速 (越大越快)", min_value=0.0, max_value=10.0, step=0.1, key="debug_speed")

# 🚀 开始下一局按钮逻辑
if st.sidebar.button("🚀 开始下一局"):
    st.session_state.round_id += 1
    st.session_state.time_to_next_round = 50
    st.session_state.countdown_bet = 30
    st.session_state.countdown_result = 15
    st.session_state.current_bets = {}
    st.session_state.final_outcome = None
    st.session_state.forced_outcome = None
    st.session_state.structure_result_cache = None  # ✅ 清除上一轮的结构模拟缓存
    st.session_state.running = True
    st.rerun()
# ----- 主界面展示 -----
# 已删除主标题，节省纵向空间

left_col, right_col = st.columns([3, 4])

with left_col:
    st.markdown("<h5 style='margin-bottom: 0.2rem'>🎲 当前下注概况</h5>", unsafe_allow_html=True)
    structure_sums = {i: 0 for i in range(1, 9)}
    for bets in st.session_state.current_bets.values():
        for area, amt in bets.items():
            if area in structure_sums:
                structure_sums[area] += amt
    chart_df = pd.DataFrame.from_dict(structure_sums, orient="index", columns=["下注总额"])
    chart_df.index.name = "区域"
    chart_df = chart_df.loc[[k for k in range(1, 9)]].reset_index()
    if st.session_state.final_outcome:
        highlight_areas = set(st.session_state.final_outcome["winning_areas"])
    elif st.session_state.time_to_next_round > 20 and st.session_state.current_bets and st.session_state.structure_result_cache is None and st.session_state.countdown_bet == 29:
        preview = evaluate_outcomes(
    st.session_state.player_pool,
    st.session_state.current_bets,
    confidence_level=st.session_state.confidence_level,
    target_rtp=st.session_state.target_rtp
)
        st.session_state.structure_result_cache = preview
        highlight_areas = set()
        for r in preview["all_structures"]:
            if r["within_confidence"]:
                highlight_areas.update(r["winning_areas"])
    elif st.session_state.structure_result_cache:
        highlight_areas = set()
        for r in st.session_state.structure_result_cache["all_structures"]:
            if r["within_confidence"]:
                highlight_areas.update(r["winning_areas"])
    else:
        highlight_areas = set()

    chart_df["颜色"] = chart_df["区域"].apply(
        lambda x: "强控" if st.session_state.forced_outcome and x in st.session_state.forced_outcome["winning_areas"]
        else ("推荐" if x in highlight_areas else "默认"))

    import altair as alt
    color_map = {"强控": "crimson", "推荐": "green", "默认": "steelblue"}
    bar_chart = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X("区域:N", axis=alt.Axis(labelAngle=0, title=None)),
        y=alt.Y("下注总额:Q"),
        color=alt.Color("颜色:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None)
    ).properties(height=240)
    from streamlit import columns
    if st.session_state.final_outcome:
        outcome_to_show = st.session_state.final_outcome
        forced_flag = st.session_state.forced_outcome is not None and st.session_state.final_outcome == st.session_state.forced_outcome
        label_prefix = "【强控】" if forced_flag else ""
        lower, upper = outcome_to_show["std_bounds"]
        bar_caption = f"{label_prefix}开奖结果：{outcome_to_show['winning_areas']}（STD: {outcome_to_show['std']:.4f}）"
        st.session_state.sidebar_ci = f"置信区间：[ {lower:.4f}, {upper:.4f} ]"
        st.altair_chart(bar_chart, use_container_width=True)
        st.markdown(f"<div style='font-weight:600; font-size:15px; margin-top:-30px'>{bar_caption}</div>", unsafe_allow_html=True)
    elif st.session_state.current_bets:
        preview = evaluate_outcomes(st.session_state.player_pool, st.session_state.current_bets)
        st.session_state.structure_result_cache = preview
        recommended = [r["winning_areas"] for r in preview["all_structures"] if r["within_confidence"]]
        lower, upper = preview["std_bounds"]
        st.altair_chart(bar_chart, use_container_width=True)
        st.session_state.sidebar_ci = f"置信区间：[ {lower:.4f}, {upper:.4f} ]"

    if st.session_state.final_outcome:
        outcome_to_show = st.session_state.final_outcome
        forced_flag = st.session_state.forced_outcome is not None and st.session_state.final_outcome == st.session_state.forced_outcome
        label_prefix = "【强控】" if forced_flag else ""
        table_df = pd.DataFrame(outcome_to_show["all_structures"]).copy()  # ✅ 防止引用旧数据残留
    elif st.session_state.structure_result_cache:
        table_df = pd.DataFrame(st.session_state.structure_result_cache["all_structures"]).copy()  # ✅ 防止引用旧数据残留
    else:
        table_df = pd.DataFrame()

    if not table_df.empty:
        st.markdown("<h5 style='margin-top: 0.8rem; margin-bottom: 0.2rem'>🎯 控奖结构模拟结果</h5>", unsafe_allow_html=True)
        headers = ["区域", "累计投注", "预计开奖", "系统盈亏", "标准差", "符合预期", "强制开奖"]
        header_cols = st.columns(len(headers), gap="small")
        for i, h in enumerate(headers):
            header_cols[i].markdown(f"**{h}**")

        for i, row in table_df.iterrows():
            is_forced = st.session_state.forced_outcome and row["winning_areas"] == st.session_state.forced_outcome["winning_areas"]
            cols = st.columns(len(headers), gap="small")
            win_areas = ",".join(map(str, row["winning_areas"]))
            est_award = 0
            related_bet = 0
            total_bet = sum(sum(bets.values()) for bets in st.session_state.current_bets.values())
            for bets in st.session_state.current_bets.values():
                for a, v in bets.items():
                    if a in row["winning_areas"]:
                        related_bet += v
                        est_award += v * PAYOUT_RATES[a]
            profit = total_bet - est_award
            std = row["std"]
            within = row["within_confidence"]

            highlight_style = "background-color: rgba(255,0,0,0.1); border-left: 4px solid red; padding: 6px; border-radius: 5px;" if is_forced else ""
            cols[0].markdown(f"<div style='{highlight_style}'>{win_areas}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div style='{highlight_style}'>{related_bet:,.0f}</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div style='{highlight_style}'>{est_award:,.0f}</div>", unsafe_allow_html=True)
            cols[3].markdown(f"<div style='{highlight_style}'>{profit:,.0f}</div>", unsafe_allow_html=True)
            cols[4].markdown(f"<div style='{highlight_style}'>{std:.2f}</div>", unsafe_allow_html=True)
            cols[5].markdown(f"<div style='{highlight_style}'>{'√' if within else '×'}</div>", unsafe_allow_html=True)
            if st.session_state.time_to_next_round > 5:
                force_btn_label = "🔴 取消" if is_forced else "确认"
                if cols[6].button(force_btn_label, key=f"force_btn_{i}"):
                    if is_forced:
                        st.session_state.forced_outcome = None
                    else:
                        selected = st.session_state.structure_result_cache["all_structures"][i]
                        st.session_state.forced_outcome = {
                            **selected,
                            "round_id": st.session_state.round_id,
                            "all_structures": st.session_state.structure_result_cache["all_structures"],
                            "std_bounds": st.session_state.structure_result_cache["std_bounds"],
                            "std_analysis": st.session_state.structure_result_cache["std_analysis"],
                            "sample_size": st.session_state.structure_result_cache["sample_size"],
                        }
            else:
                cols[6].write("❌")

with right_col:
    st.subheader("👤 玩家下注明细")
    # 重新构建 styled_df 数据逻辑（恢复原始构造）
    records = []
    index = 1
    for pid in sorted(st.session_state.current_bets.keys()):
        bets = st.session_state.current_bets[pid]
        total = sum(bets.values())
        stats = st.session_state.player_pool[pid]
        latest_rtp = stats.rtp()
        row = {"序号": index, "UID": pid.replace('player_', ''), "总投注": total, "当前RTP": f"{latest_rtp * 100:.1f}%"}
        for a in range(1, 9):
            row[f"结构{a}"] = bets.get(a, 0)
        row["结构9"] = sum(bets.get(a, 0) for a in range(1, 5))
        row["结构10"] = sum(bets.get(a, 0) for a in range(5, 9))
        records.append(row)
        index += 1
    df = pd.DataFrame(records)

    profit_colors, loss_colors, yellow_colors = [], [], []
    for row in df.itertuples():
        bets = {f"结构{i}": getattr(row, f"结构{i}") for i in range(1, 11)}
        total = getattr(row, "总投注")
        profit_map = {}
        for i in range(1, 11):
            hit_areas = [i] if i <= 8 else list(range(1, 5)) if i == 9 else list(range(5, 9))
            payout = sum(bets.get(f"结构{a}", 0) * PAYOUT_RATES.get(a, 0) for a in hit_areas)
            profit_map[f"结构{i}"] = payout - total

        best_structure = max(profit_map, key=profit_map.get)
        worst_structure = min(profit_map, key=profit_map.get)

        colors = ["" for _ in range(len(df.columns))]
        if best_structure in df.columns:
            colors[df.columns.get_loc(best_structure)] = "background-color: #d4edda"
        profit_colors.append(colors)

        colors = ["" for _ in range(len(df.columns))]
        if worst_structure in df.columns:
            colors[df.columns.get_loc(worst_structure)] = "background-color: #f8d7da"
        loss_colors.append(colors)

        rtp_map = {}
        for i in range(1, 11):
            hit_areas = [i] if i <= 8 else list(range(1, 5)) if i == 9 else list(range(5, 9))
            payout = sum(bets.get(f"结构{a}", 0) * PAYOUT_RATES.get(a, 0) for a in hit_areas)
            rtp = payout / total if total > 0 else 0
            rtp_map[f"结构{i}"] = abs(rtp - 1)

        closest_structure = min(rtp_map, key=rtp_map.get)
        colors = ["" for _ in range(len(df.columns))]
        if closest_structure in df.columns:
            colors[df.columns.get_loc(closest_structure)] = "background-color: #fff3cd"
        yellow_colors.append(colors)

    styled_df = df.style.apply(lambda _: profit_colors.pop(0), axis=1)
    styled_df = styled_df.apply(lambda _: loss_colors.pop(0), axis=1)
    styled_df = styled_df.apply(lambda _: yellow_colors.pop(0), axis=1)

    st.dataframe(styled_df, use_container_width=True, hide_index=True, height=930)

# 对局流程逻辑
if st.session_state.running:
    if st.session_state.time_to_next_round > 20:
        if st.session_state.countdown_bet > 0:
            new_bets = generate_bets(player_ids)
            for pid, bets in new_bets.items():
                if pid not in st.session_state.current_bets:
                    st.session_state.current_bets[pid] = bets
                else:
                    for a, v in bets.items():
                        st.session_state.current_bets[pid][a] = st.session_state.current_bets[pid].get(a, 0) + v
            st.session_state.countdown_bet -= 1

    elif st.session_state.time_to_next_round > 5:
        if st.session_state.countdown_result > 0:
            st.session_state.countdown_result -= 1

    elif st.session_state.time_to_next_round == 5:
        st.subheader("🔒 封盘 & 开奖中 ...")
        if st.session_state.forced_outcome:
            st.session_state.final_outcome = st.session_state.forced_outcome
        else:
            st.session_state.final_outcome = evaluate_outcomes(
    st.session_state.player_pool,
    st.session_state.current_bets,
    confidence_level=st.session_state.confidence_level,
    target_rtp=st.session_state.target_rtp
)

    elif st.session_state.time_to_next_round == 0:
        # ✅ 结算每位玩家的返还和投注
        winning_areas = st.session_state.final_outcome["winning_areas"]
        for pid, bets in st.session_state.current_bets.items():
            bet_sum = sum(bets.values())
            payout = sum(v * PAYOUT_RATES[a] for a, v in bets.items() if a in winning_areas)
            st.session_state.player_pool[pid].update(bet_sum, payout)
            rtp = st.session_state.player_pool[pid].rtp()
            st.session_state.rtp_history.setdefault(pid, []).append(rtp)
        st.session_state.running = False

    st.session_state.time_to_next_round -= 1
    time.sleep(1.0 / st.session_state.debug_speed)
    st.rerun()
