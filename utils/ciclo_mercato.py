"""
ciclo_mercato.py — Rilevamento del regime di mercato.

Supporta USA ed Europa. Analizza ETF benchmark, volatilità
e tassi per classificare il mercato in 4 regimi:
Bull / Laterale / Bear / Stress-Crash.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class RegimeMercato:
    nome: str
    colore: str
    emoji: str
    descrizione: str
    score: float
    segnali: Dict[str, str] = field(default_factory=dict)


REGIMI = {
    "Bull":     RegimeMercato("Bull",     "#2d7a2d", "🐂", "Mercato in trend rialzista sostenuto. Momentum favorito.", 3.0),
    "Laterale": RegimeMercato("Laterale", "#b38600", "↔️", "Mercato senza direzione chiara. Qualità e dividendi favoriti.", 2.0),
    "Bear":     RegimeMercato("Bear",     "#c0392b", "🐻", "Mercato in trend ribassista. Massima cautela, privilegia low-vol.", 1.0),
    "Stress":   RegimeMercato("Stress",   "#7b0000", "💥", "Mercato sotto stress/crash. Difensivo: dividendi e bassa volatilità.", 0.0),
}

# ── Configurazione per mercato ────────────────────────────────
CONFIG_MERCATI = {
    "🇺🇸 USA (S&P 500)": {
        "benchmark":   "SPY",
        "vol_index":   "^VIX",
        "rate_10y":    "^TNX",
        "breadth":     [("QQQ", "Nasdaq"), ("IWM", "Russell 2000")],
        "vix_label":   "VIX",
        "rate_label":  "Treasury 10Y",
    },
    "🇪🇺 Europa (Stoxx 600)": {
        "benchmark":   "IEURP",        # iShares Core MSCI Europe ETF (EUR)
        "vol_index":   "^STOXX50E",    # Euro Stoxx 50 come proxy (VSTOXX non su yfinance)
        "rate_10y":    "^TNX",         # Bund 10Y non disponibile gratis, usiamo come proxy
        "breadth":     [("EZU", "Eurozona"), ("EWG", "Germania DAX")],
        "vix_label":   "Euro Stoxx 50",
        "rate_label":  "Tasso 10Y (proxy)",
    },
    "🇩🇪 Germania (DAX)": {
        "benchmark":   "EWG",          # iShares MSCI Germany ETF
        "vol_index":   "^GDAXI",       # DAX index
        "rate_10y":    "^TNX",
        "breadth":     [("EZU", "Eurozona"), ("IEURP", "Europa")],
        "vix_label":   "DAX",
        "rate_label":  "Tasso 10Y (proxy)",
    },
    "🇮🇹 Italia (FTSE MIB)": {
        "benchmark":   "EWI",          # iShares MSCI Italy ETF
        "vol_index":   "^FTSEMIB",     # FTSE MIB come proxy volatilità
        "rate_10y":    "^TNX",
        "breadth":     [("EZU", "Eurozona"), ("EWG", "Germania")],
        "vix_label":   "FTSE MIB",
        "rate_label":  "Tasso 10Y (proxy)",
    },
    "🇬🇧 UK (FTSE 100)": {
        "benchmark":   "EWU",          # iShares MSCI United Kingdom ETF
        "vol_index":   "^FTSE",        # FTSE 100
        "rate_10y":    "^TNX",
        "breadth":     [("IEURP", "Europa"), ("EZU", "Eurozona")],
        "vix_label":   "FTSE 100",
        "rate_label":  "Tasso 10Y (proxy)",
    },
}


@st.cache_data(ttl=7200, show_spinner=False)
def rileva_regime_mercato(mercato: str = "🇺🇸 USA (S&P 500)") -> RegimeMercato:
    """
    Analizza i segnali di mercato per il mercato selezionato
    e ritorna il regime attuale.
    """
    cfg = CONFIG_MERCATI.get(mercato, CONFIG_MERCATI["🇺🇸 USA (S&P 500)"])
    segnali = {}

    # ── 1. Scarica dati ──────────────────────────────────────────
    tickers_da_scaricare = list({
        cfg["benchmark"], cfg["vol_index"], cfg["rate_10y"],
        *[t for t, _ in cfg["breadth"]]
    })

    try:
        raw = yf.download(
            tickers_da_scaricare,
            period="1y", interval="1d",
            auto_adjust=True, progress=False, threads=True,
        )
        if raw.empty:
            return _regime_default()
        close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    except Exception:
        return _regime_default()

    # ── 2. Analisi Benchmark ──────────────────────────────────────
    spy_score = 0
    bench = close.get(cfg["benchmark"], pd.Series(dtype=float)).dropna()

    if len(bench) >= 50:
        ma50  = bench.rolling(50).mean().iloc[-1]
        n200  = min(200, len(bench)//2)
        ma200 = bench.rolling(n200).mean().iloc[-1]
        now   = bench.iloc[-1]
        p1m   = bench.iloc[max(0, len(bench)-21)]
        p3m   = bench.iloc[max(0, len(bench)-63)]
        ret1m = (now/p1m - 1) if p1m > 0 else 0
        ret3m = (now/p3m - 1) if p3m > 0 else 0

        if now > ma200:
            spy_score += 2
            segnali[f"{cfg['benchmark']} vs MA200"] = f"🟢 Benchmark sopra MA200 ({now:.1f} > {ma200:.1f})"
        else:
            dd = (now/ma200 - 1)
            segnali[f"{cfg['benchmark']} vs MA200"] = f"🔴 Benchmark sotto MA200 ({dd:+.1%})"

        if now > ma50:
            spy_score += 1
            segnali[f"{cfg['benchmark']} vs MA50"] = "🟢 Benchmark sopra MA50"
        else:
            segnali[f"{cfg['benchmark']} vs MA50"] = "🔴 Benchmark sotto MA50"

        if ret3m > 0.03:
            spy_score += 1
            segnali["Trend 3M"] = f"🟢 Benchmark +{ret3m:.1%} in 3 mesi"
        elif ret3m < -0.08:
            spy_score -= 1
            segnali["Trend 3M"] = f"🔴 Benchmark {ret3m:.1%} in 3 mesi"
        else:
            segnali["Trend 3M"] = f"🟡 Benchmark {ret3m:+.1%} in 3 mesi (laterale)"

        # Breadth
        for etf, nome in cfg["breadth"]:
            s = close.get(etf, pd.Series(dtype=float)).dropna()
            if len(s) >= 50:
                ma = s.rolling(50).mean().iloc[-1]
                if s.iloc[-1] > ma:
                    spy_score += 0.5
                    segnali[f"{nome} vs MA50"] = f"🟢 {nome} sopra MA50"
                else:
                    segnali[f"{nome} vs MA50"] = f"🔴 {nome} sotto MA50"

    # ── 3. Analisi indice di volatilità / momentum ────────────────
    vix_score = 0
    vol_idx = close.get(cfg["vol_index"], pd.Series(dtype=float)).dropna()
    is_usa  = mercato == "🇺🇸 USA (S&P 500)"

    if len(vol_idx) >= 20:
        vol_now = float(vol_idx.iloc[-1])
        vol_ma  = float(vol_idx.rolling(20).mean().iloc[-1])

        if is_usa:
            # VIX: valori assoluti hanno significato
            if vol_now < 15:   vix_score = 2;  label = f"🟢 VIX basso ({vol_now:.1f}) — mercato sereno"
            elif vol_now < 20: vix_score = 1;  label = f"🟢 VIX normale ({vol_now:.1f})"
            elif vol_now < 25: vix_score = 0;  label = f"🟡 VIX elevato ({vol_now:.1f}) — attenzione"
            elif vol_now < 35: vix_score = -1; label = f"🔴 VIX alto ({vol_now:.1f}) — stress"
            else:              vix_score = -2; label = f"💥 VIX panico ({vol_now:.1f}) — crash"
        else:
            # Per indici europei usiamo il momentum dell'indice stesso
            ret_idx_1m = (vol_now / float(vol_idx.iloc[max(0, len(vol_idx)-21)]) - 1) if len(vol_idx) >= 21 else 0
            if ret_idx_1m > 0.03:   vix_score = 1;  label = f"🟢 {cfg['vix_label']} in salita (+{ret_idx_1m:.1%})"
            elif ret_idx_1m > -0.02: vix_score = 0; label = f"🟡 {cfg['vix_label']} stabile ({ret_idx_1m:+.1%})"
            else:                    vix_score = -1; label = f"🔴 {cfg['vix_label']} in calo ({ret_idx_1m:.1%})"

        segnali[cfg["vix_label"]] = label

    # ── 4. Analisi tassi ──────────────────────────────────────────
    rate_score = 0
    tnx = close.get(cfg["rate_10y"], pd.Series(dtype=float)).dropna()
    if len(tnx) >= 20:
        tnx_now = float(tnx.iloc[-1])
        tnx_3m  = float(tnx.iloc[max(0, len(tnx)-63)])
        delta   = tnx_now - tnx_3m
        if delta > 0.5:
            rate_score = -1
            segnali[cfg["rate_label"]] = f"🔴 Tassi in salita (+{delta:.2f}%) — pressione su equity"
        elif delta < -0.3:
            rate_score = 1
            segnali[cfg["rate_label"]] = f"🟢 Tassi in calo ({delta:.2f}%) — favorevole"
        else:
            segnali[cfg["rate_label"]] = f"🟡 Tassi stabili ({tnx_now:.2f}%)"

    # ── 5. Score totale → Regime ──────────────────────────────────
    totale = spy_score + vix_score + rate_score

    if totale >= 5.5:    regime_key = "Bull"
    elif totale >= 2.5:  regime_key = "Laterale"
    elif totale >= 0:    regime_key = "Bear"
    else:                regime_key = "Stress"

    if is_usa and vix_score <= -2:
        regime_key = "Stress"

    import copy
    regime = copy.deepcopy(REGIMI[regime_key])
    regime.segnali = segnali
    return regime


def _regime_default() -> RegimeMercato:
    import copy
    r = copy.deepcopy(REGIMI["Laterale"])
    r.segnali = {"Info": "⚪ Dati non disponibili — regime neutro applicato"}
    return r


def rileva_regime(mercato: str = "🇺🇸 USA (S&P 500)") -> RegimeMercato:
    """Wrapper non cached — usa rileva_regime_mercato internamente."""
    return rileva_regime_mercato(mercato)


def get_mercati_disponibili():
    return list(CONFIG_MERCATI.keys())



@st.cache_data(ttl=7200, show_spinner=False)   # cache 2 ore
def rileva_regime() -> RegimeMercato:
    """
    Analizza i segnali di mercato e ritorna il regime attuale.
    Usa SPY per trend, ^VIX per volatilità, ^TNX per tasso 10Y.
    """
    segnali = {}

    # ── 1. Scarica dati ──────────────────────────────────────────
    try:
        raw = yf.download(
            ["SPY", "^VIX", "^TNX", "QQQ", "IWM"],
            period="1y", interval="1d",
            auto_adjust=True, progress=False, threads=True,
        )
        if raw.empty:
            return _regime_default()

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:
            close = raw

    except Exception:
        return _regime_default()

    # ── 2. Analisi SPY ───────────────────────────────────────────
    spy_score = 0
    spy = close.get("SPY", pd.Series(dtype=float)).dropna()

    if len(spy) >= 50:
        ma50  = spy.rolling(50).mean().iloc[-1]
        ma200 = spy.rolling(200).mean().iloc[-1] if len(spy) >= 200 else spy.rolling(len(spy)//2).mean().iloc[-1]
        spy_now = spy.iloc[-1]
        spy_1m  = spy.iloc[max(0, len(spy)-21)]
        spy_3m  = spy.iloc[max(0, len(spy)-63)]

        ret_1m = (spy_now / spy_1m - 1) if spy_1m > 0 else 0
        ret_3m = (spy_now / spy_3m - 1) if spy_3m > 0 else 0

        # SPY sopra MA200 → +2 punti
        if spy_now > ma200:
            spy_score += 2
            segnali["SPY vs MA200"] = f"🟢 SPY sopra MA200 ({spy_now:.0f} > {ma200:.0f})"
        else:
            dd = (spy_now / ma200 - 1)
            segnali["SPY vs MA200"] = f"🔴 SPY sotto MA200 ({dd:+.1%})"

        # SPY sopra MA50 → +1 punto
        if spy_now > ma50:
            spy_score += 1
            segnali["SPY vs MA50"] = f"🟢 SPY sopra MA50"
        else:
            segnali["SPY vs MA50"] = f"🔴 SPY sotto MA50"

        # Rendimento 3M positivo → +1 punto
        if ret_3m > 0.03:
            spy_score += 1
            segnali["Trend 3M"] = f"🟢 SPY +{ret_3m:.1%} in 3 mesi"
        elif ret_3m < -0.08:
            spy_score -= 1
            segnali["Trend 3M"] = f"🔴 SPY {ret_3m:.1%} in 3 mesi"
        else:
            segnali["Trend 3M"] = f"🟡 SPY {ret_3m:+.1%} in 3 mesi (laterale)"

        # Breadth: QQQ e IWM concordi con SPY
        for etf, nome in [("QQQ", "Nasdaq"), ("IWM", "Russell")]:
            s = close.get(etf, pd.Series(dtype=float)).dropna()
            if len(s) >= 50:
                ma = s.rolling(50).mean().iloc[-1]
                if s.iloc[-1] > ma:
                    spy_score += 0.5
                    segnali[f"{nome} vs MA50"] = f"🟢 {nome} sopra MA50"
                else:
                    segnali[f"{nome} vs MA50"] = f"🔴 {nome} sotto MA50"

    # ── 3. Analisi VIX ──────────────────────────────────────────
    vix_score = 0
    vix = close.get("^VIX", pd.Series(dtype=float)).dropna()

    if len(vix) >= 20:
        vix_now = float(vix.iloc[-1])
        vix_ma  = float(vix.rolling(20).mean().iloc[-1])

        if vix_now < 15:
            vix_score = 2
            segnali["VIX"] = f"🟢 VIX basso ({vix_now:.1f}) — mercato sereno"
        elif vix_now < 20:
            vix_score = 1
            segnali["VIX"] = f"🟢 VIX normale ({vix_now:.1f})"
        elif vix_now < 25:
            vix_score = 0
            segnali["VIX"] = f"🟡 VIX elevato ({vix_now:.1f}) — attenzione"
        elif vix_now < 35:
            vix_score = -1
            segnali["VIX"] = f"🔴 VIX alto ({vix_now:.1f}) — stress"
        else:
            vix_score = -2
            segnali["VIX"] = f"💥 VIX in panico ({vix_now:.1f}) — crash"
    else:
        vix_score = 0
        segnali["VIX"] = "⚪ VIX non disponibile"

    # ── 4. Analisi Treasury 10Y ──────────────────────────────────
    rate_score = 0
    tnx = close.get("^TNX", pd.Series(dtype=float)).dropna()

    if len(tnx) >= 20:
        tnx_now  = float(tnx.iloc[-1])
        tnx_3m   = float(tnx.iloc[max(0, len(tnx)-63)])
        delta_tnx = tnx_now - tnx_3m

        if delta_tnx > 0.5:
            rate_score = -1
            segnali["Treasury 10Y"] = f"🔴 Tassi in salita (+{delta_tnx:.2f}%) — pressione su equity"
        elif delta_tnx < -0.3:
            rate_score = 1
            segnali["Treasury 10Y"] = f"🟢 Tassi in calo ({delta_tnx:.2f}%) — favorevole"
        else:
            rate_score = 0
            segnali["Treasury 10Y"] = f"🟡 Tassi stabili ({tnx_now:.2f}%)"

    # ── 5. Score totale → Regime ─────────────────────────────────
    totale = spy_score + vix_score + rate_score

    if totale >= 5.5:
        regime_key = "Bull"
    elif totale >= 2.5:
        regime_key = "Laterale"
    elif totale >= 0:
        regime_key = "Bear"
    else:
        regime_key = "Stress"

    # VIX in panico sovrascrive tutto
    if vix_score <= -2:
        regime_key = "Stress"

    regime = REGIMI[regime_key]
    regime.segnali = segnali
    return regime


def _regime_default() -> RegimeMercato:
    r = REGIMI["Laterale"]
    r.segnali = {"Info": "⚪ Dati non disponibili — regime neutro applicato"}
    return r


def get_regime_summary(regime: RegimeMercato) -> str:
    """Stringa riassuntiva per UI."""
    return f"{regime.emoji} **{regime.nome}** — {regime.descrizione}"

def get_regime_summary(regime: RegimeMercato) -> str:
    return f"{regime.emoji} **{regime.nome}** — {regime.descrizione}"
