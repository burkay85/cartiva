def analyze_competitors(competitor_data):
    prices = [c["price"] for c in competitor_data if "price" in c]
    if not prices:
        return 0
    return sum(prices) / len(prices)
