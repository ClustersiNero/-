import matplotlib.pyplot as plt

def plot_rtp_trends(rtp_history):
    plt.figure()
    for pid, rtp_list in rtp_history.items():
        plt.plot(rtp_list, alpha=0.3)
    plt.title("玩家 RTP 趋势")
    plt.xlabel("Round")
    plt.ylabel("RTP")
    plt.grid(True)
    plt.savefig("results/rtp_trend_all_players.png")

def plot_platform_profit(profit_list):
    cumulative = [sum(profit_list[:i+1]) for i in range(len(profit_list))]
    plt.figure()
    plt.plot(cumulative, label="平台累计盈亏")
    plt.xlabel("Round")
    plt.ylabel("Profit")
    plt.title("平台盈亏趋势")
    plt.grid(True)
    plt.savefig("results/platform_profit_trend.png")
