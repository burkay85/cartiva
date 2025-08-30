# backend/core/rl/env_definition.py
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
from backend.core.rules_guard import CostParams, breakdown, target_price_for_margin
from backend.core.rl.demand_simulator import predict_sales

@dataclass
class ProductInfo:
    base_price: float = 100.0
    unit_cost: float = 60.0

class PricingEnv:
    """
    Mevcut basit ortam (geri uyum için).
    """
    def __init__(self, product_info: Dict[str, float]):
        self.product_info = product_info
        self.action_space = [-0.05, 0.0, 0.05]  # % değişim
    # ... (var olan minimal tanımın kalsın)

class EnhancedPricingEnv:
    """
    Genişletilmiş RL ortamı:
    - Aksiyon uzayı: [-10, -5, 0, +5, +10] %
    - Ödül: (tahmini satış * birim net kâr) - stok elde tutma cezası - min marj ihlali cezası
    """
    def __init__(self,
                 holding_cost_per_unit: float = 0.2,
                 min_margin_pct: float = 0.10,
                 elasticity: float = -1.2,
                 seasonality: float = 1.0):
        self.action_space = [-0.10, -0.05, 0.0, 0.05, 0.10]
        self.holding_cost_per_unit = holding_cost_per_unit
        self.min_margin_pct = min_margin_pct
        self.elasticity = elasticity
        self.seasonality = seasonality

    def step(self, state: Dict[str, float], costs: CostParams, action_idx: int) -> Tuple[Dict[str, float], float]:
        """
        state: {stock_level, last_price, competitor_price, sales_last_week}
        """
        a = self.action_space[action_idx]
        new_price = round(state["last_price"] * (1 + a), 2)

        # Talep simülasyonu (rakip fiyatı referans)
        est_sales = predict_sales(
            base_sales=max(0.0, state.get("sales_last_week", 0.0)),
            price=new_price,
            competitor_price=state["competitor_price"],
            elasticity=self.elasticity,
            seasonality=self.seasonality
        )

        # Net kâr / marj (birim)
        brk = breakdown(new_price, costs)
        unit_net = brk["net_profit"]               # birim net kâr (TL)
        unit_margin = brk["margin_pct"]            # 0-1
        total_profit = unit_net * est_sales

        # Cezalar
        holding_pen = self.holding_cost_per_unit * max(0.0, state["stock_level"] - est_sales)
        guard_pen = 0.0
        if unit_margin < self.min_margin_pct:
            # min marj altını caydır
            guard_pen = (self.min_margin_pct - unit_margin) * 50.0 * (1.0 + est_sales/10.0)

        reward = total_profit - holding_pen - guard_pen

        # Sonraki durum (basit stok akışı)
        next_state = {
            "stock_level": max(0.0, state["stock_level"] - est_sales),
            "last_price": new_price,
            "competitor_price": state["competitor_price"],
            "sales_last_week": est_sales
        }
        return next_state, float(reward)
