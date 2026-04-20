"""
data.py — Fetching dati da yfinance (Universe) e FMP (Watchlist)
Usa st.cache_data per evitare chiamate ripetute e rispettare i limiti API.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import streamlit as st
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import time

from utils.config import TICKER_MAP

FMP_BASE = "https://financialmodelingprep.com/api/v3"

# ══════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════

def get_fmp_key() -> str:
    try:
        return st.secrets.get("FMP_API_KEY", "")
    except Exception:
        return ""


def fmp_get(endpoint: str, params: dict = None) -> Optional[dict]:
    """Chiamata GET a FMP con gestione errori."""
    key = get_fmp_key()
    if not key:
        return None
    p = params or {}
    p["apikey"] = key
    try:
        r = requests.get(f"{FMP_BASE}/{endpoint}", params=p, timeout=15)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


# ══════════════════════════════════════════════
# LISTE TICKER INDICI
# ══════════════════════════════════════════════

@st.cache_data(ttl=86400, show_spinner=False)
def get_sp500_tickers() -> pd.DataFrame:
    """Scarica S&P 500 da Wikipedia con fallback hardcoded robusto."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers=headers, timeout=20
        )
        tables = pd.read_html(resp.text)
        for table in tables:
            sym_col = None
            for c in table.columns:
                if str(c).lower() in ["symbol", "ticker", "ticker symbol"]:
                    sym_col = c
                    break
            if sym_col is None:
                continue
            name_col = next((c for c in table.columns if any(k in str(c).lower() for k in ["security","name","company"])), None)
            sec_col  = next((c for c in table.columns if "sector" in str(c).lower()), None)
            tickers = table[sym_col].astype(str).str.replace(".", "-", regex=False).str.strip()
            mask = tickers.str.match(r'^[A-Z\-]{1,6}$')
            if mask.sum() < 100:
                continue
            result = pd.DataFrame()
            result["ticker"]  = tickers[mask].values
            result["nome"]    = table.loc[mask, name_col].astype(str).str.strip().values if name_col else tickers[mask].values
            result["settore"] = table.loc[mask, sec_col].astype(str).str.strip().values if sec_col else "N/A"
            if len(result) >= 100:
                return result.reset_index(drop=True)
    except Exception:
        pass
    # Fallback hardcoded top 100 S&P 500
    data = [
        ("AAPL","Apple Inc.","Technology"),("MSFT","Microsoft","Technology"),
        ("NVDA","NVIDIA","Technology"),("AMZN","Amazon","Consumer Discretionary"),
        ("GOOGL","Alphabet A","Technology"),("META","Meta Platforms","Technology"),
        ("TSLA","Tesla","Consumer Discretionary"),("BRK-B","Berkshire Hathaway","Financials"),
        ("LLY","Eli Lilly","Healthcare"),("JPM","JPMorgan Chase","Financials"),
        ("V","Visa","Financials"),("UNH","UnitedHealth","Healthcare"),
        ("XOM","Exxon Mobil","Energy"),("MA","Mastercard","Financials"),
        ("AVGO","Broadcom","Technology"),("PG","Procter & Gamble","Consumer Staples"),
        ("JNJ","Johnson & Johnson","Healthcare"),("HD","Home Depot","Consumer Discretionary"),
        ("MRK","Merck","Healthcare"),("COST","Costco","Consumer Staples"),
        ("ABBV","AbbVie","Healthcare"),("CVX","Chevron","Energy"),
        ("CRM","Salesforce","Technology"),("BAC","Bank of America","Financials"),
        ("KO","Coca-Cola","Consumer Staples"),("NFLX","Netflix","Communication"),
        ("PEP","PepsiCo","Consumer Staples"),("TMO","Thermo Fisher","Healthcare"),
        ("ORCL","Oracle","Technology"),("ACN","Accenture","Technology"),
        ("WMT","Walmart","Consumer Staples"),("MCD","McDonald's","Consumer Discretionary"),
        ("CSCO","Cisco","Technology"),("ABT","Abbott Labs","Healthcare"),
        ("DHR","Danaher","Healthcare"),("NKE","Nike","Consumer Discretionary"),
        ("TXN","Texas Instruments","Technology"),("ADBE","Adobe","Technology"),
        ("LIN","Linde","Materials"),("NEE","NextEra Energy","Utilities"),
        ("PM","Philip Morris","Consumer Staples"),("RTX","RTX Corp","Industrials"),
        ("QCOM","Qualcomm","Technology"),("BMY","Bristol-Myers","Healthcare"),
        ("IBM","IBM","Technology"),("HON","Honeywell","Industrials"),
        ("AMGN","Amgen","Healthcare"),("LOW","Lowe's","Consumer Discretionary"),
        ("UNP","Union Pacific","Industrials"),("CAT","Caterpillar","Industrials"),
        ("SPGI","S&P Global","Financials"),("GE","GE Aerospace","Industrials"),
        ("INTU","Intuit","Technology"),("AXP","American Express","Financials"),
        ("AMAT","Applied Materials","Technology"),("GS","Goldman Sachs","Financials"),
        ("SYK","Stryker","Healthcare"),("MS","Morgan Stanley","Financials"),
        ("ISRG","Intuitive Surgical","Healthcare"),("BLK","BlackRock","Financials"),
        ("T","AT&T","Communication"),("MDT","Medtronic","Healthcare"),
        ("BKNG","Booking Holdings","Consumer Discretionary"),("ADP","ADP","Technology"),
        ("MU","Micron Technology","Technology"),("VRTX","Vertex Pharma","Healthcare"),
        ("ETN","Eaton","Industrials"),("GILD","Gilead Sciences","Healthcare"),
        ("LRCX","Lam Research","Technology"),("ADI","Analog Devices","Technology"),
        ("MMC","Marsh McLennan","Financials"),("PLD","Prologis","Real Estate"),
        ("REGN","Regeneron","Healthcare"),("CI","Cigna","Healthcare"),
        ("TJX","TJX Companies","Consumer Discretionary"),("SHW","Sherwin-Williams","Materials"),
        ("KLAC","KLA Corp","Technology"),("BSX","Boston Scientific","Healthcare"),
        ("PGR","Progressive","Financials"),("SO","Southern Company","Utilities"),
        ("CB","Chubb","Financials"),("SNPS","Synopsys","Technology"),
        ("CDNS","Cadence Design","Technology"),("DUK","Duke Energy","Utilities"),
        ("ITW","Illinois Tool Works","Industrials"),("WM","Waste Management","Industrials"),
        ("CME","CME Group","Financials"),("EOG","EOG Resources","Energy"),
        ("MCO","Moody's","Financials"),("ZTS","Zoetis","Healthcare"),
        ("CVS","CVS Health","Healthcare"),("USB","US Bancorp","Financials"),
        ("TGT","Target","Consumer Discretionary"),("EMR","Emerson Electric","Industrials"),
        ("NOC","Northrop Grumman","Industrials"),("AON","Aon","Financials"),
        ("FDX","FedEx","Industrials"),("PNC","PNC Financial","Financials"),
        ("MMM","3M","Industrials"),("FCX","Freeport-McMoRan","Materials"),
    ]
    return pd.DataFrame(data, columns=["ticker", "nome", "settore"])


