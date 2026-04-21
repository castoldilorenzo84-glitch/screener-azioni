"""
price_targets.py — Calcolo Fair Value e livelli di prezzo di riferimento.

Metodologie combinate:
  1. P/E relativo al settore (peer comparison)
  2. Graham Number (valore intrinseco classico)
  3. DCF semplificato (Discounted Cash Flow su EPS)
  4. Supporti/resistenze tecniche (MA200, 52W high/low)
  5. Fibonacci extension

Output: valutazione (sotto/corretto/sopra), livelli di ingresso,
        target di uscita con scale-out personalizzabile.
"""

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field


# ── Medie P/E per settore (fonte: dati storici mercato USA) ───
PE_MEDI_SETTORE = {
    "Technology":             28.0,
    "Healthcare":             22.0,
    "Financials":             12.0,
    "Consumer Discretionary": 24.0,
    "Consumer Staples":       21.0,
    "Energy":                 14.0,
    "Industrials":            20.0,
    "Materials":              17.0,
    "Utilities":              18.0,
    "Real Estate":            35.0,
    "Communication":          22.0,
    "N/A":                    20.0,  # default
}

# ── Soglie valutazione ────────────────────────────────────────
SOGLIA_SOTTOSTIMATO = -0.15   # prezzo < fair value - 15%
SOGLIA_SOVRASTIMATO =  0.20   # prezzo > fair value + 20%


@dataclass
class LivelliPrezzo:
    ticker:          str
    prezzo_corrente: float
    fair_value:      float
    valutazione:     str        # "Sottostimato" | "Corretto" | "Sovrastimato"
    scostamento_pct: float      # (prezzo - FV) / FV
    minimo_stimato:  float      # supporto / scenario pessimistico
    massimo_stimato: float      # resistenza / scenario ottimistico
    target1:         float      # primo livello di uscita
    target2:         float      # secondo livello di uscita
    target3:         float      # uscita completa
    pct_uscita1:     float      # % posizione da vendere a target1
    pct_uscita2:     float      # % della posizione rimanente a target2
    pct_uscita3:     float      # % della posizione rimanente a target3
    metodi:          Dict[str, float] = field(default_factory=dict)  # dettaglio metodi
    note:            str = ""


@dataclass
class ScaleOutPlan:
    """Piano di uscita progressiva per una posizione specifica."""
    ticker:          str
    prezzo_entrata:  float
    quantita_totale: int
    target1:         float
    target2:         float
    target3:         float
    pct1:            float      # es. 0.50 = 50%
    pct2:            float      # es. 0.50 = 50% del rimanente
    pct3:            float      # es. 1.00 = tutto il rimanente

    @property
    def qty1(self) -> int:
        """Quantità da vendere al target 1."""
        return max(1, round(self.quantita_totale * self.pct1))

    @property
    def qty2(self) -> int:
        """Quantità da vendere al target 2 (sul rimanente dopo T1)."""
        rimasto = self.quantita_totale - self.qty1
        return max(0, round(rimasto * self.pct2))

    @property
    def qty3(self) -> int:
        """Quantità rimanente da vendere al target 3."""
        return max(0, self.quantita_totale - self.qty1 - self.qty2)

    @property
    def profitto_atteso_t1(self) -> float:
        return self.qty1 * (self.target1 - self.prezzo_entrata)

    @property
    def profitto_atteso_t2(self) -> float:
        return self.qty2 * (self.target2 - self.prezzo_entrata)

    @property
    def profitto_atteso_t3(self) -> float:
        return self.qty3 * (self.target3 - self.prezzo_entrata)

    @property
    def profitto_totale_atteso(self) -> float:
        return self.profitto_atteso_t1 + self.profitto_atteso_t2 + self.profitto_atteso_t3

    @property
    def rendimento_atteso_pct(self) -> float:
        costo = self.quantita_totale * self.prezzo_entrata
        return self.profitto_totale_atteso / costo if costo > 0 else 0

    @property
    def risk_reward(self) -> float:
        """Risk/Reward approssimato: reward medio / distanza dal minimo."""
        reward = (self.target3 - self.prezzo_entrata)
        risk   = self.prezzo_entrata * 0.10   # stop loss implicito 10%
        return round(reward / risk, 2) if risk > 0 else 0


