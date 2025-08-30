from backend.core.rl.qlearning_agent import QLearningAgent
from backend.core.rl.env_definition import PricingEnv

def test_agent_learning():
    env = PricingEnv({"base_price":50,"unit_cost":20})
    agent = QLearningAgent(env.action_space)
    state = {"stock_level":100,"last_price":50,"competitor_price":55,"sales_last_week":10}
    next_state, reward, done, _ = env.step(1)
    agent.learn(state, 1, reward, next_state)
    assert len(agent.q_table) > 0
