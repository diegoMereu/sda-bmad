---
tipo: sf
titolo: "Eurodis autoproduttore"
codice_iniziativa: "136596"
prj: null
ticket: null
compilato_da: "GDL ACN"
verificato_da: ""
approvato_da: ""
versione: "0.1"
distribuito_a: "DTO/IT/BASSPDCB/IT AS COR ESPR"
revisioni:
  - {data: "04/11/2026", versione: "0.1", stato: "Bozza", descrizione: "Prima emissione", autore: "ACN"}
---

# Introduzione

## Scopo

Il presente documento contiene l'analisi degli impatti funzionali relativi all'Iniziativa "136596 - Eurodis autoproduttore".

## Definizione, Acronimi e Abbreviazioni

| Sigla | Significato esteso |
|---|---|
| ADR | Accordo europeo sul trasporto internazionale di merci pericolose su strada |
| API | Application Programming Interface |
| APT | Codice del servizio accessorio nel formato PDB (es. `APT000918`) |
| BEP | Sistema SDA di gestione delle lettere di vettura |
| CE | Corriere Espresso |
| F1 | Anagrafica commerciale (contratto, codice cliente, AUC) |
| HTTP | HyperText Transfer Protocol |
| ICD | Interface Control Document |
| ISO2 / ISO4 | Codifica del paese a due caratteri / codifica a quattro caratteri attesa da PDB |
| JSON | JavaScript Object Notation |
| LDV | Lettera Di Vettura |
| ms | Microservizio |
| PAN | Dati di spedizione che EURODIS trasmette al partner tramite l'API `receive-pan` |
| PDB | Poste Delivery Business |
| PUDO | Pick Up Drop Off, punto di ritiro |
| UUID | Universally Unique Identifier |

## Riferimenti

| Id. Documento | Tipo di Documento | Titolo Documento | Allegato |
|---|---|---|---|
| 1 | Specifica API | EURODIS `receive-pan`, Release v1 (OpenAPI, ambiente TEST) | eurodis-receive-pan-swagger-v1.json |
| 2 | ICD | ICD_PREADVISING_LDV_EVENT_SOURCE v11, Tracciato unico preadvising | ICD_PREADVISING_LDV_EVENT_SOURCE_v11.xlsx |
| 3 | Specifica | Specifica dei servizi accessori nei flussi PDB | FlussiPreadvisingInfo.csv |
| 4 | Riscontro | Riscontro SDA sul perimetro dei servizi EURODIS del 11/09/2026 (flusso via file) | — |
| 5 | Mapping | Mapping dal tracciato unico alla richiesta LDV verso BEP | mapping-tracciatoDTO-bep.md |
| 6 | SF | SF_138972(PRJ0042827) Reply v1.0 e PRJTASK0609165 SI, processo di preadvising | SF_138972(PRJ0042827)_Reply_v1.0.docx |
| 7 | Esempio | Tracciato unico del flusso EURODIS esistente, canale `EUD_INVIOFILE` (dati di test) | esempio-eud-inviofile.json |

## Vincoli, Assunzioni, Esclusioni ed Open Point

