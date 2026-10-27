from typing import Dict, Any, List
try:
    from .profiler import user_profiler
except (ImportError, ValueError):
    from personalization.profiler import user_profiler

class PortfolioService:
    """
    Manages current portfolio holdings, risk heatmap computation,
    and trade impact simulations with behavioral nudge warnings.
    """

    def __init__(self):
        # Base realistic portfolio holdings
        self.default_holdings = [
            {
                "ticker": "RELIANCE",
                "company_name": "Reliance Industries Ltd.",
                "shares": 50,
                "avg_cost": 2720.00,
                "current_price": 2845.50,
                "market_value": 142275.0,
                "pnl_percent": 4.61,
                "sector": "Energy",
                "beta": 0.88,
                "weight_pct": 28.5
            },
            {
                "ticker": "TCS",
                "company_name": "Tata Consultancy Services Ltd.",
                "shares": 30,
                "avg_cost": 3850.00,
                "current_price": 3915.00,
                "market_value": 117450.0,
                "pnl_percent": 1.69,
                "sector": "Tech",
                "beta": 0.72,
                "weight_pct": 23.5
            },
            {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "shares": 35,
                "avg_cost": 215.00,
                "current_price": 234.50,
                "market_value": 68450.0, # normalized INR equivalent approx
                "pnl_percent": 9.07,
                "sector": "Tech",
                "beta": 1.05,
                "weight_pct": 28.5
            },
            {
                "ticker": "HDFCBANK",
                "company_name": "HDFC Bank Ltd.",
                "shares": 40,
                "avg_cost": 1640.00,
                "current_price": 1695.00,
                "market_value": 67800.0,
                "pnl_percent": 3.35,
                "sector": "Financials",
                "beta": 0.92,
                "weight_pct": 19.5
            }
        ]

    def get_portfolio(self) -> Dict[str, Any]:
        holdings = self.default_holdings
        total_market_value = sum(h["market_value"] for h in holdings)
        cash = 104025.0
        total_portfolio_value = total_market_value + cash

        # Calculate exact sector percentages
        sector_totals: Dict[str, float] = {}
        weighted_beta_sum = 0.0

        for h in holdings:
            sector = h["sector"]
            val = h["market_value"]
            sector_totals[sector] = sector_totals.get(sector, 0.0) + val
            weighted_beta_sum += h["beta"] * val

        portfolio_beta = round(weighted_beta_sum / total_market_value, 2) if total_market_value > 0 else 1.0

        sector_allocations = []
        for sec, val in sector_totals.items():
            pct = round((val / total_portfolio_value) * 100, 1)
            sector_allocations.append({
                "sector": sec,
                "value": round(val, 2),
                "allocation_pct": pct
            })
        
        cash_pct = round((cash / total_portfolio_value) * 100, 1)
        sector_allocations.append({
            "sector": "Cash",
            "value": cash,
            "allocation_pct": cash_pct
        })

        # Dynamic concentration heatmap
        concentration_heatmap = []
        for alloc in sector_allocations:
            if alloc["sector"] == "Cash":
                continue
            sec_name = alloc["sector"]
            pct = alloc["allocation_pct"]
            thresh = 40.0 if sec_name == "Tech" else (30.0 if sec_name == "Energy" else 25.0)
            risk_lvl = "HIGH" if pct > thresh else ("MODERATE" if pct > (thresh * 0.7) else "LOW")
            concentration_heatmap.append({
                "name": f"{sec_name} Sector",
                "concentration_pct": pct,
                "risk_level": risk_lvl,
                "threshold_pct": thresh
            })
        
        # Single stock max concentration
        if holdings:
            max_h = max(holdings, key=lambda h: h["market_value"])
            max_stock_pct = round((max_h["market_value"] / total_portfolio_value) * 100, 1)
            concentration_heatmap.append({
                "name": f"Single Stock Max ({max_h['ticker']})",
                "concentration_pct": max_stock_pct,
                "risk_level": "HIGH" if max_stock_pct > 20.0 else ("MODERATE" if max_stock_pct > 12.0 else "LOW"),
                "threshold_pct": 15.0
            })

        return {
            "total_value": round(total_portfolio_value, 2),
            "invested_value": round(total_market_value, 2),
            "cash": cash,
            "portfolio_beta": portfolio_beta,
            "holdings": holdings,
            "sector_allocations": sector_allocations,
            "concentration_heatmap": concentration_heatmap
        }

    def simulate_trade(self, trade_req: Dict[str, Any]) -> Dict[str, Any]:
        ticker = trade_req.get("ticker", "TSLA").upper()
        action = trade_req.get("action", "BUY").upper()
        quantity = max(1, int(trade_req.get("quantity", 10)))
        price = max(0.01, float(trade_req.get("price", 240.0)))
        user_prof = trade_req.get("user_profile") or {}
        risk_level = user_prof.get("risk_level", "conservative")
        if risk_level:
            risk_level = risk_level.lower()
        else:
            risk_level = "conservative"

        # Check stock risk profile
        stock_betas = {
            "TSLA": 2.05,
            "NVDA": 1.75,
            "RELIANCE": 0.88,
            "TCS": 0.72,
            "INFY": 0.85,
            "AAPL": 1.05
        }
        stock_volatilities = {
            "TSLA": 52,
            "NVDA": 46,
            "RELIANCE": 22,
            "TCS": 18,
            "INFY": 24,
            "AAPL": 21
        }
        stock_sectors = {
            "TSLA": "Tech",
            "NVDA": "Tech",
            "AAPL": "Tech",
            "INFY": "Tech",
            "TCS": "Tech",
            "RELIANCE": "Energy"
        }

        beta = stock_betas.get(ticker, 1.20)
        vol = stock_volatilities.get(ticker, 28)
        sector = stock_sectors.get(ticker, "Tech")

        # Dynamic portfolio baseline
        portfolio_state = self.get_portfolio()
        current_total = portfolio_state["total_value"]
        current_invested = portfolio_state["invested_value"]
        current_beta = portfolio_state["portfolio_beta"]

        tech_alloc = next((s for s in portfolio_state["sector_allocations"] if s["sector"] == "Tech"), None)
        current_tech_pct = tech_alloc["allocation_pct"] if tech_alloc else 46.5
        current_tech_val = tech_alloc["value"] if tech_alloc else (current_total * current_tech_pct / 100.0)

        # Multi-currency normalization (USD equities converted to INR base portfolio)
        usd_to_inr = 83.5
        is_usd = ticker in ["TSLA", "NVDA", "AAPL"]
        trade_amount = quantity * price * (usd_to_inr if is_usd else 1.0)

        if action == "BUY":
            new_total = current_total + trade_amount
            new_invested = current_invested + trade_amount
            new_tech_val = (current_tech_val + trade_amount) if sector == "Tech" else current_tech_val
            projected_tech_pct = round((new_tech_val / new_total) * 100, 1)
            projected_beta = round(((current_invested * current_beta) + (trade_amount * beta)) / new_invested, 2)
        else: # SELL
            new_total = max(1.0, current_total - trade_amount)
            new_invested = max(1.0, current_invested - trade_amount)
            new_tech_val = max(0.0, current_tech_val - trade_amount) if sector == "Tech" else current_tech_val
            projected_tech_pct = round((new_tech_val / new_total) * 100, 1)
            projected_beta = round(max(0.4, current_beta - ((beta - current_beta) * 0.15)), 2)

        # Evaluate if nudge warning triggers
        warning_triggered = False
        nudge_message = ""
        suggested_alternative = ""

        if risk_level == "conservative" and (beta > 1.2 or vol > 35 or projected_tech_pct > 50.0):
            warning_triggered = True
            nudge_message = (
                f"Hold on! Your profile is Conservative, but {ticker} has an annualized volatility of {vol}% "
                f"and the Fundamental Agent notes elevated risk. Adding this will increase your portfolio "
                f"Tech concentration to {projected_tech_pct}% and portfolio beta to {projected_beta}."
            )
            suggested_alternative = "Consider an index ETF or low-beta blue chip like TCS."
        elif risk_level == "moderate" and (beta > 1.8 or projected_tech_pct > 65.0):
            warning_triggered = True
            nudge_message = (
                f"Careful: Purchasing {quantity} shares of {ticker} raises Tech concentration to {projected_tech_pct}%, "
                f"approaching your maximum risk threshold."
            )
            suggested_alternative = "Consider staggering purchases in 3 tranches to average volatility."
        else:
            warning_triggered = False
            nudge_message = f"Trade size is well-aligned with your {risk_level} profile and portfolio boundaries."
            suggested_alternative = "Proceed with scheduled limit orders."

        return {
            "warning_triggered": warning_triggered,
            "nudge_message": nudge_message,
            "portfolio_delta": {
                "current_tech_pct": current_tech_pct,
                "projected_tech_pct": projected_tech_pct,
                "current_beta": current_beta,
                "projected_beta": projected_beta
            },
            "suggested_alternative": suggested_alternative
        }

portfolio_service = PortfolioService()
