# YAML per „Incolla codice" in Power Apps Studio

Come scrivere YAML che Studio accetta al primo colpo. Fonti: documentazione Microsoft Learn (Code view, Source code files pa.yaml, Power Fx YAML formula grammar, Build responsive apps) e lo schema pa.yaml v3.0 di PowerApps-Tooling, verificati a novembre 2026. Il formato è in evoluzione: quando qualcosa non torna, la versione copiata dallo Studio dell'utente ha sempre ragione.

## Indice

1. Come si incolla
2. Struttura di un controllo
3. Regole di sintassi che fanno fallire l'incolla
4. Tipi di controllo da usare
5. Contenitori con layout automatico
6. Proprietà di stile dei controlli classici
7. Il tema in App.Formulas
8. Schermata: struttura consigliata
9. Dati: SharePoint, Dataverse, Excel, SQL
10. Messaggi di errore e cosa significano

---

## 1. Come si incolla

- In Studio, nella visualizzazione ad albero, si seleziona una schermata (o un contenitore) e si usa **Incolla codice** dal menu, oppure Ctrl+V con lo YAML negli appunti. Studio valida il codice e crea i controlli. Il browser deve avere il permesso di leggere gli appunti.
- Si incollano **controlli**, non l'oggetto App: `App.Formulas`, `App.OnStart` e `App.StartScreen` si scrivono a mano nella barra della formula selezionando **App** nell'albero.
- Una schermata intera non si incolla in modo affidabile: il metodo sicuro è **creare una schermata vuota, rinominarla e incollarci dentro un unico contenitore radice** che contiene tutto il resto.
- Il colore di sfondo della schermata (`Fill`) e il suo nome si impostano a mano; dagli in consegna il valore (`=Colori.Sfondo`).
- Nelle impostazioni dell'app (Impostazioni → Visualizzazione) va disattivato **Adatta alla pagina** se l'app deve adattarsi a telefono e desktop.

## 2. Struttura di un controllo

Lo YAML da incollare è una lista (ogni elemento comincia con `- `) di controlli; ogni controllo ha un nome unico e queste chiavi:

```yaml
- conElencoRadice:
    Control: GroupContainer
    Variant: AutoLayout
    Properties:
      Width: =Parent.Width
      Height: =Parent.Height
      LayoutDirection: =LayoutDirection.Vertical
    Children:
      - lblTitolo:
          Control: Label
          Properties:
            Text: ="Le mie richieste"
```

- `Control`: il tipo. Si può scrivere senza versione (`Label`) e Studio usa la versione più recente: è la scelta consigliata. Non inventare mai un numero di versione; se l'utente vuole le versioni esatte, chiedigli di copiare un controllo dello stesso tipo dalla sua app e leggerle da lì. Nella stessa app tutti i controlli di un tipo devono avere la stessa versione.
- `Variant`: obbligatoria per `GroupContainer` (`AutoLayout`, `ManualLayout`, `GridLayout`) e `Gallery` (`Vertical`, `Horizontal`, `VariableHeight`); non usarla sugli altri controlli se non sai che la prevedono.
- `Properties`: ogni valore è una formula Power Fx e **comincia con `=`**. Scrivi solo le proprietà che cambiano rispetto al predefinito.
- `Children`: lista ordinata. Nei contenitori con layout automatico l'ordine è l'ordine di visualizzazione; altrove è l'ordine di sovrapposizione (il primo sta sotto).
- Indentazione con **spazi**, mai tabulazioni.

## 3. Regole di sintassi che fanno fallire l'incolla

1. **Ogni valore comincia con `=`**: `Text: ="Salva"`, `Width: =320`, `Visible: =true`.
2. **Due punti seguiti da spazio dentro un valore** (anche dentro una stringa) rompono lo YAML: `Text: ="Totale: " & n` fallisce. **Doppio cancelletto e cancelletto** idem (`ColorValue("#0F6CBD")` su una riga è a rischio). Soluzione: blocco `|-`.
3. **Record letterali** (`{Value: "x"}`) vanno sempre in un blocco `|-` o tra apici singoli.
4. **Formule su più righe**: blocco `|-`, con `=` all'inizio della prima riga di contenuto.

```yaml
Text: |-
  ="Ferie residue: " & varGiorniResidui & " giorni"
OnSelect: |-
  =Patch(Richieste; Defaults(Richieste); {Titolo: txtTitolo.Text});;
  Navigate(scrElencoRichieste)
```

Regola pratica: **usa `|-` per ogni formula che contiene una stringa con due punti, un cancelletto, un record o più istruzioni**. Non costa nulla ed evita l'errore più comune.

