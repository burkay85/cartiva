def explain_action(state, q_values):
    """
    Q-learning ajanının önerdiği aksiyon için sezgisel bir açıklama üretir.

    Args:
        state (dict): Ortamın mevcut durumu.
        q_values (list): Mevcut duruma ait Q-değerleri.

    Returns:
        str: Seçilen aksiyona dair açıklayıcı mesaj.
    """
    action = int(q_values.index(max(q_values)))

    stock = state.get("stock_level", 0)
    sales = state.get("sales_last_week", 0)
    price = state.get("last_price", 0)
    competitor = state.get("competitor_price", 0)

    # Geliştirilmiş mantıklı açıklamalar
    if action == 0:
        if stock > 100:
            return "📦 Stok seviyesi yüksek → satışları hızlandırmak için fiyatı düşürmek mantıklı."
        if sales < 10:
            return "📉 Son hafta satışlar düşüktü → fiyat indirimi ile talep artırılabilir."
        return "🔽 Genel piyasa koşulları fiyat düşürmeyi işaret ediyor."

    elif action == 1:
        if abs(price - competitor) < 5:
            return "⚖️ Fiyat rakiplerle uyumlu → şu an için fiyatı sabit tutmak uygun."
        return "⏸️ Büyük bir değişiklik gerekmiyor → dengeyi korumak için fiyat sabit kalmalı."

    elif action == 2:
        if sales > 30 and stock < 50:
            return "🔥 Talep yüksek ve stok sınırlı → fiyat artırmak kârlı olabilir."
        if competitor < price:
            return "🏆 Rekabet fiyat olarak geride → marjı artırmak için fiyat yükseltilebilir."
        return "🔼 Koşullar uygun → fiyat artışı düşünülebilir."

    return "❓ Karar açıklaması üretilemedi."
