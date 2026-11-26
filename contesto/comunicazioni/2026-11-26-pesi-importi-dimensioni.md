# Pesi, importi e dimensioni nel tracciato unico preadvising

Nota tecnica – 26/11/2026

## 1. Premessa

La nota descrive le unità di misura con cui pesi, dimensioni e importi del tracciato unico
preadvising attraversano oggi la catena dei microservizi.

I sistemi esterni coinvolti hanno ruoli diversi:

- **BEP/PDB** ha due ruoli: è una **sorgente** per i canali PDB, PDW e ILP, i cui preadvising nascono
  dalle anagrafiche LDV di PDB, ed è un **sistema intermedio**, perché durante l'arricchimento la
  catena vi crea la LDV e ne riceve l'esito;
- **SEW, palmari e i consumatori dei topic .completed.poste e .completed.sda** sono i sistemi a valle.

La nota riporta le incoerenze rilevate e, nella seconda parte, gli impatti di un'eventuale
uniformazione degli importi in centesimi di euro e delle dimensioni in centimetri interi.

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
- **A valle**: SEW e palmari.

### 2.1 Pesi

| Campo | ICD v12 | Ingresso | Verso BEP | Completed (osservato in collaudo) | A valle |
|---|---|---|---|---|---|
| `spedizione/collo/peso` | unità non indicata | grammi | grammi interi | **kg**, fino a 3 decimali, su tutti i canali | SEW: kg. Palmari: grammi |
| `spedizione/internazionale/peso` | grammi | grammi | non inviato | **misto**: kg per PDB, grammi per EUD_INVIOSYSTEM | non utilizzato |
| `spedizione/collo/articolo/peso_totale` | grammi | grammi | grammi | grammi | non utilizzato |
| `ritiro/contenuto/peso` | unità non indicata | grammi | non inviato | grammi | non utilizzato |

Il peso del collo passa da grammi a kg in due punti:

- nella validazione, per i soli canali SDA (IF, IS, IE);
- nella lettura dell'esito della creazione LDV su BEP, per gli altri canali.

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
| `spedizione/collo/articolo/valore` | centesimi | centesimi | centesimi | centesimi (in euro dopo alcune fasi di esito PDB) | non utilizzato |
| `spedizione/internazionale/importo_oneri` | centesimi | centesimi interi | non inviato | non valorizzato nel campione | Palmari: intero |
| `spedizione/importi/*` (diritti postali e doganali, tassa di ritorno, incassi) | centesimi | centesimi interi | non inviati | non valorizzati nel campione | non inviati a SEW né ai palmari |

### 2.4 Incoerenze rilevate

1. **spedizione/valore ha due unità.** I canali SDA lo valorizzano in euro, i canali PDB in
   centesimi, mentre l'ICD lo indica in centesimi. Verso SEW il valore viene scritto senza conversione
   nella colonna `valore_dich` (in euro): per i canali PDB il valore dichiarato risulta **100 volte
   maggiore**.
2. **spedizione/internazionale/peso ha due unità.** Arriva in kg per PDB e in grammi per EURODIS,
   mentre l'ICD lo indica in grammi.
3. **Unità diverse nello stesso messaggio PDB.** Il peso degli articoli resta in grammi mentre il peso
   del collo è in kg; il peso del contenuto del ritiro resta in grammi.
4. **Valore degli articoli.** Su PDB resta in centesimi o passa in euro secondo la fase di esito.
5. **Unità non dichiarate nell'ICD.** Mancano per il peso del collo, l'importo del contrassegno e le
   dimensioni.
6. **Importi interi con decimali.** Gli importi dichiarati interi (oneri, diritti) perdono la parte
   decimale senza errore quando arrivano con decimali.
7. **Peso troncato verso BEP.** Il peso viene troncato e non arrotondato; un collo senza peso viene
   inviato con peso 0.

## 3. Impatti di un adeguamento: importi in centesimi e dimensioni in cm interi

### 3.1 Obiettivo e approccio ipotizzato

- **Importi**: tutti in centesimi di euro interi dalla fase di validazione in poi, quindi su
  `preadvising.enrichment`, `preadvising.completed`, `.completed.poste` e `.completed.sda`.
- **Dimensioni**: centimetri interi, arrotondati.
- **Pesi**: invariati, non rientrano in questo adeguamento.
- **Acquisizione invariata.** I servizi di acquisizione (file cliente, API EURODIS) non cambiano, e
  su `preadvising.pre-enrichment` gli importi restano in euro. Si evita così di intervenire sulle
  configurazioni dei singoli clienti a file.
- **Trascodifica centralizzata nel validatore**, da cui passano tutti i canali. Le regole di
  validazione restano espresse in euro; la conversione è l'ultimo passo prima della pubblicazione.
- **Marcatore dell'unità**: `versione_tracciato = 2` indica importi in centesimi; un valore assente o
  pari a 1 indica euro. Il marcatore permette ai sistemi a valle di distinguere i messaggi durante la
  transizione, nei reinvii e nei dati storici.

### 3.2 Campi interessati