5. **Separatori della lingua**: con Studio in italiano gli argomenti si separano con `;`, le istruzioni concatenate con `;;` e i decimali con `,`. In inglese `,` `;` `.`. Chiedi o deduci la lingua dell'utente (dalle formule che ha incollato) e usa una sola convenzione; se non lo sai, usa quella italiana e dillo nella consegna. In questo file gli esempi usano `;`.
6. **Niente chiavi vuote**: un `Properties:` senza proprietà fa fallire tutto; toglilo.
7. **Niente proprietà duplicate** nello stesso controllo.
8. **I commenti YAML (`#`) vengono scartati**: se un commento serve davvero, va dentro la formula con `//`. Di norma non serve.

## 4. Tipi di controllo da usare

Usa i controlli **classici**: si incollano senza sorprese, accettano tutte le proprietà di stile e si legano al tema. I controlli moderni (Fluent) usano un sistema di temi proprio; usali solo se l'utente li ha già nell'app, e in quel caso chiedigli di copiarne uno per avere il tipo esatto.

| Serve per | `Control:` | Note |
|---|---|---|
| Contenitore | `GroupContainer` + `Variant: AutoLayout` | struttura di ogni schermata |
| Testo | `Label` | etichette, titoli, valori |
| Pulsante | `Classic/Button` | |
| Casella di testo | `Classic/TextInput` | `HintText` per il segnaposto |
| Data | `Classic/DatePicker` | `InputTextPlaceholder` per il segnaposto, `Format: =DateTimeFormat.ShortDate`, `Language: ="it-IT"` |
| Menu a discesa | `Classic/DropDown` | pochi valori fissi |
| Casella combinata | `Classic/ComboBox` | molti valori, ricerca, persone |
| Icona | `Classic/Icon` | `Icon: =Icon.ChevronRight`, `Icon.Edit`, `Icon.Trash`, `Icon.Add`, `Icon.ChevronLeft`, `Icon.Search`, `Icon.Cancel` |
| Elenco | `Gallery` + `Variant: Vertical` | i figli sono il modello della riga |
| Linea divisoria o fondo | `Rectangle` | non ha angoli arrotondati |
| Interruttore / casella di spunta | `Classic/Toggle` / `Classic/CheckBox` | |
| Immagine | `Image` | solo se l'immagine serve |

**Evita i moduli (`Form` con schede dati) nello YAML incollato**: il collegamento delle schede dati alle colonne è fragile in incolla. Per i moduli costruisci i campi con etichette e caselle in un contenitore e salva con `Patch`; oppure, se l'utente preferisce un modulo standard, digli di inserirlo da Studio e di applicare le proprietà di stile che gli fornisci.

Se Studio risponde „tipo di controllo sconosciuto", il nome è cambiato: chiedi all'utente di copiare un controllo di quel tipo dalla sua app e usa il nome che compare.

## 5. Contenitori con layout automatico

Dentro un `GroupContainer` con `Variant: AutoLayout` la posizione dei figli la decide il contenitore: `X` e `Y` dei figli vengono ignorati, non scriverli.

Proprietà del contenitore:

| Proprietà | Valori |
|---|---|
| `LayoutDirection` | `=LayoutDirection.Vertical` / `=LayoutDirection.Horizontal` |
| `LayoutGap` | spazio tra i figli (`=Spazio.M`) |
| `PaddingTop`, `PaddingBottom`, `PaddingLeft`, `PaddingRight` | margini interni |
| `LayoutAlignItems` | allineamento sull'asse trasversale: `=LayoutAlignItems.Start`, `.Center`, `.End`, `.Stretch` |
| `LayoutJustifyContent` | sull'asse principale: `=LayoutJustifyContent.Start`, `.Center`, `.End`, `.SpaceBetween` |
| `LayoutOverflowY` | `=LayoutOverflow.Scroll` per scorrere |
| `LayoutWrap` | `=true` per andare a capo |
| `Fill`, `BorderColor`, `BorderThickness`, `DropShadow`, `RadiusTopLeft`/`TopRight`/`BottomLeft`/`BottomRight` | stile |

Proprietà dei figli:

| Proprietà | Uso |
|---|---|
| `FillPortions` | quota dello spazio libero (`=1` occupa il resto); `=0` per mantenere `Width`/`Height` fissi |
| `AlignInContainer` | `=AlignInContainer.Stretch`, `.Start`, `.Center`, `.End`, `.SetByContainer` |
| `LayoutMinWidth`, `LayoutMinHeight`, `LayoutMaxWidth`, `LayoutMaxHeight` | limiti |

Regole:
- Un figlio a dimensione fissa (intestazione alta 56, pulsante largo 140) ha `FillPortions: =0` e la sua `Height`/`Width`.
- Il contenuto che deve occupare il resto (la galleria) ha `FillPortions: =1`.
- Il contenitore radice ha `X: =0`, `Y: =0`, `Width: =Parent.Width`, `Height: =Parent.Height`.
- Un contenitore non ha `OnSelect`: per rendere cliccabile un'area usa un pulsante o un'icona.
- `DropShadow`: `=DropShadow.None` di norma; `Light` o `Semilight` solo su un popup.

