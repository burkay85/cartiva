# backend/core/rl/qlearning_agent.py
import random
import math
import pickle
from typing import Dict, Any, List, Tuple

class QLearningAgent:
    def __init__(self, action_space: List[float], alpha=0.2, gamma=0.92, epsilon=0.1):
        self.action_space = action_space
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table: Dict[str, List[float]] = {}

    def get_state_key(self, s: Dict[str, float]) -> str:
        # kaba ayrıklaştırma: (stok/20), (fiyat/5), (rakip/5), (satış/5)
        def binv(x, w): 
            try: return int(float(x) // w)
            except: return 0
        return f"{binv(s.get('stock_level',0),20)}|{binv(s.get('last_price',0),5)}|{binv(s.get('competitor_price',0),5)}|{binv(s.get('sales_last_week',0),5)}"

    def _ensure_state(self, key: str):
        if key not in self.q_table:
            self.q_table[key] = [0.0 for _ in self.action_space]

    def choose_action(self, state: Dict[str, float], explore: bool = True) -> int:
        key = self.get_state_key(state)
        self._ensure_state(key)
        if explore and random.random() < self.epsilon:
            return random.randrange(len(self.action_space))
        qvals = self.q_table[key]
        return int(max(range(len(qvals)), key=lambda i: qvals[i]))

    def learn(self, s_key: str, a_idx: int, reward: float, s_next_key: str):
        self._ensure_state(s_key)
        self._ensure_state(s_next_key)
        best_next = max(self.q_table[s_next_key])
        td_target = reward + self.gamma * best_next
        td_error = td_target - self.q_table[s_key][a_idx]
        self.q_table[s_key][a_idx] += self.alpha * td_error

    def fit(self, env, trajectories: List[Tuple[Dict[str,float], Any]], costs, 
            episodes: int = 50, epsilon_start=0.3, epsilon_end=0.05):
        """
        trajectories: sadece başlangıç state’leri; env.step ile ilerliyoruz.
        costs: CostParams veya callable(state)->CostParams
        """
        self.epsilon = epsilon_start
        decay = (epsilon_start - epsilon_end) / max(1, episodes-1)
        for ep in range(episodes):
            for init_state in trajectories:
                s = dict(init_state)  # kopya
                for _ in range(24):   # her ep için 24 adım (ör. 24 hafta)
                    s_key = self.get_state_key(s)
                    a_idx = self.choose_action(s, explore=True)
                    cp = costs(s) if callable(costs) else costs
                    s_next, r = env.step(s, cp, a_idx)
                    s_next_key = self.get_state_key(s_next)
                    self.learn(s_key, a_idx, r, s_next_key)
                    s = s_next
            # epsilon decay
            self.epsilon = max(epsilon_end, self.epsilon - decay)

    def save_q_table(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, path: str):
        with open(path, "rb") as f:
            self.q_table = pickle.load(f)