@st.cache_data(ttl=86400, show_spinner=False)
def get_nasdaq100_tickers() -> pd.DataFrame:
    """Scarica Nasdaq 100 da Wikipedia con fallback hardcoded robusto."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/Nasdaq-100",
            headers=headers, timeout=20
        )
        tables = pd.read_html(resp.text)
        for table in tables:
            sym_col = next((c for c in table.columns if str(c).lower() in ["ticker","symbol","ticker symbol"]), None)
            if sym_col is None:
                continue
            name_col = next((c for c in table.columns if any(k in str(c).lower() for k in ["company","name"])), None)
            sec_col  = next((c for c in table.columns if "sector" in str(c).lower() or "industry" in str(c).lower()), None)
            tickers = table[sym_col].astype(str).str.strip()
            mask = tickers.str.match(r'^[A-Z\-]{1,6}$')
            if mask.sum() < 80:
                continue
            result = pd.DataFrame()
            result["ticker"]  = tickers[mask].values
            result["nome"]    = table.loc[mask, name_col].astype(str).str.strip().values if name_col else tickers[mask].values
            result["settore"] = table.loc[mask, sec_col].astype(str).str.strip().values if sec_col else "Technology"
            if len(result) >= 80:
                return result.reset_index(drop=True)
    except Exception:
        pass
    # Fallback hardcoded Nasdaq 100
    data = [
        ("AAPL","Apple","Technology"),("MSFT","Microsoft","Technology"),
        ("NVDA","NVIDIA","Technology"),("AMZN","Amazon","Consumer Disc."),
        ("META","Meta","Technology"),("GOOGL","Alphabet A","Technology"),
        ("GOOG","Alphabet C","Technology"),("TSLA","Tesla","Consumer Disc."),
        ("AVGO","Broadcom","Technology"),("COST","Costco","Consumer Staples"),
        ("NFLX","Netflix","Communication"),("ASML","ASML Holding","Technology"),
        ("AZN","AstraZeneca","Healthcare"),("TMUS","T-Mobile","Communication"),
        ("AMD","AMD","Technology"),("INTU","Intuit","Technology"),
        ("QCOM","Qualcomm","Technology"),("AMAT","Applied Materials","Technology"),
        ("ISRG","Intuitive Surgical","Healthcare"),("TXN","Texas Instruments","Technology"),
        ("BKNG","Booking Holdings","Consumer Disc."),("AMGN","Amgen","Healthcare"),
        ("MU","Micron","Technology"),("LRCX","Lam Research","Technology"),
        ("KLAC","KLA Corp","Technology"),("ADI","Analog Devices","Technology"),
        ("PANW","Palo Alto Networks","Technology"),("SNPS","Synopsys","Technology"),
        ("CDNS","Cadence Design","Technology"),("REGN","Regeneron","Healthcare"),
        ("MELI","MercadoLibre","Consumer Disc."),("CRWD","CrowdStrike","Technology"),
        ("FTNT","Fortinet","Technology"),("MNST","Monster Beverage","Consumer Staples"),
        ("CTAS","Cintas","Industrials"),("ADSK","Autodesk","Technology"),
        ("MRVL","Marvell Tech","Technology"),("CSX","CSX Corp","Industrials"),
        ("PAYX","Paychex","Technology"),("ORLY","O'Reilly Auto","Consumer Disc."),
        ("PCAR","PACCAR","Industrials"),("ROST","Ross Stores","Consumer Disc."),
        ("CPRT","Copart","Industrials"),("AEP","AEP","Utilities"),
        ("IDXX","IDEXX Labs","Healthcare"),("ODFL","Old Dominion","Industrials"),
        ("FAST","Fastenal","Industrials"),("KDP","Keurig Dr Pepper","Consumer Staples"),
        ("EA","Electronic Arts","Communication"),("VRSK","Verisk Analytics","Industrials"),
        ("EXC","Exelon","Utilities"),("DXCM","DexCom","Healthcare"),
        ("GEHC","GE HealthCare","Healthcare"),("XEL","Xcel Energy","Utilities"),
        ("KHC","Kraft Heinz","Consumer Staples"),("CTSH","Cognizant","Technology"),
        ("LULU","Lululemon","Consumer Disc."),("ON","ON Semiconductor","Technology"),
        ("BIIB","Biogen","Healthcare"),("SBUX","Starbucks","Consumer Disc."),
        ("ILMN","Illumina","Healthcare"),("FANG","Diamondback Energy","Energy"),
        ("CDW","CDW Corp","Technology"),("ANSS","ANSYS","Technology"),
        ("MDLZ","Mondelez","Consumer Staples"),("WBD","Warner Bros","Communication"),
        ("ZS","Zscaler","Technology"),("TEAM","Atlassian","Technology"),
        ("DDOG","Datadog","Technology"),("NXPI","NXP Semi","Technology"),
        ("WDAY","Workday","Technology"),("CHTR","Charter Comm","Communication"),
        ("VRSN","VeriSign","Technology"),("ENPH","Enphase Energy","Technology"),
        ("OKTA","Okta","Technology"),("CEG","Constellation Energy","Utilities"),
        ("HON","Honeywell","Industrials"),("PYPL","PayPal","Technology"),
        ("INTC","Intel","Technology"),("PDD","PDD Holdings","Consumer Disc."),
        ("ABNB","Airbnb","Consumer Disc."),("DASH","DoorDash","Consumer Disc."),
        ("ZM","Zoom","Technology"),("PLTR","Palantir","Technology"),
        ("ARM","Arm Holdings","Technology"),("APP","Applovin","Technology"),
        ("MSTR","MicroStrategy","Technology"),("SMCI","Super Micro","Technology"),
        ("MRNA","Moderna","Healthcare"),("DLTR","Dollar Tree","Consumer Disc."),
        ("SIRI","Sirius XM","Communication"),("ALGN","Align Technology","Healthcare"),
        ("MDB","MongoDB","Technology"),("TTWO","Take-Two","Communication"),
        ("GFS","GlobalFoundries","Technology"),("RIVN","Rivian","Consumer Disc."),
        ("LCID","Lucid Group","Consumer Disc."),("WBA","Walgreens","Consumer Staples"),
    ]
    return pd.DataFrame(data, columns=["ticker", "nome", "settore"])


def get_tickers_for_index(indice: str) -> pd.DataFrame:
    """Ritorna DataFrame con ticker/nome/settore per l'indice selezionato."""
    if indice == "S&P 500":
        df = get_sp500_tickers()
        if len(df) > 0:
            return df
    if indice == "Nasdaq 100":
        df = get_nasdaq100_tickers()
        if len(df) > 0:
            return df
    # Fallback: ticker hardcoded
    tickers = TICKER_MAP.get(indice, [])
    return pd.DataFrame({
        "ticker":  tickers,
        "nome":    tickers,
        "settore": ["N/A"] * len(tickers),
    })


