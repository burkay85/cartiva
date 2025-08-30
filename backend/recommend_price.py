from backend.demand_forecast import forecast_demand
from backend.cps_score import analyze_competitors
from backend.rules_guard import apply_pricing_rules

def recommend_price_for_sku(sku_id, current_price, cost, sales_history, competitor_data, stock):
    avg_sales = forecast_demand(sales_history)
    avg_competitor_price = analyze_competitors(competitor_data)
    recommended_price = apply_pricing_rules(current_price, cost, avg_sales, avg_competitor_price, stock)
    return recommended_price
