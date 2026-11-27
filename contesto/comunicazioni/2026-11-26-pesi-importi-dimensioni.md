# Pesi, importi e dimensioni nel tracciato unico preadvising

Nota tecnica – 26/11/2026

## 1. Premessa

La nota descrive le unità di misura con cui pesi, dimensioni e importi del tracciato unico
preadvising attraversano oggi la catena dei microservizi.

I sistemi esterni coinvolti hanno ruoli diversi:

- **BEP/PDB** ha due ruoli: è una **sorgente** per i canali PDB, PDW e ILP, i cui preadvising nascono
  dalle anagrafiche LDV di PDB, ed è un **sistema intermedio**, perché durante l'arricchimento la
  catena vi crea la LDV e ne riceve l'esito;
- **SEW, palmari, il file impianti generato dal completed e i consumatori dei topic .completed.poste e
  .completed.sda** sono i sistemi a valle.

La nota riporta le incoerenze rilevate e, nella seconda parte, gli impatti di un'eventuale
uniformazione delle unità su tutto il tracciato: importi in centesimi di euro, pesi in grammi e dimensioni in centimetri, tutti interi.

Fonti dell'analisi:

- ICD del tracciato unico preadvising, versione 12;
- configurazione e codice dei microservizi della catena preadvising;
- campione di 1998 messaggi del topic `preadvising.completed` dell'ambiente di collaudo (24-26/11/2026;
  canali PDB, OMP, EUD_INVIOFILE, EUD_INVIOSYSTEM, PDW, IS, IE). Del campione sono stati estratti
  solo i valori numerici, senza dati anagrafici.

## 2. Stato attuale dei campi

Colonne delle tabelle:

- **Ingresso**: il messaggio pubblicato su `preadvising.pre-enrichment` dai servizi di acquisizione
  (file cliente, API EURODIS, anagrafiche LDV di PDB per i canali PDB, PDW e ILP, TUP);
- **Verso BEP**: la richiesta di creazione della LDV inviata a BEP durante l'arricchimento;
- **Completed**: il messaggio finale su `preadvising.completed`, da cui derivano `.completed.poste` e
  `.completed.sda`;
- **A valle**: SEW e palmari. Il file impianti, generato dal completed, è da analizzare (§3.7).

### 2.1 Pesi

| Campo | ICD v12 | Ingresso | Verso BEP | Completed (osservato in collaudo) | A valle |
|---|---|---|---|---|---|
| `spedizione/collo/peso` | unità non indicata | grammi | grammi interi | **kg**, fino a 3 decimali, su tutti i canali | SEW: kg. Palmari: grammi |
| `spedizione/internazionale/peso` | grammi | grammi | non inviato | **misto**: kg per PDB, grammi per EUD_INVIOSYSTEM | non utilizzato |
| `spedizione/collo/articolo/peso_totale` | grammi | grammi | grammi | **misto**: grammi per il canale PDB (osservato); kg per i canali PDB_INVIOSYSTEM, PDB_INVIOEASY, PDB_STAMPAMASSIVA, PDB_INVIOFILE ed EUD_INVIOSYSTEM (da codice, non presenti nel campione) | non utilizzato |
| `ritiro/contenuto/peso` | unità non indicata | grammi | non inviato | grammi | non utilizzato |

Il peso del collo passa da grammi a kg in tre punti:

- nella validazione, per i soli canali SDA (IF, IS, IE);
- nella lettura dell'esito della creazione LDV su BEP (canali PDB_INVIO* ed EUD_INVIOSYSTEM), che
  converte anche il peso degli articoli;
- nella trasformazione delle anagrafiche LDV di PDB (canali PDB e PDW).

Nella seconda fase degli esiti PDB anche il peso degli articoli viene convertito in kg.

### 2.2 Dimensioni

| Campo | ICD v12 | Ingresso | Verso BEP | Completed (osservato in collaudo) | A valle |
|---|---|---|---|---|---|
| `spedizione/collo/lunghezza`, `altezza`, `profondita` | unità non indicata | cm, a volte con decimali | cm | cm (es. `"50.0"` e `"50"`) | SEW: cm. Palmari: cm interi, con i decimali troncati |
| `ritiro/contenuto/altezza`, `larghezza`, `profondita` | unità non indicata | cm | non inviati | non presenti nel campione | non utilizzati |

### 2.3 Importi