## 6. Proprietà di stile dei controlli classici

**Label**: `Text`, `Font` (`=Font.'Segoe UI'`), `Size`, `FontWeight` (`=FontWeight.Semibold`, `.Normal`), `Color`, `Fill`, `Align` (`=Align.Left`, `.Right`, `.Center`), `VerticalAlign` (`=VerticalAlign.Middle`), `PaddingLeft`/`Right`/`Top`/`Bottom`, `Height`, `Width`, `AutoHeight` (`=true` per testi che vanno a capo), `Wrap`.

**Classic/Button**: `Text`, `OnSelect`, `Fill`, `Color`, `HoverFill`, `HoverColor`, `PressedFill`, `BorderColor`, `BorderThickness`, `HoverBorderColor`, `RadiusTopLeft`/`TopRight`/`BottomLeft`/`BottomRight`, `Font`, `Size`, `FontWeight`, `Height`, `Width`, `DisplayMode`, `DisabledFill`, `DisabledColor`, `FocusedBorderThickness`.

**Classic/TextInput**: `Default`, `HintText`, `Mode` (`=TextMode.MultiLine` per le note), `Fill`, `Color`, `BorderColor`, `HoverBorderColor`, `FocusedBorderColor`, `BorderThickness`, `FocusedBorderThickness`, `Radius*`, `Font`, `Size`, `Height`, `PaddingLeft`, `AccessibleLabel`.

**Classic/Icon**: `Icon`, `Color`, `HoverColor`, `OnSelect`, `AccessibleLabel`, `Height`, `Width`, `PaddingTop`/`Bottom`/`Left`/`Right` (un'icona 20 in un'area toccabile 40: `Width: =40`, padding 10).

**Gallery**: `Items`, `TemplateSize` (altezza della riga), `TemplatePadding` (`=0` per righe con divisore), `OnSelect`, `ShowScrollbar`, `TemplateFill` (per evidenziare la riga selezionata: `=If(ThisItem.IsSelected; Colori.SfondoSecondario; Colori.Sfondo)`). Dentro la galleria i figli si posizionano con `X`/`Y`/`Width` relativi a `Parent.TemplateWidth` e `Parent.TemplateHeight`, oppure con un contenitore orizzontale con layout automatico come unico figlio. Non calcolare l'altezza della galleria da `CountRows(...)`: dai `FillPortions: =1` nel contenitore.

**Colori**: `Colori.Primario` (dal tema), `RGBA(15, 108, 189, 1)`, `ColorValue("#0F6CBD")`, `Color.White`, `ColorFade(Colori.Primario; -10%)`. Nei controlli usa sempre il tema; i valori letterali stanno solo in `App.Formulas`.

## 7. Il tema in App.Formulas

Le formule con nome si scrivono nella proprietà **Formulas** dell'oggetto App (barra della formula, non YAML). Si calcolano quando servono e si richiamano ovunque. Modello completo in `assets/tema.fx`; la struttura:

```
Colori = {
    Primario: ColorValue("#0F6CBD");
    PrimarioHover: ColorValue("#115EA3");
    PrimarioPremuto: ColorValue("#0F548C");
    Sfondo: ColorValue("#FFFFFF");
    SfondoSecondario: ColorValue("#F5F5F5");
    Bordo: ColorValue("#E0E0E0");
    BordoCampo: ColorValue("#D1D1D1");
    Testo: ColorValue("#242424");
    TestoSecondario: ColorValue("#616161");
    TestoDisattivato: ColorValue("#A19F9D");
    Errore: ColorValue("#C50F1F");
    ErroreSfondo: ColorValue("#FDF3F4");
    Successo: ColorValue("#107C10");
    SuccessoSfondo: ColorValue("#F1FAF1");
    Avviso: ColorValue("#BC4B09");
    AvvisoSfondo: ColorValue("#FFF9F5")
};;
Carattere = { Titolo: 20; Sezione: 16; Testo: 14; Piccolo: 12 };;
Spazio = { XS: 4; S: 8; M: 12; L: 16; XL: 24; XXL: 32 };;
Raggio = 4;;
```

Con Studio in inglese i separatori sono `,` dentro i record e `;` tra le formule. Ogni formula con nome finisce con il separatore di istruzioni (`;;` in italiano, `;` in inglese).

Nei controlli: `Fill: =Colori.Primario`, `Size: =Carattere.Testo`, `PaddingLeft: =Spazio.L`, `RadiusTopLeft: =Raggio`. Il font si imposta per controllo (`Font: =Font.'Segoe UI'`); non serve metterlo nel tema.

