# backend/core/rl/demand_simulator.py
import math

def predict_sales(base_sales: float,
                  price: float,
                  competitor_price: float,
                  elasticity: float = -1.2,
                  seasonality: float = 1.0) -> float:
    """
    Basit sabit esneklikli talep modeli.
    price/competitor_price oranına göre talep = base_sales * (rel ** elasticity) * seasonality
    """
    try:
        base = float(base_sales) if base_sales is not None else 10.0
    except Exception:
        base = 10.0

    price = max(0.01, float(price))
    comp  = max(0.01, float(competitor_price))

    rel = price / comp
    demand = base * (rel ** float(elasticity)) * float(seasonality)
    return max(0.0, float(demand))
