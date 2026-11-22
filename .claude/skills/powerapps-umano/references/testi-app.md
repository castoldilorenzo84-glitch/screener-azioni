# Testi delle app Power Apps

Regole per i testi visibili all'utente. Le regole sull'aspetto grafico sono in `design-visivo.md`, quelle sullo YAML in `yaml-power-apps.md`.

Regole operative per scrivere e rivedere i testi visibili all'utente in un'app Power Apps (canvas o model-driven) in italiano, rivolgendosi all'utente con il „tu".

## Indice

1. Principi
2. Lavorare sulle formule Power Fx senza romperle
3. Regole per tipo di testo e controllo
4. Limiti di lunghezza
5. Formati it-IT in Power Fx
6. Glossario delle azioni
7. Accessibilità
8. Esempi prima/dopo
9. Checklist finale

## 1. Principi

- **L'utente scansiona, non legge.** Ogni testo deve dire cosa c'è o cosa fare, nel minor numero di parole che restano chiare. Le parole importanti vanno all'inizio, perché un controllo stretto tronca la fine.
- **L'app parla con il „tu", in modo uniforme.** Imperativo per le istruzioni („Seleziona un reparto"), indicativo per gli stati („Richiesta inviata", „Non hai richieste aperte"). Mai mescolare con „Lei", „voi" o infinito impersonale („Selezionare"). Il „tu" non autorizza il tono confidenziale: niente „Ehi!", „Dai!", battute.
- **L'app non ha un io e non prova emozioni.** Niente „Siamo felici di…", „Purtroppo", „Ops!", „Fantastico!", emoji, esclamativi. „Scusa" solo se l'app ha davvero causato un disagio all'utente (un servizio fuori uso), mai per un errore di inserimento.
- **Stessa cosa, stessa parola.** Se una schermata dice „Richiesta" e un'altra „Pratica" per lo stesso oggetto, l'utente pensa che siano due cose. Fissa un glossario (sezione 6) e applicalo ovunque: titoli, pulsanti, messaggi, colonne delle gallerie.
- **Il testo segue il dato reale.** Un messaggio di errore può dire solo ciò che la formula sa. Se `Patch` fallisce e la formula non distingue la causa, il messaggio non inventa „Connessione assente": dice cosa non è riuscito e cosa può fare l'utente, e la causa mancante va nelle lacune da segnalare.
- **Maiuscola solo all'iniziale (sentence case)** per titoli, pulsanti, etichette e voci di menu. Mai TUTTO MAIUSCOLO nel testo: se il design lo richiede, si ottiene con le proprietà del controllo o con `Upper()`, non scrivendo la stringa in maiuscolo.

## 2. Lavorare sulle formule Power Fx senza romperle

Quando l'utente incolla formule (barra della formula, „Copia codice", YAML di `pa.yaml`, sorgente scompattata):