| Campo | ICD v12 | Ingresso | Verso BEP | Completed (osservato in collaudo) | A valle |
|---|---|---|---|---|---|
| `spedizione/contrassegno/importo_contrassegno` | unità non indicata | euro, 2 decimali | euro, 2 decimali | euro (es. 123.45) | SEW: euro. Palmari: centesimi |
| `spedizione/assicurata/importo_assicurata` | euro | euro | euro, 2 decimali | euro (es. 258.23) | SEW: euro. Palmari: centesimi |
| `spedizione/internazionale/valore_spedizione` | euro | euro | euro, 2 decimali | euro | Palmari: centesimi |
| `spedizione/valore` | centesimi | **misto** | non inviato | **misto**: euro per i canali SDA (IS: 200.0), centesimi per PDB (fino a 31545) | SEW (`valore_dich`): scritto senza conversione |
| `spedizione/collo/articolo/valore` | centesimi | centesimi | centesimi | **misto**: centesimi per il canale PDB (osservato); euro per i canali PDB_INVIOSYSTEM, PDB_INVIOEASY, PDB_STAMPAMASSIVA, PDB_INVIOFILE ed EUD_INVIOSYSTEM e nella seconda fase degli esiti PDB (da codice, non presenti nel campione) | non utilizzato |
| `spedizione/internazionale/importo_oneri` | centesimi | centesimi interi | non inviato | non valorizzato nel campione | Palmari: intero |
| `spedizione/importi/*` (diritti postali e doganali, tassa di ritorno, incassi) | centesimi | centesimi interi | non inviati | non valorizzati nel campione | non inviati a SEW né ai palmari |

### 2.4 Incoerenze rilevate

1. **spedizione/valore ha due unità.** I canali SDA lo valorizzano in euro, i canali PDB in
   centesimi, mentre l'ICD lo indica in centesimi. Verso SEW il valore viene scritto senza conversione
   nella colonna `valore_dich` (in euro): per i canali PDB il valore dichiarato risulta **100 volte
   maggiore**.
2. **spedizione/internazionale/peso ha due unità.** Arriva in kg per PDB e in grammi per EURODIS,
   mentre l'ICD lo indica in grammi.
3. **Unità diverse nello stesso messaggio.** Sul canale PDB il peso degli articoli resta in grammi
   mentre il peso del collo è in kg. Il peso del contenuto del ritiro resta in grammi su tutti i canali.
4. **Articoli con unità diverse secondo il canale.** Valore e peso degli articoli sono in centesimi e
   grammi sul canale PDB, mentre sui canali che creano la LDV in modo asincrono e nella seconda fase
   degli esiti PDB sono in euro e kg.
5. **Unità non dichiarate nell'ICD.** Mancano per il peso del collo, l'importo del contrassegno e le
   dimensioni.
6. **Importi interi con decimali.** Gli importi dichiarati interi (oneri, diritti) perdono la parte
   decimale senza errore quando arrivano con decimali.
7. **Peso troncato verso BEP.** Il peso viene troncato e non arrotondato; un collo senza peso viene
   inviato con peso 0.

## 3. Impatti di un adeguamento: unità uniche su tutto il tracciato

### 3.1 Obiettivo e approccio ipotizzato

Obiettivo: una sola unità per grandezza, su tutto il tracciato.

| Grandezza | Unità |
|---|---|
| Importi | **centesimi di euro**, interi |
| Pesi | **grammi**, interi |
| Dimensioni | **centimetri**, interi |

Approccio:

- **Nessuna conversione interna alla catena.** Le conversioni presenti oggi tra un servizio e l'altro
  vengono tolte. Una conversione resta solo dove un sistema esterno richiede un'unità diversa e non si
  adegua (§3.5).
- **Acquisizione invariata.** I servizi di acquisizione (file cliente, API EURODIS) producono già pesi
  in grammi e dimensioni in cm, e restano invariati. Gli importi in ingresso, oggi in euro, vengono
  convertiti in centesimi in un solo punto, il validatore, da cui passano tutti i canali. Si evita così
  di intervenire sulle configurazioni dei singoli clienti a file.
- **Marcatore dell'unità.** `versione_tracciato = 2` indica il tracciato con le nuove unità; un valore
  assente o pari a 1 indica le unità attuali. Il marcatore permette di distinguere i messaggi durante
  la transizione, nei reinvii e nei dati storici.

### 3.2 Campi interessati

