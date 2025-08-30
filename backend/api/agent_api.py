# backend/api/agent_api.py

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from backend.core.rl.qlearning_agent import QLearningAgent
from backend.core.rl.env_definition import PricingEnv
from backend.core.rl.xai.explain_decision import explain_action
from backend.core.rules_guard import (
    CostParams, break_even_price, target_price_for_margin, breakdown
)

# -------------------- FastAPI App (geliştirme için CORS açık) --------------------
app = FastAPI(title="Cognitive Pricing – Agent API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # DEV için açık; prod'da domain bazlı kısıtla
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/agent", tags=["Pricing Agent"])

# -------------------- Girdi Modelleri --------------------
class StateInput(BaseModel):
    stock_level: int = Field(ge=0)
    last_price: float = Field(gt=0)
    competitor_price: float = Field(gt=0)
    sales_last_week: int = Field(ge=0)

class CostInput(BaseModel):
    unit_cost: Optional[float] = 60.0
    commission_pct: Optional[float] = 0.12
    payment_fee_pct: Optional[float] = 0.02
    tax_pct: Optional[float] = 0.00
    shipping_cost: Optional[float] = 25.0
    packaging_cost: Optional[float] = 3.0
    other_fixed_cost: Optional[float] = 0.0
    min_margin_pct: Optional[float] = 0.10  # Margin Guard eşiği (örn. 0.10 => %10)

class RecommendRequest(BaseModel):
    state: StateInput
    costs: Optional[CostInput] = None

class SimulateRequest(BaseModel):
    price: float = Field(gt=0)
    costs: Optional[CostInput] = None
    apply_guard: bool = True

# -------------------- Ortam & Ajan --------------------
product_info = {"base_price": 100.0, "unit_cost": 60.0}
env = PricingEnv(product_info)
agent = QLearningAgent(action_space=env.action_space)
try:
    agent.load_q_table("backend/data/q_table.pkl")
except Exception:
    print("[!] Q tablosu bulunamadı: backend/data/q_table.pkl. Yeni tablo başlatılıyor.")

# -------------------- Fiyat Öneri Endpoint --------------------
@router.post("/recommend-price")
def recommend_price(req: RecommendRequest) -> Dict[str, Any]:
    # 1) RL kararı
    s = req.state.model_dump()
    action = agent.choose_action(s)           # 0: düşür, 1: koru, 2: artır
    rl_pct = [-0.05, 0.0, 0.05][action]
    rl_price = round(req.state.last_price * (1 + rl_pct), 2)

    # 2) Margin Guard
    ci = (req.costs or CostInput())
    cp = CostParams(**ci.model_dump())

    be_price = break_even_price(cp)
    guard_price = target_price_for_margin(cp, cp.min_margin_pct)  # min marj hedef fiyatı
    guard_applied = False

    final_price = rl_price
    if final_price < guard_price:
        final_price = round(guard_price, 2)
        guard_applied = True

    # 3) Döküm & XAI
    brk = breakdown(final_price, cp)  # brk["margin_pct"] => 0–1 arası
    state_key = agent.get_state_key(s)
    q_values = agent.q_table.get(state_key, [0, 0, 0])
    explanation = explain_action(s, q_values)
    if guard_applied:
        explanation += " | Margin Guard: En az kâr marjı sağlanmadığı için fiyat yukarı düzeltildi."

    # -------------------- v1.0 FRONTEND ŞEMASI --------------------
    response = {
        "recommended_price": round(final_price, 2),
        "guard": {
            "applied": guard_applied,
            "break_even": round(be_price, 2),
            "min_margin_price": round(guard_price, 2),
            "target_margin_price": round(guard_price, 2),
        },
        "profit": {
            "net_profit": round(brk["net_profit"], 2),
            "margin_pct": float(brk["margin_pct"]),  # 0–1 arası
        },
        "xai": explanation,
    }

    # ---- Geriye dönük uyumluluk ----
    response.update({
        "recommended_action": action,
        "rl_price_estimate": rl_price,
        "price_change_pct": (final_price / req.state.last_price) - 1.0,
        "new_price_estimate": round(final_price, 2),
        "breakdown": {
            "net_profit": round(brk["net_profit"], 2),
            "margin_pct": round(brk["margin_pct"] * 100, 2),
            "unit_cost": cp.unit_cost,
            "percentage_fees_total_pct": round(brk["percentage_fees_total_pct"] * 100, 2),
            "fixed_fees_total": brk["fixed_fees_total"],
            "components": brk["components"],
        },
        "guard_legacy": {
            "break_even_price": round(be_price, 2),
            "min_margin_pct": cp.min_margin_pct,
            "min_margin_target_price": round(guard_price, 2),
        }
    })

    return response

# -------------------- Senaryo Simülasyonu Endpoint --------------------
@router.post("/simulate")
def simulate_price(req: SimulateRequest) -> Dict[str, Any]:
    ci = (req.costs or CostInput())
    cp = CostParams(**ci.model_dump())

    be_price = break_even_price(cp)
    guard_price = target_price_for_margin(cp, cp.min_margin_pct)

    final_price = req.price
    guard_applied = False
    if req.apply_guard and final_price < guard_price:
        final_price = round(guard_price, 2)
        guard_applied = True

    brk = breakdown(final_price, cp)

    return {
        "input_price": req.price,
        "applied_price": round(final_price, 2),
        "guard": {
            "applied": guard_applied,
            "break_even": round(be_price, 2),
            "min_margin_price": round(guard_price, 2),
            "min_margin_pct": cp.min_margin_pct,
        },
        "profit": {
            "net_profit": round(brk["net_profit"], 2),
            "margin_pct": float(brk["margin_pct"]),  # 0–1
        }
    }
@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Cognitive Pricing Agent API",
        "endpoints": ["/agent/recommend-price", "/agent/simulate", "/docs"]
    }

# Router'ı app'e ekle
app.include_router(router)

# ...
from backend.api import retrain_api
app.include_router(retrain_api.router)