1. **Tocca solo il contenuto delle stringhe letterali** (il testo tra doppie virgolette che l'utente vede). Tutto il resto resta identico carattere per carattere: nomi di controlli (`btnInvia`, `lblErrore`), variabili (`varUtente`, `locMostraPopup`), collezioni (`colRighe`), nomi di colonne e tabelle, funzioni, enumerazioni (`NotificationType.Error`), numeri, spazi e a capo significativi.
2. **Separatori della lingua di creazione**: con Power Apps in italiano il separatore di argomenti è `;`, il concatenamento di formule è `;;` e il decimale è `,`. In inglese sono `,`, `;` e `.`. Mantieni esattamente quelli che usa l'utente; non „correggere" mai una formula da una convenzione all'altra.
3. **Virgolette dentro le stringhe**: una virgoletta doppia dentro una stringa si scrive raddoppiata: `"Seleziona ""Nuova richiesta"""`. Più semplice: usa le virgolette tipografiche o le caporali nel testo (`"Seleziona «Nuova richiesta»"`), che non richiedono escape. Gli apostrofi (`'`) dentro le stringhe sono sicuri.
4. **Interpolazione**: in `$"Ciao {User().FullName}"` il contenuto tra `{}` è codice: non tradurlo né modificarlo. Nelle concatenazioni con `&` cura gli spazi ai bordi delle stringhe (`"Hai " & CountRows(colRighe) & " righe"`).
5. **Plurali**: Power Fx non gestisce i plurali da solo. Se il testo dipende da un numero, usa `If(n = 1; "1 richiesta"; n & " richieste")` solo se l'utente vuole modificare la logica; altrimenti scegli una formulazione che regga entrambi i casi („Richieste: 3").
6. **Messaggi di errore di sistema**: `FirstError.Message`, `Errors(...)` e simili restituiscono testo tecnico, spesso in inglese. Non mostrarlo da solo: anteponi una frase utile e, se serve per l'assistenza, metti il dettaglio dopo („Salvataggio non riuscito. Riprova; se il problema continua, invia questo dettaglio all'assistenza: " & FirstError.Message).
7. **Consegna**: restituisci le formule complete, pronte da incollare, e una tabella delle sole stringhe cambiate. Prima di consegnare, confronta ogni formula con l'originale fuori dalle virgolette.
8. **Model-driven / Dataverse**: nomi visualizzati di tabelle e colonne, descrizioni (che diventano tooltip), etichette di moduli e viste seguono le stesse regole; i nomi logici (`cr123_datainizio`) non si toccano mai.

## 3. Regole per tipo di testo e controllo

### Titoli di schermata e intestazioni (Label in header, `Title` di Form)
- Sostantivo o sintagma nominale che nomina il contenuto: „Le mie richieste", „Nuova richiesta", „Dettaglio ordine", „Approvazioni in attesa".
- Niente saluti nel titolo („Benvenuto nel portale ferie!" → „Richieste ferie"; il saluto, se serve, va in un testo secondario: „Ciao, {nome}").
- Niente punto finale, niente esclamativi.

### Pulsanti e voci di menu (`Text` di Button, icone con testo)
- Verbo all'imperativo + oggetto quando serve a distinguere: „Salva", „Invia richiesta", „Aggiungi riga", „Esporta in Excel".
- Il verbo dice cosa succede davvero: „Invia" se il dato parte verso un approvatore, „Salva" se resta in bozza.
- Vietati: „Clicca qui", „Premi qui", „OK" quando l'azione ha un nome, „Procedi", „Continua" generico se esiste un verbo specifico, „Sì/No" nelle conferme.
- L'azione principale ha un solo pulsante evidenziato per schermata.

### Etichette dei campi (`DisplayName` delle DataCard, Label sopra gli input)
- Sostantivo con l'iniziale maiuscola: „Data di inizio", „Centro di costo", „Note".
- Niente istruzioni nell'etichetta („Inserisci qui la data di inizio della ferie" → „Data di inizio").
- Due punti finali: o tutti o nessuno nell'app (la scelta consigliata è nessuno).
- Campo obbligatorio: lo indica il controllo (asterisco); non scrivere „(obbligatorio)" a mano se il modulo lo fa già.

### Testo segnaposto (`HintText` della casella di testo, `InputTextPlaceholder` del selettore data classico)
- Esempio di formato o di valore: „es. 24/11/2026", „es. Mario Rossi", „Cerca per nome o numero".
- Mai la ripetizione dell'etichetta („Data di inizio" → HintText „Inserisci la data di inizio" è inutile).
- Mai al posto dell'etichetta: scompare quando l'utente scrive e molti lettori di schermo non lo leggono come etichetta.

### Messaggi di validazione (Label di errore sotto i campi, `ErrorMessage` delle DataCard)
- Cosa correggere, in forma di istruzione: „Inserisci una data di fine successiva alla data di inizio.", „Il numero di telefono deve avere almeno 9 cifre."
- Nessuna colpa („Hai sbagliato…", „Valore non valido!"), nessun „Errore:" come prefisso.
- Il messaggio compare vicino al campo, non solo in un Notify generico.

### Notifiche (`Notify(messaggio; NotificationType.X; durata)`)
- **Successo** (`Success`): participio + oggetto, una frase: „Richiesta inviata.", „Modifiche salvate.", „Ordine 4521 approvato." Mai „con successo", mai esclamativi o emoji.
- **Errore** (`Error`): cosa non è riuscito + cosa fare: „Richiesta non inviata. Controlla la connessione e riprova." (solo se la formula sa che è un problema di connessione; altrimenti „Richiesta non inviata. Riprova tra qualche minuto; se il problema continua, contatta l'assistenza IT.").
- **Avviso** (`Warning`): la conseguenza e come evitarla: „Le ore superano il limite giornaliero di 8. Controlla le righe evidenziate."
- **Informazione** (`Information`): fatto utile, non decorativo. Se l'informazione non serve per agire, togli il Notify.
- Una frase, al massimo due. Durata: lascia quella esistente.

### Finestre di conferma (popup costruiti con contenitori o dialoghi)
- Titolo: domanda con infinito che nomina azione e oggetto: „Eliminare la richiesta?", „Annullare le modifiche?"
- Corpo: la conseguenza concreta: „La richiesta del 24/11 verrà eliminata e non potrai recuperarla."
- Pulsanti: il verbo dell'azione e „Annulla": „Elimina" / „Annulla", „Esci senza salvare" / „Continua a modificare". Mai „Sì" / „No", mai „Sei sicuro?" come unico testo.
- Il pulsante distruttivo non è quello evidenziato di default.

### Schermate e gallerie vuote
- Cosa manca + come rimediare: „Nessuna richiesta. Per crearne una, seleziona Nuova richiesta." / „Nessun risultato per «rossi». Prova con un altro nome."
- Se l'utente non può fare nulla, basta lo stato: „Nessuna approvazione in attesa."

### Caricamento e stati
- „Caricamento…", „Invio in corso…", „Salvataggio…". Carattere „…" unico.
- Niente „Attendere prego", „Un attimo di pazienza!".

### Tooltip (`Tooltip`) e testo di aiuto
- Aggiungono informazione che l'etichetta non ha: una regola, un limite, una conseguenza. „Le ferie si possono chiedere fino a 60 giorni prima."
- Se il tooltip ripete l'etichetta, toglilo.

### Saluti e onboarding
- „Ciao, {nome}" o nessun saluto. Evita „Benvenuto/a" (barra per il genere) e „Benvenuto" al maschile generico; se serve un benvenuto, „Ti diamo il benvenuto in Richieste ferie".
- Testi di introduzione: al massimo due frasi su cosa si fa con l'app; niente „Questa app rivoluzionerà il tuo modo di gestire le ferie".

### Linguaggio inclusivo
- Rivolgendosi con il „tu" e con forme impersonali („Richiesta inviata") si evitano quasi tutti i problemi di genere. Evita „l'utente", „il richiedente", „il dipendente" nei testi rivolti alla persona; usa „tu" o riformula („Chi ha creato la richiesta" invece di „Il richiedente").

