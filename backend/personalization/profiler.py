from typing import Dict, Any, List

class UserProfiler:
    """
    Manages user financial psychology, risk scoring, panic selling tendency,
    and portfolio constraint profiles.
    """

    DEFAULT_PROFILES = {
        "conservative": {
            "risk_level": "conservative",
            "investment_horizon": "medium",
            "panic_sell_tendency": 0.8,
            "max_portfolio_beta": 1.0,
            "max_single_stock_pct": 8.0,
            "max_tech_sector_pct": 40.0,
            "preferred_sectors": ["Energy", "Tech", "Consumer"],
            "portfolio_cash": 250000
        },
        "moderate": {
            "risk_level": "moderate",
            "investment_horizon": "long",
            "panic_sell_tendency": 0.45,
            "max_portfolio_beta": 1.25,
            "max_single_stock_pct": 15.0,
            "max_tech_sector_pct": 55.0,
            "preferred_sectors": ["Tech", "Energy", "Healthcare"],
            "portfolio_cash": 200000
        },
        "aggressive": {
            "risk_level": "aggressive",
            "investment_horizon": "long",
            "panic_sell_tendency": 0.2,
            "max_portfolio_beta": 1.6,
            "max_single_stock_pct": 25.0,
            "max_tech_sector_pct": 75.0,
            "preferred_sectors": ["Tech", "Semiconductors", "Green Energy"],
            "portfolio_cash": 150000
        }
    }

    def get_profile(self, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        if not user_profile:
            return self.DEFAULT_PROFILES["conservative"]

        risk_level = user_profile.get("risk_level", "conservative").lower()
        base = self.DEFAULT_PROFILES.get(risk_level, self.DEFAULT_PROFILES["conservative"]).copy()
        
        # Override with any custom values
        for k, v in user_profile.items():
            if v is not None:
                base[k] = v

        return base

user_profiler = UserProfiler()
