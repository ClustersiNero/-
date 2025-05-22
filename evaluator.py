from typing import Dict
from copy import deepcopy
import random
from config import PAYOUT_RATES, WINNING_STRUCTURES, STD_THRESHOLD, CONFIDENCE_LEVEL, MINIMUM_BET_THRESHOLD
from player_stats import PlayerStats, calculate_weighted_std
from scipy.stats import norm

# 全局标准差历史缓存
std_history: list[float] = []

def compute_dynamic_std_confidence_interval(base_std: float, confidence: float, sample_size: int):
    if sample_size <= 1:
        return base_std, base_std  # 无法计算标准误差
    z = norm.ppf(1 - (1 - confidence) / 2)
    margin = z * base_std / (sample_size ** 0.5)
    return base_std - margin, base_std + margin

def evaluate_outcomes(
    current_players: Dict[str, PlayerStats],
    current_bets: Dict[str, Dict[int, float]]
) -> Dict:
    global std_history

    BASE_STD = STD_THRESHOLD
    eligible_players = [
        current_players[pid]
        for pid, bets in current_bets.items()
        if sum(bets.values()) >= MINIMUM_BET_THRESHOLD
    ]    
    rtp_std_low, rtp_std_high = compute_dynamic_std_confidence_interval(BASE_STD, CONFIDENCE_LEVEL, len(eligible_players))

    results = []
    std_analysis_data = []

    for structure in WINNING_STRUCTURES:
        winning_areas = structure["areas"]
        weight = structure["weight"]
        simulated_players = deepcopy(current_players)

        for player_id, bets in current_bets.items():
            payout = sum(amount * PAYOUT_RATES[area] for area, amount in bets.items() if area in winning_areas)
            simulated_players[player_id].update(sum(bets.values()), payout)

        # 只保留当前局中有下注且达阈值的玩家
        filtered_players = {
            pid: simulated_players[pid]
            for pid, bets in current_bets.items()
            if sum(bets.values()) >= MINIMUM_BET_THRESHOLD
        }
        std_value, std_details = calculate_weighted_std(filtered_players, return_details=True)

        results.append({
            "winning_areas": winning_areas,
            "std": std_value,
            "weight": weight,
            "within_confidence": rtp_std_low <= std_value <= rtp_std_high
        })

        std_analysis_data.append({
            "winning_areas": winning_areas,
            "std": std_value,
            "details": std_details
        })

    filtered = [r for r in results if r["within_confidence"]]
    round_num = len(std_history) + 1
    std_bounds = (rtp_std_low, rtp_std_high)

    if filtered:
        total_weight = sum(r["weight"] for r in filtered)
        pick = random.uniform(0, total_weight)
        current = 0
        for r in filtered:
            current += r["weight"]
            if current >= pick:
                std_history.append(r["std"])
                return {
                    **r,
                    "round_id": round_num,
                    "all_structures": results,
                    "std_bounds": std_bounds,
                    "std_analysis": std_analysis_data,
                    "sample_size": len(eligible_players)
                }
    else:
        # 优先从返奖率小于100%的结构中选择最接近目标STD的结构
        loss_only = []
        for r in results:
            payout = 0
            for pid, bets in current_bets.items():
                payout += sum(amount * PAYOUT_RATES[area] for area, amount in bets.items() if area in r['winning_areas'])
            total_bet = sum(sum(bets.values()) for bets in current_bets.values())
            rtp = payout / total_bet if total_bet > 0 else 0
            if rtp < 1.0:
                loss_only.append((abs(r['std'] - BASE_STD), r))
        if loss_only:
            _, best = min(loss_only, key=lambda x: x[0])
        else:
            best = min(results, key=lambda x: abs(x['std'] - BASE_STD))
        std_history.append(best['std'])
        return {
            **best,
            "round_id": round_num,
            "all_structures": results,
            "std_bounds": std_bounds,
            "std_analysis": std_analysis_data,
            "sample_size": len(eligible_players)
        }
        std_history.append(best["std"])
        return {
            **best,
            "round_id": round_num,
            "all_structures": results,
            "std_bounds": std_bounds,
            "std_analysis": std_analysis_data,
            "sample_size": len(eligible_players)
        }
