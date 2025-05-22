import os
from config import PAYOUT_RATES

def clear_logs():
    os.makedirs("results", exist_ok=True)
    for fname in ["control_log.txt", "player_log.txt"]:
        fpath = os.path.join("results", fname)
        if os.path.exists(fpath):
            os.remove(fpath)

def log_player_outcomes(round_id, current_bets, outcome, global_players):
    log_path = "results/player_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"👤 玩家日志 - Round {round_id}\n")
        f.write("="*60 + "\n")
        win_areas = set(outcome["winning_areas"])
        for pid in sorted(current_bets.keys()):
            bets = current_bets[pid]
            total_bet = sum(bets.values())
            real_payout = sum(amount * PAYOUT_RATES[area] for area, amount in bets.items() if area in win_areas)
            status = "🎯中奖！" if any(area in win_areas for area in bets) else "❌未中奖"
            stats = global_players[pid]

            # 排序下注区域并格式化输出
            sorted_bets = {k: bets[k] for k in sorted(bets)}
            bet_str = ", ".join(f"{area}: {amount}" for area, amount in sorted_bets.items())

            f.write(f"玩家 {pid}：\n")
            f.write(f"  🎲 下注区域分布：{{{bet_str}}}\n")
            f.write(f"  🏆 命中区域：{sorted(outcome['winning_areas'])} → {status}\n")
            f.write(f"  💰 实得返还：{real_payout:.2f}\n")
            f.write(f"  📊 当前 RTP：{stats.rtp():.2f}（投注 {stats.total_bet:.2f} / 返还 {stats.total_return:.2f}）\n")
            f.write("-" * 60 + "\n")
        f.write("\n")

def log_control_round(round_id, player_bets, std_bounds, structure_results, selected, sample_size):
    log_path = "results/control_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[Round {round_id}]\n")

        bet_lines = ", ".join(f"{k}: {v}" for k, v in sorted(player_bets.items()))
        f.write(f"🎯 输入下注区域分布：{{{bet_lines}}}\n")

        f.write(f"📊 结构候选总数：{len(structure_results)}\n")
        f.write(f"🧪 当前局有效样本数：{sample_size}\n")
        std_range = (std_bounds[1] - std_bounds[0]) / 2
        f.write(f"🎯 置信区间范围：±{std_range:.4f} → [{std_bounds[0]:.4f}, {std_bounds[1]:.4f}]\n\n")

        f.write("✅ 结构评估列表：\n")
        for idx, r in enumerate(structure_results):
            mark = "✓" if r["within_confidence"] else "✗（超出范围）"
            f.write(f"    - ID {idx:<2} | 区域: {r['winning_areas']} | std={r['std']:.4f} {mark}\n")

        hits = [idx for idx, r in enumerate(structure_results) if r["within_confidence"]]
        selected_idx = next(
            (i for i, r in enumerate(structure_results)
             if r["winning_areas"] == selected["winning_areas"] and abs(r["std"] - selected["std"]) < 1e-6),
            -1
        )

        if hits:
            f.write(f"\n🎯 命中结构共 {len(hits)} 个，按权重抽样 → ID: {selected_idx}（{selected['winning_areas']}）\n")
        else:
            f.write(f"\n⚠ 无结构落入置信区间、在“返奖率 < 100%”的结构中选取“标准差最接近 STD_THRESHOLD 的 → ID: {selected_idx}（{selected['winning_areas']}）\n")

        f.write(f"🏁 最终选中结构 ID: {selected_idx}，标准差：{selected['std']:.4f}\n")
        f.write("--------------------------------------------------\n")

def log_std_analysis(round_id, std_analysis_data):
    log_path = "results/std_analysis_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"📊 控奖标准差分析日志 - Round {round_id}\n")
        f.write("=" * 70 + "\n")
        for idx, entry in enumerate(std_analysis_data):
            f.write(f"结构 ID {idx} → 区域: {entry['winning_areas']}\n")
            f.write(f"  标准差 STD = {entry['std']:.4f}\n")
            f.write(f"  玩家数据如下：\n")
            for player in entry["details"]["players"]:
                f.write(f"    - {player['id']:10s} | bet={player['bet']:6.1f} | return={player['return']:6.1f} | RTP={player['rtp']:.3f} | 权重贡献={(player['weight'] * 100):5.1f}%\n")
            f.write(f"  ▶ 目标 RTP = {entry['details']['target_rtp']:.4f}\n")
            f.write(f"  ▶ 加权方差 = {entry['details']['weighted_variance']:.6f}\n")
            f.write("-" * 70 + "\n")

def log_round_players(round_id, current_bets, player_pool):
    log_path = "results/round_players_log.txt"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"🧾 玩家参与明细 - Round {round_id}\n")
        f.write("=" * 60 + "\n")
        for pid in sorted(current_bets.keys()):
            bets = current_bets[pid]
            total_bet = sum(bets.values())
            stats = player_pool[pid]
            sorted_bets = {k: bets[k] for k in sorted(bets)}
            bet_str = ", ".join(f"{area}: {amount}" for area, amount in sorted_bets.items())
            f.write(f"玩家 {pid}：\n")
            f.write(f"  🎲 本轮投注区域分布：{{{bet_str}}}\n")
            f.write(f"  💼 开始前累计投注={stats.total_bet:.2f}, 累计返还={stats.total_return:.2f}\n")
            f.write(f"  📊 当前 RTP（前一局后）={stats.rtp():.4f}\n")
            f.write("-" * 60 + "\n")
        f.write("\n")
