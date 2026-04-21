"""
config.py — Configurazione globale dello screener
Contiene: parametri scoring, definizioni indici, ticker europei hardcoded.
"""

# ══════════════════════════════════════════════
# PARAMETRI MODELLO DI SCORING (Watchlist)
# ══════════════════════════════════════════════

SCORING_WEIGHTS = {
    "mom_6m":   0.20,   # Momentum 6 mesi
    "mom_12m":  0.15,   # Momentum 12 mesi
    "roe":      0.10,   # Return on Equity
    "de_inv":   0.10,   # Debt/Equity inverso (meno debito = meglio)
    "margin":   0.10,   # Gross Margin
    "lowvol":   0.15,   # Bassa volatilità (inverso)
    "pe_inv":   0.10,   # P/E inverso (non troppo caro)
    "div_yld":  0.10,   # Dividend Yield
}

ZSCORE_CAP = 3.0        # Clip z-score a ±3 (elimina outlier)
MCAP_MIN_M  = 2000      # Market cap minima in milioni USD
VOL_MAX_PCT = 0.60      # Volatilità massima annualizzata (60%)
RET12M_MIN  = -0.30     # Rendimento 12M minimo per tier "Alta"

# ══════════════════════════════════════════════
# PRE-FILTRO UNIVERSE (colori semaforo)
# ══════════════════════════════════════════════

PREFILTER = {
    "verde": {
        "pe_min": 5, "pe_max": 35,
        "roe_min": 0.08,
        "de_max": 1.5,
        "mom6m_min": 0.0,
        "mcap_min_M": 2000,
    },
    "rosso": {
        "pe_max_abs": 60,       # P/E > 60 o negativo
        "roe_min_abs": 0.0,     # ROE negativo
        "de_max_abs": 3.0,      # D/E > 3
        "ret12m_min_abs": -0.30,# Crollo > 30%
    }
}

# ══════════════════════════════════════════════
# STRUTTURA MERCATI E INDICI
# ══════════════════════════════════════════════

MERCATI = {
    "🇺🇸 USA": {
        "indici": ["S&P 500", "Nasdaq 100", "Dow Jones 30", "Russell 2000 (top 200)"],
        "valuta": "USD",
        "suffisso_yf": "",
    },
    "🇩🇪 Germania (DAX)": {
        "indici": ["DAX 40"],
        "valuta": "EUR",
        "suffisso_yf": ".DE",
    },
    "🇬🇧 UK (FTSE)": {
        "indici": ["FTSE 100"],
        "valuta": "GBP",
        "suffisso_yf": ".L",
    },
    "🇫🇷 Francia (CAC)": {
        "indici": ["CAC 40"],
        "valuta": "EUR",
        "suffisso_yf": ".PA",
    },
    "🇮🇹 Italia (MIB)": {
        "indici": ["FTSE MIB", "Euronext Milan (Top 80)"],
        "valuta": "EUR",
        "suffisso_yf": ".MI",
    },
    "🇳🇱 Olanda (AEX)": {
        "indici": ["AEX 25"],
        "valuta": "EUR",
        "suffisso_yf": ".AS",
    },
    "🇪🇸 Spagna (IBEX)": {
        "indici": ["IBEX 35"],
        "valuta": "EUR",
        "suffisso_yf": ".MC",
    },
}

# ══════════════════════════════════════════════
# TICKER HARDCODED PER INDICI EUROPEI + DOW JONES
# (S&P 500 e Nasdaq 100 vengono da Wikipedia)
# ══════════════════════════════════════════════

TICKERS_DOW30 = [
    "AAPL","AMGN","AXP","BA","CAT","CRM","CSCO","CVX","DIS","DOW",
    "GS","HD","HON","IBM","JNJ","JPM","KO","MCD","MMM","MRK",
    "MSFT","NKE","PG","TRV","UNH","V","VZ","WBA","WMT","INTC",
]