## 4. Limiti di lunghezza

L'italiano è in media il 20–30 % più lungo dell'inglese, e le app Power Apps vengono spesso usate su telefono. Valori indicativi (caratteri, spazi compresi); se l'utente fornisce larghezze o font, verifica con quelli:

| Testo | Limite indicativo |
|---|---|
| Pulsante | ≤ 20 (ideale 1–2 parole) |
| Voce di menu / scheda | ≤ 18 |
| Titolo di schermata | ≤ 30 |
| Etichetta di campo | ≤ 25 |
| HintText | ≤ 30 |
| Notify | ≤ 90 (una frase; il banner tronca su mobile) |
| Messaggio di validazione | ≤ 80 |
| Titolo di conferma | ≤ 40 |
| Corpo di conferma | ≤ 140 |
| Stato vuoto | ≤ 100 |
| Tooltip | ≤ 120 |

Se una stringa supera il limite, accorciala togliendo riempitivi („Si prega di", „Attenzione:", „in modo da poter") prima di toccare il contenuto. Se non si accorcia senza perdere informazione, segnalalo invece di tagliare contenuto.

## 5. Formati it-IT in Power Fx

- **Date**: preferisci i formati predefiniti con la lingua esplicita, che si adattano da soli: `Text(DataInizio; DateTimeFormat.ShortDate; "it-IT")` → „24/11/2026"; `Text(DataInizio; DateTimeFormat.LongDate; "it-IT")` → „martedì 24 novembre 2026". Con formati personalizzati: `Text(DataInizio; "dd/mm/yyyy")`, `Text(DataInizio; "d mmmm yyyy"; "it-IT")`.
- **Mesi e giorni minuscoli**: „24 novembre", „martedì". Se un testo scritto a mano ha „Novembre" o „Martedì", correggilo.
- **Numeri e valuta**: virgola decimale e punto delle migliaia. Con la lingua esplicita: `Text(Importo; "[$-it-IT]#.##0,00 €"; "it-IT")` → „1.234,50 €". Verifica nell'app il risultato, perché il formato dipende dalla lingua di creazione e da quella del dispositivo.
- **Orari**: `Text(Ora; "hh:mm")` → „15:30"; niente AM/PM.
- **Non cambiare la logica per i formati** se l'utente non lo chiede: segnala la stringa formattata male e proponi la formula corretta a parte.

## 6. Glossario delle azioni

Una parola per azione, in tutta l'app. Glossario di partenza (adattalo a quello che l'app usa già, se è coerente):

