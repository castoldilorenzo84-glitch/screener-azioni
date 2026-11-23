#!/usr/bin/env python3
"""Controllo meccanico dei segni "da IA" nello YAML di schermate Power Apps.

Uso:
    python controlla_app.py schermata.yaml [altra.yaml ...]

Legge lo YAML come testo (non serve PyYAML) e segnala candidati da giudicare
con references/design-visivo.md. Non è un verdetto: una scelta voluta resta.
"""
import re
import sys
from collections import Counter

EMOJI = re.compile("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B50\u2705]")
PALETTE_IA = {"6366F1", "8B5CF6", "7C3AED", "A855F7", "4F46E5", "EC4899", "D946EF", "06B6D4", "3B82F6"}
NOMI_PREDEFINITI = re.compile(r"^\s*-?\s*((Label|Button|TextInput|Gallery|Container|Icon|Rectangle|Image|Form|DataCard|Dropdown|DropDown|ComboBox|DatePicker|Toggle|Checkbox|HtmlText|Screen|Text)\d+)\s*:", re.M)
PREFISSI = ("scr", "cnt", "lbl", "btn", "txt", "gal", "con", "ico", "img", "frm", "frmv", "dc", "drp", "cmb", "dtp", "tgl", "chk", "htm", "rec", "cmp", "shp", "pop", "nav", "hdr", "tab")
SCALA = {0, 4, 8, 12, 16, 24, 32, 40, 48}
TESTI_IA = re.compile(r"con successo|\bops\b|oops|clicca qui|benvenut[oa]\b|fantastico|qualcosa è andato storto|si prega|sei sicur[oa]\?", re.I)