TICKERS_RUSSELL200 = [
    # Top 200 Russell 2000 per market cap (selezione rappresentativa)
    "SMCI","RBLX","LYFT","WISH","AFRM","ASAN","BILL","CLOV","DKNG","FROG",
    "GTLB","HCP","IONQ","JOBY","KRTX","LOVE","MNDY","NCNO","OUST","PLMR",
    "QLYS","RELY","SMAR","TDUP","UPST","VLD","WDAY","XMTR","YEXT","ZETA",
    "ACVA","BARK","CANO","DOCS","EVBG","FRSH","GDRX","HIMS","INVA","JAMF",
    "KROS","LPSN","MAPS","NKLA","OPEN","PTLO","QUBT","RXRX","SANA","TMDI",
    "EVER","TASK","TLRY","VERV","ACHL","BOWX","CCXI","DCPH","ENVX","FTIV",
    "GRPH","HALO","IOVA","JMIA","KIDS","LIDR","MNTV","NRIX","OPRX","PHAT",
    "RETA","SIBN","TELA","VNDA","XNCR","YMAB","ZPAY","ALTO","BLNK","CRIS",
    "DNAZ","ESTA","FWBI","GTHX","HRMY","IMTX","JNCE","KERN","LQDA","MGNI",
    "NSTG","ORGO","PRTK","QURE","RCUS","SNDL","TTCF","URGN","VLRS","WKHS",
    "XBIT","YMTX","ZYME","ATRC","BLDE","CDMO","DCBO","EVFM","FROG","GEVO",
    "HOWL","INPX","JANX","KALI","LMND","MMAT","NKTR","OFIX","PHAT","QDEL",
    "RGEN","SEER","TPVG","UTHR","VNET","WOOF","XAIR","YCBD","ZGNX","ACST",
    "BLCM","CHRS","DFIN","EPZM","FENC","GNFT","HGEN","IDCC","JBSS","KDMN",
    "LKFN","MBNKP","NBTB","OCFC","PFIS","QCRH","RBCAA","SBCF","TRMK","UVSP",
    "VLGEA","WABC","XBRL","YDKN","ZION","ABCB","BSVN","CASS","DCOM","EGBN",
    "FFIN","GBNK","HAFC","ITIC","JOUT","KFRC","LCNB","MFIN","NFBK","OVBC",
    "PFBX","QFIN","RBKB","SASR","TCBK","UNTY","VBFC","WASH","XBKS","ZION",
    "AMSF","BHLB","CBTX","ESSA","FCNCA","GABC","HOPE","ISTR","JFBC","KRNY",
]

TICKERS_DAX40 = [
    "ADS.DE","AIR.DE","ALV.DE","BAS.DE","BAYN.DE","BEI.DE","BMW.DE","BNR.DE",
    "CON.DE","1COV.DE","DB1.DE","DBK.DE","DHL.DE","DTE.DE","EOAN.DE","FME.DE",
    "FRE.DE","HEI.DE","HEN3.DE","HNR1.DE","IFX.DE","LIN.DE","MBG.DE","MRK.DE",
    "MTX.DE","MUV2.DE","P911.DE","PAH3.DE","PUM.DE","QIA.DE","RHM.DE","RWE.DE",
    "SAP.DE","SHL.DE","SIE.DE","SY1.DE","VNA.DE","VOW3.DE","ZAL.DE","ENR.DE",
]

TICKERS_FTSE100 = [
    "AZN.L","SHEL.L","HSBA.L","ULVR.L","BP.L","GSK.L","RIO.L","BATS.L",
    "LSEG.L","NG.L","VOD.L","DGE.L","GLEN.L","BARC.L","LLOY.L","REL.L",
    "NWG.L","PRU.L","IMB.L","AAL.L","EXPN.L","RR.L","STAN.L","CRH.L",
    "TSCO.L","PSON.L","SGE.L","BA.L","ABF.L","WPP.L","AHT.L","HIK.L",
    "HLN.L","HLMA.L","IHG.L","JET.L","KGF.L","NXT.L","OCDO.L","RTO.L",
    "SDR.L","SGRO.L","SMIN.L","SMT.L","SN.L","SSE.L","SVT.L","WEIR.L",
    "III.L","CRDA.L","LAND.L","MNG.L","PSN.L","SMDS.L","JD.L","MKS.L",
    "RKT.L","SKG.L","SSON.L","UTG.L","CCH.L","DCC.L","FRAS.L","WTB.L",
    "ENT.L","IMI.L","RS1.L","BT.L","CPG.L","ITRK.L","PAG.L","MNDI.L",
    "AUTO.L","BDEV.L","BNZL.L","BWY.L","CNA.L","DPLM.L","EZJ.L","FLTR.L",
    "GFS.L","HWDN.L","IGG.L","JMAT.L","LMP.L","MSLH.L","POLY.L","SPX.L",
    "TEMP.L","TBCG.L","TRIG.L","UU.L","VCT.L","WISE.L","GKN.L","HAT.L",
    "INTU.L","JUST.L","MCRO.L","OXIG.L",
]

