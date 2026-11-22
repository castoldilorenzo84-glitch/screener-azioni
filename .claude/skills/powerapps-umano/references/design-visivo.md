# Design visivo: app che sembrano progettate da una persona

Come si riconosce a colpo d'occhio un'app canvas generata da un'IA, e come si costruisce invece un'app che sembra disegnata da uno sviluppatore esperto che conosce il processo.

## Indice

1. Perché un'app „sembra IA"
2. Il catalogo dei segni visivi da IA
3. Il sistema visivo di base (colori, tipografia, spaziature, forme)
4. Schemi di schermata
5. Elementi ricorrenti: intestazione, pulsanti, elenchi, moduli, stati
6. Telefono, tablet, desktop
7. Esempi prima/dopo
8. Checklist visiva

---

## 1. Perché un'app „sembra IA"

Un'app generata parte da un modello di „app moderna" valido per tutto, non dal processo dell'utente: schermata di benvenuto, cruscotto, card arrotondate, sfumature, un'icona per ogni cosa. Il risultato è decorato ma generico: potrebbe essere l'app di chiunque, per qualsiasi cosa. Un'app progettata da una persona è riconoscibile per il contrario: è **sobria e specifica**. Si apre sul lavoro da fare, usa pochi colori con un significato, ha una gerarchia chiara, e ogni elemento sullo schermo è lì perché l'utente ne ha bisogno.

Il test che riassume tutto, l'equivalente del test della portabilità per i testi: **se cambi il titolo e le colonne, la schermata andrebbe bene per un'altra app qualsiasi?** Se sì, è un modello generico. La forma deve venire dal contenuto: un elenco di ordini da approvare ha un aspetto diverso da un modulo di nota spese, perché i dati e le azioni sono diversi.

## 2. Il catalogo dei segni visivi da IA

Gravità: **P1** = si nota subito e fa sembrare l'app generata, va tolto; **P2** = rifinitura.