# ══════════════════════════════════════════════
# UNIVERSE: PREZZI BATCH (yfinance)
# ══════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_prices_batch(tickers: tuple, period: str = "1y") -> pd.DataFrame:
    """
    Scarica prezzi di chiusura giornalieri per una lista di ticker.
    Ritorna DataFrame con date sull'indice e ticker sulle colonne.
    tickers deve essere tuple (hashable per caching).
    """
    if not tickers:
        return pd.DataFrame()
    try:
        # yfinance batch download
        raw = yf.download(
            list(tickers),
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        if raw.empty:
            return pd.DataFrame()
        # Se un solo ticker, yfinance non fa MultiIndex
        if len(tickers) == 1:
            if "Close" in raw.columns:
                return raw[["Close"]].rename(columns={"Close": tickers[0]})
            return pd.DataFrame()
        # Multi-ticker: prendi solo colonna Close
        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw
        return close
    except Exception:
        return pd.DataFrame()


def compute_price_metrics(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola ret_6m, ret_12m, vol_ann da DataFrame prezzi.
    Ritorna DataFrame con ticker come indice.
    """
    results = []
    today = prices.index[-1] if len(prices) > 0 else None

    for col in prices.columns:
        series = prices[col].dropna()
        if len(series) < 30:
            continue
        latest = series.iloc[-1]
        # Momentum
        idx_6m  = max(0, len(series) - 126)
        idx_12m = max(0, len(series) - 252)
        ret_6m  = (latest / series.iloc[idx_6m]  - 1) if series.iloc[idx_6m]  > 0 else np.nan
        ret_12m = (latest / series.iloc[idx_12m] - 1) if series.iloc[idx_12m] > 0 else np.nan
        # Volatilità annualizzata
        log_ret = np.log(series / series.shift(1)).dropna()
        vol_ann = log_ret.std() * np.sqrt(252) if len(log_ret) >= 20 else np.nan
        results.append({
            "ticker":  col,
            "prezzo":  round(latest, 2),
            "ret_6m":  ret_6m,
            "ret_12m": ret_12m,
            "vol_ann": vol_ann,
        })
    return pd.DataFrame(results).set_index("ticker") if results else pd.DataFrame()


# ══════════════════════════════════════════════
# UNIVERSE: FONDAMENTALI (yfinance .info parallelo)
# ══════════════════════════════════════════════

def _fetch_single_info(ticker: str) -> dict:
    """Fetch yfinance info per un singolo ticker. Usata in parallelo."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "ticker":    ticker,
            "nome":      info.get("longName") or info.get("shortName", ticker),
            "settore":   info.get("sector", "N/A"),
            "mktcap_M":  (info.get("marketCap") or 0) / 1e6,
            "pe":        info.get("trailingPE") or info.get("forwardPE"),
            "roe":       info.get("returnOnEquity"),
            "de_ratio":  (info.get("debtToEquity") or 0) / 100,
        }
    except Exception:
        return {"ticker": ticker, "nome": ticker, "settore": "N/A",
                "mktcap_M": None, "pe": None, "roe": None, "de_ratio": None}


@st.cache_data(ttl=14400, show_spinner=False)
def fetch_fundamentals_batch(tickers: tuple, max_workers: int = 20) -> pd.DataFrame:
    """
    Fetch fondamentali (P/E, ROE, D/E, mktcap) in parallelo.
    Limitare a max 150 ticker per evitare timeout.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch_single_info, t): t for t in tickers}
        for future in as_completed(futures):
            results.append(future.result())
    df = pd.DataFrame(results)
    if df.empty:
        return pd.DataFrame()
    return df.set_index("ticker")


# ══════════════════════════════════════════════
# UNIVERSE: DATI COMPLETI (prezzi + fondamentali)
# ══════════════════════════════════════════════

def fetch_universe_data(tickers_df: pd.DataFrame, progress_cb=None) -> pd.DataFrame:
    """
    Pipeline completo per il foglio Universe.
    tickers_df deve avere colonne: ticker, nome, settore
    Ritorna DataFrame con tutte le metriche per il pre-filtro.
    """
    tickers = tickers_df["ticker"].tolist()
    if not tickers:
        return pd.DataFrame()

    # Step 1: prezzi batch
    if progress_cb:
        progress_cb(0.1, "Scaricamento prezzi storici...")
    prices = fetch_prices_batch(tuple(tickers))
    metrics = compute_price_metrics(prices) if not prices.empty else pd.DataFrame()

    # Step 2: fondamentali (parallelo, max 150)
    if progress_cb:
        progress_cb(0.4, "Caricamento dati fondamentali...")
    fund = fetch_fundamentals_batch(tuple(tickers[:150]))

    # Step 3: merge
    if progress_cb:
        progress_cb(0.85, "Elaborazione dati...")

    base = tickers_df.set_index("ticker")
    df = base.copy()

    if not metrics.empty:
        df = df.join(metrics[["prezzo", "ret_6m", "ret_12m", "vol_ann"]], how="left")
    else:
        for col in ["prezzo", "ret_6m", "ret_12m", "vol_ann"]:
            df[col] = np.nan

    if not fund.empty:
        for col in ["mktcap_M", "pe", "roe", "de_ratio"]:
            if col in fund.columns:
                df[col] = fund[col].reindex(df.index)
            else:
                df[col] = np.nan
        # Aggiorna nome/settore se disponibile
        if "nome" in fund.columns:
            mask = fund["nome"].notna() & (fund["nome"] != fund.index)
            df.loc[mask[mask].index, "nome"] = fund.loc[mask[mask].index, "nome"]
        if "settore" in fund.columns:
            mask = fund["settore"].notna() & (fund["settore"] != "N/A")
            df.loc[mask[mask].index, "settore"] = fund.loc[mask[mask].index, "settore"]
    else:
        for col in ["mktcap_M", "pe", "roe", "de_ratio"]:
            if col not in df.columns:
                df[col] = np.nan

    if progress_cb:
        progress_cb(1.0, "Completato!")

    return df.reset_index()


# ══════════════════════════════════════════════
# WATCHLIST: DATI DETTAGLIATI (FMP + yfinance fallback)
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
# WATCHLIST: DATI DETTAGLIATI
# ══════════════════════════════════════════════

def _empty_row(ticker: str) -> dict:
    return {
        "ticker": ticker, "nome": ticker, "settore": "N/A",
        "mktcap_M": None, "prezzo": None,
        "ret_6m": None, "ret_12m": None, "vol_ann": None,
        "pe": None, "roe": None, "de_ratio": None,
        "gross_margin": None, "div_yield": None,
    }


def fetch_watchlist_all(tickers: List[str], progress_cb=None) -> pd.DataFrame:
    """
    Fetch dati per tutti i ticker della Watchlist.
    Usa yfinance batch per prezzi (veloce) + yfinance info per fondamentali.
    Fallback a FMP se API key disponibile.
    """
    if not tickers:
        return pd.DataFrame()

    results = {t: _empty_row(t) for t in tickers}

    # ── STEP 1: prezzi batch con yfinance (sempre disponibile) ──
    if progress_cb:
        progress_cb(0.05, "Download prezzi storici (batch)...")
    try:
        raw = yf.download(
            tickers, period="1y", interval="1d",
            auto_adjust=True, progress=False, threads=True,
        )
        if not raw.empty:
            # Gestisci sia singolo ticker che multi-ticker
            if isinstance(raw.columns, pd.MultiIndex):
                close_df = raw["Close"]
            else:
                close_df = raw[["Close"]].rename(columns={"Close": tickers[0]}) if len(tickers) == 1 else raw

            for ticker in tickers:
                if ticker not in close_df.columns:
                    continue
                series = close_df[ticker].dropna()
                if len(series) < 20:
                    continue
                latest  = float(series.iloc[-1])
                idx_6m  = max(0, len(series) - 126)
                idx_12m = max(0, len(series) - 252)
                p6  = float(series.iloc[idx_6m])
                p12 = float(series.iloc[idx_12m])
                log_ret = np.log(series / series.shift(1)).dropna()
                results[ticker]["prezzo"]  = round(latest, 2)
                results[ticker]["ret_6m"]  = (latest / p6  - 1) if p6  > 0 else None
                results[ticker]["ret_12m"] = (latest / p12 - 1) if p12 > 0 else None
                results[ticker]["vol_ann"] = float(log_ret.std() * np.sqrt(252)) if len(log_ret) >= 20 else None
    except Exception:
        pass

    # ── STEP 2: fondamentali ticker per ticker ──
    total = len(tickers)
    key   = get_fmp_key()

    for i, ticker in enumerate(tickers):
        if progress_cb:
            pct = 0.1 + 0.88 * (i / total)
            progress_cb(pct, f"Fondamentali {ticker} ({i+1}/{total})...")

        if key:
            # --- FMP prima scelta ---
            try:
                profile = fmp_get(f"profile/{ticker}")
                if profile and isinstance(profile, list) and profile:
                    p = profile[0]
                    results[ticker]["nome"]     = p.get("companyName", ticker)
                    results[ticker]["settore"]  = p.get("sector", "N/A")
                    results[ticker]["mktcap_M"] = (p.get("mktCap") or 0) / 1e6
                    if results[ticker]["prezzo"] is None:
                        results[ticker]["prezzo"] = p.get("price")
            except Exception:
                pass
            try:
                ratios = fmp_get(f"ratios-ttm/{ticker}")
                if ratios and isinstance(ratios, list) and ratios:
                    r = ratios[0]
                    results[ticker]["pe"]           = r.get("peRatioTTM")
                    results[ticker]["roe"]          = r.get("returnOnEquityTTM")
                    results[ticker]["de_ratio"]     = r.get("debtEquityRatioTTM")
                    results[ticker]["gross_margin"] = r.get("grossProfitMarginTTM")
                    results[ticker]["div_yield"]    = r.get("dividendYieldTTM") or r.get("dividendYielTTM")
            except Exception:
                pass

            # --- Fallback yfinance se FMP non ha restituito i fondamentali chiave ---
            missing = (
                results[ticker]["pe"] is None and
                results[ticker]["roe"] is None and
                results[ticker]["gross_margin"] is None
            )
            if missing:
                try:
                    info_full = yf.Ticker(ticker).info
                    if results[ticker]["nome"] == ticker:
                        results[ticker]["nome"]     = info_full.get("longName") or info_full.get("shortName", ticker)
                    if results[ticker]["settore"] == "N/A":
                        results[ticker]["settore"]  = info_full.get("sector", "N/A")
                    if not results[ticker]["mktcap_M"]:
                        results[ticker]["mktcap_M"] = (info_full.get("marketCap") or 0) / 1e6
                    if results[ticker]["prezzo"] is None:
                        results[ticker]["prezzo"]   = info_full.get("currentPrice") or info_full.get("regularMarketPrice")
                    results[ticker]["pe"]           = info_full.get("trailingPE") or info_full.get("forwardPE")
                    results[ticker]["roe"]          = info_full.get("returnOnEquity")
                    results[ticker]["de_ratio"]     = (info_full.get("debtToEquity") or 0) / 100
                    results[ticker]["gross_margin"] = info_full.get("grossMargins")
                    if results[ticker]["div_yield"] is None:
                        results[ticker]["div_yield"] = info_full.get("dividendYield")
                except Exception:
                    pass
        else:
            # --- yfinance info ---
            try:
                info = yf.Ticker(ticker).fast_info
                # fast_info è più affidabile di .info su versioni recenti di yfinance
                results[ticker]["mktcap_M"] = (getattr(info, "market_cap", None) or 0) / 1e6
                if results[ticker]["prezzo"] is None:
                    results[ticker]["prezzo"] = getattr(info, "last_price", None)
            except Exception:
                pass
            try:
                info_full = yf.Ticker(ticker).info
                results[ticker]["nome"]         = info_full.get("longName") or info_full.get("shortName", ticker)
                results[ticker]["settore"]      = info_full.get("sector", "N/A")
                if not results[ticker]["mktcap_M"]:
                    results[ticker]["mktcap_M"] = (info_full.get("marketCap") or 0) / 1e6
                if results[ticker]["prezzo"] is None:
                    results[ticker]["prezzo"]   = info_full.get("currentPrice") or info_full.get("regularMarketPrice")
                results[ticker]["pe"]           = info_full.get("trailingPE") or info_full.get("forwardPE")
                results[ticker]["roe"]          = info_full.get("returnOnEquity")
                results[ticker]["de_ratio"]     = (info_full.get("debtToEquity") or 0) / 100
                results[ticker]["gross_margin"] = info_full.get("grossMargins")
                results[ticker]["div_yield"]    = info_full.get("dividendYield")
            except Exception:
                pass

        time.sleep(0.15)

    if progress_cb:
        progress_cb(1.0, "Completato!")

    df = pd.DataFrame(list(results.values()))
    return df.set_index("ticker") if not df.empty else pd.DataFrame()


# funzione singola mantenuta per compatibilità con Preferiti e Dividendi
def fetch_watchlist_ticker(ticker: str) -> dict:
    df = fetch_watchlist_all([ticker])
    if not df.empty:
        row = df.iloc[0].to_dict()
        row["ticker"] = ticker
        return row
    return _empty_row(ticker)


# ══════════════════════════════════════════════
# STORICO PREZZI (per grafici)
# ══════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Scarica storico prezzi per un singolo ticker (grafico Storico)."""
    key = get_fmp_key()
    if key:
        days = 252 if period == "1y" else 504 if period == "2y" else 1260
        hist = fmp_get(f"historical-price-full/{ticker}", {"timeseries": days})
        if hist and "historical" in hist:
            records = hist["historical"]
            df = pd.DataFrame(records)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "open", "high", "low", "close", "volume"]]
    # yfinance fallback
    try:
        tkr = yf.Ticker(ticker)
        df = tkr.history(period=period, interval="1d", auto_adjust=True)
        df.index.name = "date"
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        return df[["date", "open", "high", "low", "close", "volume"]]
    except Exception:
        return pd.DataFrame()


# ══════════════════════════════════════════════
# DIVIDENDI (per foglio Dividendi)
# ══════════════════════════════════════════════

@st.cache_data(ttl=14400, show_spinner=False)
def fetch_dividends(ticker: str) -> pd.DataFrame:
    """Scarica storico dividendi per un ticker."""
    key = get_fmp_key()
    if key:
        data = fmp_get(f"historical-price-full/stock_dividend/{ticker}")
        if data and "historical" in data:
            df = pd.DataFrame(data["historical"])
            df["date"] = pd.to_datetime(df.get("date", df.get("paymentDate", pd.NaT)))
            df = df.sort_values("date", ascending=False).reset_index(drop=True)
            amt_col = "adjDividend" if "adjDividend" in df.columns else "dividend"
            return df[["date", amt_col]].rename(columns={amt_col: "dividendo"}).head(20)
    # yfinance fallback
    try:
        tkr = yf.Ticker(ticker)
        divs = tkr.dividends
        if not divs.empty:
            df = divs.reset_index()
            df.columns = ["date", "dividendo"]
            df["date"] = pd.to_datetime(df["date"])
            return df.sort_values("date", ascending=False).head(20)
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()
