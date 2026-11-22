---
name: powerapps-umano
description: 'Progetta e costruisce app canvas Microsoft Power Apps come le farebbe uno sviluppatore esperto, non come le genera un''IA: aspetto sobrio e specifico (niente schermate di benvenuto, cruscotti inventati, sfumature, card arrotondate ovunque, emoji, palette viola), tema centralizzato in App.Formulas, layout responsive con contenitori, testi chiari in italiano al "tu". Consegna lo YAML delle schermate da incollare in Power Apps Studio con "Incolla codice", più le formule dell''app e le istruzioni per collegare i dati (SharePoint, Dataverse, Excel, SQL). Usala ogni volta che l''utente chiede di creare, progettare, rifare, ridisegnare o migliorare un''app Power Apps, una schermata, una galleria, un modulo, un tema o un layout canvas, anche se non dice "umano" o "non da IA"; e quando dice che un''app "sembra fatta da ChatGPT", "è troppo carica", "sembra un template", "non sembra professionale". Non serve per testi generici (post, email, report): per quelli c''è unslop-it.'
---

# Power Apps umano

Costruisce app canvas Power Apps che sembrano progettate da una persona che conosce il processo: sobrie, specifiche, coerenti, facili da mantenere. Consegna YAML da incollare in Power Apps Studio.

## Cosa distingue un'app „da IA" da un'app progettata

Un'app generata parte da un modello di „app moderna" uguale per tutto: schermata di benvenuto, cruscotto con numeri grandi, card arrotondate con ombre, sfumature, un'icona per ogni etichetta, emoji, colori viola e indaco. È decorata ma generica: cambiando titolo e colonne andrebbe bene per qualsiasi altra app.

Un'app progettata da una persona è riconoscibile per il contrario: **si apre sul lavoro da fare, usa un solo colore d'accento con un significato, ha una gerarchia chiara, e ogni elemento è sullo schermo perché all'utente serve.** La forma di ogni schermata viene dal suo contenuto: un elenco di approvazioni non somiglia a un modulo di nota spese.

Il test che riassume la skill: **se cambi titolo e colonne, la schermata andrebbe bene per un'altra app qualsiasi?** Se sì, è un template: rifalla partendo dal compito.

## Flusso di lavoro

### 1. Capire il processo prima di disegnare

Le app sembrano generiche soprattutto quando chi le costruisce non sa per chi sono. Prima di scrivere YAML devi sapere:

- **Chi la usa e su che dispositivo** (telefono in reparto, desktop in ufficio, tablet).
- **Il compito principale**: cosa fa l'utente nove volte su dieci quando apre l'app. Diventa la schermata iniziale.
- **I dati**: origine (lista SharePoint, tabella Dataverse, Excel, SQL), nome e colonne con il loro tipo. Non inventare mai colonne: se non le conosci, chiedile; se l'utente vuole procedere lo stesso, usa nomi segnaposto evidenti (`[NomeColonnaData]`) ed elencali tra le cose da sostituire.
- **Le regole del processo**: chi approva, quali campi sono obbligatori, quali stati esistono.
- **Il brand**: colore aziendale, logo, font. Se non c'è, usa la palette neutra Fluent di `references/design-visivo.md`.

Se la richiesta lascia aperti punti che cambiano il progetto (dispositivo, origine dati, colonne), fai **una sola** domanda raggruppata. Per il resto scegli valori sensati e dichiarali.

### 2. Disegnare il minimo di schermate

Elenca le schermate prima di costruirle, con una riga per ciascuna su cosa contiene e da dove si arriva. Di solito bastano 2–4 schermate (elenco, dettaglio, modulo, eventualmente approvazione): vedi gli schemi in `references/design-visivo.md`, sezione 4. Niente schermate di benvenuto, cruscotti, impostazioni, profili o menu che l'utente non ha chiesto; se pensi che una funzione in più sarebbe utile, proponila in fondo, non costruirla.

### 3. Fissare il tema in App.Formulas

Colori, font, dimensioni e spaziature si definiscono una volta come formule con nome e si richiamano nei controlli (`Colori.Primario`, `Colori.TestoSecondario`, `Carattere.Testo`, `Spazio.L`, `Raggio`). È quello che fa uno sviluppatore esperto ed è ciò che tiene coerente l'app: cambiare colore aziendale diventa una modifica sola. Modello in `assets/tema.fx` e regole in `references/yaml-power-apps.md`.

### 4. Costruire le schermate in YAML

Leggi `references/yaml-power-apps.md` prima di scrivere: contiene il formato accettato da „Incolla codice", i tipi di controllo, le proprietà dei contenitori e gli errori che fanno fallire l'incolla. Regole che contano di più:

- **Contenitori con layout automatico** e dimensioni relative, non coordinate fisse: l'app si adatta a telefono e desktop e si modifica facilmente.
- **Nomi dei controlli con prefisso e significato** (`scrElencoRichieste`, `galRichieste`, `btnNuovaRichiesta`, `lblTitolo`), mai `Label1` o `Button3`.
- **Formule essenziali**: niente commenti che ripetono il codice, niente `With()` e `IfError()` annidati per abitudine. Gestisci gli errori dove l'operazione può fallire davvero (`Patch`, `SubmitForm`).
- **Formule delegabili** sulle origini grandi (SharePoint, Dataverse, SQL): `Filter` e `Sort` su colonne semplici, niente `Search` o `in` su liste che possono superare 500/2000 elementi senza avvisare l'utente del limite.
- **Testi** secondo `references/testi-app.md`: al „tu", niente esclamativi, emoji, „con successo", pulsanti con verbo, errori con rimedio, conferme con verbo e conseguenza.

