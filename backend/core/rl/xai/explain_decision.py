def explain_action(state: dict, q_values: list):
    action = int(q_values.index(max(q_values)))
    reasons = {
        0: "Stok fazlası veya talep düşük → fiyat düşürmek mantıklı.",
        1: "Durum stabil → fiyatı koru.",
        2: "Talep yüksek veya rekabet zayıf → fiyat artırmak kârlı."
    }
    return reasons.get(action, "Karar açıklanamıyor.")