| Azione | Usa | Evita come sinonimi |
|---|---|---|
| Creare un elemento nuovo | Nuova richiesta / Aggiungi | Crea nuovo, Inserisci nuovo, + Nuovo record |
| Salvare senza inviare | Salva | Memorizza, Registra, Conferma |
| Mandare all'approvazione | Invia | Sottometti, Inoltra, Trasmetti |
| Annullare l'operazione in corso | Annulla | Chiudi (se non chiude), Indietro, Esci |
| Togliere definitivamente | Elimina | Cancella, Rimuovi (se significano la stessa cosa) |
| Modificare | Modifica | Edita, Aggiorna, Cambia |
| Tornare alla schermata precedente | Indietro | Torna, Esci |
| Approvare / respingere | Approva / Rifiuta | Accetta / Nega, OK / KO |
| Cercare | Cerca | Ricerca, Trova |
| Filtrare | Filtra | Seleziona filtri |
| Scaricare un file | Scarica / Esporta in Excel | Download, Esporta (senza formato) |

Quando l'input copre più schermate, restituisci il glossario effettivo dell'app come parte dell'output.

## 7. Accessibilità

- **AccessibleLabel** per ogni icona, immagine cliccabile e pulsante senza testo: descrive la funzione, non l'aspetto („Elimina riga", non „Icona cestino"; „Apri dettaglio ordine 4521" se il contesto lo permette con l'interpolazione già presente).
- Le immagini decorative hanno AccessibleLabel vuoto, non „immagine".
- Il colore non è l'unico segnale di errore: il messaggio di testo serve sempre.
- Niente testo dentro immagini.

## 8. Esempi prima/dopo

Formule con separatori italiani (`;`). Solo le stringhe cambiano.

- PRIMA: `Notify("Fantastico! 🎉 La tua richiesta è stata inviata con successo!"; NotificationType.Success)`
- DOPO: `Notify("Richiesta inviata."; NotificationType.Success)`

- PRIMA: `Notify("Ops! Qualcosa è andato storto 😕"; NotificationType.Error)`
- DOPO: `Notify("Richiesta non inviata. Riprova; se il problema continua, contatta l'assistenza IT."; NotificationType.Error)` (Lacuna: la formula non distingue la causa del fallimento.)

- PRIMA: pulsante `"Clicca Qui Per Inviare"` → DOPO: `"Invia richiesta"`
- PRIMA: titolo `"Benvenuto Nel Portale Ferie!"` → DOPO: `"Richieste ferie"`
- PRIMA: HintText `"Inserire la data di inizio"` sotto l'etichetta „Data di inizio" → DOPO: `"es. 24/11/2026"`
- PRIMA: validazione `"Errore: data non valida!!"` → DOPO: `"Inserisci una data di fine successiva alla data di inizio."` (solo se la regola di validazione è proprio questa; altrimenti segnala la lacuna.)
- PRIMA: conferma `"Sei sicuro?"` con pulsanti `"Sì"` / `"No"` → DOPO: titolo `"Eliminare la richiesta?"`, corpo `"Non potrai recuperarla."`, pulsanti `"Elimina"` / `"Annulla"`
- PRIMA: galleria vuota `"Non ci sono elementi da visualizzare al momento."` → DOPO: `"Nessuna richiesta. Per crearne una, seleziona Nuova richiesta."`
- PRIMA: `"Si prega di attendere il caricamento dei dati..."` → DOPO: `"Caricamento…"`
- PRIMA (registri misti): `"Inserisca il codice"`, `"Selezionare il reparto"`, `"Scegli la data"` → DOPO: `"Inserisci il codice"`, `"Seleziona il reparto"`, `"Scegli la data"`

Sosia da lasciare stare:

- `Notify("Le ore superano il limite giornaliero di 8. Controlla le righe evidenziate."; NotificationType.Warning)`: già chiaro, specifico e con rimedio.
- `"Ordine " & ThisItem.Numero & " approvato."`: concatenazione corretta; non trasformarla in interpolazione.
- Un AccessibleLabel vuoto su un'immagine decorativa: è corretto.

## 9. Checklist finale

1. Tutto al „tu", nessun „Lei", „voi" o infinito impersonale nelle istruzioni?
2. Zero esclamativi, emoji, „con successo", „Ops", „Clicca qui", „Sì/No" nelle conferme?
3. Ogni pulsante ha un verbo specifico, coerente con il glossario?
4. Ogni errore dice cosa fare, senza inventare la causa?
5. Titoli ed etichette sono sostantivi, in maiuscola solo all'iniziale?
6. HintText e tooltip aggiungono informazione?
7. Lunghezze entro i limiti della sezione 4?
8. Date, numeri, mesi e giorni nel formato italiano?
9. AccessibleLabel presenti e funzionali?
10. Ogni formula, fuori dalle virgolette, è identica all'originale?
