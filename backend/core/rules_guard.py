# backend/core/rules_guard.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class CostParams:
    unit_cost: float = 60.0                # Alış maliyeti
    commission_pct: float = 0.12           # Pazaryeri komisyonu (örn: %12)
    payment_fee_pct: float = 0.02          # Ödeme altyapısı (örn: %2)
    tax_pct: float = 0.00                  # Vergi kesintisi (fiyattan %)
    shipping_cost: float = 25.0            # Kargo (sabit TL)
    packaging_cost: float = 3.0            # Paketleme (sabit TL)
    other_fixed_cost: float = 0.0          # Diğer sabit giderler (TL)
    min_margin_pct: float = 0.10           # En az kâr marjı hedefi (ör: %10)

def _pct_total(cp: CostParams) -> float:
    """Fiyattan düşülecek tüm yüzdesel giderlerin toplamı."""
    return max(0.0, min(0.95, cp.commission_pct + cp.payment_fee_pct + cp.tax_pct))

def _fixed_total(cp: CostParams) -> float:
    """Sabit giderlerin toplamı (TL)."""
    return max(0.0, cp.shipping_cost + cp.packaging_cost + cp.other_fixed_cost)

def profit(price: float, cp: CostParams) -> float:
    """Net kâr (TL)."""
    pct = _pct_total(cp)
    fixed = _fixed_total(cp)
    return price * (1 - pct) - cp.unit_cost - fixed

def margin_pct(price: float, cp: CostParams) -> float:
    """Kâr marjı (kâr/fiyat)."""
    if price <= 0: return -1.0
    return profit(price, cp) / price

def break_even_price(cp: CostParams) -> float:
    """Kâra sıfır geçiş fiyatı."""
    pct = _pct_total(cp)
    denom = (1 - pct)
    if denom <= 0.000001:
        return float("inf")
    return (cp.unit_cost + _fixed_total(cp)) / denom

def target_price_for_margin(cp: CostParams, target_margin_pct: float) -> float:
    """
    Hedef marj (kâr/fiyat) için gereken fiyat.
    price * ((1 - pct_total) - target_margin) = unit_cost + fixed
    """
    pct = _pct_total(cp)
    denom = (1 - pct) - target_margin_pct
    if denom <= 0.000001:
        return float("inf")
    return (cp.unit_cost + _fixed_total(cp)) / denom

def breakdown(price: float, cp: CostParams) -> Dict:
    """Fiyat için ayrıntılı gider/kâr dökümü."""
    pct = _pct_total(cp)
    fixed = _fixed_total(cp)
    net = profit(price, cp)
    return {
        "price": price,
        "percentage_fees_total_pct": pct,
        "fixed_fees_total": fixed,
        "unit_cost": cp.unit_cost,
        "net_profit": net,
        "margin_pct": margin_pct(price, cp),
        "components": {
            "commission_pct": cp.commission_pct,
            "payment_fee_pct": cp.payment_fee_pct,
            "tax_pct": cp.tax_pct,
            "shipping_cost": cp.shipping_cost,
            "packaging_cost": cp.packaging_cost,
            "other_fixed_cost": cp.other_fixed_cost,
        }
    }
