# backend/api/retrain_api.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import io, csv

from backend.core.rl.qlearning_agent import QLearningAgent
from backend.core.rl.env_definition import EnhancedPricingEnv
from backend.core.rules_guard import CostParams, breakdown

router = APIRouter(prefix="/agent", tags=["Training & Tools"])

class TrainRow(BaseModel):
    stock_level: float
    last_price: float
    competitor_price: float
    sales_last_week: float

class TrainConfig(BaseModel):
    episodes: int = 40
    alpha: float = 0.2
    gamma: float = 0.92
    epsilon_start: float = 0.3
    epsilon_end: float = 0.05
    holding_cost_per_unit: float = 0.2
    min_margin_pct: float = 0.10
    elasticity: float = -1.2
    seasonality: float = 1.0
    # default maliyet (satırlarda yoksa kullanılacak)
    unit_cost: float = 60.0
    commission_pct: float = 0.12
    payment_fee_pct: float = 0.02
    tax_pct: float = 0.00
    shipping_cost: float = 25.0
    packaging_cost: float = 3.0
    other_fixed_cost: float = 0.0

class RetrainRequest(BaseModel):
    data: List[TrainRow]
    config: Optional[TrainConfig] = None

def _costs_from_cfg(cfg: TrainConfig):
    base_cp = CostParams(
        unit_cost=cfg.unit_cost,
        commission_pct=cfg.commission_pct,
        payment_fee_pct=cfg.payment_fee_pct,
        tax_pct=cfg.tax_pct,
        shipping_cost=cfg.shipping_cost,
        packaging_cost=cfg.packaging_cost,
        other_fixed_cost=cfg.other_fixed_cost,
        min_margin_pct=cfg.min_margin_pct,
    )
    return base_cp

@router.post("/retrain")
def retrain(req: RetrainRequest):
    cfg = req.config or TrainConfig()
    env = EnhancedPricingEnv(
        holding_cost_per_unit=cfg.holding_cost_per_unit,
        min_margin_pct=cfg.min_margin_pct,
        elasticity=cfg.elasticity,
        seasonality=cfg.seasonality,
    )
    # mevcut global ajanı al
    from backend.api.agent_api import agent as GLOBAL_AGENT

    # ajan hiperparametre güncelle
    GLOBAL_AGENT.alpha = cfg.alpha
    GLOBAL_AGENT.gamma = cfg.gamma

    base_cp = _costs_from_cfg(cfg)
    def cp_fn(_s): return base_cp

    # eğitim
    trajectories = [r.model_dump() for r in req.data]
    GLOBAL_AGENT.fit(env, trajectories, cp_fn,
                     episodes=cfg.episodes,
                     epsilon_start=cfg.epsilon_start,
                     epsilon_end=cfg.epsilon_end)

    # kaydet
    GLOBAL_AGENT.save_q_table("backend/data/q_table.pkl")

    return {
        "status":"ok",
        "q_states": len(GLOBAL_AGENT.q_table),
        "alpha": GLOBAL_AGENT.alpha,
        "gamma": GLOBAL_AGENT.gamma,
        "epsilon": GLOBAL_AGENT.epsilon
    }

class CurveCosts(BaseModel):
    unit_cost: float = 60.0
    commission_pct: float = 0.12
    payment_fee_pct: float = 0.02
    tax_pct: float = 0.00
    shipping_cost: float = 25.0
    packaging_cost: float = 3.0
    other_fixed_cost: float = 0.0
    min_margin_pct: float = 0.10

class CurveRequest(BaseModel):
    base_price: float
    competitor_price: float
    base_sales: float = 12
    costs: CurveCosts
    pct_min: int = -20
    pct_max: int = 20
    step: int = 1
    apply_guard: bool = True

@router.post("/simulate-curve")
def simulate_curve(req: CurveRequest):
    labels = list(range(req.pct_min, req.pct_max+1, req.step))
    cp = CostParams(**req.costs.model_dump())
    out = {"labels": labels, "net_profit": [], "margin_pct": [], "guard": []}

    for pct in labels:
        price = max(0.01, req.base_price * (1 + pct/100))
        brk = breakdown(price, cp)
        out["net_profit"].append(round(brk["net_profit"] * req.base_sales, 2))
        out["margin_pct"].append(round(brk["margin_pct"]*100, 2))
        out["guard"].append({
            "break_even": round(req.base_price*(1+0),2),  # sade placeholder
            "min_margin_price": round(
                price if brk["margin_pct"] >= cp.min_margin_pct else
                price / max(1e-9, brk["margin_pct"]) * cp.min_margin_pct, 2)
        })
    return out
