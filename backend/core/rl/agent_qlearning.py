import random
import numpy as np
import pickle
from collections import defaultdict

class QLearningAgent:
    def __init__(self, action_space, learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        self.action_space = action_space
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: np.zeros(action_space.n))

    def get_state_key(self, state):
        """
        State'i hashlenebilir bir tuple'a çevir (basit discretization ile)
        """
        return (
            int(state["stock_level"] / 10),       # örn: 100 → 10
            int(state["last_price"]),
            int(state["competitor_price"]),
            int(state["sales_last_week"] / 5)
        )

    def choose_action(self, state):
        state_key = self.get_state_key(state)
        if random.random() < self.epsilon:
            return self.action_space.sample()  # Explore
        return int(np.argmax(self.q_table[state_key]))  # Exploit

    def learn(self, state, action, reward, next_state):
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)

        current_q = self.q_table[state_key][action]
        max_next_q = np.max(self.q_table[next_state_key])

        # Q-learning update rule
        new_q = current_q + self.lr * (reward + self.gamma * max_next_q - current_q)
        self.q_table[state_key][action] = new_q

    def save_q_table(self, filepath="data/q_table.pkl"):
        with open(filepath, "wb") as f:
            pickle.dump(dict(self.q_table), f)

    def load_q_table(self, filepath="data/q_table.pkl"):
        with open(filepath, "rb") as f:
            q_dict = pickle.load(f)
            self.q_table = defaultdict(lambda: np.zeros(self.action_space.n), q_dict)
