# 146073 — Compliance USA Entry Type 13: nuovi campi e controlli sul preadvising — analisi

Versione 0.2 del 2026-11-16.

## Fonti

| Documento | Ruolo |
|---|---|
| `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` e `_fase_2.xlsx` (HLD v.1 del 09/11/2026, "Dazi dati preadvising") | **Perimetro e impatti di Accenture**: si stima e si sviluppa solo quello che c'è qui |
| `cliente/20261116_descrizione_compliance_usa_entry_type_13.md` | Contesto generale dell'iniziativa: dati, regole, flusso Zonos, casi di test. Ha come titolo "146023", probabilmente un refuso |

Sistema impattato: **AP-00988 Corriere Espresso / PK-03089 ce-dichiarato**.

## Obiettivo

Le spedizioni business verso gli USA che contengono merce devono rispettare la normativa
USA **Entry Type 13**.

- **Fase 1, dati di accettazione**: il preavviso porta due nuovi campi, che vanno validati
  e propagati lungo tutta la catena preadvising fino alle tabelle SEW:
  - **Account Key**: uno per spedizione;
  - **Product ID**: uno per articolo.
- **Fase 2, lavorazione Zonos**: per queste spedizioni la catena chiama **Zonos**
  attraverso un nuovo microservizio comune, realizzato dal team applicativo. Zonos
  restituisce **Declaration ID**, dazi e fee, oppure un errore bloccante. Il risultato
  va salvato e propagato. Nell'HLD Zonos è scritto "SOROS".

Fuori dal nostro perimetro, secondo la descrizione:
- `ce-dichiarato-builder`, che resta al team applicativo: acquisisce i campi dai canali e
  li pubblica su pre-enrichment e cambio stato;
- portali, servizi di spedizione, Internazionale/SLP, Partner, mappe Sterling;
- il microservizio Zonos, salvo l'integrazione per chiamarlo e gestirne gli esiti.

## I dati

| Campo | Fase | Cardinalità | Regola | Posizione proposta nel tracciato unico |
|---|---|---|---|---|
| Account Key | 1 | una per spedizione | obbligatoria per le spedizioni soggette (vedi R-01); lunghezza **52** | testata `spedizione[]` (nome JSON da concordare col builder, es. `account_key`) |
| Product ID | 1 | uno per **articolo** | obbligatorio per **ogni** articolo delle spedizioni soggette; lunghezza **1–255** | `spedizione[].collo[].articolo[]` (array che esiste già, con `posizione`, `codice_taric`, `valore`, `quantita`…), es. `product_id` |
| Declaration ID | 2 | uno per spedizione | restituito da Zonos | testata `spedizione[]` |
| Dazi, fee | 2 | da contratto Zonos | restituiti da Zonos | da contratto (oggi in `spedizione.importi` ci sono `importo_diritti_doganali`, `importo_oneri`…) |

**I 3 campi dell'HLD.** Gli interventi 07, 08 e 09 della fase 1 parlano di "3 nuovi campi"
da salvare nelle SEW e da inviare dal producer. In fase 2 l'HLD presume che il "campo
propagato dal nuovo sistema integrato" sia già predisposto in fase 1. La lettura più
coerente è questa: i 3 campi sono Account Key, Product ID e **Declaration ID**, e il
Declaration ID si predispone nella fase 1 e si valorizza nella fase 2 (PA-01).

### Regole

- **R-01**: l'obbligatorietà vale solo per le spedizioni **business**, **dirette negli
  USA**, **con merce** (non documenti) e appartenenti ai **prodotti interessati**. Campi
  candidati nel tracciato unico:
  - `importi.cliente_business`;
  - `destinatario.codice_nazione` / `codice_nazione_iso_2` (USA / US);
  - `tipo_merce` o `collo.codice_contenuto` / `internazionale.codice_contenuto` per merce o documenti;
  - `codice_prodotto` / `id_servizio` per i prodotti.

  Valori e prodotti sono da confermare (PA-02).
- **R-02**: il validatore controlla **solo presenza e lunghezza**. Niente lookup in
  anagrafica, niente chiamate a Zonos.