Altre formule con nome utili, solo se servono davvero all'app: l'utente corrente (`UtenteCorrente = User();;`), un filtro riusato in più schermate, l'elenco degli stati (`Stati = ["In attesa"; "Approvata"; "Rifiutata"];;` con Studio in italiano, `["In attesa", ...]` in inglese). Non spostare in `App.OnStart` ciò che può stare in `App.Formulas`.

## 8. Schermata: struttura consigliata

```
scrElencoRichieste (schermata vuota creata a mano, Fill = Colori.Sfondo)
└─ conElencoRadice          GroupContainer AutoLayout verticale, tutta la schermata
   ├─ conElencoIntestazione  orizzontale, Height 56, FillPortions 0, divisore sotto (BorderThickness o Rectangle)
   │  ├─ lblElencoTitolo     FillPortions 1
   │  └─ btnNuovaRichiesta   FillPortions 0, Width dal testo
   ├─ conElencoFiltri        orizzontale, solo se servono
   └─ galRichieste           FillPortions 1
      └─ (modello della riga: etichette, stato, icona freccia, divisore)
```

Prefissi dei nomi: `scr` schermata, `con` contenitore, `lbl` etichetta, `btn` pulsante, `txt` casella di testo, `dtp` data, `drp` menu a discesa, `cmb` casella combinata, `gal` galleria, `ico` icona, `rec` rettangolo, `tgl` interruttore, `chk` casella di spunta, `img` immagine. Il nome dice cosa è e a cosa serve (`lblRigaStato`, `btnInviaRichiesta`). Poiché i nomi dei controlli sono unici in tutta l'app, ripeti un pezzo del nome della schermata quando lo stesso ruolo compare in più schermate (`lblElencoTitolo`, `lblDettaglioTitolo`).

Variabili: `var` globali (`Set`), `loc` di contesto (`UpdateContext`), `col` collezioni.

## 9. Dati: SharePoint, Dataverse, Excel, SQL

- L'origine dati si aggiunge a mano in Studio (Dati → Aggiungi dati); nello YAML si usa il nome che avrà nell'app. Dillo nella consegna: „aggiungi la lista SharePoint *Richieste ferie*: nelle formule si chiama `'Richieste ferie'`".
- Nomi con spazi tra apici singoli: `'Richieste ferie'`, `ThisItem.'Data inizio'`.
- **Colonne di SharePoint**: le colonne di scelta si leggono con `.Value` (`ThisItem.Stato.Value`), le colonne persona con `.DisplayName` / `.Email`, le colonne di ricerca con `.Value`. In `Patch` una scelta si scrive come record: `{Stato: {Value: "In attesa"}}` (in un blocco `|-`).
- **Dataverse**: le scelte si confrontano con l'enumerazione (`ThisItem.Stato = 'Stato (Richieste)'.'In attesa'`); le ricerche si leggono come record.
- **Excel**: il file deve essere su OneDrive/SharePoint con i dati formattati come tabella; non è delegabile, va bene per poche centinaia di righe.
- **SQL**: le tabelle hanno bisogno di una chiave primaria per essere modificate.
- **Delega**: `Filter`, `Sort`, `SortByColumns`, `LookUp` con confronti semplici sono delegabili su SharePoint, Dataverse e SQL; `Search`, `in`, `Len`, funzioni sui testi spesso no. Se una formula non è delegabile su un'origine che può crescere, dillo e proponi l'alternativa (per esempio `StartsWith` invece di `Search` su SharePoint).
- Non inventare nomi di liste, colonne o valori di scelta: chiedili o usa segnaposto evidenti e mettili nell'elenco „Da completare".

## 10. Messaggi di errore e cosa significano

| Messaggio di Studio | Causa | Correzione |
|---|---|---|
| `Power Fx expressions must start with '='` | valore senza `=` | aggiungi `=` |
| `While scanning a plain scalar value, found invalid mapping` | due punti e spazio in un valore, o record letterale | blocco `|-` |
| `did not find expected '-' indicator` | figlio senza `- ` | aggiungi `- ` |
| `Named object value cannot be null` | chiave vuota (`Properties:` vuoto) | togli la chiave |
| `Duplicate name` | proprietà ripetuta | togli il duplicato |
| `found character that cannot start any token` | tabulazione | sostituisci con spazi |
| `Unknown property` | proprietà che quel controllo non ha (es. raggio su `Rectangle`) | togli la proprietà o cambia controllo |
| Nome di controllo già esistente | nomi unici in tutta l'app | rinomina |

Quando consegni, ricorda all'utente che un errore di incolla è quasi sempre un carattere sbagliato, e che può incollarti il messaggio per correggerlo.
