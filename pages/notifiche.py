"""
Notifiche — Configurazione e invio manuale notifiche Telegram
"""

import streamlit as st
import pandas as pd
from utils.notifiche import (
    telegram_configured, test_connection,
    invia_digest_top5, invia_alert_score,
    controlla_alert_preferiti, send_message,
)
from utils.storage import load_preferiti, gdrive_available


st.title("🔔 Notifiche Telegram")
st.caption("Ricevi digest e alert direttamente sul tuo telefono via Telegram.")

# ── Stato configurazione ──────────────────────────────────────
configured = telegram_configured()

if not configured:
    st.error("""
    **Telegram non ancora configurato.**
    Segui i 3 passi nella sezione qui sotto per attivarlo.
    """)
else:
    st.success("✅ Telegram configurato e attivo.")

# ── Guida configurazione ──────────────────────────────────────
with st.expander("📋 Come configurare Telegram (3 passi, 5 minuti)", expanded=not configured):
    st.markdown("""
    ### Passo 1 — Crea il Bot
    1. Apri Telegram e cerca **@BotFather**
    2. Scrivi `/newbot`
    3. Dai un nome al bot (es. `ScreenerAzioniBot`)
    4. BotFather ti risponde con un **token** tipo: `7123456789:AAFxxxxxxxx`
    5. Copia quel token

    ### Passo 2 — Ottieni il tuo Chat ID
    1. Cerca il tuo bot appena creato su Telegram e scrivi `/start`
    2. Apri questo link nel browser (sostituisci TON_TOKEN con il tuo):
       `https://api.telegram.org/botTON_TOKEN/getUpdates`
    3. Cerca nella risposta il campo `"id"` dentro `"chat"` — quel numero è il tuo **Chat ID**

    ### Passo 3 — Aggiungi al secrets.toml
    Aggiungi queste due righe al tuo file `.streamlit/secrets.toml`:
    ```
    TELEGRAM_BOT_TOKEN = "7123456789:AAFxxxxxxxx"
    TELEGRAM_CHAT_ID   = "123456789"
    ```
    Poi aggiorna anche i Secrets su **Streamlit Community Cloud**
    (Settings → Secrets → aggiungi le stesse righe → Save).
    """)

if not configured:
    st.stop()

# ── Test connessione ──────────────────────────────────────────
st.divider()
st.subheader("🧪 Test Connessione")

col1, col2 = st.columns([2, 3])
with col1:
    if st.button("📨 Invia messaggio di test", use_container_width=True):
        with st.spinner("Invio in corso..."):
            ok, msg = test_connection()
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")
with col2:
    st.info("Premi il pulsante per verificare che il bot risponda sul tuo Telegram.")

# ── Digest manuale Top 5 ──────────────────────────────────────
st.divider()
st.subheader("📊 Invia Digest Top 5")

df_watch: pd.DataFrame = st.session_state.get("watchlist_data")

if df_watch is None or df_watch.empty:
    st.warning("Nessun dato Watchlist disponibile. Vai in Watchlist e aggiorna i dati prima di inviare il digest.")
else:
    col1, col2 = st.columns([2, 3])
    with col1:
        indice_label = st.text_input(
            "Etichetta indice (opzionale)",
            placeholder="es. S&P 500, FTSE MIB...",
            key="digest_indice",
        )
        if st.button("📤 Invia Digest Top 5 ora", type="primary", use_container_width=True):
            with st.spinner("Invio digest..."):
                ok = invia_digest_top5(df_watch, indice=indice_label)
            if ok:
                st.success("✅ Digest inviato! Controlla Telegram.")
            else:
                st.error("❌ Errore nell'invio. Controlla la configurazione.")
    with col2:
        top5 = df_watch.reset_index().sort_values("rank").head(5)
        st.caption("Anteprima — Top 5 che verrà inviato:")
        if "ticker" in top5.columns and "score" in top5.columns:
            st.dataframe(
                top5[["ticker", "nome", "score", "tier"]].reset_index(drop=True),
                hide_index=True, use_container_width=True,
                column_config={
                    "score": st.column_config.NumberColumn("Score", format="%.3f"),
                }
            )

# ── Alert Preferiti ───────────────────────────────────────────
st.divider()
st.subheader("⭐ Alert Preferiti — Variazioni Score")

if not gdrive_available():
    st.warning("Google Sheets non configurato. I Preferiti non sono disponibili.")
else:
    col1, col2 = st.columns([2, 3])
    with col1:
        soglia = st.slider(
            "Soglia variazione score per alert",
            min_value=0.05, max_value=0.50,
            value=0.10, step=0.05,
            key="soglia_alert",
            help="Variazione minima dello score tra due snapshot per generare un alert",
        )
        if st.button("🔍 Controlla e invia alert", use_container_width=True):
            with st.spinner("Caricamento Preferiti e analisi..."):
                df_pref = load_preferiti()
                alert_list = controlla_alert_preferiti(df_pref, soglia_score=soglia)

            if not alert_list:
                st.info("Nessuna variazione significativa rilevata nei Preferiti.")
            else:
                inviati = 0
                for alert in alert_list:
                    ok = invia_alert_score(
                        ticker=alert["ticker"],
                        nome=alert["nome"],
                        score_old=alert["score_old"],
                        score_new=alert["score_new"],
                        tier_old=alert["tier_old"],
                        tier_new=alert["tier_new"],
                    )
                    if ok:
                        inviati += 1
                st.success(f"✅ {inviati} alert inviati su {len(alert_list)} variazioni rilevate.")

    with col2:
        st.info(f"""
        **Come funziona:**

        Il sistema confronta gli ultimi due snapshot di ogni ticker nei Preferiti.
        Se lo score è cambiato di più di **{soglia:.2f}** punti, o se il tier è cambiato
        (es. da Media ad Alta), ricevi un messaggio Telegram con i dettagli.

        💡 Usa questo pulsante dopo aver aggiornato i Preferiti ogni settimana.
        """)

# ── Messaggio personalizzato ──────────────────────────────────
st.divider()
st.subheader("✏️ Messaggio Personalizzato")

with st.expander("Invia un messaggio libero sul bot"):
    testo_custom = st.text_area(
        "Testo del messaggio",
        placeholder="Scrivi qui il tuo messaggio...",
        key="custom_msg",
        height=100,
    )
    if st.button("📨 Invia", key="btn_custom"):
        if not testo_custom.strip():
            st.warning("Il messaggio è vuoto.")
        else:
            ok = send_message(testo_custom)
            if ok:
                st.success("✅ Messaggio inviato!")
            else:
                st.error("❌ Errore nell'invio.")

# ── Programma invio automatico ────────────────────────────────
st.divider()
st.subheader("🗓 Invio Automatico")

st.info("""
**Nota sul funzionamento automatico:**

Streamlit Community Cloud non supporta task schedulati in background.
Per ricevere digest automatici settimanali senza aprire l'app, hai due opzioni:

**Opzione A — Manuale** *(consigliata per iniziare)*
Apri l'app ogni settimana, aggiorna la Watchlist e premi "Invia Digest Top 5".

**Opzione B — GitHub Actions** *(automatica, richiede 15 min di setup)*
Si può configurare un workflow su GitHub che esegue uno script Python ogni lunedì mattina,
aggiorna i dati e invia il digest automaticamente. Scrivimi se vuoi implementarlo.
""")
