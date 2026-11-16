"""
NIFTY 500 Semi-Annual Universe Refresh Script
Connects to NSE Archives to download the latest ind_nifty500list.csv and updates
backend/data/nifty500_metadata.json. Falls back gracefully to the bundled master builder
if NSE denies automated HTTP traffic.
"""

import os
import sys
import csv
import json
import io

def refresh_nifty500():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    target_path = os.path.join(project_root, "backend", "data", "nifty500_metadata.json")
    
    csv_url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    print(f"Connecting to NSE Archives: {csv_url}...")
    content = None
    
    try:
        import requests
        import urllib3
        urllib3.disable_warnings()
        session = requests.Session()
        session.headers.update(headers)
        # Attempt handshake
        session.get("https://www.nseindia.com", timeout=10, verify=False)
        res = session.get(csv_url, timeout=10, verify=False)
        if res.status_code == 200 and len(res.content) > 1000:
            content = res.content.decode("utf-8", errors="ignore")
            print(f"Successfully downloaded latest NIFTY 500 CSV ({len(content)} characters).")
    except Exception as e:
        print(f"NSE download attempt notice: {e}")

    if not content:
        print("Using bundled high-fidelity generator to refresh universe...")
        from scripts.build_nifty500 import generate_nifty500_universe
        count = generate_nifty500_universe()
        print(f"Refreshed offline NIFTY 500 universe with {count} equities.")
        return

    # Parse CSV content
    reader = csv.DictReader(io.StringIO(content))
    universe = []
    seen = set()
    
    for row in reader:
        symbol = (row.get("Symbol") or row.get("symbol") or "").strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        name = (row.get("Company Name") or row.get("company_name") or symbol).strip()
        industry = (row.get("Industry") or row.get("industry") or "Diversified").strip()
        isin = (row.get("ISIN Code") or "").strip()
        
        # Sector derivation
        sector = "Diversified"
        ind_lower = industry.lower()
        if any(w in ind_lower for w in ["bank", "financial", "insurance", "capital markets", "nbfc"]):
            sector = "Financials"
        elif any(w in ind_lower for w in ["information tech", "software", "computer"]):
            sector = "IT Services"
        elif any(w in ind_lower for w in ["power", "utility", "gas", "electricity"]):
            sector = "Utilities"
        elif any(w in ind_lower for w in ["oil", "petroleum", "energy", "fuel"]):
            sector = "Energy"
        elif any(w in ind_lower for w in ["pharma", "health", "hospital", "biotech"]):
            sector = "Healthcare"
        elif any(w in ind_lower for w in ["auto", "vehicle", "tyre"]):
            sector = "Automotive"
        elif any(w in ind_lower for w in ["metal", "steel", "mining", "aluminium"]):
            sector = "Metals & Mining"
        elif any(w in ind_lower for w in ["defense", "ship", "aerospace"]):
            sector = "Defense"
        elif any(w in ind_lower for w in ["telecom"]):
            sector = "Telecom"
        elif any(w in ind_lower for w in ["fmcg", "consumer goods", "food", "beverage"]):
            sector = "FMCG"
        elif any(w in ind_lower for w in ["realty", "real estate", "housing"]):
            sector = "Real Estate"
        elif any(w in ind_lower for w in ["chemical", "fertilizer"]):
            sector = "Materials"
        elif any(w in ind_lower for w in ["rail"]):
            sector = "Railways"

        universe.append({
            "symbol": symbol,
            "company_name": name,
            "industry": industry,
            "sector": sector,
            "cap_tier": "Mid Cap" if len(universe) > 100 else "Large Cap",
            "ticker": f"{symbol}.NS",
            "isin": isin,
            "baseline_beta": 1.0,
            "baseline_volatility": 0.25,
            "keywords": [symbol.lower(), name.lower(), industry.lower(), sector.lower()]
        })

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(universe, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated {len(universe)} equities into {target_path}")

if __name__ == "__main__":
    refresh_nifty500()
