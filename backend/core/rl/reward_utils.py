def compute_profit_reward(price, cost, sales):
    """
    Basit kâr tabanlı ödül fonksiyonu
    """
    return (price - cost) * sales


def compute_kpi_weighted_reward(price, cost, sales, kpi_weights=None):
    """
    Genişletilmiş KPI ağırlıklı ödül:
    - Kâr
    - Ciro (revenue)
    - Satış hacmi
    - Stok tüketimi cezası (opsiyonel)
    """
    if kpi_weights is None:
        kpi_weights = {
            "profit": 0.6,
            "revenue": 0.3,
            "volume": 0.1
        }

    profit = (price - cost) * sales
    revenue = price * sales
    volume = sales

    reward = (
        kpi_weights["profit"] * profit +
        kpi_weights["revenue"] * revenue +
        kpi_weights["volume"] * volume
    )
    return reward