### Struttura e flusso
- **Schermata di benvenuto o „splash"** con logo grande, saluto („Benvenuto, Mario! 👋"), pulsante „Inizia". (P1) L'app si apre sulla schermata di lavoro più usata.
- **Cruscotto non richiesto**: 3–4 card con un numero grande („12 richieste", „3 in attesa", „98 % approvate") prima di arrivare al lavoro. (P1) I numeri si mostrano solo se l'utente li deve usare per decidere, e dentro la schermata dove servono (per esempio un contatore „3 da approvare" sopra l'elenco).
- **Menu di navigazione sproporzionato**: barra in basso con 4–5 icone o menu hamburger per un'app con 2–3 schermate. (P1) Con poche schermate basta navigare dall'elenco al dettaglio e tornare indietro.
- **Schermate fotocopia**: ogni schermata con lo stesso banner, la stessa griglia di card, la stessa disposizione anche se il contenuto è diverso. (P1)
- **Funzioni non richieste**: modalità scura, impostazioni, profilo, notifiche, ricerca vocale, grafici. (P1) Costruisci ciò che è stato chiesto; le aggiunte utili si propongono a parte, non si costruiscono.
- **Dati finti**: nomi inventati, avatar, numeri di esempio, testo „Lorem ipsum" lasciati nell'app. (P0 se restano nell'app consegnata)

### Colore
- **Sfumature** (immagini SVG con gradient, rettangoli sovrapposti con trasparenze) nell'intestazione o negli sfondi. (P1)
- **Palette „IA"**: indaco/viola (#6366F1, #8B5CF6, #7C3AED), azzurro elettrico, rosa acceso, combinazioni viola-blu, come colore principale senza che sia il colore dell'azienda. (P1)
- **Troppi colori**: ogni card, categoria o pulsante con un colore diverso; badge arcobaleno. (P1) Un colore d'accento, i grigi, e i colori di stato.
- **Colore senza significato**: verde o rosso usati come decorazione invece che per dire „approvato" o „errore". (P1)
- **Sfondo grigio con card bianche ovunque**, anche quando non c'è niente da raggruppare. (P2)
- **Colori scritti a mano in ogni controllo** (`RGBA(99, 102, 241, 1)` ripetuto in 40 punti) invece che da un tema. (P2 visivo, ma rende l'app impossibile da mantenere)

### Forme, ombre, profondità
- **Card dentro card**, contenitori arrotondati annidati. (P1)
- **Ombre forti** (`DropShadow.Bold` o `ExtraBold`) su card e pulsanti. (P1) Se serve separare, una linea sottile o un'ombra leggera.
- **Angoli molto arrotondati** (raggio 16–24 o pulsanti „a pillola") ovunque, e raggi diversi tra un controllo e l'altro. (P1) Un solo raggio, piccolo (4), in tutta l'app.
- **Bordi spessi colorati** intorno a ogni elemento. (P2)

### Icone ed emoji
- **Emoji** nei titoli, nei pulsanti, negli stati, nei messaggi. (P1) Mai in un'app aziendale.
- **Un'icona accanto a ogni etichetta** (calendario accanto a „Data", persona accanto a „Nome"). (P1) Le icone servono per le azioni (modifica, elimina, indietro, aggiungi) o dove sono universalmente comprese; altrimenti basta il testo.
- **Icone grandi decorative** in cima a una schermata o dentro le card del cruscotto. (P1)

### Tipografia e gerarchia
- **Tutto centrato**: titoli, testi, moduli. (P1) Allinea a sinistra; si centra solo uno stato vuoto o un messaggio isolato.
- **Troppe dimensioni di carattere** (più di 4) o tutto della stessa dimensione. (P1)
- **Grassetto ovunque**, etichette in MAIUSCOLO con spaziatura, titoli in Title Case. (P1)
- **Più font** nella stessa app, o font „di carattere" (Lato, Montserrat, Poppins) senza che siano del brand. (P2)

### Spazio e densità
- **Spazi enormi** e card alte con poco contenuto: l'utente deve scorrere per vedere tre voci. (P1) Gli elenchi aziendali sono densi: si vedono 6–10 righe senza scorrere.
- **Spaziature casuali** (7, 13, 22 px) invece di una scala. (P2)
- **Tutto della stessa importanza**: niente distingue l'azione principale, il dato principale di una riga, il titolo. (P1)

### Pulsanti e interazione
- **Più pulsanti primari** nella stessa schermata, tutti colorati. (P1)
- **Pulsanti giganti a tutta larghezza** su tablet e desktop. (P2) Su telefono il pulsante primario a tutta larghezza in basso va bene.
- **Animazioni, timer, transizioni** decorative (dissolvenze a ogni navigazione, controlli che pulsano, caricamenti finti). (P1)
- **Popup per tutto**, anche dove basterebbe un messaggio sotto il campo. (P2)

## 3. Il sistema visivo di base

Definisci il sistema una volta, in `App.Formulas` (vedi `yaml-power-apps.md`), e fai riferimento a quello in ogni controllo. È quello che fa uno sviluppatore esperto, ed è anche ciò che rende l'app coerente.

### Colori

Se l'utente ha un colore aziendale, usalo come unico accento. Altrimenti usa la palette neutra di Fluent (il linguaggio visivo di Microsoft 365, quindi coerente con Teams e SharePoint):

| Ruolo | Valore | Uso |
|---|---|---|
| Primario | #0F6CBD | pulsante primario, link, elemento selezionato, focus |
| Primario hover/premuto | #115EA3 / #0F548C | stati del pulsante primario |
| Sfondo app | #FFFFFF | sfondo delle schermate |
| Sfondo secondario | #F5F5F5 | barra di intestazione chiara, righe alternate se servono, sfondo di sezioni |
| Bordo e divisori | #E0E0E0 | linee tra righe, bordi dei campi (#D1D1D1 per i campi) |
| Testo principale | #242424 | titoli, valori |
| Testo secondario | #616161 | etichette, date, metadati |
| Testo disattivato | #A19F9D | |
| Errore | #C50F1F (sfondo #FDF3F4) | messaggi di errore, stato „Rifiutata" |
| Successo | #107C10 (sfondo #F1FAF1) | stato „Approvata" |
| Avviso | #BC4B09 (sfondo #FFF9F5) | stato „In attesa", avvisi |

Regole:
- **Un solo colore d'accento.** Tutto il resto è grigio. Il colore deve voler dire „puoi agire qui" o „questo è selezionato".
- **I colori di stato si usano solo per gli stati**, e sempre insieme al testo (mai solo un pallino colorato).
- **Contrasto**: testo su sfondo almeno 4,5:1. Il grigio secondario #616161 su bianco va bene; il #A19F9D solo per testi disattivati.
- **Niente sfumature, niente trasparenze decorative.**

### Tipografia

- Un solo font: `Font.'Segoe UI'` (quello di Microsoft 365). Un font del brand solo se l'utente lo chiede.
- Scala con 4 dimensioni al massimo:

| Ruolo | Dimensione | Peso |
|---|---|---|
| Titolo della schermata | 20 | Semibold |
| Titolo di sezione / testo principale di una riga | 16 (sezioni) / 14 (righe) | Semibold |
| Testo, valori, campi | 14 | Normal |
| Etichette secondarie, metadati, date | 12 | Normal |

- Il grassetto si usa per una cosa per blocco: il titolo, oppure il dato principale di una riga.
- Maiuscola solo all'iniziale, allineamento a sinistra, numeri e importi allineati a destra nelle tabelle.

### Spaziature

Scala da 4: **4, 8, 12, 16, 24, 32**. Margini laterali della schermata 16 (telefono) o 24 (tablet/desktop); distanza tra campi di un modulo 12–16; distanza tra sezioni 24; padding interno di una riga di elenco 12. Nessun altro valore.

### Forme

- Raggio degli angoli **4** per pulsanti, campi e contenitori; 0 per righe di elenco e intestazioni.
- Bordi da 1 px nel colore #E0E0E0 per separare; ombre solo se un elemento galleggia davvero (un popup), e leggere (`DropShadow.Light` o `Semilight`).
- Niente contenitori annidati con bordo dentro contenitori con bordo.

## 4. Schemi di schermata

Una schermata prende la forma del suo compito. I quattro schemi che coprono la maggior parte delle app aziendali:

### Elenco (la schermata iniziale tipica)
- Intestazione: titolo della schermata a sinistra, azione principale a destra („Nuova richiesta") o in basso su telefono.
- Sotto: ricerca e filtri in una riga (casella di ricerca + uno o due menu a discesa), solo se l'elenco può superare le 15–20 voci.
- Galleria a righe (non a card): altezza 64–72, divisore sottile tra le righe. Per ogni riga: il dato che identifica l'elemento in 14 semibold (es. „Ferie 24–28/11"), sotto i metadati in 12 grigio („Inviata il 10/11 · 5 giorni"), a destra lo stato come testo colorato o etichetta piccola con sfondo chiaro, e una freccia `ChevronRight` piccola e grigia se la riga apre il dettaglio.
- Ordinamento sensato (le più recenti in alto, o quelle che richiedono un'azione).
- Stato vuoto e stato di caricamento.

### Dettaglio
- Intestazione con freccia indietro, titolo che nomina l'elemento („Richiesta del 24/11"), azioni secondarie a destra (modifica, elimina come icone con AccessibleLabel).
- Contenuto come coppie etichetta/valore, etichetta 12 grigia sopra il valore 14, in una colonna su telefono e in due colonne su schermi larghi.
- Azioni di processo (Approva / Rifiuta) in basso: una primaria, una secondaria.

### Modulo
- Una colonna su telefono; due colonne su tablet solo per campi che stanno bene affiancati (data inizio / data fine).
- Etichetta sopra il campo, campi alti 36–40, larghezza proporzionata al contenuto atteso (un CAP non è largo quanto una nota).
- Raggruppa con un titolo di sezione solo se i campi sono più di 8.
- Validazione sotto il campo, in rosso, al momento giusto (all'uscita dal campo o all'invio, non mentre si scrive).
- Pulsante primario („Invia") e secondario („Annulla") in fondo, nello stesso punto in tutte le schermate di modulo.

### Approvazione / coda di lavoro
- Elenco delle voci in attesa con il dato che serve per decidere già nella riga (importo, richiedente, date).
- Dettaglio con azioni Approva / Rifiuta; la motivazione del rifiuto in un campo che compare solo quando serve.

## 5. Elementi ricorrenti

### Intestazione
- Una barra semplice, alta 48–56: sfondo bianco con divisore in basso, oppure il colore primario con testo bianco (una scelta per tutta l'app).
- Contenuto: freccia indietro (se non è la schermata iniziale), titolo, al massimo una o due azioni a destra.
- Niente logo grande, niente saluto, niente immagine di sfondo. Il nome dell'utente, se serve, in piccolo a destra.
- Uguale in tutte le schermate: costruiscila come componente o come contenitore copiato identico.

### Pulsanti
- Primario: sfondo primario, testo bianco, raggio 4, altezza 32–40, larghezza dal testo + 24 di padding (non a tutta larghezza su desktop).
- Secondario: sfondo bianco, bordo #D1D1D1, testo #242424.
- Distruttivo: come il secondario, con testo rosso, oppure rosso pieno solo nella conferma finale.
- Disattivato: `DisplayMode.Disabled` quando l'azione non è possibile (con il motivo visibile vicino, se non è ovvio).

### Elenchi
- Righe, non card. Le card si usano solo per contenuti visivi (prodotti con foto, documenti con anteprima).
- La riga selezionata o premuta ha un leggero sfondo (#F5F5F5), non un bordo colorato spesso.

### Stati
- **Vuoto**: un testo grigio centrato nell'area dell'elenco, eventualmente con l'azione per uscirne. Niente illustrazioni grandi.
- **Caricamento**: l'indicatore di caricamento predefinito o un testo „Caricamento…"; niente spinner personalizzati animati con timer.
- **Errore**: messaggio sotto il campo o `Notify`; vedi `testi-app.md`.

## 6. Telefono, tablet, desktop

- Chiedi o deduci il dispositivo principale: un'app per chi lavora in magazzino è per telefono, un'app di back office è per desktop.
- Usa contenitori con layout automatico e dimensioni relative (`Parent.Width`, `FillPortions`) invece di coordinate fisse, e disattiva „Adatta alla pagina" (Scale to fit) se l'app deve adattarsi a più dispositivi.
- Su telefono: una colonna, azione principale in basso a tutta larghezza, aree toccabili alte almeno 40.
- Su desktop: contenuto con larghezza massima (circa 960–1200) invece di righe lunghissime; elenco e dettaglio affiancati se l'utente lavora su molte voci di fila.

## 7. Esempi prima/dopo

**Schermata iniziale di un'app ferie**
- PRIMA (IA): sfondo con sfumatura viola-blu; in alto „Ciao Mario! 👋 Pronto a pianificare le tue vacanze?"; 4 card colorate arrotondate con icone grandi („Ferie residue 12", „In attesa 2", „Approvate 8", „Rifiutate 1"); sotto, un pulsante a pillola viola „🚀 Nuova richiesta"; barra di navigazione in basso con 5 icone.
- DOPO: intestazione bianca con „Le mie richieste" a sinistra e „Nuova richiesta" (pulsante primario) a destra; una riga sotto con „Ferie residue: 12 giorni" in grigio, perché è l'unico numero che l'utente usa per decidere; elenco a righe delle richieste, ordinate per data, con lo stato come testo colorato. Nessuna barra in basso: le altre schermate (nuova richiesta, dettaglio) si raggiungono da qui.

**Riga di elenco**
- PRIMA: card bianca con raggio 16 e ombra marcata, icona calendario blu a sinistra, titolo in grassetto 18, tre righe di testo, badge verde a pillola „✅ APPROVATA", altezza 140.
- DOPO: riga alta 64 senza bordo, divisore sotto; „Ferie 24–28/11" in 14 semibold; „5 giorni · inviata il 10/11" in 12 grigio; a destra „Approvata" in 12 verde #107C10 su sfondo #F1FAF1 con raggio 4.

**Modulo**
- PRIMA: campi centrati larghi quanto lo schermo dentro una card con ombra, ogni etichetta con un'icona, pulsante „Invia ✨" a pillola con sfumatura.
- DOPO: campi allineati a sinistra con etichetta sopra, data di inizio e di fine affiancate su tablet, „Invia" primario e „Annulla" secondario in fondo a destra.

## 8. Checklist visiva

1. L'app si apre sulla schermata di lavoro, senza benvenuto né cruscotto non richiesto?
2. Un solo colore d'accento, colori di stato usati solo per gli stati, niente sfumature né palette viola/indaco non richiesta?
3. Colori, font e misure vengono dal tema in `App.Formulas`, non scritti a mano in ogni controllo?
4. Un font, al massimo 4 dimensioni, grassetto con parsimonia, niente MAIUSCOLO né Title Case?
5. Spaziature solo dalla scala 4–8–12–16–24–32, raggio 4 ovunque, ombre assenti o leggere, niente card dentro card?
6. Icone solo per azioni o concetti universali, zero emoji?
7. Elenchi a righe compatte, allineati a sinistra, con il dato principale evidenziato?
8. Un solo pulsante primario per schermata, nella stessa posizione in tutte le schermate dello stesso tipo?
9. Stati vuoto, caricamento ed errore progettati?
10. Ogni schermata ha la forma del suo compito? Il test „cambio titolo e colonne: andrebbe bene per un'altra app?" dà no?
11. Nessuna funzione, schermata o dato che l'utente non ha chiesto?
