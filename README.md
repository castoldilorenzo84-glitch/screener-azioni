# 📊 Screener Azioni USA & Europa — Medio Periodo

App Streamlit per la ricerca di opportunità di investimento (orizzonte 1–12 mesi).
Accessibile da browser e smartphone, hostata gratuitamente su Streamlit Community Cloud.

---

## 🗺️ Struttura dell'app

| Sezione | Funzione |
|---|---|
| 🌍 **Universe** | Scarica un intero indice, pre-filtra con colori 🟢🟡🔴, seleziona i candidati |
| 📋 **Watchlist** | Scoring multi-fattoriale (8 fattori, z-score pesati) sui ticker selezionati |
| 🏆 **Dashboard** | Top 5 con card, radar chart, metriche chiave |
| 📈 **Storico Prezzi** | Grafico interattivo (candele + MA) per ogni ticker |
| 💰 **Dividendi** | Storico distribuzioni, DGR, yield forward |
| ⭐ **Preferiti** | Memoria storica su Google Sheets: salva snapshot, traccia l'evoluzione |

---

## ⚡ Setup rapido (30 minuti totali)

### 1. Prerequisiti

- Python 3.10+ installato
- Account GitHub (gratuito) → [github.com](https://github.com)
- Account Streamlit Community Cloud (gratuito) → [share.streamlit.io](https://share.streamlit.io)
- Account Google (per i Preferiti, facoltativo in fase iniziale)

---

### 2. Configurazione locale (test sul PC)

```bash
# Clona o scarica questo progetto
git clone <url-del-tuo-repo>
cd screener_app

# Crea ambiente virtuale
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Installa dipendenze
pip install -r requirements.txt

# Configura secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# → Modifica secrets.toml con le tue chiavi API
```

Avvio locale:
```bash
streamlit run app.py
```
→ Apri `http://localhost:8501` nel browser.

---

### 3. API Key Financial Modeling Prep (FMP)

> **Per cosa serve:** dati fondamentali dettagliati nella Watchlist (P/E, ROE, D/E, margini, dividendi).
> Senza API key l'app usa yfinance come fallback (dati meno completi ma funzionanti).

1. Vai su [financialmodelingprep.com/developer/docs](https://financialmodelingprep.com/developer/docs)
2. Registrati → piano **Basic** (gratuito, 250 chiamate/giorno)
3. Copia la tua API key
4. Incollala in `.streamlit/secrets.toml`:
   ```toml
   FMP_API_KEY = "la_tua_chiave_qui"
   ```

**Gestione chiamate API (250/giorno):**
- Universe (yfinance): 0 chiamate FMP
- Watchlist 20 ticker (FMP): ~60 chiamate
- Dividendi per ticker: ~1 chiamata
- Puoi fare ~3-4 aggiornamenti watchlist al giorno con il piano gratuito

---

### 4. Google Sheets per i Preferiti

> I Preferiti vengono salvati su un Google Sheet condiviso, accessibile da qualsiasi dispositivo.

#### Passo 1: Abilita le API Google
1. Vai su [console.cloud.google.com](https://console.cloud.google.com)
2. Crea un nuovo progetto (es. "screener-azioni")
3. Menu laterale → **API e servizi** → **Libreria**
4. Cerca e abilita:
   - **Google Sheets API**
   - **Google Drive API**

#### Passo 2: Crea Service Account
1. **API e servizi** → **Credenziali** → **Crea credenziali** → **Account di servizio**
2. Nome: `screener-service-account` (o qualsiasi)
3. Ruolo: **Editor** (o "Utente di base Fogli")
4. Clicca sulla riga del Service Account appena creato
5. Tab **Chiavi** → **Aggiungi chiave** → **Crea nuova chiave** → **JSON**
6. Scarica il file JSON (lo usi nel prossimo passo)

#### Passo 3: Crea il Google Sheet
1. Vai su [sheets.google.com](https://sheets.google.com)
2. Crea un nuovo foglio vuoto
3. Rinominalo `Screener_Preferiti` (esattamente così)
4. Apri il JSON scaricato, copia il valore di `client_email`
5. Nel Google Sheet: **Condividi** → incolla l'email del Service Account → **Editor** → Invia

#### Passo 4: Configura secrets.toml
Apri il file JSON del Service Account e copia i campi in `secrets.toml`:

```toml
FMP_API_KEY = "la_tua_chiave_fmp"

GSHEET_NAME = "Screener_Preferiti"

[gcp_service_account]
type = "service_account"
project_id = "screener-azioni"
private_key_id = "abc123..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "screener-service-account@screener-azioni.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

> ⚠️ **IMPORTANTE**: Non caricare mai `secrets.toml` su GitHub. Aggiungi al `.gitignore`:
> ```
> .streamlit/secrets.toml
> ```

---

### 5. Deploy su Streamlit Community Cloud

1. Carica il progetto su GitHub (repository pubblico o privato)
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/tuo-username/screener-azioni.git
   git push -u origin main
   ```
2. Vai su [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Seleziona il repository, branch `main`, file `app.py`
4. **Secrets**: clicca **Advanced settings** → **Secrets** → incolla il contenuto di `secrets.toml`
5. **Deploy!** → l'app sarà disponibile su `https://tuo-username-screener-azioni.streamlit.app`

L'URL funziona su qualsiasi browser, incluso smartphone.

---

## 🧮 Metodologia di scoring (Watchlist)

Ogni azione viene valutata su **8 fattori**, normalizzati via **z-score** rispetto alla watchlist corrente:

| Fattore | Peso | Note |
|---|---|---|
| Momentum 6M | 20% | Rendimento 6 mesi relativo |
| Momentum 12M | 15% | Rendimento 12 mesi |
| ROE | 10% | Return on Equity |
| D/E inverso | 10% | Meno debito = meglio |
| Gross Margin | 10% | Efficienza operativa |
| Low Volatility | 15% | Bassa vol = anomalia persistente in letteratura |
| P/E inverso | 10% | Non troppo caro |
| Dividend Yield | 10% | Rendimento da dividendi |

**Score composito** = somma pesata dei z-score (clippati a ±3 per gestire outlier).

**Tier affidabilità**:
- 🟢 **Alta**: dati completi + MktCap > $2B + Vol < 60% + Ret12M > -30%
- 🟡 **Media**: alcuni dati mancanti o criteri borderline
- 🔴 **Bassa**: molti dati mancanti o sotto soglie di rischio

Per modificare i pesi: `utils/config.py → SCORING_WEIGHTS` (devono sommare a 1.0).

---

## ⚠️ Disclaimer

Questo strumento è a scopo **educativo e di supporto all'analisi personale**.
Non costituisce consulenza finanziaria. I mercati comportano rischi di perdita del capitale.
I fattori storici non garantiscono performance future.

---

## 📁 Struttura file

```
screener_app/
├── app.py                      # Entry point Streamlit
├── requirements.txt
├── README.md
├── .streamlit/
│   └── secrets.toml.example    # Template credenziali
├── utils/
│   ├── config.py               # Parametri, pesi, liste ticker
│   ├── data.py                 # Fetch dati (yfinance + FMP)
│   ├── scoring.py              # Modello z-score e pre-filtro
│   └── storage.py              # Google Sheets (Preferiti)
└── pages/
    ├── universe.py             # 🌍 Fase 1 - screening largo
    ├── watchlist.py            # 📋 Fase 2 - scoring dettagliato
    ├── dashboard.py            # 🏆 Top 5
    ├── storico.py              # 📈 Prezzi storici
    ├── dividendi.py            # 💰 Dividendi
    └── preferiti.py            # ⭐ Memoria storica
```

---

*Versione 1.0 — Basato su letteratura factor investing (Jegadeesh-Titman, Asness, Frazzini-Pedersen)*