# ══════════════════════════════════════════════════════════════
# CALCOLO FAIR VALUE
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def calc_livelli_prezzo(
    ticker: str,
    settore: str = "N/A",
    dati_watchlist: Optional[Dict] = None,
) -> Optional[LivelliPrezzo]:
    """
    Calcola i livelli di prezzo di riferimento per un ticker.
    Combina analisi fondamentale e tecnica.
    """
    # ── 1. Scarica dati storici ───────────────────────────────
    try:
        tkr = yf.Ticker(ticker)
        hist = tkr.history(period="2y", interval="1d", auto_adjust=True)
        if hist.empty or len(hist) < 60:
            return None
        info = tkr.info
    except Exception:
        return None

    prezzo = float(hist["Close"].iloc[-1])
    if prezzo <= 0:
        return None

    # ── 2. Raccolta dati fondamentali ─────────────────────────
    if dati_watchlist:
        pe    = _safe_float(dati_watchlist.get("pe"))
        eps   = _safe_float(info.get("trailingEps"))
        roe   = _safe_float(dati_watchlist.get("roe"))
        bvps  = _safe_float(info.get("bookValue"))
        fcf   = _safe_float(info.get("freeCashflow"))
        shares= _safe_float(info.get("sharesOutstanding"))
    else:
        pe    = _safe_float(info.get("trailingPE") or info.get("forwardPE"))
        eps   = _safe_float(info.get("trailingEps"))
        roe   = _safe_float(info.get("returnOnEquity"))
        bvps  = _safe_float(info.get("bookValue"))
        fcf   = _safe_float(info.get("freeCashflow"))
        shares= _safe_float(info.get("sharesOutstanding"))

    fcf_per_share = (fcf / shares) if fcf and shares and shares > 0 else None

    # ── 3. Calcolo supporti/resistenze tecniche ───────────────
    close = hist["Close"]
    high  = hist["High"]
    low   = hist["Low"]

    ma50  = float(close.rolling(50).mean().iloc[-1])  if len(close) >= 50  else prezzo
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else prezzo
    high52w = float(high.rolling(252).max().iloc[-1]) if len(high) >= 252 else float(high.max())
    low52w  = float(low.rolling(252).min().iloc[-1])  if len(low)  >= 252 else float(low.min())

    # ATR 14 giorni per stop loss
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr14 = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else prezzo * 0.02

    # ── 4. Metodi di valutazione ──────────────────────────────
    metodi = {}

    # Metodo A: P/E relativo al settore
    pe_settore = PE_MEDI_SETTORE.get(settore, PE_MEDI_SETTORE["N/A"])
    if eps and eps > 0:
        fv_pe = eps * pe_settore
        metodi["P/E settore"] = round(fv_pe, 4)

    # Metodo B: Graham Number
    # GN = sqrt(22.5 × EPS × BVPS)
    if eps and eps > 0 and bvps and bvps > 0:
        gn = (22.5 * eps * bvps) ** 0.5
        metodi["Graham Number"] = round(gn, 4)

    # Metodo C: DCF semplificato su FCF o EPS
    # Crescita stimata: media ROE * (1 - payout) oppure 5% default
    growth_rate = 0.05   # default conservativo
    if roe and roe > 0.02:
        growth_rate = min(roe * 0.6, 0.15)   # cap al 15%

    base_earning = fcf_per_share or eps
    if base_earning and base_earning > 0:
        # DCF 10 anni, tasso sconto 9%
        discount = 0.09
        fv_dcf = sum(
            base_earning * ((1 + growth_rate) ** y) / ((1 + discount) ** y)
            for y in range(1, 11)
        )
        # Valore terminale (multiplo 15x)
        terminal = (base_earning * ((1 + growth_rate) ** 10) * 15) / ((1 + discount) ** 10)
        fv_dcf = fv_dcf + terminal
        metodi["DCF (10Y)"] = round(fv_dcf, 4)

    # Metodo D: MA200 come anchor (valore tecnico di lungo)
    metodi["MA 200"] = round(ma200, 4)

    # ── 5. Fair Value composito (media pesata) ────────────────
    pesi_metodi = {
        "P/E settore":   0.30,
        "Graham Number": 0.25,
        "DCF (10Y)":     0.30,
        "MA 200":        0.15,
    }
    fv_sum = 0.0
    peso_tot = 0.0
    for nome, val in metodi.items():
        if val > 0:
            p = pesi_metodi.get(nome, 0.1)
            fv_sum  += val * p
            peso_tot += p

    if peso_tot < 0.1 or fv_sum <= 0:
        # Fallback: P/E corrente * 0.9 (leggero sconto)
        if pe and pe > 0 and eps and eps > 0:
            fv_sum   = eps * pe * 0.9
            peso_tot = 1.0
        else:
            fv_sum   = ma200
            peso_tot = 1.0

    fair_value = round(fv_sum / peso_tot, 4)

    # ── 6. Valutazione ────────────────────────────────────────
    scostamento = (prezzo - fair_value) / fair_value
    if scostamento <= SOGLIA_SOTTOSTIMATO:
        valutazione = "Sottostimato"
    elif scostamento >= SOGLIA_SOVRASTIMATO:
        valutazione = "Sovrastimato"
    else:
        valutazione = "Corretto"

    # ── 7. Livelli tecnici ────────────────────────────────────
    # Minimo stimato: supporto tecnico (max tra low52w e MA200 - 10%)
    minimo = max(low52w, ma200 * 0.88)
    minimo = round(minimo, 4)

    # Massimo stimato: resistenza (max storico 52W oppure +2 sigma)
    rendimenti = close.pct_change().dropna()
    sigma_ann  = float(rendimenti.std() * np.sqrt(252))
    massimo = round(min(high52w * 1.05, prezzo * (1 + sigma_ann * 1.5)), 4)

    # ── 8. Target di uscita ───────────────────────────────────
    # Calcolati su range prezzo → massimo in 3 step con progressione fibonacci
    range_up = massimo - prezzo
    t1 = round(prezzo + range_up * 0.382, 4)   # 38.2% del range
    t2 = round(prezzo + range_up * 0.618, 4)   # 61.8% del range
    t3 = round(prezzo + range_up * 0.850, 4)   # 85% del range

    # Assicura che i target siano sempre crescenti
    t1 = max(t1, prezzo * 1.03)
    t2 = max(t2, t1 * 1.02)
    t3 = max(t3, t2 * 1.02)

    note = _genera_note(valutazione, scostamento, pe, pe_settore, ma200, prezzo, sigma_ann)

    return LivelliPrezzo(
        ticker=ticker,
        prezzo_corrente=prezzo,
        fair_value=fair_value,
        valutazione=valutazione,
        scostamento_pct=scostamento,
        minimo_stimato=minimo,
        massimo_stimato=massimo,
        target1=t1,
        target2=t2,
        target3=t3,
        pct_uscita1=0.50,   # default personalizzabile in UI
        pct_uscita2=0.50,
        pct_uscita3=1.00,
        metodi=metodi,
        note=note,
    )


