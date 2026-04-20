"""
scoring.py — Modello di scoring multi-fattoriale v3
Aggiornamenti:
  - Z-score settore-neutro (confronta ticker vs media del suo settore)
  - Sharpe Ratio e Sortino Ratio come fattori aggiuntivi
  - Supporto pesi dinamici da ml_weights.py
  - Pre-filtro Universe invariato
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Optional, List, Dict
from utils.config import SCORING_WEIGHTS, ZSCORE_CAP, MCAP_MIN_M, VOL_MAX_PCT, RET12M_MIN, PREFILTER


# ══════════════════════════════════════════════
# PRE-FILTRO UNIVERSE
# ══════════════════════════════════════════════

def classify_universe_row(row: pd.Series) -> str:
    """Classifica una riga Universe in verde/giallo/rosso."""
    pf_v = PREFILTER["verde"]
    pf_r = PREFILTER["rosso"]

    def _num(val):
        """Converte a float in modo sicuro, ritorna None se non numerico."""
        if val is None:
            return None
        try:
            v = float(val)
            return None if (v != v) else v  # NaN check
        except (ValueError, TypeError):
            return None

    pe      = _num(row.get("pe"))
    roe     = _num(row.get("roe"))
    de      = _num(row.get("de_ratio"))
    ret_6m  = _num(row.get("ret_6m"))
    ret_12m = _num(row.get("ret_12m"))
    mktcap  = _num(row.get("mktcap_M"))

    if pe is not None and (pe < 0 or pe > pf_r["pe_max_abs"]):
        return "rosso"
    if roe is not None and roe < pf_r["roe_min_abs"]:
        return "rosso"
    if de is not None and de > pf_r["de_max_abs"]:
        return "rosso"
    if ret_12m is not None and ret_12m < pf_r["ret12m_min_abs"]:
        return "rosso"

    verde_score = 0
    if pe is not None and pf_v["pe_min"] <= pe <= pf_v["pe_max"]:
        verde_score += 1
    if roe is not None and roe >= pf_v["roe_min"]:
        verde_score += 1
    if de is not None and de <= pf_v["de_max"]:
        verde_score += 1
    if ret_6m is not None and ret_6m >= pf_v["mom6m_min"]:
        verde_score += 1
    if mktcap is not None and mktcap >= pf_v["mcap_min_M"]:
        verde_score += 1

    return "verde" if verde_score >= 3 else "giallo"


def apply_universe_ratings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rating"] = df.apply(classify_universe_row, axis=1)
    return df


def compute_universe_score(row: pd.Series) -> float:
    def _n(val):
        try:
            v = float(val)
            return None if (v != v) else v
        except (TypeError, ValueError):
            return None

    score = 0.0
    count = 0
    ret_6m  = _n(row.get("ret_6m"))
    ret_12m = _n(row.get("ret_12m"))
    pe      = _n(row.get("pe"))
    roe     = _n(row.get("roe"))
    de      = _n(row.get("de_ratio"))
    vol     = _n(row.get("vol_ann"))

    if ret_6m  is not None: score += 0.30 * np.clip(ret_6m  / 0.5,  -1, 1); count += 1
    if ret_12m is not None: score += 0.20 * np.clip(ret_12m / 0.8,  -1, 1); count += 1
    if pe is not None and pe > 0:
        s = 1.0 - (pe - 5) / 20 if pe <= 25 else -min(1.0, (pe - 25) / 25)
        score += 0.15 * s; count += 1
    if roe is not None: score += 0.15 * np.clip(roe / 0.25, -1,  1);   count += 1
    if de  is not None: score += 0.10 * np.clip(-de / 3,    -1,  0.5); count += 1
    if vol is not None: score += 0.10 * np.clip(-vol / 0.6 + 0.5, -1, 1); count += 1
    return round(score, 4) if count > 0 else 0.0


def select_auto_top_n(df: pd.DataFrame, n: int = 20) -> List[str]:
    df = df.copy()
    df["__score"] = df.apply(compute_universe_score, axis=1)
    verdi  = df[df["rating"] == "verde"].sort_values("__score", ascending=False)
    gialli = df[df["rating"] == "giallo"].sort_values("__score", ascending=False)
    selected = verdi["ticker"].tolist()
    remaining = n - len(selected)
    if remaining > 0:
        selected.extend(gialli["ticker"].tolist()[:remaining])
    return selected[:n]


# ══════════════════════════════════════════════
# Z-SCORE HELPERS
# ══════════════════════════════════════════════

def zscore_series(series: pd.Series, invert: bool = False,
                  ref_mean: float = None, ref_std: float = None) -> pd.Series:
    """
    Calcola z-score per una Serie, clippato a ±ZSCORE_CAP.
    Se ref_mean/ref_std forniti, usa quelli (settore-neutro).
    """
    mask = series.notna()
    if mask.sum() < 2 and ref_mean is None:
        return pd.Series(0.0, index=series.index)
    mean = ref_mean if ref_mean is not None else series[mask].mean()
    std  = ref_std  if ref_std  is not None else series[mask].std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    z = (series - mean) / std
    if invert:
        z = -z
    return z.clip(-ZSCORE_CAP, ZSCORE_CAP).fillna(0)


def _sector_stats(df: pd.DataFrame, col: str) -> Dict[str, tuple]:
    """
    Calcola media e std per ogni settore su una colonna numerica.
    Ritorna dict {settore: (mean, std)}.
    """
    stats = {}
    if "settore" not in df.columns or col not in df.columns:
        return stats
    for settore, grp in df.groupby("settore"):
        s = pd.to_numeric(grp[col], errors="coerce").dropna()
        if len(s) >= 3:
            stats[str(settore)] = (s.mean(), s.std())
    return stats


def _zscore_settore_neutro(df: pd.DataFrame, col: str, invert: bool = False) -> pd.Series:
    """
    Z-score relativo al settore: confronta ogni ticker con la media
    del suo settore invece che con l'intero indice.
    Se il settore ha meno di 3 ticker, cade back al global z-score.
    """
    sector_stats = _sector_stats(df, col)
    global_series = pd.to_numeric(df[col], errors="coerce") if col in df.columns else pd.Series(dtype=float)

    z_values = []
    for idx, row in df.iterrows():
        val = pd.to_numeric(row.get(col), errors="coerce")
        settore = str(row.get("settore", ""))
        if pd.isna(val):
            z_values.append(0.0)
            continue
        if settore in sector_stats:
            mean, std = sector_stats[settore]
            if std > 0 and not np.isnan(std):
                z = (val - mean) / std
            else:
                z = 0.0
        else:
            # Fallback globale
            gm  = global_series.mean()
            gs  = global_series.std()
            z   = (val - gm) / gs if gs > 0 else 0.0
        if invert:
            z = -z
        z = np.clip(z, -ZSCORE_CAP, ZSCORE_CAP)
        z_values.append(float(z) if not np.isnan(z) else 0.0)

    return pd.Series(z_values, index=df.index)


# ══════════════════════════════════════════════
# SHARPE / SORTINO
# ══════════════════════════════════════════════

def calc_sharpe(ret_12m: Optional[float], vol_ann: Optional[float],
                risk_free: float = 0.045) -> Optional[float]:
    """
    Sharpe Ratio semplificato: (Ret12M - RiskFree) / VolAnn.
    Risk free default = 4.5% (approssimazione Treasury USA 2025).
    """
    if ret_12m is None or vol_ann is None or vol_ann <= 0:
        return None
    try:
        return round((float(ret_12m) - risk_free) / float(vol_ann), 3)
    except Exception:
        return None


def calc_sortino(ret_12m: Optional[float], vol_ann: Optional[float],
                 risk_free: float = 0.045) -> Optional[float]:
    """
    Sortino Ratio approssimato: (Ret12M - RiskFree) / (VolAnn * 0.7).
    Il downside deviation è approssimato come ~70% della vol totale.
    Per calcolo preciso servirebbero i rendimenti giornalieri.
    """
    if ret_12m is None or vol_ann is None or vol_ann <= 0:
        return None
    try:
        downside_vol = float(vol_ann) * 0.70
        return round((float(ret_12m) - risk_free) / downside_vol, 3)
    except Exception:
        return None


# ══════════════════════════════════════════════
# SCORING WATCHLIST PRINCIPALE
# ══════════════════════════════════════════════

def compute_watchlist_scores(
    df: pd.DataFrame,
    pesi_override: Dict[str, float] = None,
    settore_neutro: bool = True,
) -> pd.DataFrame:
    """
    Calcola z-score per ogni fattore e score composito pesato.

    Parametri:
    - pesi_override:  se forniti (da ml_weights), usa questi invece dei default
    - settore_neutro: se True, z-score relativo al settore (più preciso)
    """
    df = df.copy()

    # Usa pesi dinamici se disponibili in session_state, altrimenti default
    if pesi_override:
        w = pesi_override
    else:
        w = st.session_state.get("pesi_dinamici", SCORING_WEIGHTS)

    # ── Z-scores ──────────────────────────────────────────────
    fn = _zscore_settore_neutro if settore_neutro and "settore" in df.columns else _zscore_globale

    df["z_mom6m"]  = fn(df, "ret_6m",       invert=False)
    df["z_mom12m"] = fn(df, "ret_12m",      invert=False)
    df["z_roe"]    = fn(df, "roe",           invert=False)
    df["z_de"]     = fn(df, "de_ratio",      invert=True)
    df["z_margin"] = fn(df, "gross_margin",  invert=False)
    df["z_lowvol"] = fn(df, "vol_ann",       invert=True)
    df["z_pe"]     = fn(df, "pe",            invert=True)
    df["z_div"]    = fn(df, "div_yield",     invert=False)

    # ── Sharpe e Sortino ──────────────────────────────────────
    df["sharpe"]  = df.apply(lambda r: calc_sharpe(r.get("ret_12m"), r.get("vol_ann")), axis=1)
    df["sortino"] = df.apply(lambda r: calc_sortino(r.get("ret_12m"), r.get("vol_ann")), axis=1)

    # Z-score anche per Sharpe (bonus aggiuntivo, non entra nei pesi principali)
    df["z_sharpe"] = zscore_series(pd.to_numeric(df["sharpe"], errors="coerce"))

    # ── Score composito ───────────────────────────────────────
    df["score"] = (
        df["z_mom6m"]  * w.get("mom_6m",  0.20) +
        df["z_mom12m"] * w.get("mom_12m", 0.15) +
        df["z_roe"]    * w.get("roe",     0.10) +
        df["z_de"]     * w.get("de_inv",  0.10) +
        df["z_margin"] * w.get("margin",  0.10) +
        df["z_lowvol"] * w.get("lowvol",  0.15) +
        df["z_pe"]     * w.get("pe_inv",  0.10) +
        df["z_div"]    * w.get("div_yld", 0.10)
    )
    # Bonus Sharpe: piccolo contributo aggiuntivo (+5% peso)
    df["score"] = df["score"] + df["z_sharpe"] * 0.05
    df["score"] = df["score"].round(4)

    # ── Rank, Tier, Percentile ────────────────────────────────
    df["rank"]       = df["score"].rank(ascending=False, method="min").astype(int)
    df["tier"]       = df.apply(_classify_tier, axis=1)
    df["percentile"] = (df["score"].rank(pct=True) * 100).round(0).astype(int)

    return df


def _zscore_globale(df: pd.DataFrame, col: str, invert: bool = False) -> pd.Series:
    """Fallback: z-score globale (non settore-neutro)."""
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return zscore_series(
        pd.to_numeric(df[col], errors="coerce"), invert=invert
    ).reindex(df.index).fillna(0)


def _classify_tier(row: pd.Series) -> str:
    key_fields = ["ret_6m", "ret_12m", "vol_ann", "pe", "roe", "de_ratio", "gross_margin"]
    missing = sum(1 for f in key_fields if pd.isna(row.get(f)))
    mktcap  = row.get("mktcap_M", 0) or 0
    vol_ann = row.get("vol_ann", 1) or 1
    ret_12m = row.get("ret_12m") or 0
    cond_alta  = (missing == 0 and mktcap >= MCAP_MIN_M and
                  vol_ann <= VOL_MAX_PCT and ret_12m >= RET12M_MIN)
    cond_bassa = (missing >= 3 or mktcap < MCAP_MIN_M * 0.5 or
                  vol_ann > VOL_MAX_PCT * 1.5)
    if cond_alta:  return "Alta"
    if cond_bassa: return "Bassa"
    return "Media"



# ══════════════════════════════════════════════
# PRE-FILTRO UNIVERSE
# ══════════════════════════════════════════════

def classify_universe_row(row: pd.Series) -> str:
    """
    Classifica una riga del dataframe Universe in verde/giallo/rosso.
    Ritorna stringa: 'verde', 'giallo', 'rosso'.
    """
    pf_v = PREFILTER["verde"]
    pf_r = PREFILTER["rosso"]

    def _num(val):
        if val is None:
            return None
        try:
            v = float(val)
            return None if (v != v) else v
        except (ValueError, TypeError):
            return None

    pe      = _num(row.get("pe"))
    roe     = _num(row.get("roe"))
    de      = _num(row.get("de_ratio"))
    ret_6m  = _num(row.get("ret_6m"))
    ret_12m = _num(row.get("ret_12m"))
    mktcap  = _num(row.get("mktcap_M"))

    # ── ROSSO: qualsiasi flag negativo forte ──
    if pe is not None and (pe < 0 or pe > pf_r["pe_max_abs"]):
        return "rosso"
    if roe is not None and roe < pf_r["roe_min_abs"]:
        return "rosso"
    if de is not None and de > pf_r["de_max_abs"]:
        return "rosso"
    if ret_12m is not None and ret_12m < pf_r["ret12m_min_abs"]:
        return "rosso"

    # ── VERDE: tutti i criteri positivi soddisfatti ──
    verde_score = 0
    verde_required = 3  # almeno 3 criteri su 5 per essere verde

    if pe is not None and pf_v["pe_min"] <= pe <= pf_v["pe_max"]:
        verde_score += 1
    if roe is not None and roe >= pf_v["roe_min"]:
        verde_score += 1
    if de is not None and de <= pf_v["de_max"]:
        verde_score += 1
    if ret_6m is not None and ret_6m >= pf_v["mom6m_min"]:
        verde_score += 1
    if mktcap is not None and mktcap >= pf_v["mcap_min_M"]:
        verde_score += 1

    if verde_score >= verde_required:
        return "verde"

    return "giallo"


def apply_universe_ratings(df: pd.DataFrame) -> pd.DataFrame:
    """Aggiunge colonna 'rating' al DataFrame Universe."""
    df = df.copy()
    df["rating"] = df.apply(classify_universe_row, axis=1)
    return df


def compute_universe_score(row: pd.Series) -> float:
    """
    Score semplice per ranking Universe (per selezione automatica Top N).
    Combinazione lineare normalizzata tra 0 e 1.
    """
    def _n(val):
        try:
            v = float(val)
            return None if (v != v) else v
        except (TypeError, ValueError):
            return None

    score = 0.0
    count = 0

    ret_6m  = _n(row.get("ret_6m"))
    ret_12m = _n(row.get("ret_12m"))
    pe      = _n(row.get("pe"))
    roe     = _n(row.get("roe"))
    de      = _n(row.get("de_ratio"))
    vol     = _n(row.get("vol_ann"))

    if ret_6m is not None:
        score += 0.30 * np.clip(ret_6m / 0.5, -1, 1); count += 1
    if ret_12m is not None:
        score += 0.20 * np.clip(ret_12m / 0.8, -1, 1); count += 1
    if pe is not None and pe > 0:
        if pe < 5:    s = -0.5
        elif pe <= 25: s = 1.0 - (pe - 5) / 20
        else:          s = -min(1.0, (pe - 25) / 25)
        score += 0.15 * s; count += 1
    if roe is not None:
        score += 0.15 * np.clip(roe / 0.25, -1, 1); count += 1
    if de is not None:
        score += 0.10 * np.clip(-de / 3, -1, 0.5); count += 1
    if vol is not None:
        score += 0.10 * np.clip(-vol / 0.6 + 0.5, -1, 1); count += 1

    return round(score, 4) if count > 0 else 0.0


def select_auto_top_n(df: pd.DataFrame, n: int = 20) -> List[str]:
    """
    Selezione automatica Top N ticker dal DataFrame Universe.
    Priorità: verde > giallo. Entrambi ordinati per score decrescente.
    Ritorna lista di ticker.
    """
    df = df.copy()
    df["__score"] = df.apply(compute_universe_score, axis=1)

    verdi  = df[df["rating"] == "verde"].sort_values("__score", ascending=False)
    gialli = df[df["rating"] == "giallo"].sort_values("__score", ascending=False)

    selected = []
    selected.extend(verdi["ticker"].tolist())
    remaining = n - len(selected)
    if remaining > 0:
        selected.extend(gialli["ticker"].tolist()[:remaining])

    return selected[:n]



# ══════════════════════════════════════════════
# SCORING WATCHLIST (z-score multi-fattoriale)
# ══════════════════════════════════════════════

def zscore_series(series: pd.Series, invert: bool = False) -> pd.Series:
    """
    Calcola z-score per una Serie, clippato a ±ZSCORE_CAP.
    Se invert=True, moltiplica per -1 (dove più basso = meglio).
    """
    mask = series.notna()
    if mask.sum() < 2:
        return pd.Series(0.0, index=series.index)
    mean = series[mask].mean()
    std  = series[mask].std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=series.index)
    z = (series - mean) / std
    if invert:
        z = -z
    return z.clip(-ZSCORE_CAP, ZSCORE_CAP).fillna(0)


def compute_watchlist_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola z-score per ogni fattore e score composito pesato.
    Input: DataFrame con colonne metriche (prezzo, ret_6m, ret_12m, vol_ann, pe, roe, de_ratio, gross_margin, div_yield)
    Output: DataFrame con colonne z_*, score, rank, tier aggiunte.
    """
    df = df.copy()
    w = SCORING_WEIGHTS

    # Z-scores per ogni fattore
    df["z_mom6m"]   = zscore_series(pd.to_numeric(df.get("ret_6m",   pd.Series(dtype=float)), errors="coerce"), invert=False)
    df["z_mom12m"]  = zscore_series(pd.to_numeric(df.get("ret_12m",  pd.Series(dtype=float)), errors="coerce"), invert=False)
    df["z_roe"]     = zscore_series(pd.to_numeric(df.get("roe",      pd.Series(dtype=float)), errors="coerce"), invert=False)
    df["z_de"]      = zscore_series(pd.to_numeric(df.get("de_ratio", pd.Series(dtype=float)), errors="coerce"), invert=True)   # inverso
    df["z_margin"]  = zscore_series(pd.to_numeric(df.get("gross_margin", pd.Series(dtype=float)), errors="coerce"), invert=False)
    df["z_lowvol"]  = zscore_series(pd.to_numeric(df.get("vol_ann",  pd.Series(dtype=float)), errors="coerce"), invert=True)   # inverso
    df["z_pe"]      = zscore_series(pd.to_numeric(df.get("pe",       pd.Series(dtype=float)), errors="coerce"), invert=True)   # inverso
    df["z_div"]     = zscore_series(pd.to_numeric(df.get("div_yield",pd.Series(dtype=float)), errors="coerce"), invert=False)

    # Score composito pesato
    df["score"] = (
        df["z_mom6m"]  * w["mom_6m"]  +
        df["z_mom12m"] * w["mom_12m"] +
        df["z_roe"]    * w["roe"]     +
        df["z_de"]     * w["de_inv"]  +
        df["z_margin"] * w["margin"]  +
        df["z_lowvol"] * w["lowvol"]  +
        df["z_pe"]     * w["pe_inv"]  +
        df["z_div"]    * w["div_yld"]
    )
    df["score"] = df["score"].round(4)

    # Rank
    df["rank"] = df["score"].rank(ascending=False, method="min").astype(int)

    # Tier
    df["tier"] = df.apply(_classify_tier, axis=1)

    # Percentile rispetto alla watchlist
    df["percentile"] = (df["score"].rank(pct=True) * 100).round(0).astype(int)

    return df


def _classify_tier(row: pd.Series) -> str:
    """Classifica tier di affidabilità del segnale."""
    # Conta dati mancanti nei campi fondamentali
    key_fields = ["ret_6m", "ret_12m", "vol_ann", "pe", "roe", "de_ratio", "gross_margin"]
    missing = sum(1 for f in key_fields if pd.isna(row.get(f)))

    mktcap  = row.get("mktcap_M", 0) or 0
    vol_ann = row.get("vol_ann", 1) or 1
    ret_12m = row.get("ret_12m", 0)
    if ret_12m is None:
        ret_12m = 0

    cond_alta = (
        missing == 0 and
        mktcap >= MCAP_MIN_M and
        vol_ann <= VOL_MAX_PCT and
        ret_12m >= RET12M_MIN
    )
    cond_bassa = (
        missing >= 3 or
        mktcap < MCAP_MIN_M * 0.5 or
        vol_ann > VOL_MAX_PCT * 1.5
    )

    if cond_alta:
        return "Alta"
    if cond_bassa:
        return "Bassa"
    return "Media"