TICKERS_CAC40 = [
    "AI.PA","AIR.PA","ALO.PA","BN.PA","BNP.PA","CA.PA","CAP.PA","AXA.PA",
    "DG.PA","DSY.PA","ENGI.PA","EL.PA","GLE.PA","HO.PA","KER.PA","LR.PA",
    "MC.PA","ML.PA","MT.PA","ORA.PA","RI.PA","RMS.PA","RNO.PA","SAF.PA",
    "SAN.PA","SGO.PA","STLA.PA","SU.PA","TTE.PA","VIE.PA","VIV.PA","FR.PA",
    "PUB.PA","SW.PA","AC.PA","WLN.PA","TE.PA","RCO.PA","TFI.PA","URW.PA",
]

TICKERS_FTSEMIB = [
    "A2A.MI","AMP.MI","ATL.MI","AZM.MI","BAMI.MI","CPR.MI","ENEL.MI","ENI.MI",
    "ERG.MI","EXOR.MI","FBK.MI","G.MI","HER.MI","ISP.MI","IT.MI","LDO.MI",
    "MB.MI","MONC.MI","NEXI.MI","PRY.MI","PST.MI","RACE.MI","SRG.MI","STM.MI",
    "TEN.MI","TIT.MI","TRN.MI","UCG.MI","SFER.MI","SPM.MI","DIA.MI","INW.MI",
    "PIRC.MI","BGN.MI","IVECO.MI","BMED.MI","CIG.MI","REC.MI","SFL.MI","UNI.MI",
]

TICKERS_AEX25 = [
    "ASML.AS","ADYEN.AS","HEIA.AS","INGA.AS","PHIA.AS","REN.AS","AKZA.AS",
    "ABN.AS","AGN.AS","ASM.AS","BESI.AS","EXOR.AS","GTO.AS","IMCD.AS",
    "KPN.AS","NN.AS","RAND.AS","SBMO.AS","TKWY.AS","UMG.AS","UNA.AS",
    "URW.AS","WKL.AS","DSFIR.AS","LIGHT.AS",
]

TICKERS_IBEX35 = [
    "ACS.MC","ACX.MC","AENA.MC","ANA.MC","BBVA.MC","BKT.MC","CABK.MC",
    "CLNX.MC","COL.MC","ELE.MC","ENG.MC","GRF.MC","IAG.MC","IBE.MC",
    "IDR.MC","ITX.MC","MAP.MC","MEL.MC","MTS.MC","NTGY.MC","RED.MC",
    "REP.MC","ROVI.MC","SAB.MC","SAN.MC","TEF.MC","VIS.MC","FER.MC",
    "LOG.MC","AMS.MC","CAF.MC","CIE.MC","PHM.MC","SOL.MC","TRE.MC",
]