### 5. Controllare l'aspetto prima di consegnare

Salva ogni schermata in un file `.yaml` ed esegui `python scripts/controlla_app.py <file.yaml>`. Prima di tutto controlla la **sintassi** (valori senza `=`, due punti in formule su una riga, record letterali non protetti, tabulazioni, nomi duplicati, YAML non valido): un errore P0 qui significa che l'incolla fallirà, e capita anche a chi scrive YAML con attenzione. Poi segnala in modo meccanico emoji, colori scritti a mano invece che dal tema, troppi colori o dimensioni di carattere, raggi e ombre eccessivi, spaziature fuori scala, nomi di controlli predefiniti, testi da IA. Poi ripassa a mente la checklist visiva (sezione 8 di `references/design-visivo.md`) e il test del template. Correggi e riesegui finché il controllo non segnala più nulla che non sia una scelta voluta.

## I segni da IA da evitare (versione breve)

Il catalogo completo, con la gravità, è in `references/design-visivo.md`, sezione 2. I più frequenti:

1. Schermata di benvenuto o saluto con emoji („Ciao Mario! 👋").
2. Cruscotto di card con numeri grandi che nessuno ha chiesto.
3. Sfumature, trasparenze decorative, palette viola/indaco/azzurro elettrico.
4. Card arrotondate con ombra ovunque, card dentro card, pulsanti a pillola.
5. Un'icona accanto a ogni etichetta, icone grandi decorative, emoji.
6. Tutto centrato, tutto in grassetto, titoli in Title Case, etichette in MAIUSCOLO.
7. Spazi enormi: tre voci per schermata invece di otto.
8. Più pulsanti primari, colori diversi per ogni categoria, badge arcobaleno.
9. Barra di navigazione con 5 icone per un'app con 3 schermate.
10. Animazioni, timer, transizioni decorative.
11. Dati finti, avatar, „Lorem ipsum" lasciati nell'app.
12. Colori e misure scritti a mano in ogni controllo invece che dal tema.

E i loro contrari, il sistema di base: **sfondo bianco, un colore d'accento, grigi per la gerarchia, colori di stato solo per gli stati, Segoe UI con 4 dimensioni al massimo, spaziature dalla scala 4–8–12–16–24–32, raggio 4, divisori sottili invece delle ombre, righe compatte invece delle card.** Valori esatti in `references/design-visivo.md`, sezione 3.

## Salvaguardie

- **Non inventare dati**: nomi di liste, colonne, valori di scelta, utenti, numeri. Quello che non sai diventa un segnaposto evidente e una voce nell'elenco „Da completare".
- **Non aggiungere funzioni**: costruisci ciò che è stato chiesto. Le idee in più vanno in una riga di proposta.
- **Su un'app esistente**, cambia ciò che è stato chiesto e lascia intatto il resto: nomi di controlli, variabili, collezioni e logica che l'utente non ha chiesto di toccare restano identici. Se trovi un problema fuori dal perimetro (una formula non delegabile, un bug), segnalalo senza correggerlo di tua iniziativa.
- **Non garantire ciò che non puoi verificare**: non puoi aprire Studio. Di' quali parti vanno controllate dopo l'incolla (versioni dei controlli, nomi delle colonne, delega).

## Formato di consegna

Consegna nell'ordine, senza preamboli:

1. **Progetto in breve**: le schermate, una riga ciascuna (cosa contiene, da dove si arriva), e le scelte fatte su dispositivo, colori e dati.
2. **Formule dell'app**: il blocco `App.Formulas` (tema e formule con nome) e `App.OnStart` solo se serve davvero, da incollare nella barra della formula dell'oggetto App.
3. **Una sezione per schermata** con lo YAML completo in un blocco di codice `yaml`, pronto per „Incolla codice".
4. **Come incollare e collegare**: i passaggi (aggiungere l'origine dati con il nome usato nelle formule, creare una schermata vuota, incollare, impostare la schermata iniziale in `App.StartScreen`).
5. **Da completare o verificare**: segnaposto da sostituire, colonne da confermare, controlli da verificare dopo l'incolla, avvisi di delega.

Se il file YAML è lungo, salvalo anche come file `.yaml` (uno per schermata) e indica dove si trova.

## Riferimenti

- `references/design-visivo.md`: segni visivi da IA, sistema visivo di base (colori, tipografia, spaziature, forme), schemi di schermata, elementi ricorrenti, esempi prima/dopo, checklist. **Da leggere sempre.**
- `references/yaml-power-apps.md`: formato YAML di „Incolla codice", tipi e versioni dei controlli, proprietà dei contenitori, App.Formulas, errori comuni. **Da leggere prima di scrivere YAML.**
- `references/testi-app.md`: regole per i testi dell'interfaccia (pulsanti, errori, Notify, conferme, stati vuoti, accessibilità). Da leggere quando scrivi i testi.
- `assets/tema.fx`: tema di partenza in App.Formulas. `assets/schermata-elenco.yaml`, `assets/schermata-modulo.yaml`: schermate di esempio da adattare al processo, non da copiare così come sono.
- `scripts/controlla_app.py`: controllo meccanico dello YAML prodotto.
