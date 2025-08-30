import matplotlib.pyplot as plt
from .env_definition import PricingEnv
from .qlearning_agent import QLearningAgent

def train_agent(product_info, episodes=200):
    """
    Q-learning ajanını belirtilen ürün bilgisi ile eğitir ve Q-tablosunu kaydeder.
    """
    # Ortam ve ajanı başlat
    env = PricingEnv(product_info)
    agent = QLearningAgent(env.action_space)

    rewards = []

    for ep in range(episodes):
        state_vec = env.reset()
        state = {
            "stock_level": state_vec[0],
            "last_price": state_vec[1],
            "competitor_price": state_vec[2],
            "sales_last_week": state_vec[3]
        }
        total_reward = 0
        done = False

        while not done:
            action = agent.choose_action(state)
            next_vec, reward, done, _ = env.step(action)
            next_state = {
                "stock_level": next_vec[0],
                "last_price": next_vec[1],
                "competitor_price": next_vec[2],
                "sales_last_week": next_vec[3]
            }
            agent.learn(state, action, reward, next_state)
            state = next_state
            total_reward += reward

        rewards.append(total_reward)

    # Q-table kaydet
    agent.save_q_table("data/q_table.pkl")

    # Eğitim sonrası ödül grafiği
    plt.figure(figsize=(10, 5))
    plt.plot(rewards, label="Toplam Ödül")
    plt.title("Eğitim Süreci")
    plt.xlabel("Episode")
    plt.ylabel("Ödül")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    return agent