def _genera_note(valutazione, scost, pe, pe_settore, ma200, prezzo, sigma) -> str:
    note = []
    if valutazione == "Sottostimato":
        note.append(f"Il prezzo è {abs(scost)*100:.1f}% sotto il fair value stimato.")
    elif valutazione == "Sovrastimato":
        note.append(f"Il prezzo è {scost*100:.1f}% sopra il fair value stimato.")
    else:
        note.append("Il prezzo è in linea con il fair value stimato.")
    if pe and pe_settore:
        if pe < pe_settore * 0.7:
            note.append(f"P/E {pe:.1f} molto inferiore alla media settore ({pe_settore:.0f}x): potenziale valore nascosto.")
        elif pe > pe_settore * 1.3:
            note.append(f"P/E {pe:.1f} superiore alla media settore ({pe_settore:.0f}x): il mercato sconta crescita futura elevata.")
    if prezzo > ma200 * 1.15:
        note.append("Attenzione: prezzo molto sopra MA200, possibile mean reversion nel breve.")
    elif prezzo < ma200 * 0.90:
        note.append("Prezzo sotto MA200: trend ribassista di lungo, attendi conferma prima di entrare.")
    if sigma > 0.50:
        note.append(f"Alta volatilità annua ({sigma*100:.0f}%): i target hanno ampia incertezza.")
    return " ".join(note)


def calc_scale_out(
    livelli: LivelliPrezzo,
    prezzo_entrata: float,
    quantita: int,
    pct1: float = 0.50,
    pct2: float = 0.50,
    pct3: float = 1.00,
) -> ScaleOutPlan:
    """Genera il piano di uscita progressiva personalizzato."""
    return ScaleOutPlan(
        ticker=livelli.ticker,
        prezzo_entrata=prezzo_entrata,
        quantita_totale=quantita,
        target1=livelli.target1,
        target2=livelli.target2,
        target3=livelli.target3,
        pct1=pct1,
        pct2=pct2,
        pct3=pct3,
    )


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        v = float(val)
        return None if (v != v) else v
    except (TypeError, ValueError):
        return None