def controlla(percorso):
    testo = open(percorso, encoding="utf-8").read()
    righe = testo.splitlines()
    out = []

    def add(g, msg):
        out.append((g, msg))

    for m in EMOJI.finditer(testo):
        n = testo[:m.start()].count("\n") + 1
        add("P1", f"emoji „{m.group(0)}\" (riga {n})")

    for m in TESTI_IA.finditer(testo):
        n = testo[:m.start()].count("\n") + 1
        add("P1", f"testo da IA „{m.group(0)}\" (riga {n})")

    esclam = [i + 1 for i, r in enumerate(righe)
              if any("!" in lit for lit in re.findall(r'"((?:[^"]|"")*)"', r.split("//")[0]))]
    if esclam:
        add("P1", f"punti esclamativi in stringhe (righe {', '.join(map(str, esclam[:8]))})")

    # colori scritti a mano
    rgba = re.findall(r"RGBA\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", testo)
    hexs = re.findall(r'ColorValue\(\s*"#?([0-9A-Fa-f]{6})', testo)
    colori = {"%02X%02X%02X" % tuple(int(x) for x in c) for c in rgba} | {h.upper() for h in hexs}
    colori_controlli = len(rgba) + len(hexs)
    usa_tema = bool(re.search(r"\bColori\.", testo))
    in_formulas = "Formulas" in testo
    if colori_controlli > 6 and not in_formulas:
        add("P2", f"{colori_controlli} colori scritti a mano nei controlli: definiscili nel tema in App.Formulas" + ("" if usa_tema else " (il file non usa Colori.)"))
    cromatici = [c for c in colori if not _grigio(c)]
    if len(cromatici) > 5:
        add("P1", f"{len(cromatici)} colori non grigi diversi ({', '.join(sorted(cromatici)[:8])}): un accento più i colori di stato bastano")
    viola = sorted(c for c in colori if c in PALETTE_IA or _viola(c))
    if viola:
        add("P1", f"palette tipica da IA (viola/indaco/azzurro elettrico): {', '.join(viola)}")
    if re.search(r"gradient|linearGradient|radialGradient", testo, re.I):
        add("P1", "sfumatura (gradient) nello YAML")

    # forme e ombre
    raggi = [int(x) for x in re.findall(r"Radius\w*:\s*=\s*(\d+)", testo)]
    if raggi:
        grandi = sorted({r for r in raggi if r > 8})
        if grandi:
            add("P1", f"angoli molto arrotondati: raggio {', '.join(map(str, grandi))} (usa 4)")
        if len(set(raggi)) > 2:
            add("P2", f"raggi diversi nella stessa app: {sorted(set(raggi))}")
    ombre = re.findall(r"DropShadow:\s*=\s*DropShadow\.(\w+)", testo)
    forti = [o for o in ombre if o in ("Bold", "ExtraBold", "Regular", "Semibold")]
    if forti:
        add("P1", f"ombre marcate: {Counter(forti)} (nessuna ombra, o Light/Semilight solo sui popup)")

    # tipografia
    dimensioni = sorted({int(x) for x in re.findall(r"\bSize:\s*=\s*(\d+)", testo)})
    if len(dimensioni) > 4:
        add("P1", f"{len(dimensioni)} dimensioni di carattere: {dimensioni} (al massimo 4)")
    font = set(re.findall(r"Font:\s*=\s*Font\.'?([\w ]+)'?", testo))
    if len(font) > 1:
        add("P2", f"più font: {sorted(font)}")
    bold = len(re.findall(r"FontWeight\.(Bold|Semibold)", testo))
    testi = len(re.findall(r"\bText:\s*=", testo))
    if testi >= 6 and bold > testi * 0.5:
        add("P1", f"grassetto su {bold} di {testi} testi")
    centrati = len(re.findall(r"Align\.Center", testo))
    if testi >= 6 and centrati > testi * 0.5:
        add("P1", f"testo centrato in {centrati} casi su {testi} testi")
    for m in re.finditer(r'Text:\s*=\s*"([^"]{4,})"', testo):
        s = m.group(1)
        parole = [p for p in re.findall(r"[A-Za-zÀ-ÿ']+", s) if len(p) >= 3]
        if len(parole) >= 3 and all(p[0].isupper() for p in parole):
            add("P1", f"Title Case: „{s}\"")
        if len(s) >= 6 and s.isupper():
            add("P1", f"testo in MAIUSCOLO: „{s}\"")

    # spaziature fuori scala
    spazi = [int(x) for x in re.findall(r"(?:LayoutGap|Gap):\s*=\s*(\d+)", testo)] + _padding_contenitori(testo)
    fuori = sorted({s for s in spazi if s not in SCALA})
    if fuori:
        add("P2", f"spaziature fuori scala: {fuori} (usa 4, 8, 12, 16, 24, 32)")
    if spazi and max(spazi) > 48:
        add("P1", f"spaziatura molto grande: {max(spazi)}")

    # sintassi YAML e valori a rischio per "Incolla codice"
    blocco = None  # indentazione della chiave che ha aperto un blocco |-
    for i, r in enumerate(righe, 1):
        if "\t" in r:
            add("P0", f"tabulazione alla riga {i}: Studio rifiuta lo YAML")
        rientro = len(r) - len(r.lstrip())
        if blocco is not None:
            if not r.strip() or rientro > blocco:
                continue  # dentro una formula su più righe
            blocco = None
        m = re.match(r"^\s*[A-Za-z]+:\s+(.+)$", r)
        if m:
            v = m.group(1)
            if v in ("|-", "|", ">-", ">", "|+"):
                blocco = rientro
                continue
            if v.startswith(("'", '"')):
                continue
            if not v.startswith("=") and not re.match(r"^\s*(Control|Variant|Layout|ComponentName|Group|MetadataKey|IsLocked):", r):
                add("P0", f"valore senza '=' alla riga {i}: {v[:50]}")
            elif ": " in v or " #" in v or v.rstrip().endswith(":"):
                add("P0", f"due punti o cancelletto in una formula su una riga sola (riga {i}): usa un blocco |-")
    vuoti = re.findall(r"^\s*Properties:\s*\n(?!\s+\S+:)", testo + "\n", re.M)
    if vuoti:
        add("P0", "blocco Properties vuoto: toglilo")
    try:
        import yaml  # facoltativo
        try:
            dati = yaml.safe_load(testo)
            _controlla_albero(dati, add)
        except yaml.YAMLError as e:
            add("P0", f"YAML non valido: {str(e).splitlines()[0]} {getattr(e, 'problem_mark', '')}")
    except ImportError:
        pass

    # struttura
    for m in NOMI_PREDEFINITI.finditer(testo):
        add("P2", f"nome predefinito „{m.group(1)}\": usa prefisso e significato (es. lblTitolo)")
    for m in re.finditer(r"^\s*-\s*([A-Za-z_]\w*)\s*:\s*$", testo, re.M):
        nome = m.group(1)
        if not nome.startswith(PREFISSI) and not NOMI_PREDEFINITI.match(m.group(0)):
            add("P2", f"nome senza prefisso riconoscibile: „{nome}\"")
    if re.search(r"benvenut|welcome|splash", testo, re.I):
        add("P1", "sembra esserci una schermata o un testo di benvenuto: l'app si apre sul lavoro")
    if re.search(r"Timer@|Classic/Timer|\bTimer\b", testo):
        add("P1", "timer: animazioni o caricamenti finti?")
    if re.search(r"lorem ipsum|Mario Rossi|John Doe|esempio@", testo, re.I):
        add("P0", "dati finti nel file")
    commenti = len(re.findall(r"//", testo))
    if commenti > 10:
        add("P2", f"{commenti} commenti nelle formule: tieni solo quelli che spiegano un perché")

    return out


