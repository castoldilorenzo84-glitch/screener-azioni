"""
pdf_report.py — Genera un PDF "one-pager" con analisi completa di un ticker.

Usa reportlab (pip install reportlab).
Output: file PDF in memoria (BytesIO) pronto per il download.
"""

import io
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Optional, Dict

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_OK = True

    # ── Colori brand ─────────────────────────────────────────────
    BLU   = colors.HexColor("#1F4E78")
    BLU_M = colors.HexColor("#2E75B6")
    BLU_L = colors.HexColor("#DEEAF1")
    GRN   = colors.HexColor("#276221")
    GRN_L = colors.HexColor("#C6EFCE")
    GIL   = colors.HexColor("#7D5A00")
    GIL_L = colors.HexColor("#FFEB9C")
    RED   = colors.HexColor("#9C0006")
    RED_L = colors.HexColor("#FFC7CE")
    GRY   = colors.HexColor("#F2F2F2")
    WHT   = colors.white
    BLK   = colors.black

except ImportError:
    REPORTLAB_OK = False
    # Placeholder per evitare NameError se reportlab non installato
    BLU = BLU_M = BLU_L = GRN = GRN_L = GIL = GIL_L = RED = RED_L = GRY = WHT = BLK = None


def reportlab_disponibile() -> bool:
    return REPORTLAB_OK