| Id | Tipo | Descrizione | Riferimento |
|---|---|---|---|
| 1 | Vincolo | L'API `receive-pan` restituisce solo le spedizioni non ancora consegnate al partner, non prevede conferma di ricezione (ack), filtri o paginazione, e non offre un canale per rifiutare una spedizione. | Acquisizione; documento di riferimento ID 1 |
| 2 | Vincolo | Alcuni valori del flusso eccedono le dimensioni dichiarate nell'ICD: `id_preadvising` (UUID, 36 caratteri contro 15), `data_spedizione` (10 contro 8), `id_ldv_associata` (24 contro 3). I valori non vengono troncati: la validazione a valle deve accettarli. Componente che effettua l'adeguamento: DA DEFINIRE. | Trasformazione |
| 3 | Assunzione | EURODIS considera consegnata una spedizione nel momento in cui la restituisce: una risposta persa (timeout, caduta del servizio) comporta la perdita delle spedizioni contenute, recuperabili solo con la rilettura puntuale per `edReference`. Da confermare con EURODIS. | Acquisizione |
| 4 | Assunzione | La rilettura puntuale (`GET /shipment/{edReference}/v1`) non ha effetti collaterali e funziona anche su spedizioni già scaricate. Da confermare con EURODIS. | Recupero delle spedizioni |
| 5 | Assunzione | Il destinatario è sempre in Italia; il mittente può essere estero. Le spedizioni sono trattate come nazionali e i dati internazionali richiesti da BEP non sono necessari. | Trasformazione |
| 6 | Esclusione | Spedizioni di tipo pickup (P): transitano via FTP e non dall'API. Locker, Uffici Postali, Time Definite ore 9, reverse a domicilio e abbandono sono fuori perimetro. Perimetro definito per il flusso via file (documento di riferimento ID 4), da confermare per l'API. | Servizi accessori |
| 7 | Open Point | Codice PRJ dell'iniziativa: DA DEFINIRE. | Poste |
| 8 | Open Point | Conferma del modello di consegna di `receive-pan` (assunzione 3) e comportamento in caso di errore fra la risposta e il salvataggio. | Acquisizione; EURODIS (Chiapponi) |
| 9 | Open Point | Contenuto della prima chiamata: tutto lo storico arretrato o solo da una certa data. | Acquisizione; EURODIS (Chiapponi) |
| 10 | Open Point | Comportamento dell'API: gestione di aggiornamenti e annullamenti, numero massimo di spedizioni per risposta, limiti di chiamata, fuso orario dei timestamp, rotazione della chiave. | Acquisizione; EURODIS (Chiapponi) |
| 11 | Open Point | Restituzione a EURODIS di un esito negativo (spedizione non valida o non lavorabile). Si propone di valutare l'invio di un evento di eccezione tramite l'API di tracking. | Tracciamento; EURODIS (Chiapponi) |
| 12 | Open Point | Chiave API di produzione e payload di esempio di produzione, con i dati sensibili oscurati. | Acquisizione; EURODIS (Chiapponi) |
| 13 | Open Point | Volumi attesi (spedizioni per giorno e per chiamata). | Acquisizione; EURODIS (Chiapponi) |
| 14 | Open Point | Avvio graduale: definizione del perimetro di ogni fase (per mittente, ufficio o volume) e di chi lo applica (EURODIS tramite chiave API, o SDA). Un filtro lato SDA non è possibile senza perdita, perché le spedizioni lette risultano già consegnate. | Acquisizione; EURODIS (Chiapponi) |
| 15 | Open Point | Durata di conservazione dello storico delle chiamate e delle spedizioni: DA DEFINIRE. | Acquisizione; Poste |
| 16 | Open Point | Regole di validità e di univocità secondo SDA delle LDV generate da EURODIS. | Trasformazione; SDA (Marzilli), EURODIS |
| 17 | Open Point | LDV nel multicollo: conferma che `consignorsColloBarcode` contenga la LDV anche nelle spedizioni ordinarie; quale `europlateBarcode` usare per `internazionale.id_ldv_itz` con più colli (si propone il primo valorizzato); valorizzazione di LDV madre, figlia e `collo.id_collo`; trattamento del valore `0` di `europlateBarcode`. | Trasformazione; EURODIS (Chiapponi), SDA |
| 18 | Chiuso | Valore del `canale`: confermato `EUD_INVIOFILE`. Da verificare che il mapping verso BEP trasmetta `collo.id_ldv` anche per questo canale (oggi lo fa solo per INVIOSYSTEM). | Trasformazione; SDA |
| 19 | Open Point | Valorizzazione di `id_canale`, `id_file` e `id_partner`. | Trasformazione; SDA |
| 20 | Open Point | Campo sorgente della data di spedizione (`entranceTimestamp` oppure `clearanceTimestamp`, come nel riscontro SDA) e regola se il campo è assente. | Trasformazione; SDA, EURODIS |
| 21 | Open Point | Codice nazione: campo ICD in cui scrivere l'ISO2 (`codice_nazione` come nel flusso `EUD_INVIOFILE`, oppure solo `codice_nazione_iso_2`) e componente che produce l'ISO4 richiesto da PDB. | Trasformazione; SDA, responsabile `ce-dichiarato-ldv-pdb-sync` |
| 22 | Open Point | Conferma della traduzione proposta dei servizi accessori EURODIS nei codici PDB, e trattamento dei valori non coperti (`D`, `7`, `T`; `W` come appuntamento) o fuori perimetro (`A`, Locker, assicurazione, tipo P): servizio, spedizione ordinaria o scarto. | Servizi accessori; EURODIS (Chiapponi), SDA |
| 23 | Open Point | Punto Poste: sorgente del nome del punto, obbligatorio per PDB e non garantito da EURODIS, e comportamento se assente. | Servizi accessori; EURODIS (Chiapponi) |
| 24 | Open Point | Contrassegno: formato e valuta dell'importo e codifica del tipo di incasso (3 → `CON`, 5 → `ABM`). | Servizi accessori; EURODIS (Chiapponi) |
| 25 | Open Point | Assicurazione: si propone di considerarla fuori perimetro e di non valorizzarla anche se EURODIS invia il valore della merce. | Servizi accessori; SDA |
| 26 | Open Point | Reso (rientro al mittente): necessità del servizio `APT000930` e semantica dei valori; riconoscimento di resi e rettifiche. | Servizi accessori; SDA |
| 27 | Open Point | Preavviso: si propone di non mappare i flag di preavviso EURODIS, perché SDA notifica il destinatario in presenza dei contatti. Il preavviso telefonico non ha un campo nell'ICD. | Trasformazione; SDA |
| 28 | Open Point | `rif_prodotto_cliente` e `centro_costo` (obbligatorio per BEP): costanti di contratto o valori da derivare. | Trasformazione; SDA |
| 29 | Open Point | Componente che esegue l'arricchimento da F1 (contratto, codice cliente, AUC) e la determinazione del prodotto con ce-rules: il ms di trasformazione o la catena a valle. | Trasformazione |
| 30 | Open Point | Trattamento dei messaggi non trasformabili o non validi (scarto, coda di errore o altro), cause di scarto e visibilità dell'esito. | Trasformazione |
| 31 | Open Point | Deduplica: una spedizione ricevuta più volte viene inoltrata ogni volta, con un `id_preadvising` diverso. Si assume che la verifica di duplicato avvenga nella validazione a valle, come nel processo di preadvising (documento di riferimento ID 6): da confermare che la catena EURODIS ne passi. | Trasformazione; Propagazione |
| 32 | Open Point | Peso e dimensioni a 0 e valori oltre i limiti di BEP (città 30, nome 35, indirizzo 40, civico 4, telefono 15): quale componente applica i default e gli adeguamenti, dato che il ms di trasformazione non tronca e `ce-dichiarato-ldv-pdb-sync` non applica default. | Propagazione; responsabile `ce-dichiarato-ldv-pdb-sync` |
| 33 | Open Point | Spedizioni con dogana e con merci pericolose (ADR): rientrano nel perimetro? | Trasformazione; EURODIS (Chiapponi) |
| 34 | Open Point | Osservazioni su `ce-dichiarato-ldv-pdb-sync`, oggi in test: canale (`POU` o `WEBSERVICE`), ISO4 non risolto, default di peso e dimensioni, nome del Punto Poste, contrassegno a 0. | Propagazione; responsabile `ce-dichiarato-ldv-pdb-sync` |
| 35 | Open Point | Campi EURODIS senza corrispondenza nell'ICD o con semantica diversa: secondo numero di telefono, `region` (testo libero) contro `provincia` (sigla), valore della merce in valuta diversa da EUR. | Trasformazione; SDA |
| 36 | Open Point | Tracciamento verso EURODIS: API da invocare, eventi SDA da trasmettere e loro codifica, sorgente delle tracce, frequenza. | Tracciamento; EURODIS (Chiapponi) |
| 37 | Open Point | Namespace OpenShift di `ce-dichiarato-eurodis-mapper` e di `ce-eurodis-send-tracking`; topic letti e scritti da `ce-eurodis-send-tracking`. | Soluzione |

