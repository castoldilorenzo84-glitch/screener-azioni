"""
ml_weights.py — Pesi dinamici del modello di scoring.

In base al regime di mercato (Bull/Laterale/Bear/Stress),
il sistema adatta automaticamente i pesi dei fattori per
ottimizzare il segnale nel contesto corrente.

Logica basata su evidenza empirica:
- Bull:    momentum domina, valutazione meno importante
- Laterale: qualità e dividendi offrono stabilità
- Bear:    low-vol e dividendi proteggono il portafoglio
- Stress:  massima difensività, momentum invertito
"""

from typing import Dict
from utils.ciclo_mercato import RegimeMercato

# ══════════════════════════════════════════════
# PESI PER REGIME
# ══════════════════════════════════════════════

PESI_BULL = {
    "mom_6m":   0.28,   # momentum forte in bull market
    "mom_12m":  0.20,
    "roe":      0.12,
    "de_inv":   0.07,
    "margin":   0.08,
    "lowvol":   0.08,   # bassa priorità in bull
    "pe_inv":   0.07,
    "div_yld":  0.10,
}

PESI_LATERALE = {
    "mom_6m":   0.18,
    "mom_12m":  0.14,
    "roe":      0.14,
    "de_inv":   0.12,
    "margin":   0.12,
    "lowvol":   0.12,
    "pe_inv":   0.10,
    "div_yld":  0.08,
}

PESI_BEAR = {
    "mom_6m":   0.10,   # momentum meno affidabile in bear
    "mom_12m":  0.08,
    "roe":      0.12,
    "de_inv":   0.15,   # solidità finanziaria cruciale
    "margin":   0.12,
    "lowvol":   0.22,   # bassa volatilità protegge
    "pe_inv":   0.10,
    "div_yld":  0.11,   # dividendi come cuscinetto
}

PESI_STRESS = {
    "mom_6m":   0.05,   # momentum negativo in crash
    "mom_12m":  0.05,
    "roe":      0.10,
    "de_inv":   0.20,   # aziende senza debito sopravvivono
    "margin":   0.10,
    "lowvol":   0.28,   # massima priorità a bassa vol
    "pe_inv":   0.07,
    "div_yld":  0.15,   # dividendi = cashflow reale
}

REGIME_PESI = {
    "Bull":     PESI_BULL,
    "Laterale": PESI_LATERALE,
    "Bear":     PESI_BEAR,
    "Stress":   PESI_STRESS,
}

# Pesi di default (fallback)
PESI_DEFAULT = {
    "mom_6m":   0.20,
    "mom_12m":  0.15,
    "roe":      0.10,
    "de_inv":   0.10,
    "margin":   0.10,
    "lowvol":   0.15,
    "pe_inv":   0.10,
    "div_yld":  0.10,
}


def get_pesi_dinamici(regime: RegimeMercato) -> Dict[str, float]:
    """
    Ritorna i pesi adattati al regime corrente.
    Fa un blend 70% regime / 30% default per evitare
    cambiamenti troppo bruschi.
    """
    regime_w = REGIME_PESI.get(regime.nome, PESI_DEFAULT)
    blend = {}
    for k in PESI_DEFAULT:
        blend[k] = round(0.70 * regime_w.get(k, PESI_DEFAULT[k]) +
                         0.30 * PESI_DEFAULT[k], 4)
    # Normalizza per assicurarsi che la somma sia 1.0
    tot = sum(blend.values())
    return {k: round(v / tot, 4) for k, v in blend.items()}


def confronta_pesi(pesi_attuali: Dict[str, float]) -> list:
    """
    Ritorna una lista di dict con confronto tra pesi default e dinamici.
    Utile per la visualizzazione in UI.
    """
    labels = {
        "mom_6m":  "Momentum 6M",
        "mom_12m": "Momentum 12M",
        "roe":     "ROE",
        "de_inv":  "D/E inverso",
        "margin":  "Gross Margin",
        "lowvol":  "Low Volatility",
        "pe_inv":  "P/E inverso",
        "div_yld": "Dividend Yield",
    }
    rows = []
    for k, label in labels.items():
        default = PESI_DEFAULT.get(k, 0)
        attuale = pesi_attuali.get(k, 0)
        delta   = attuale - default
        rows.append({
            "Fattore":    label,
            "Default":    f"{default*100:.0f}%",
            "Dinamico":   f"{attuale*100:.0f}%",
            "Variazione": f"{delta*100:+.0f}%",
            "_delta":     delta,
        })
    return rows