def genera_pdf(
    ticker: str,
    dati: Dict,
    zscore: Dict = None,
    note: str = "",
    regime_nome: str = "",
) -> Optional[bytes]:
    """
    Genera il PDF one-pager per un ticker.

    Parametri:
    - ticker:      simbolo borsa
    - dati:        dict con tutti i dati fondamentali e di scoring
    - zscore:      dict con z-score dei singoli fattori (opzionale)
    - note:        testo libero dell'analista
    - regime_nome: regime di mercato corrente

    Ritorna bytes del PDF o None se reportlab non disponibile.
    """
    if not REPORTLAB_OK:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()

    # Stili custom
    s_title = ParagraphStyle("title", fontSize=22, textColor=WHT,
                              fontName="Helvetica-Bold", spaceAfter=4,
                              backColor=BLU, leftIndent=-5, rightIndent=-5,
                              leading=28)
    s_sub   = ParagraphStyle("sub", fontSize=11, textColor=BLU_M,
                              fontName="Helvetica", spaceAfter=2)
    s_h2    = ParagraphStyle("h2", fontSize=13, textColor=BLU,
                              fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    s_body  = ParagraphStyle("body", fontSize=10, fontName="Helvetica",
                              leading=14, spaceAfter=4)
    s_note  = ParagraphStyle("note", fontSize=9, fontName="Helvetica-Oblique",
                              textColor=colors.HexColor("#555555"), leading=12)
    s_disc  = ParagraphStyle("disc", fontSize=7.5, fontName="Helvetica-Oblique",
                              textColor=RED, leading=10)
    s_center = ParagraphStyle("center", fontSize=10, fontName="Helvetica",
                               alignment=TA_CENTER)

    story = []

    # ── HEADER ───────────────────────────────────────────────────
    nome    = dati.get("nome", ticker)
    settore = dati.get("settore", "N/A")
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    story.append(Paragraph(f"  {ticker} — {nome}", s_title))
    story.append(Paragraph(f"{settore}  |  Generato il {data_str}  |  Regime: {regime_nome or 'N/A'}", s_sub))
    story.append(HRFlowable(width="100%", thickness=1, color=BLU_M, spaceAfter=8))

    # ── METRICHE PRINCIPALI ──────────────────────────────────────
    story.append(Paragraph("Metriche Principali", s_h2))

    def _fmt(v, pct=False, dec=1, prefix=""):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return "—"
        if pct:
            return f"{float(v)*100:+.{dec}f}%"
        return f"{prefix}{float(v):,.{dec}f}"

    score    = dati.get("score")
    tier     = dati.get("tier", "—")
    prezzo   = dati.get("prezzo")
    ret_6m   = dati.get("ret_6m")
    ret_12m  = dati.get("ret_12m")
    vol_ann  = dati.get("vol_ann")
    pe       = dati.get("pe")
    roe      = dati.get("roe")
    de       = dati.get("de_ratio")
    margin   = dati.get("gross_margin")
    div_yld  = dati.get("div_yield")
    mktcap   = dati.get("mktcap_M")
    pct_rank = dati.get("percentile")

    tier_color = {"Alta": GRN_L, "Media": GIL_L, "Bassa": RED_L}.get(str(tier), GRY)

    metriche = [
        ["Score Composito", f"{score:.3f}" if score else "—",
         "Tier Affidabilità", str(tier)],
        ["Prezzo", _fmt(prezzo, prefix="$"),
         "Percentile", f"{pct_rank}°" if pct_rank else "—"],
        ["Ret 6M", _fmt(ret_6m, pct=True),
         "Ret 12M", _fmt(ret_12m, pct=True)],
        ["Volatilità Ann.", _fmt(vol_ann, pct=True),
         "Market Cap", f"${mktcap:,.0f}M" if mktcap else "—"],
        ["P/E", _fmt(pe),
         "ROE", _fmt(roe, pct=True)],
        ["D/E", _fmt(de, dec=2),
         "Gross Margin", _fmt(margin, pct=True)],
        ["Dividend Yield", _fmt(div_yld, pct=True, dec=2),
         "", ""],
    ]

    col_w = [3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm]
    t_met = Table(metriche, colWidths=col_w)
    t_met.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), BLU_L),
        ("BACKGROUND",  (2, 0), (2, -1), BLU_L),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHT, GRY]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0), (-1, -1), 4),
    ]))
    # Colora cella Tier
    tier_row = 0
    t_met.setStyle(TableStyle([
        ("BACKGROUND", (3, tier_row), (3, tier_row), tier_color),
    ]))
    story.append(t_met)
    story.append(Spacer(1, 0.3*cm))

    # ── Z-SCORES ─────────────────────────────────────────────────
    if zscore:
        story.append(Paragraph("Dettaglio Z-Scores (fattori)", s_h2))
        labels = {
            "z_mom6m":  "Momentum 6M",
            "z_mom12m": "Momentum 12M",
            "z_roe":    "ROE",
            "z_de":     "D/E inv.",
            "z_margin": "Gross Margin",
            "z_lowvol": "Low Volatility",
            "z_pe":     "P/E inv.",
            "z_div":    "Dividend Yield",
        }
        z_rows = [["Fattore", "Z-Score", "Segnale"]]
        for k, label in labels.items():
            z = zscore.get(k)
            if z is None:
                continue
            try:
                zv = float(z)
            except Exception:
                continue
            if zv > 0.5:
                seg = "🟢 Positivo"
                fill = GRN_L
            elif zv < -0.5:
                seg = "🔴 Negativo"
                fill = RED_L
            else:
                seg = "🟡 Neutro"
                fill = GIL_L
            z_rows.append([label, f"{zv:+.3f}", seg])

        t_z = Table(z_rows, colWidths=[5*cm, 3*cm, 5.5*cm])
        t_z.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), BLU),
            ("TEXTCOLOR",    (0, 0), (-1, 0), WHT),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 9),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHT, GRY]),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ]))
        story.append(t_z)
        story.append(Spacer(1, 0.3*cm))

    # ── NOTE ANALISTA ────────────────────────────────────────────
    story.append(Paragraph("Note dell'Analista", s_h2))
    if note and note.strip():
        story.append(Paragraph(note, s_body))
    else:
        story.append(Paragraph("(nessuna nota inserita)", s_note))

    # Spazio per note manuali (linee bianche)
    for _ in range(4):
        story.append(HRFlowable(width="100%", thickness=0.3,
                                color=colors.HexColor("#CCCCCC"), spaceAfter=10))
    story.append(Spacer(1, 0.3*cm))

    # ── FOOTER DISCLAIMER ────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=BLU_M, spaceBefore=6))
    story.append(Paragraph(
        "⚠️ DISCLAIMER: Documento a uso personale per supporto all'analisi. "
        "Non costituisce consulenza finanziaria. I mercati comportano rischi "
        "di perdita del capitale. I dati sono basati su fonti pubbliche e potrebbero "
        "non essere aggiornati. Verifica sempre le informazioni prima di agire.",
        s_disc
    ))

    doc.build(story)
    return buffer.getvalue()
