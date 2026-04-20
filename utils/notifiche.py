"""
notifiche.py — Invio notifiche via Telegram Bot.
Supporta: digest settimanale Top 5, alert su variazione score Preferiti,
          alert su cambio tier o attraversamento soglia.
"""

import requests
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List


# ══════════════════════════════════════════════
# CONFIGURAZIONE
# ══════════════════════════════════════════════

def get_telegram_config() -> tuple[str, str]:
    """Legge token e chat_id dai secrets. Ritorna (token, chat_id)."""
    try:
        token   = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
        return str(token), str(chat_id)
    except Exception:
        return "", ""


def telegram_configured() -> bool:
    token, chat_id = get_telegram_config()
    return bool(token) and bool(chat_id)


# ══════════════════════════════════════════════
# INVIO BASE
# ══════════════════════════════════════════════

def send_message(testo: str, parse_mode: str = "HTML") -> bool:
    """
    Invia un messaggio al bot Telegram configurato.
    Ritorna True se inviato con successo.
    """
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id":    chat_id,
            "text":       testo,
            "parse_mode": parse_mode,
        }
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def test_connection() -> tuple[bool, str]:
    """
    Verifica la connessione al bot Telegram.
    Ritorna (successo, messaggio_esito).
    """
    token, chat_id = get_telegram_config()
    if not token:
        return False, "TELEGRAM_BOT_TOKEN non configurato in secrets.toml"
    if not chat_id:
        return False, "TELEGRAM_CHAT_ID non configurato in secrets.toml"
    ok = send_message("✅ <b>Screener Azioni</b> — Connessione Telegram attiva!")
    if ok:
        return True, "Messaggio di test inviato con successo!"
    return False, "Errore nell'invio. Controlla token e chat_id."


# ══════════════════════════════════════════════
# MESSAGGI STRUTTURATI
# ══════════════════════════════════════════════

def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{float(v)*100:+.1f}%"

def _fmt_num(v, dec=1) -> str:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{float(v):,.{dec}f}"

def _tier_emoji(tier: str) -> str:
    return {"Alta": "🟢", "Media": "🟡", "Bassa": "🔴"}.get(str(tier), "⚪")


def invia_digest_top5(df_watchlist: pd.DataFrame, indice: str = "") -> bool:
    """
    Invia il digest settimanale con i Top 5 della Watchlist.
    df_watchlist deve avere le colonne standard (rank, score, tier, ecc.)
    """
    if df_watchlist is None or df_watchlist.empty:
        return False

    display = df_watchlist.reset_index() if "ticker" not in df_watchlist.columns else df_watchlist.copy()
    top5 = display.sort_values("rank").head(5)

    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    header = f"📊 <b>Screener Azioni — Top 5</b>\n"
    if indice:
        header += f"🗂 Indice: <i>{indice}</i>\n"
    header += f"🕐 {now}\n\n"

    righe = []
    medaglie = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (_, row) in enumerate(top5.iterrows()):
        ticker  = str(row.get("ticker", ""))
        nome    = str(row.get("nome", ticker))
        score   = row.get("score", 0)
        tier    = str(row.get("tier", ""))
        ret6    = row.get("ret_6m")
        ret12   = row.get("ret_12m")
        pe      = row.get("pe")

        riga = (
            f"{medaglie[i]} <b>{ticker}</b> — {nome}\n"
            f"   Score: <b>{score:.3f}</b>  {_tier_emoji(tier)} {tier}\n"
            f"   Ret 6M: {_fmt_pct(ret6)}  |  Ret 12M: {_fmt_pct(ret12)}"
        )
        if pe:
            riga += f"  |  P/E: {_fmt_num(pe)}"
        righe.append(riga)

    footer = "\n\n⚠️ <i>Non è consulenza finanziaria. Fai sempre le tue verifiche.</i>"
    testo = header + "\n\n".join(righe) + footer
    return send_message(testo)


