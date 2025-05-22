import random
from config import PAYOUT_RATES

AREAS = list(PAYOUT_RATES.keys())

def generate_bets(player_ids):
    # 随机决定本轮参与下注的玩家数量：3~50人之间
    num_active = random.randint(3, min(20, len(player_ids)))
    active_players = random.sample(player_ids, num_active)

    current_bets = {}
    for pid in active_players:
        area_count = random.choices(range(0, 9), weights=[20, 8, 7, 6, 5, 4, 3, 2, 1], k=1)[0]
        selected = random.sample(AREAS, area_count)
        total_amount = random.randint(200, 1200)
        weights = [1 / PAYOUT_RATES[a] for a in selected]
        total_weight = sum(weights)
        proportions = [w / total_weight for w in weights]
        current_bets[pid] = {a: max(1, int(total_amount * p)) for a, p in zip(selected, proportions)}

    return current_bets