- **R-03**: l'errore deve indicare il campo e, per il Product ID, **l'articolo** non valido
  (collo e `posizione` dell'articolo).
- **R-04**: i servizi Preadvising non normalizzano, non convertono e non ricalcolano i due
  campi. Il Product ID resta legato al suo articolo anche con più articoli, retry, replay e
  reinvii.
- **R-05**: i nuovi campi non devono rompere gli scenari non USA né gli eventi storici che
  non li hanno: sono campi opzionali nei DTO e nel JSON.
- **R-06 (fase 2)**: Zonos si chiama solo attraverso il microservizio comune. Questi esiti
  sono **bloccanti** per il completamento dell'accettazione: timeout, errore tecnico,
  errore di autorizzazione, risposta non valida, esito funzionale negativo.
- **R-07 (fase 2)**: i retry sono idempotenti, con una chiave condivisa. Per la stessa
  versione della spedizione non si crea più di una dichiarazione.
- Niente modifiche alle stampe LDV. Niente nuovo framework di logging né nuovo correlation ID.

## Fase 1 — interventi (HLD)

| Int. | Microservizio | Cosa fa | Indicazioni dalla descrizione | Stima TOW 1.2 | Repo |
|---|---|---|---|---|---|
| 01 | `ce-dichiarato-validatore` | Modifica il DTO, riconosce le spedizioni soggette e aggiunge la validazione dedicata | Account Key in testata, Product ID nella lista degli articoli; regole R-01, R-02, R-03 | 0,80 | `ce-dichiarato-validatore` (regole Drools in `rules/`, handler per famiglia di canale) |
| 02 | `ce-dichiarato-orchestratore` | Modifica il DTO, il salvataggio a DB e il merge | Nessuna perdita dei campi nei rami, nei retry e nelle ripartenze; il Product ID non si appiattisce a livello spedizione | 0,40 | `ce-dichiarato-orchestratore` |
| 03 | `ce-dichiarato-smistatore` | Riceve e propaga i nuovi campi | Inoltro solo ai destinatari previsti dai contratti; compatibilità con i destinatari non adeguati | 0,40 | `ce-dichiarato-smistatore` |
| 04 | monitoring, event store, bff | Riceve e propaga i nuovi campi | Event store: cardinalità per articolo nella serializzazione, replay e ricostruzione dello stato, eventi storici senza i campi | 0,40 | `ce-event-handler-monitoring`, `ce-event-handler-event-store`, `ce-dichiarato-bff` |
| 05 | `ce-dichiarato-adapter` | Riceve e propaga i nuovi campi nei 3 consumer (PDB, PDW, ILP) | Account Key sulla spedizione, ogni Product ID sul suo articolo; campi assenti senza effetti sugli scenari non applicabili | 0,40 | `ce-dichiarato-adapter` (`KafkaConsumerPDB`, `KafkaConsumerPDW`, consumer ILP) |
| 07 | Consumer `sew_spedizioni` | Salva i 3 campi in `sew_spedizioni_work` | — | 0,32 | `gitposte/SDA/preadvising/sda-ldv-preadv-consumer/consumer-sew_sped` (ha già `ArticoloColloDTO`) |
| 08 | Consumer `sew_spedizioni_poste` | Salva i 3 campi in `sew_spedizioni_poste`; impatto Database M50 | — | 0,32 | `gitposte/SDA/ESITI/poste-ldv-preadv-consumer/consumer-sew_sped_poste` (scrive già una tabella articoli, `kafka.tabella.articolo`) |
| 09 | Producer dei dati da portali e web service | Il batch invia anche i 3 campi | — | 0,45 | da individuare (forse `sda-ldv-preadv-consumer/producer-sew-sped`) |

Per le SEW il Product ID, che è per articolo, va nella **tabella articoli**. Account Key e
Declaration ID vanno nella tabella della spedizione (PA-05).

## Fase 2 — interventi (HLD)

| Int. | Microservizio | Cosa fa | Indicazioni dalla descrizione | Stima TOW 1.2 |
|---|---|---|---|---|
| 02 | `ce-dichiarato-orchestratore` | Instrada le spedizioni soggette verso una **nuova lavorazione** (Zonos) e ne riceve l'esito, con l'elenco dei campi che la lavorazione può sovrascrivere | Avvio quando i dati necessari sono disponibili (LDV/S10); esiti positivo, errore funzionale, timeout ed errore tecnico gestiti separatamente; nessun completamento positivo senza successo Zonos; idempotenza; Declaration ID, dazi e fee disponibili alle lavorazioni successive | 1,00 |
| 05 | `ce-dichiarato-adapter` | Riceve il nuovo campo nei 3 consumer (non anticipabile in fase 1) | Declaration ID, dazi e fee solo dove richiesto; importi e valute senza perdita di precisione; niente esiti parziali spacciati per completi | 0,50 |
| 06 | Invio e ricezione verso BEP | Aggiunge alla richiesta verso BEP i **due nuovi campi** che servono alla verifica Zonos (evento Kafka verso BEP) | — | 0,54 |
| 03, 04, 07, 08, 09 | smistatore, monitoring/event store/bff, consumer SEW, producer | Nessuna stima: l'HLD presume che il campo sia già predisposto in fase 1 | Event store: esito e stato della lavorazione Zonos, replay senza chiamate duplicate | — |

I "due nuovi campi" verso BEP sono, con ogni probabilità, Account Key e Product ID (PA-07).
Verso BEP passano `ce-dichiarato-ldv-pdb` (asincrono, `preadvising.enrichment.pdb`) e
`ce-dichiarato-ldv-pdb-sync` (`waybillCreate`).

### Differenze fra la descrizione e l'HLD

Vale l'HLD. Le differenze sono da allineare con Poste:

| Nella descrizione, non nell'HLD | Nell'HLD, non nella descrizione |
|---|---|
| `ce-dichiarato-ldv`: mantenere i campi nell'associazione della LDV (fase 1); coordinare la chiamata Zonos e associare il Declaration ID (fase 2) | Consumer `sew_spedizioni_work` e `sew_spedizioni_poste` (int. 07, 08) |
| `ce-dichiarato-state-machine-handler`: stati della lavorazione Zonos (fase 2) | Producer da portali e web service (int. 09) |
| Event store: persistenza dell'esito Zonos (fase 2) | `ce-event-handler-monitoring` e `ce-dichiarato-bff` (int. 04) |
| Dazi e fee da persistere e propagare | Invio dei due campi a BEP (int. 06 fase 2) |

Ci sono anche due punti da chiarire nel contenuto:

- La descrizione chiede all'adapter di aggiornare "i mapping verso PDB, IPER". Nel codice e
  nell'HLD, invece, l'adapter è un ingresso: consuma PDB, PDW e ILP e pubblica su
  `preadvising.pre-enrichment`.
- Il passaggio dei campi da `ce-dichiarato-ldv` / `ldv-pdb` serve anche alla fase 1, perché
  la LDV si crea lì. L'HLD della fase 1 però non lo stima.

## Punti aperti

| # | Punto | Serve per |
|---|---|---|
| PA-01 | Conferma che i "3 nuovi campi" dell'HLD sono Account Key, Product ID e Declaration ID, e che il Declaration ID si predispone in fase 1 | DTO, DDL, ICD |
| PA-02 | Regola R-01 sui campi del tracciato: come si riconoscono "business" (`cliente_business` = S?), "USA" (`destinatario.codice_nazione_iso_2` = US?), "merce" (`tipo_merce`, `codice_contenuto`?) e quali sono i "prodotti interessati" (codici prodotto/servizio) | Validatore |
| PA-03 | Nomi JSON dei campi nel tracciato unico, decisi con il team del builder, e aggiornamento dell'ICD | Tutti |
| PA-04 | Codici e descrizioni dei nuovi errori di validazione (Account Key assente, Account Key di lunghezza errata, Product ID assente o errato per articolo) e loro effetto: scarto della spedizione | Validatore, scarti |
| PA-05 | DDL: colonne in `sew_spedizioni_work` (e `_2`?), `sew_spedizioni_poste` e nelle tabelle articoli; chi le esegue | Int. 07, 08 |
| PA-06 | Repo del batch producer dei preavvisi da portali e web service | Int. 09 |
| PA-07 | Fase 2: quali sono i due campi verso BEP, con quale contratto e quale flusso (`ldv-pdb` o `ldv-pdb-sync`) | Int. 06 |
| PA-08 | Fase 2: contratto del microservizio comune Zonos (sincrono o su topic, chiave di idempotenza, formato di dazi e fee, codici di errore) e punto del processo in cui si avvia la lavorazione | Orchestratore fase 2 |
| PA-09 | Fase 2: elenco dei campi che la lavorazione Zonos può sovrascrivere nel preavviso; dazi e fee rientrano? | Orchestratore fase 2 |
| PA-10 | `ce-dichiarato-ldv` e `ce-dichiarato-state-machine-handler` compaiono nella descrizione ma non nell'HLD: chi li fa? | Perimetro |
| PA-11 | Palmari (`sew_sped_pre_adv_online_out_tot`), T&T-Repo e OneTracking: sono fuori perimetro? | Perimetro |

## Casi di test minimi (fase 1, dalla descrizione)

- Spedizione USA con un articolo, Account Key e Product ID validi.
- Spedizione USA con più articoli e Product ID distinti.
- Account Key assente o di lunghezza non valida.
- Un solo articolo senza Product ID.
- Retry e replay senza perdita dei nuovi campi.
- Ricostruzione dello stato dall'event store.
- Spedizione non USA, e spedizione USA con soli documenti: i campi non sono obbligatori.
- Eventi storici privi dei nuovi campi.
- Propagazione a valle con la cardinalità corretta (spedizione / articolo), fino alle SEW.

## Stime HLD (Accenture)

| | TOW 1.1 Analisi | TOW 1.2 Sviluppo | TOW 1.3 Collaudo | TOW 1.4 Delivery | Importo |
|---|---|---|---|---|---|
| Fase 1 | 1,89 | 3,49 | 1,25 | 1,10 | 22.388,73 € |
| Fase 2 | 1,08 | 2,04 | 0,71 | 0,61 | 12.969,62 € |

Catalogo:
- Fase 1: 11 Servizio/API/Microservizio medio 0,5 e 1 Database medio 0,5.
- Fase 2: 6 Servizio/API/Microservizio medio 0,5.

Le voci Integration SFTP e Sterling Integrator (basso 0,3) non sono legate a nessun
intervento: sembrano un residuo del template.

## Incongruenze negli HLD

- Il file della fase 2 ha come titolo interno "…dati preadvising_fase1".
- Nel foglio Impatti la numerazione non corrisponde a quella del foglio HLD:
  - in fase 1 l'intervento 04 compare solo come "monitoring";
  - in fase 2 gli interventi sono numerati 01, 02 e 03, mentre nel foglio HLD sono 02, 05 e 06.
- In fase 1 non esiste un intervento 06.