TICKERS_EURONEXT_MILAN = [
    # FTSE MIB (40 principali)
    "A2A.MI","AMP.MI","ATL.MI","AZM.MI","BAMI.MI","CPR.MI","ENEL.MI","ENI.MI",
    "ERG.MI","EXOR.MI","FBK.MI","G.MI","HER.MI","ISP.MI","IT.MI","LDO.MI",
    "MB.MI","MONC.MI","NEXI.MI","PRY.MI","PST.MI","RACE.MI","SRG.MI","STM.MI",
    "TEN.MI","TIT.MI","TRN.MI","UCG.MI","SFER.MI","SPM.MI","DIA.MI","INW.MI",
    "PIRC.MI","BGN.MI","IVECO.MI","BMED.MI","CIG.MI","REC.MI","SFL.MI","UNI.MI",
    # Mid cap e altri Euronext Milan
    "MAIRE.MI","MFEA.MI","MFEB.MI","CALT.MI","FNM.MI","IGD.MI","IMA.MI","MARR.MI",
    "OVS.MI","SAVE.MI","SESA.MI","SOL.MI","TBS.MI","TINEXTA.MI",
    "TOD.MI","WEBUILD.MI","WIIT.MI","ENAV.MI","AEFFE.MI",
    "BASICNET.MI","BRUNELLO.MI","CREDEM.MI",
    "DATALOGIC.MI","ELICA.MI","EMAK.MI",
    "GEFRAN.MI","GEWISS.MI","GUALA.MI",
    "ILLIMITY.MI","INTERPUMP.MI","ITALMOBILIARE.MI",
    "JUVENTUS.MI","MUTUIONLINE.MI","NEWLAT.MI","PANARIAGROUP.MI",
    "PIAGGIO.MI","PRYSMIAN.MI","RECORDATI.MI",
    "REPLY.MI","SAES.MI","SAFILO.MI","SAIPEM.MI",
    "SALCEF.MI","SANLORENZO.MI","SICIT.MI","SOGEFI.MI",
    "TECHNOGYM.MI","TERNA.MI","TREVI.MI","FALCK.MI",
    "ALERION.MI","ASKOLL.MI","AXTERIA.MI","BFC.MI","CEVA.MI",
    "CLABO.MI","DMAVE.MI","EL.EN.MI","EPIQ.MI","ERAR.MI",
    "GEDI.MI","GEL.MI","GVS.MI","IMMSI.MI","IREN.MI",
    "ISAGRO.MI","KME.MI","LU-VE.MI","MAPS.MI","MKT.MI",
    "MOLTIPLY.MI","MRL.MI","NICE.MI","OPENJOBMETIS.MI","PHARMANUTRA.MI",
    "PLANETEL.MI","PLT.MI","PORTOBELLO.MI","PRIMA.MI","RCS.MI",
    "RELATECH.MI","REVO.MI","RGS.MI","RINA.MI","RWAY.MI",
]

# Mappa indice → lista ticker hardcoded
TICKER_MAP = {
    "Dow Jones 30":            TICKERS_DOW30,
    "Russell 2000 (top 200)":  TICKERS_RUSSELL200,
    "DAX 40":                  TICKERS_DAX40,
    "FTSE 100":                TICKERS_FTSE100,
    "CAC 40":                  TICKERS_CAC40,
    "FTSE MIB":                TICKERS_FTSEMIB,
    "Euronext Milan (Top 80)": TICKERS_EURONEXT_MILAN,
    "AEX 25":                  TICKERS_AEX25,
    "IBEX 35":                 TICKERS_IBEX35,
    # S&P 500 e Nasdaq 100 → Wikipedia scraping
}

# ══════════════════════════════════════════════
# UI / STILE
# ══════════════════════════════════════════════

COLORI = {
    "verde":  "#2d7a2d",
    "giallo": "#b38600",
    "rosso":  "#c0392b",
    "blu":    "#1a5276",
    "grigio": "#7f8c8d",
}

COLORI_BG = {
    "verde":  "#d5f5e3",
    "giallo": "#fef9e7",
    "rosso":  "#fadbd8",
    "blu":    "#d6eaf8",
}

# Schema colori tier Watchlist
TIER_COLORI = {
    "Alta":   {"bg": "#C6EFCE", "fg": "#276221"},
    "Media":  {"bg": "#FFEB9C", "fg": "#7D5A00"},
    "Bassa":  {"bg": "#FFC7CE", "fg": "#9C0006"},
}

# Etichette per la UI
LABEL_RATING = {
    "verde":  "🟢 Verde",
    "giallo": "🟡 Giallo",
    "rosso":  "🔴 Rosso",
}

# Colonne visualizzate nella tabella Universe
UNIVERSE_DISPLAY_COLS = [
    "ticker", "nome", "settore", "mktcap_M", "prezzo",
    "ret_6m", "ret_12m", "vol_ann", "pe", "roe", "de_ratio", "rating"
]

UNIVERSE_COL_LABELS = {
    "ticker":    "Ticker",
    "nome":      "Nome",
    "settore":   "Settore",
    "mktcap_M":  "MktCap $M",
    "prezzo":    "Prezzo",
    "ret_6m":    "Ret 6M",
    "ret_12m":   "Ret 12M",
    "vol_ann":   "Vol Ann",
    "pe":        "P/E",
    "roe":       "ROE",
    "de_ratio":  "D/E",
    "rating":    "Rating",
}