def _padding_contenitori(testo):
    """Padding numerici dei soli GroupContainer (le icone usano padding per l'area toccabile)."""
    valori = []
    try:
        import yaml
        dati = yaml.safe_load(testo)
    except Exception:
        return valori

    def visita(n):
        if isinstance(n, list):
            for el in n:
                if isinstance(el, dict):
                    for ctrl in el.values():
                        if isinstance(ctrl, dict):
                            if str(ctrl.get("Control", "")).startswith("GroupContainer"):
                                for k, v in (ctrl.get("Properties") or {}).items():
                                    m = re.fullmatch(r"=\s*(\d+)", str(v).strip())
                                    if k.startswith("Padding") and m:
                                        valori.append(int(m.group(1)))
                            visita(ctrl.get("Children"))
    visita(dati)
    return valori


def _controlla_albero(nodo, add, genitore_auto=False, nomi=None):
    """Controlli che richiedono la struttura: X/Y dentro AutoLayout, nomi duplicati."""
    if nomi is None:
        nomi = Counter()
    if isinstance(nodo, list):
        for el in nodo:
            if isinstance(el, dict):
                for nome, ctrl in el.items():
                    nomi[nome] += 1
                    if nomi[nome] == 2:
                        add("P0", f"nome di controllo duplicato: {nome}")
                    if not isinstance(ctrl, dict):
                        continue
                    props = ctrl.get("Properties") or {}
                    if genitore_auto and ("X" in props or "Y" in props):
                        add("P2", f"{nome}: X/Y dentro un contenitore AutoLayout vengono ignorati")
                    auto = ctrl.get("Variant") == "AutoLayout"
                    if "Children" in ctrl:
                        _controlla_albero(ctrl["Children"], add, auto, nomi)
    elif isinstance(nodo, dict):
        for v in nodo.values():
            if isinstance(v, dict) and "Children" in v:
                _controlla_albero(v["Children"], add, v.get("Variant") == "AutoLayout", nomi)


def _rgb(h):
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _grigio(h):
    r, g, b = _rgb(h)
    return max(r, g, b) - min(r, g, b) < 18


def _viola(h):
    r, g, b = _rgb(h)
    return b > 180 and r > 90 and g < 120 and r < b


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    ordine = {"P0": 0, "P1": 1, "P2": 2}
    for p in sys.argv[1:]:
        risultati = sorted(set(controlla(p)), key=lambda r: (ordine[r[0]], r[1]))
        print(f"## {p}")
        if not risultati:
            print("Nessun segno meccanico. Resta da fare la checklist visiva e il test del template.\n")
            continue
        for g, msg in risultati:
            print(f"- {g} {msg}")
        print()


if __name__ == "__main__":
    main()