| Campo | Oggi su completed | Dopo l'adeguamento |
|---|---|---|
| `spedizione/collo/peso` | kg | grammi interi |
| `spedizione/internazionale/peso` | kg o grammi secondo il canale | grammi interi |
| `spedizione/collo/articolo/peso_totale` | grammi o kg secondo il canale | grammi interi |
| `ritiro/contenuto/peso` | grammi | grammi interi (unità da dichiarare nell'ICD) |
| `spedizione/contrassegno/importo_contrassegno` | euro | centesimi interi |
| `spedizione/assicurata/importo_assicurata` | euro | centesimi interi |
| `spedizione/internazionale/valore_spedizione` | euro | centesimi interi |
| `spedizione/valore` | euro o centesimi secondo il canale | centesimi interi |
| `spedizione/collo/articolo/valore` | centesimi o euro secondo il canale | centesimi interi |
| `spedizione/collo/lunghezza`, `altezza`, `profondita` | cm, anche con decimali | cm interi |
| `ritiro/contenuto/altezza`, `larghezza`, `profondita` | cm, anche con decimali | cm interi |
| `versione_tracciato` | 1 | 2 |

Restano invariati `importo_oneri` e `importi/*`, già in centesimi interi.

### 3.3 Conversioni presenti oggi e cosa ne sarebbe

| # | Punto della catena | Conversione oggi | Dopo l'adeguamento |
|---|---|---|---|
| 1 | Validatore, canali SDA | peso del collo da grammi a kg; le soglie di validazione del peso sono espresse in kg (es. 5 kg, 30 kg) | **tolta**; soglie riscritte in grammi |
| 2 | Validatore, tutti i canali | — | **nuova**: importi da euro a centesimi, dimensioni arrotondate all'intero |
| 3 | Adapter, anagrafiche LDV di PDB | peso del collo e peso internazionale da grammi a kg | **tolta** |
| 4 | Adapter, seconda fase degli esiti PDB | peso e valore degli articoli in kg ed euro; importi dei servizi accessori in euro | **tolta** sugli articoli; importi dei servizi accessori in centesimi |
| 5 | Adapter, canale PDW | peso da grammi a kg; importi da centesimi a euro | **tolte** |
| 6 | Adapter, canale ILP | sorgente in kg ed euro; solo gli oneri convertiti in centesimi | **nuova**: pesi in grammi e importi in centesimi già in ingresso |
| 7 | Adapter, valore della spedizione PDB | interpretazione euristica: un valore senza punto decimale viene letto come centesimi | **da sostituire** con una regola certa |
| 8 | Servizi di creazione LDV, esito asincrono | peso del collo e degli articoli in kg, valore degli articoli in euro | **tolte** |
| 9 | Servizi di creazione LDV, richiesta a BEP | peso in grammi, troncato all'intero; importi dei servizi accessori e valore della spedizione in euro | peso **arrotondato** invece che troncato; importi: conversione da centesimi a euro (§3.5) |
| 10 | Servizi di creazione LDV, prenotazione ritiro su SAP-EM | peso da grammi a kg | **resta**, salvo adeguamento di SAP-EM |
| 11 | ce-dichiarato-ldv, chiamate a ce-contratti e ce-vendite e massimali del contrassegno | peso in kg; assicurata e contrassegno in euro | conversione verso i servizi, oppure adeguamento dei servizi |
| 12 | Smistatore, palmari | peso da kg a grammi; importi da euro a centesimi; dimensioni troncate | **tolte**, perché i palmari usano già grammi, centesimi e cm interi |
| 13 | Consumer SEW | nessuna (SEW riceve kg ed euro) | conversione da grammi a kg e da centesimi a euro, oppure adeguamento di SEW (§3.5) |

### 3.4 Impatti sui microservizi

| Microservizio | Impatto | Entità |
|---|---|---|
| ce-dichiarato-validatore | Rimozione della conversione del peso e riscrittura in grammi delle soglie dei canali SDA. Conversione degli importi in centesimi e arrotondamento delle dimensioni, per tutti i canali. Riconoscimento dei messaggi già convertiti (reinvii), che non vanno convertiti due volte | **alta** |
| ce-dichiarato-adapter | PDB: rimozione delle conversioni di pesi e articoli, regola certa per il valore della spedizione. Seconda fase degli esiti, pubblicata senza passare dal validatore: tracciato prodotto direttamente nelle nuove unità. PDW: rimozione delle conversioni. ILP: conversione in ingresso | **alta** |
| ce-dichiarato-ldv-pdb, ce-dichiarato-ldv-pdb-sync | Esiti: rimozione delle conversioni di pesi e articoli. Richieste a BEP: importi riportati in euro, peso arrotondato. Il marcatore `versione_tracciato` va conservato | media |
| ce-dichiarato-ldv | Peso verso ce-contratti, assicurata verso ce-vendite e massimali del contrassegno: conversione o adeguamento dei servizi chiamati | media |
| ce-dichiarato-smistatore | Rimozione delle conversioni verso i palmari. Verso `.completed.poste` e `.completed.sda` nessuna modifica al codice, ma cambia il contenuto (§3.5) | bassa |
| sda-ldv-preadv-consumer (SEW) | Se SEW non cambia: conversione da grammi a kg e da centesimi a euro per peso, importi e valore dichiarato, su 5 tabelle e in entrambi i consumer. Si corregge anche l'incoerenza n. 1 del §2.4 | media |
| Generatore del file impianti | Da individuare e analizzare: il file viene generato dal completed e ne riceve le nuove unità | da valutare |
| ce-dichiarato-orchestratore | Nessuna modifica di logica | — |
| Servizi di retry, ce-dichiarato-bff | I reinvii devono conservare `versione_tracciato`. Nel bff pesi e importi vanno riconvertiti per la visualizzazione | bassa |
| preavviso, monitoraggio | Visualizzazione di pesi in kg e importi in euro | bassa |
| Servizi di acquisizione (builder, EURODIS), TUP | Nessuno | — |

### 3.5 Impatti sui sistemi esterni e sull'ICD

| Sistema | Unità che usa oggi | Impatto |
|---|---|---|
| Consumatori di `.completed.poste` e `.completed.sda` (a valle) | kg ed euro; articoli in euro o centesimi secondo il canale | **Impatto principale.** Pesi in grammi, importi e articoli in centesimi: ogni consumatore deve adeguarsi oppure leggere `versione_tracciato` |
| File impianti (a valle) | da verificare | Generato dal completed: cambia il contenuto se il generatore non converte. Va analizzato il formato del file |
| BEP/PDB (sorgente e sistema intermedio) | pesi in grammi; importi dei servizi accessori e valore della spedizione in euro con 2 decimali; articoli in centesimi (ICD BEP) | Le richieste di creazione LDV mantengono il formato BEP: per gli importi resta una conversione verso l'euro, salvo che BEP accetti i centesimi. Il peso arrotondato invece che troncato può differire di 1 grammo rispetto a oggi. Anagrafiche ed esiti di PDB: la catena smette di convertirli |
| SAP-EM (prenotazione ritiro) | kg | Resta la conversione da grammi a kg, salvo adeguamento di SAP-EM |
| SEW (a valle) | peso in kg come testo; importi in euro con 3 decimali | **Due opzioni.** (a) SEW resta invariato e la conversione si sposta nel consumer: le tabelle non cambiano, ma alcuni valori sì (valore dichiarato PDB corretto, importi arrotondati a 2 decimali, volume dei ritiri calcolato su dimensioni intere). (b) SEW passa a grammi e centesimi: vanno adeguate tabelle e procedure Informix che leggono peso e importi |
| Palmari (a valle) | grammi, centesimi, cm interi | Le conversioni verso i palmari si tolgono. Cambiano alcuni valori: contrassegno sempre intero (oggi può avere decimali), dimensioni arrotondate invece che troncate |
| ce-contratti, ce-vendite | peso in kg; assicurata in euro | Conversione nella chiamata, oppure adeguamento dei servizi |
| ICD | — | Nuova versione con le unità esplicite di tutti i campi e il significato di `versione_tracciato = 2`. Va indicato che su `preadvising.pre-enrichment` gli importi restano in euro |

### 3.6 Rilascio

1. Si rilasciano prima i servizi che leggono il tracciato (SEW, smistatore, servizi LDV, bff,
   preavviso, generatore del file impianti). Gestiscono entrambe le versioni sulla base di
   `versione_tracciato`; finché nessuno produce la versione 2, il comportamento resta quello attuale.
2. Si rilasciano poi insieme validatore e adapter, che attivano la versione 2.
3. **Rollback**: si ripristinano validatore e adapter alla versione precedente.

I dati storici (versione 1) e quelli nuovi (versione 2) convivono senza migrazione.

### 3.7 Punti da condividere

1. Quali sistemi consumano `.completed.poste` e `.completed.sda`, e se possono gestire
   `versione_tracciato`.
2. File impianti: quale servizio lo genera dal completed, con quale formato e verso quali sistemi.
3. SEW: conversione nel consumer (opzione a) oppure adeguamento di SEW (opzione b).
4. BEP e SAP-EM: se è possibile inviare importi in centesimi e pesi in grammi, oppure se le
   conversioni verso questi sistemi restano.
5. Conferma dell'uso di `versione_tracciato = 2` come marcatore dell'unità.
6. Unità degli importi sul canale OMP e nei file PDB a tracciato (valore della spedizione,
   contrassegno, copertura).
7. Unità del volume dei ritiri calcolato per SEW.
8. Se correggere subito l'incoerenza n. 1 del §2.4 (valore dichiarato PDB su SEW), indipendentemente
   dall'adeguamento.
