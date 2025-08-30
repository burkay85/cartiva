# backend/core/rl/demand_simulator.py
import math

def predict_sales(base_sales: float,
                  price: float,
                  competitor_price: float,
                  elasticity: float = -1.2,
                  seasonality: float = 1.0) -> float:
    """
    Basit sabit esneklikli talep modeli.
    rel = price / competitor_price; talep ~ rel ** elasticity
    """
    base_sales = base_sales if base_sales is not None else 10.0
    competitor_price = max(0.01, competitor_price)
    rel = price / competitor_price
    demand = base_sales * (rel ** elasticity) * seasonality
    return max(0.0, float(demand))
