import math
from typing import Dict
from config import MINIMUM_BET_THRESHOLD, TARGET_RTP

class PlayerStats:
    def __init__(self):
        self.total_bet = 0
        self.total_return = 0

    def update(self, bet: float, payout: float):
        self.total_bet += bet
        self.total_return += payout

    def rtp(self):
        return self.total_return / self.total_bet if self.total_bet > 0 else 0

def calculate_weighted_std(players: Dict[str, PlayerStats], return_details=False):
    eligible = [(pid, p) for pid, p in players.items() if p.total_bet >= MINIMUM_BET_THRESHOLD]
    total_weight = sum(p.total_bet for _, p in eligible)
    if total_weight == 0:
        if return_details:
            return 0, {"players": [], "target_rtp": TARGET_RTP, "weighted_variance": 0}
        return 0

    weighted_variance = sum(
        p.total_bet * (p.rtp() - TARGET_RTP) ** 2
        for _, p in eligible
    ) / total_weight
    std = math.sqrt(weighted_variance)

    if return_details:
        details = {
            "players": [
                {
                    "id": pid,
                    "bet": p.total_bet,
                    "return": p.total_return,
                    "rtp": p.rtp(),
                    "weight": p.total_bet / total_weight
                }
                for pid, p in eligible
            ],
            "target_rtp": TARGET_RTP,
            "weighted_variance": weighted_variance
        }
        return std, details

    return std