# Obiettivo dell'iniziativa

EURODIS è un consorzio di corrieri europei che affida a SDA spedizioni da consegnare in Italia. Già oggi esiste un flusso EURODIS in cui la lettera di vettura è prodotta da SDA (canale `EUD_INVIOFILE`). Con questa iniziativa EURODIS diventa autoproduttore del dato di spedizione: la LDV arriva già assegnata da EURODIS e i dati delle spedizioni (PAN) vengono prelevati direttamente dalla piattaforma EURODIS, tramite l'API `receive-pan`, invece che dal dichiarato tradizionale.

La presa in carico deve avvenire senza perdita di spedizioni, nonostante l'API non preveda una conferma di ricezione, e deve inserirsi nel processo di preadvising esistente tramite il tracciato unico, in modo che le spedizioni seguano la stessa catena verso PDB. SDA deve inoltre restituire a EURODIS le tracce delle spedizioni ricevute.

Gli obiettivi sono:

- acquisire periodicamente le spedizioni EURODIS dall'API `receive-pan`, conservandone lo storico integrale;
- trasformare ogni spedizione nel tracciato unico del preadvising (ICD v11), con la LDV fornita da EURODIS e i servizi accessori nel formato atteso da PDB;
- pubblicare il tracciato unico verso la catena di preadvising esistente;
- inviare a EURODIS le tracce SDA delle spedizioni prese in carico.

# Soluzione

La soluzione descritta di seguito tratta i seguenti temi:

- acquisizione delle spedizioni dall'API EURODIS;
- trasformazione delle spedizioni nel tracciato unico;
- propagazione verso PDB tramite la catena esistente;
- tracciamento verso EURODIS.

La soluzione è riportata nella figura successiva.

![Figura 1: Soluzione architetturale Eurodis autoproduttore](architettura-136596.png)