def invia_alert_score(
    ticker: str,
    score_old: float,
    score_new: float,
    tier_old: str,
    tier_new: str,
    nome: str = "",
) -> bool:
    """
    Invia un alert quando lo score di un Preferito cambia significativamente.
    """
    delta = score_new - score_old
    if abs(delta) < 0.05:
        return False   # variazione troppo piccola, non invia

    direzione = "⬆️ Miglioramento" if delta > 0 else "⬇️ Peggioramento"
    cambio_tier = tier_old != tier_new

    testo = (
        f"🔔 <b>Alert Preferiti — {ticker}</b>\n"
        f"{nome}\n\n"
        f"{direzione} dello score:\n"
        f"   {score_old:.3f} → <b>{score_new:.3f}</b>  ({delta:+.3f})\n"
    )
    if cambio_tier:
        testo += (
            f"\n📊 Cambio tier: "
            f"{_tier_emoji(tier_old)} {tier_old} → "
            f"{_tier_emoji(tier_new)} <b>{tier_new}</b>"
        )

    testo += "\n\n⚠️ <i>Non è consulenza finanziaria.</i>"
    return send_message(testo)


def invia_alert_soglia(
    ticker: str,
    nome: str,
    tipo_soglia: str,
    valore: float,
    soglia: float,
) -> bool:
    """
    Invia un alert quando un indicatore supera una soglia impostata dall'utente.
    tipo_soglia: es. "Ret 12M", "Score", "Dividend Yield"
    """
    testo = (
        f"🚨 <b>Soglia raggiunta — {ticker}</b>\n"
        f"{nome}\n\n"
        f"📈 <b>{tipo_soglia}</b> ha superato la soglia:\n"
        f"   Valore attuale: <b>{valore:.3f}</b>\n"
        f"   Soglia impostata: {soglia:.3f}\n\n"
        f"⚠️ <i>Non è consulenza finanziaria.</i>"
    )
    return send_message(testo)


def invia_alert_verde(ticker: str, nome: str, settore: str, score: float) -> bool:
    """
    Alert quando un ticker passa da Giallo a Verde nel pre-filtro Universe.
    """
    testo = (
        f"🟢 <b>Nuovo Verde — {ticker}</b>\n"
        f"{nome}  |  {settore}\n\n"
        f"Il ticker è appena entrato nella zona Verde del pre-filtro.\n"
        f"Score attuale: <b>{score:.3f}</b>\n\n"
        f"💡 Potrebbe valere una verifica in Watchlist.\n\n"
        f"⚠️ <i>Non è consulenza finanziaria.</i>"
    )
    return send_message(testo)


def controlla_alert_preferiti(
    df_preferiti: pd.DataFrame,
    soglia_score: float = 0.10,
) -> List[dict]:
    """
    Confronta gli ultimi due snapshot di ogni ticker nei Preferiti
    e ritorna la lista di alert da inviare.

    soglia_score: variazione minima dello score per generare un alert.
    """
    if df_preferiti is None or df_preferiti.empty:
        return []

    alert_list = []
    for ticker in df_preferiti["ticker"].dropna().unique():
        storico = df_preferiti[
            df_preferiti["ticker"] == ticker
        ].sort_values("data_snapshot")

        if len(storico) < 2:
            continue

        ultimo    = storico.iloc[-1]
        penultimo = storico.iloc[-2]

        score_new = pd.to_numeric(ultimo.get("score"),    errors="coerce")
        score_old = pd.to_numeric(penultimo.get("score"), errors="coerce")
        tier_new  = str(ultimo.get("tier",    ""))
        tier_old  = str(penultimo.get("tier", ""))
        nome      = str(ultimo.get("nome", ticker))

        if pd.isna(score_new) or pd.isna(score_old):
            continue

        delta = abs(score_new - score_old)
        cambio_tier = tier_old != tier_new and tier_old != "" and tier_new != ""

        if delta >= soglia_score or cambio_tier:
            alert_list.append({
                "ticker":    ticker,
                "nome":      nome,
                "score_old": float(score_old),
                "score_new": float(score_new),
                "tier_old":  tier_old,
                "tier_new":  tier_new,
                "delta":     float(score_new - score_old),
            })

    return alert_list
