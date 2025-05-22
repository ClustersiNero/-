# config.py

# 赔率配置
PAYOUT_RATES = {
    1: 5,
    2: 5,
    3: 5,
    4: 5,
    5: 10,
    6: 15,
    7: 25,
    8: 45,
}

# 中奖结构
WINNING_STRUCTURES = [
    {"areas": [1], "weight": 1930},
    {"areas": [2], "weight": 1930},
    {"areas": [3], "weight": 1930},
    {"areas": [4], "weight": 1930},
    {"areas": [5], "weight": 965},
    {"areas": [6], "weight": 640},
    {"areas": [7], "weight": 390},
    {"areas": [8], "weight": 215},
    {"areas": [1, 2, 3, 4], "weight": 60},
    {"areas": [5, 6, 7, 8], "weight": 10},
]

# 控制参数
STD_THRESHOLD = 0.15
CONFIDENCE_LEVEL = 0.95
MINIMUM_BET_THRESHOLD = 500  
TARGET_RTP = 0.995