| Campo | Oggi | Dopo l'adeguamento |
|---|---|---|
| `spedizione/contrassegno/importo_contrassegno` | euro | centesimi interi |
| `spedizione/assicurata/importo_assicurata` | euro | centesimi interi |
| `spedizione/internazionale/valore_spedizione` | euro | centesimi interi |
| `spedizione/valore` | misto | centesimi interi |
| `spedizione/collo/articolo/valore` | centesimi, in euro dopo alcune fasi di esito | sempre centesimi |
| `spedizione/collo/lunghezza`, `altezza`, `profondita` | cm, anche con decimali | cm interi |
| `ritiro/contenuto/altezza`, `larghezza`, `profondita` | cm, anche con decimali | cm interi |
| `versione_tracciato` | 1 | 2 |

Restano invariati `importo_oneri` e `importi/*`, già in centesimi interi.

### 3.3 Impatti sui microservizi

| Microservizio | Impatto | Entità |
|---|---|---|
| ce-dichiarato-validatore | Conversione degli importi in centesimi e arrotondamento delle dimensioni in uscita, per tutti i canali. Riconoscimento dei messaggi già convertiti (reinvii), che non vanno convertiti due volte | media |
| ce-dichiarato-adapter | Esiti PDB in fase 2, pubblicati senza passare dal validatore: importi direttamente in centesimi. Flusso normale: `spedizione/valore` PDB riportato in euro, così l'ingresso è omogeneo | media |
| ce-dichiarato-ldv-pdb, ce-dichiarato-ldv-pdb-sync | Verso BEP gli importi dei servizi accessori (contrassegno, assicurazione) e il valore della spedizione tornano in euro. Negli esiti non si converte più in euro il valore degli articoli. Il marcatore `versione_tracciato` va conservato | bassa |
| ce-dichiarato-ldv | Massimali del contrassegno e fascia di assicurazione richiesta a ce-vendite: conversione in euro prima del confronto o della chiamata | media |
| ce-dichiarato-smistatore | Verso i palmari non serve più la moltiplicazione per 100, perché gli importi sono già in centesimi. Verso `.completed.poste` e `.completed.sda` nessuna modifica al codice, ma cambia il contenuto (§3.4) | bassa |
| sda-ldv-preadv-consumer (SEW) | SEW resta in euro: conversione da centesimi a euro per `importo_ass`, `importo_contrass` e `valore_dich` su 5 tabelle, in entrambi i consumer. Si corregge anche l'incoerenza n. 1 del §2.4 | bassa / media |
| ce-dichiarato-orchestratore | Nessuna modifica di logica | — |
| Servizi di retry, ce-dichiarato-bff | I reinvii devono conservare `versione_tracciato`. Nel bff gli importi vanno riconvertiti in euro per la visualizzazione | bassa |
| preavviso, monitoraggio | Visualizzazione degli importi in euro | bassa |
| Servizi di acquisizione (builder, EURODIS), TUP | Nessuno | — |

### 3.4 Impatti sui sistemi esterni e sull'ICD

| Ambito | Impatto |
|---|---|
| Consumatori di `.completed.poste` e `.completed.sda` (a valle) | **Impatto principale.** Gli importi passano da euro a centesimi: ogni consumatore deve adeguarsi oppure leggere `versione_tracciato` |
| BEP/PDB (sorgente e sistema intermedio) | Nessuno: le richieste di creazione LDV restano in euro, perché la conversione avviene nei servizi ldv-pdb; gli esiti e le anagrafiche ricevute da PDB vengono convertiti dalla catena |
| SEW (a valle) | Nessuno sulle tabelle: la conversione in euro avviene nel consumer |
| Palmari (a valle) | Nessuno: ricevono già i centesimi |
| ICD | Nuova versione con le unità esplicite di tutti i campi (centesimi, cm interi, unità del peso del collo) e il significato di `versione_tracciato = 2`. Va indicato che `preadvising.pre-enrichment` resta in euro |

### 3.5 Rilascio

1. Si rilasciano prima i servizi che leggono il tracciato (SEW, smistatore, servizi LDV, bff,
   preavviso). Gestiscono entrambe le versioni sulla base di `versione_tracciato`; finché nessuno
   produce la versione 2, il comportamento resta quello attuale.
2. Si rilasciano poi insieme validatore e adapter, che attivano la versione 2.
3. **Rollback**: si ripristinano validatore e adapter alla versione precedente.

I dati storici (versione 1) e quelli nuovi (versione 2) convivono senza migrazione.

### 3.6 Punti da condividere

1. Quali sistemi consumano `.completed.poste` e `.completed.sda`, e se possono gestire
   `versione_tracciato`.
2. Conferma dell'uso di `versione_tracciato = 2` come marcatore dell'unità.
3. Unità degli importi sul canale OMP e nei file PDB a tracciato (valore della spedizione,
   contrassegno, copertura).
4. Canale ILP: se allineare in centesimi anche il valore degli articoli, oggi in euro.
5. Unità del volume dei ritiri calcolato per SEW.
6. Se correggere subito l'incoerenza n. 1 del §2.4 (valore dichiarato PDB su SEW), indipendentemente
   dall'adeguamento.
