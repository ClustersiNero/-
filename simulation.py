import os
from player_stats import PlayerStats
from evaluator import evaluate_outcomes
from betting_strategy import generate_bets
from logger import log_player_outcomes, clear_logs, log_std_analysis, log_control_round, log_round_players
from plot_utils import plot_rtp_trends, plot_platform_profit
from config import PAYOUT_RATES

def run_simulation(total_rounds=100, num_players=20):
    from tqdm import tqdm

    player_ids = [f"player_{i}" for i in range(1, num_players + 1)]
    player_pool = {pid: PlayerStats() for pid in player_ids}
    rtp_history = {pid: [] for pid in player_ids}
    platform_profits = []

    clear_logs()

    for round_index in tqdm(range(1, total_rounds + 1), desc="模拟进度"):
        current_bets = generate_bets(player_ids)
        outcome = evaluate_outcomes(player_pool, current_bets)

        # 三日志调用
        log_std_analysis(outcome["round_id"], outcome["std_analysis"])
        log_round_players(round_index, current_bets, player_pool)
        log_control_round(
            outcome["round_id"],
            {area: sum(bets.get(area, 0) for bets in current_bets.values()) for area in PAYOUT_RATES},
            outcome["std_bounds"],
            outcome["all_structures"],
            outcome,
            outcome["sample_size"]
        )

        total_bet, total_return = 0, 0
        for pid, bets in current_bets.items():
            bet_sum = sum(bets.values())
            payout = sum(amount * PAYOUT_RATES[area] for area, amount in bets.items() if area in outcome["winning_areas"])
            player_pool[pid].update(bet_sum, payout)
            rtp_history[pid].append(player_pool[pid].rtp())
            total_bet += bet_sum
            total_return += payout

        platform_profits.append(total_bet - total_return)

    plot_rtp_trends(rtp_history)
    plot_platform_profit(platform_profits)
    print("✅ 模拟完成，日志和图表已保存到 results/")