La figura mostra la sequenza: l'API EURODIS `receive-pan` è interrogata dal ms `ce-dichiarato-eurodis-in`, che salva lo storico su MongoDB e pubblica una spedizione per messaggio sul topic Kafka `preadvising.eud.pre.build`; il ms `ce-dichiarato-eurodis-mapper` consuma il topic, trasforma la spedizione nel tracciato unico e la pubblica sul topic `preadvising.pre-enrichment`; da qui la catena esistente, tramite il ms `ce-dichiarato-ldv-pdb-sync`, crea la spedizione su PDB con il servizio `waybillCreate`. Il ms `ce-eurodis-send-tracking` invia le tracce SDA a EURODIS.

Di seguito sono descritti funzionalmente i processi che compongono la soluzione.

## Acquisizione delle spedizioni da EURODIS

Questa fase è responsabile di prelevare le spedizioni che EURODIS affida a SDA e di consegnarle, una per messaggio, alla fase di trasformazione. Il suo obiettivo principale è non perdere nessuna spedizione: poiché l'API `receive-pan` considera consegnata una spedizione nel momento in cui la restituisce (assunzione 3), la risposta viene salvata integralmente prima di qualsiasi altra elaborazione.

In questa fase le spedizioni non vengono validate né interpretate: dell'intera spedizione si legge solo l'identificativo EURODIS `edReference`, mentre il contenuto viene conservato e inoltrato così come è stato ricevuto. Validazione e trasformazione sono a carico della fase successiva.

### Scarico periodico dall'API receive-pan

Ogni 2 minuti il microservizio invoca il servizio EURODIS `GET /shipments/v1`, autenticandosi con la chiave API assegnata al partner SDA (header `X-API-Key`). Il servizio restituisce tutte le spedizioni nuove non ancora consegnate al partner. La chiamata viene eseguita una sola volta per ciclo e non viene mai ripetuta automaticamente: un nuovo tentativo potrebbe restituire una risposta diversa e far perdere le spedizioni della prima.

Lo scarico è eseguito da una sola istanza del microservizio alla volta, anche in presenza di più repliche, per evitare chiamate concorrenti.

| Passo | Descrizione |
|---|---|
| 1 | Il ms `ce-dichiarato-eurodis-in` registra l'avvio dello scarico nello storico. |
| 2 | Il ms invoca `GET /shipments/v1` dell'API `receive-pan`. |
| 3 | Con esito `404` (nessuna spedizione nuova) lo scarico si chiude regolarmente, senza errori. |
| 4 | Con esito `200` il ms salva nello storico la risposta integrale, così come ricevuta, prima di qualsiasi elaborazione. |
| 5 | Con esito di errore (`401` chiave non valida, `424` partner non determinabile, `451` partner senza accesso, `500` errore generico) o in assenza di risposta, lo scarico si chiude in errore con il relativo esito. |

N.B. Lo scarico è rilasciato disattivato e viene attivato per ambiente, per consentire un avvio graduale (Open Point 14).

### Storicizzazione e scomposizione

Lo storico conserva, per ogni chiamata a EURODIS, l'esito HTTP, gli orari e la risposta integrale; per ogni spedizione, un record identificato da `edReference` con il testo della singola spedizione, la provenienza (chiamata e posizione nella risposta), lo stato di invio e il numero di ricezioni. La durata di conservazione dello storico è DA DEFINIRE (Open Point 15).

Ogni 2 minuti, 30 secondi dopo lo scarico, il microservizio elabora le risposte salvate.

| Passo | Descrizione |
|---|---|
| 1 | Il ms legge dallo storico le risposte da elaborare, in ordine di arrivo. |
| 2 | Il ms divide la risposta nelle singole spedizioni, ciascuna identica al testo ricevuto. |
| 3 | Per ogni spedizione il ms legge `edReference` e lo normalizza a numero intero senza decimali (es. `1000000000001.0` diventa `1000000000001`). |
| 4 | Il ms registra la spedizione nello storico con stato `DA_INVIARE` e la pubblica sul topic `preadvising.eud.pre.build`. |
| 5 | Ricevuta la conferma dal broker, il ms porta la spedizione in stato `INVIATA` con l'ora di invio. |
| 6 | Il ms chiude l'elaborazione della risposta con l'esito complessivo. |

Una spedizione già ricevuta che EURODIS restituisce di nuovo viene registrata sullo stesso record e inoltrata nuovamente: in questa fase non si filtrano i duplicati (Open Point 31). Una spedizione priva di `edReference` valido non viene scartata in silenzio: resta nello storico con il motivo e non viene inoltrata.

### Pubblicazione delle spedizioni

Ogni spedizione viene pubblicata in un messaggio dedicato, mai in un unico messaggio con l'intera risposta. Il messaggio ha:

- chiave: `edReference` normalizzato, in modo che tutte le versioni della stessa spedizione siano lette in ordine;
- corpo: la spedizione EURODIS (elemento `GetShipmentResponse2` dell'API) così come ricevuta, senza trasformazioni;
- intestazioni: i metadati della presa in carico, descritti nella tabella seguente.

| Intestazione | Descrizione |
|---|---|
| `edReference` | Identificativo EURODIS della spedizione, uguale alla chiave |
| `idEsecuzione` | Identificativo della chiamata a EURODIS nello storico |
| `ricevutoIl` | Istante di ricezione da EURODIS |
| `fonte` | `receive-pan/shipments/v1` per lo scarico, `receive-pan/shipment/v1` per la rilettura puntuale |
| `rifGrezzo` | Riferimento alla risposta integrale nello storico |
| `ambiente` | `TEST` o `PROD` |
| `schemaVersion` | Versione del contratto del messaggio, oggi `1` |
| `traceparent` | Contesto di tracciamento della richiesta |

#### Schema del messaggio

Esempio con valori fittizi; il corpo è abbreviato.

```
Topic:  preadvising.eud.pre.build
Chiave: 1000000000001
Header:
  edReference:   1000000000001
  idEsecuzione:  000000000000000000000001
  ricevutoIl:    2026-11-04T09:00:02.000Z
  fonte:         receive-pan/shipments/v1
  rifGrezzo:     eurodis_scarichi/000000000000000000000001
  ambiente:      TEST
  schemaVersion: 1
Corpo:
{
  "edReference": 1000000000001.0,
  "dispatchPartnersDomesticShipmentNumber": "PARTNER-0001",
  "entranceTimestamp": "2026-11-04T08:30:00",
  "numberOfHandlingUnits": 1,
  "consigneeAddress": { "companyName": "DESTINATARIO DI PROVA", "city": "ROMA", "zipcode": "00100", "countryCode": "IT", ... },
  "shipperAddress":   { "companyName": "MITTENTE DI PROVA", "countryCode": "AT", ... },
  "deliveryService":  { "deliveryService": "6", ... },
  "consigneePreAdvice": { "smsPreAdvice": false, "eMailPreAdvice": true, "telephonePreAdvice": false },
  "collis": [ { "europlateBarcode": "000000000000000000000001", "consignorsColloBarcode": "LDV0000000001", "weightOfUnit": 2.5, ... } ]
}
```

#### Esiti dello scarico e stati della spedizione

| Esito/Stato | Descrizione |
|---|---|
| `CHIAMATA_IN_CORSO` | Chiamata a EURODIS avviata. Se lo stato permane, il servizio si è interrotto durante la chiamata e le spedizioni della risposta possono essere perse (assunzione 3) |
| `NESSUNA_SPEDIZIONE` | EURODIS ha risposto `404`, oppure la risposta non contiene spedizioni |
| `ERRORE_CHIAMATA` | Chiamata fallita (`401`, `424`, `451`, `500`, timeout o rete), con l'esito registrato |
| `DA_ELABORARE` | Risposta salvata integralmente, in attesa di scomposizione |
| `IN_ELABORAZIONE` | Scomposizione e pubblicazione in corso; se interrotta, viene ripresa automaticamente |
| `INVIATO_TUTTO` | Tutte le spedizioni della risposta sono state pubblicate |
| `INVIO_PARZIALE` | Alcune spedizioni non sono state pubblicate o non sono identificabili |
| `NESSUN_INVIO` | Nessuna spedizione è stata pubblicata |
| `NON_ELABORABILE` | La risposta salvata non è un JSON valido |

Tabella 1: Esiti dello scarico

| Esito/Stato | Descrizione |
|---|---|
| `DA_INVIARE` | Spedizione salvata, pubblicazione non ancora confermata. Torna in questo stato anche quando EURODIS la restituisce di nuovo |
| `INVIATA` | Pubblicazione confermata dal broker, con l'ora di invio |
| `ERRORE_INVIO` | Pubblicazione non riuscita dopo 10 tentativi; si sblocca con il reinvio manuale |
| `NON_IDENTIFICABILE` | Spedizione senza `edReference` valido: conservata con il motivo, non pubblicata |

Tabella 2: Stati della spedizione

### Recupero delle spedizioni

Le spedizioni non pubblicate vengono ripubblicate automaticamente dopo 5 minuti, fino a 10 tentativi. Sono inoltre previste due operazioni di recupero, attivate tramite la configurazione del microservizio e senza servizi esposti:

- rilettura puntuale: per un elenco di `edReference` comunicato da EURODIS, il microservizio invoca `GET /shipment/{edReference}/v1` e tratta la risposta come uno scarico ordinario (con `fonte` di rilettura);
- reinvio: per un elenco di `edReference`, il microservizio ripubblica la spedizione salvata nello storico, senza invocare EURODIS.

La rilettura puntuale è l'unico modo per recuperare spedizioni perse in una chiamata non andata a buon fine, e richiede che EURODIS comunichi gli `edReference` del periodo interessato (assunzioni 3 e 4).

Ulteriori dettagli: per l'implementazione delle funzionalità sopra descritte viene realizzato un nuovo microservizio, denominato `ce-dichiarato-eurodis-in`, all'interno del namespace OpenShift `corriere-espresso-preadvising`. Il microservizio invoca l'API EURODIS `receive-pan` (documento di riferimento ID 1), salva lo storico su MongoDB (collezioni `eurodis_scarichi` per le chiamate e `eurodis_spedizioni` per le spedizioni) e pubblica sul topic Kafka `preadvising.eud.pre.build`. Non legge alcun topic.

## Trasformazione nel tracciato unico

Questa fase converte ogni spedizione EURODIS nel tracciato unico del preadvising (ICD v11, documento di riferimento ID 2) e la pubblica verso la catena esistente. Il flusso di riferimento è quello EURODIS già in esercizio (canale `EUD_INVIOFILE`, documento di riferimento ID 7): il flusso autoproduttore se ne discosta principalmente perché la LDV arriva già assegnata da EURODIS.

Il mapping campo per campo, con la categoria di ogni campo (diretto, trasformato, costante, generato, da F1, da ce-rules, a valle, non applicabile), è riportato nell'allegato 1. Di seguito le regole funzionali principali.

| Passo | Descrizione |
|---|---|
| 1 | Il ms `ce-dichiarato-eurodis-mapper` legge la spedizione dal topic `preadvising.eud.pre.build`, con le intestazioni della presa in carico. |
| 2 | Il ms converte la spedizione nel tracciato unico secondo le regole di questo paragrafo e dell'allegato 1. |
| 3 | Il ms pubblica il tracciato unico sul topic `preadvising.pre-enrichment`. |

### Regole generali di trasformazione

- Le convenzioni del flusso `EUD_INVIOFILE` vengono replicate: stringhe assenti valorizzate con `""`, importi assenti con `0`, date nel formato `yyyy-MM-dd`, peso del collo in grammi.
- I valori EURODIS più lunghi del limite ICD (email, SMS, civico, nome del contatto, note, codice TARIC) vengono passati interi, senza troncamento (vincolo 2, Open Point 32).
- Il tracciato è contrassegnato come autoproduttore (`flag_autoproduttore` = `"S"`), con `versione_tracciato` = `1`. Poiché ogni messaggio contiene una sola spedizione, `progressivo` vale `1`.
- Mittente e destinatario sono riportati dagli indirizzi EURODIS (`shipperAddress`, `consigneeAddress`); il cellulare deriva dal contatto SMS.
- Data e ora di spedizione derivano da `entranceTimestamp` (Open Point 20).
- Il codice paese EURODIS è in formato ISO2; il campo ICD di destinazione e la produzione dell'ISO4 richiesto da PDB sono DA DEFINIRE (Open Point 21).
- La consegna senza firma deriva dal tipo di consegna EURODIS (`deliveryType` `S` → `no_firma` `"N"`, `N` → `"S"`).
- Le note di consegna sono la concatenazione delle note del destinatario e del mittente.
- Sono costanti: `flag_stampa_ldv` = `"N"`, `flag_attivazione_ritiro` = `"N"`, `internazionale.vettore` = `"EURODIS"`.
- Il valore del `canale` è `EUD_INVIOFILE` (confermato; Open Point 18).

### Identificativi e lettera di vettura

| Campo ICD | Valorizzazione |
|---|---|
| `id_preadvising` | UUID generato dal microservizio per ogni tracciato |
| `spedizione.rif_spedizione` | `edReference`, come stringa senza decimali |
| `collo.id_ldv` | `collis[].consignorsColloBarcode`, la LDV assegnata da EURODIS |
| `internazionale.id_ldv_itz` | `collis[].europlateBarcode`; con più colli si propone il primo valorizzato (Open Point 17) |
| `id_ldv_partner_master` | `dispatchPartnersDomesticShipmentNumber`, numero della spedizione presso il partner mittente |
| `spedizione.numero_colli` | `numberOfHandlingUnits` |
| `link_file_fisico_inviato`, `upload_time` | Dalle intestazioni `rifGrezzo` e `ricevutoIl` del messaggio |
| `id_file` | Si propone l'identificativo della chiamata (`idEsecuzione`); con `id_canale` e `id_partner` DA DEFINIRE (Open Point 19) |

La validità e l'univocità delle LDV generate da EURODIS secondo le regole SDA sono DA DEFINIRE (Open Point 16); il trattamento del multicollo (LDV madre e figlia, `collo.id_collo`) è DA DEFINIRE (Open Point 17).

### Servizi accessori

I servizi accessori vengono passati a PDB tramite `codici_servizi` (codici APT separati da `|`, es. `APT000910|APT000918`) e, dove previsto, tramite i campi ICD delle sottochiavi, come per i flussi PDB (documento di riferimento ID 3). La sezione del tracciato dedicata al servizio non è sufficiente: il mapping verso BEP legge i servizi solo da `codici_servizi` (documento di riferimento ID 5).

Si propone la seguente traduzione, ricavata dal riscontro SDA sul flusso via file (documento di riferimento ID 4) e da confermare per l'API (Open Point 22).

| Servizio | Dato EURODIS | Codice in `codici_servizi` | Campi ICD delle sottochiavi |
|---|---|---|---|
| Consegna al sabato | `deliveryService` = `6` | `APT000910` | nessuno |
| Consegna di sera | `deliveryService` = `E` | `APT000911` | nessuno |
| Time Definite ore 10 | `deliveryService` = `F` | `APT000906` | nessuno |
| Time Definite ore 12 | `deliveryService` = `M` | `APT000907` | nessuno |
| Consegna su appuntamento | `deliveryService` = `B` (e `W`, da confermare) | `APT000908` | nessuno; richiede il telefono del destinatario |
| Punto Poste | `deliveryService` = `Z` e `consigneeAddress.pudoID` | `APT000947` | `consegna.codice_frazionario` = PUDO ID; `consegna.denominazione_frazionario` = nome del punto (Open Point 23) |
| Contrassegno | presenza di `cashOnDeliveryService` | `APT000918` | `contrassegno.flag` = `S`; `contrassegno.importo_contrassegno` = importo (> 0, max 999999.99); `contrassegno.tipo_pagamento_contrassegno`: 3 → `CON`, 5 → `ABM` (Open Point 24) |
| Multicollo | più elementi in `collis[]` | nessuno | aggiunto da `ce-dichiarato-ldv-pdb-sync` (`APT000945`) |
| Consegna pomeriggio | `deliveryService` = `A` | nessuno | spedizione ordinaria |

Una spedizione ha al massimo un servizio di consegna, combinabile con contrassegno e multicollo. Il contrassegno non è ammesso con la consegna a Punto Poste.

I valori `D` (giorno), `7` (domenica) e `T` (giorno e orario definito, senza codice APT) non hanno una traduzione: il loro trattamento è DA DEFINIRE (Open Point 22). Si propone di non valorizzare l'assicurazione (Open Point 25), il reso (Open Point 26) e i flag di preavviso (Open Point 27).

### Cliente, prodotto e arricchimento

Del cliente si valorizzano solo codice login, id cliente e codice AUC (uguali al codice cliente EURODIS) e il contratto, reperiti da F1; la ragione sociale del cliente coincide con quella del mittente. In assenza di `rif_prodotto_cliente`, il prodotto viene determinato a valle (in `ce-dichiarato-ldv-pdb-sync` il prodotto di default è `APT000901`). Restano DA DEFINIRE il componente che esegue l'arricchimento da F1 e la determinazione del prodotto con ce-rules (Open Point 29), e la valorizzazione di `rif_prodotto_cliente` e `centro_costo` (Open Point 28).

### Messaggi non trasformabili e duplicati

Il trattamento dei messaggi non trasformabili o non validi è DA DEFINIRE (Open Point 30). Non è previsto un canale per comunicarne l'esito a EURODIS (vincolo 1, Open Point 11).

Poiché né l'acquisizione né la trasformazione filtrano i duplicati e ogni tracciato riceve un nuovo `id_preadvising`, una spedizione ricevuta più volte produce più tracciati. Si assume che la verifica di duplicato sia svolta dalla validazione a valle (Open Point 31).

Ulteriori dettagli: per l'implementazione delle funzionalità sopra descritte viene realizzato un nuovo microservizio, denominato `ce-dichiarato-eurodis-mapper`, nel namespace OpenShift DA DEFINIRE (Open Point 37). Il microservizio consuma il topic Kafka `preadvising.eud.pre.build` e pubblica il tracciato unico sul topic Kafka `preadvising.pre-enrichment`.

## Propagazione verso PDB

Il tracciato unico pubblicato su `preadvising.pre-enrichment` segue la catena esistente: il ms `ce-dichiarato-ldv-pdb-sync` lo converte nella richiesta PDB e crea la spedizione con il servizio sincrono `waybillCreate`. Questa iniziativa non prevede sviluppi su questi componenti, ma ne usa le regole: lettura dei servizi da `codici_servizi`, aggiunta del servizio multicollo, prodotto, contratto e centro di costo di default.

Nel flusso via file i default di peso e dimensioni, il troncamento dei valori oltre i limiti di BEP e la verifica di duplicato sono svolti dalla validazione del preadvising. La conferma che la catena EURODIS passi dalla validazione, e quindi chi applica questi controlli, è DA DEFINIRE (Open Point 31 e 32). Le osservazioni emerse sul ms `ce-dichiarato-ldv-pdb-sync`, oggi in test, sono riportate nell'Open Point 34.

N.B. Il ms `ce-dichiarato-ldv-pdb-sync` è in fase di test: eventuali correzioni derivanti dall'Open Point 34 sono a carico del suo responsabile.

## Tracciamento verso EURODIS

Questa fase restituisce a EURODIS le tracce SDA delle spedizioni prese in carico. Tra le API EURODIS disponibili, quella con cui il partner trasmette gli eventi a EURODIS risulta essere `send-tracking`; per le prove di consegna esiste anche `send-pod`. L'API da invocare, gli eventi SDA da trasmettere e la loro codifica, la sorgente delle tracce e la frequenza di invio sono DA DEFINIRE (Open Point 36).

La correlazione fra la spedizione SDA e quella EURODIS è disponibile: l'identificativo EURODIS `edReference` è riportato in `spedizione.rif_spedizione` del tracciato unico ed è la chiave dello storico dell'acquisizione.

Si propone di valutare la stessa API anche per restituire a EURODIS un esito negativo sulle spedizioni non lavorabili (Open Point 11).

Ulteriori dettagli: per l'implementazione delle funzionalità sopra descritte viene realizzato un nuovo microservizio, denominato `ce-eurodis-send-tracking`. Namespace OpenShift e topic letti e scritti sono DA DEFINIRE (Open Point 37).

# Elenco Sistemi Impattati

| Sistema | Componente | Tipo intervento | Nuovo/Esistente |
|---|---|---|---|
| EURODIS | API `receive-pan` | Integrazione in lettura (ambienti TEST e PROD) | Esistente (esterno) |
| EURODIS | API di tracking (`send-tracking`, DA DEFINIRE) | Integrazione in scrittura | Esistente (esterno) |
| Preadvising (OpenShift) | `ce-dichiarato-eurodis-in` | Nuovo sviluppo | Nuovo |
| Preadvising (OpenShift) | `ce-dichiarato-eurodis-mapper` | Nuovo sviluppo | Nuovo |
| Preadvising (OpenShift) | `ce-eurodis-send-tracking` | Nuovo sviluppo | Nuovo |
| MongoDB | Storico delle chiamate e delle spedizioni EURODIS | Nuove collezioni | Nuovo |
| Kafka | Topic `preadvising.eud.pre.build` | Nuovo topic | Nuovo |
| Kafka | Topic `preadvising.pre-enrichment` | Nuovo produttore | Esistente |
| Preadvising (OpenShift) | Validazione del tracciato unico a valle | Accettazione dei valori oltre le dimensioni ICD (vincolo 2), deduplica (Open Point 31) | Esistente |
| Preadvising (OpenShift) | `ce-dichiarato-ldv-pdb-sync` | Verifica ed eventuali correzioni (Open Point 34) | Esistente |
| PDB | Servizio `waybillCreate` | Nessuna modifica prevista | Esistente |
| BEP | Ricezione della LDV dal tracciato unico | Verifica del canale (Open Point 18) | Esistente |
| F1 | Contratto, codice cliente, AUC | Consultazione (Open Point 29) | Esistente |
| ce-rules | Prodotto e servizi | Consultazione (Open Point 29) | Esistente |

# Allegati

| ID Documento | Tipo Documento | Titolo e Contenuto | Allegato |
|---|---|---|---|
| 1 | ICD | ICD v11 con il mapping EURODIS: fogli "Mapping EURODIS" (una riga per campo ICD), "Mapping inverso EURODIS" (una riga per campo EURODIS), "EURODIS non mappati", "Legenda mapping" | ICD_PREADVISING_LDV_EVENT_SOURCE_v11.xlsx |
| 2 | Specifica API | Specifica OpenAPI dell'API EURODIS `receive-pan`, Release v1 | eurodis-receive-pan-swagger-v1.json |
| 3 | Esempio | Tracciato unico del flusso EURODIS esistente, canale `EUD_INVIOFILE`, con dati di test | esempio-eud-inviofile.json |
| 4 | Architettura | Schema architetturale della soluzione (Figura 1) | in preparazione |
