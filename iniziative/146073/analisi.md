# 146073 — Compliance USA Entry Type 13: nuovi campi e controlli sul preadvising — analisi

Versione 0.4 del 2026-11-24 (decisioni di Diego del 23 e 24-11 su nomi, regola, colonne SEW, branch e
primo passo della fase 1; dal 24-11 anche colonne SDA solo su `sew_spedizioni_work`, spazi di
riempimento nel producer, nomi su MongoDB e stato dello sviluppo).

## Fonti

| Documento | Ruolo |
|---|---|
| `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` e `_fase_2.xlsx` (HLD v.1 del 09/11/2026, "Dazi dati preadvising") | **Perimetro e impatti di Accenture**: si stima e si sviluppa solo quello che c'è qui |
| `cliente/20261116_descrizione_compliance_usa_entry_type_13.md` | Contesto generale dell'iniziativa: dati, regole, flusso Zonos, casi di test. Ha come titolo "146023", probabilmente un refuso |

Sistema impattato: **AP-00988 Corriere Espresso / PK-03089 ce-dichiarato**.

## Obiettivo

Le spedizioni verso gli USA che contengono merce, per i prodotti interessati, devono rispettare la
normativa USA **Entry Type 13**.

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
| Account Key | 1 | una per spedizione | obbligatoria per le spedizioni soggette (vedi R-01); lunghezza **52** | testata `spedizione[]`, `zonos_account_key` [DECISO, Diego 23-11] |
| Product ID | 1 | uno per **articolo** | obbligatorio per **ogni** articolo delle spedizioni soggette; lunghezza **1–255** | `spedizione[].collo[].articolo[]` (array che esiste già, con `posizione`, `codice_taric`, `valore`, `quantita`…), `zonos_product_id` [DECISO, Diego 23-11] |
| Declaration ID | 2 (predisposto in 1) | uno per spedizione | restituito da Zonos; lunghezza 13 | testata `spedizione[]`, `zonos_declaration_id` [DECISO, Diego 23-11] |
| Dazi, fee | 2 | da contratto Zonos | restituiti da Zonos | da contratto (oggi in `spedizione.importi` ci sono `importo_diritti_doganali`, `importo_oneri`…) |

**I 3 campi dell'HLD.** Gli interventi 07, 08 e 09 della fase 1 parlano di "3 nuovi campi"
da salvare nelle SEW e da inviare dal producer. In fase 2 l'HLD presume che il "campo
propagato dal nuovo sistema integrato" sia già predisposto in fase 1. La lettura più
coerente è questa: i 3 campi sono Account Key, Product ID e **Declaration ID**, e il
Declaration ID si predispone nella fase 1 e si valorizza nella fase 2 (PA-01).

### Regole

- **R-01** [DECISO, Diego 23-11]: l'obbligatorietà vale solo per le spedizioni **dirette negli
  USA**, **con merce** (non documenti) e appartenenti ai **prodotti interessati**. La condizione
  "cliente business" non c'è più. Campi del tracciato unico:
  - `tipo_merce` per merce o documenti (documenti = `D`; `tipo_merce` assente = merce);
  - `destinatario.codice_nazione_iso_2` (`US`) / `destinatario.codice_nazione` (`US`, `USA`);
  - `codice_prodotto` **oppure** `id_servizio` per i prodotti: 456, 457 (EXPORT BOX), 458, 459
    (EXPORT BOX PCIM), 515, 516 (CRONO INTERNAZIONALE, 516 = assicurato). I codici vengono da
    `ce_prodotto` di ce-rules; l'elenco di CRONO INTERNAZIONALE è da confermare (PA-12).
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

## Contratto della fase 1 (base comune dei funzionali)

Decisione di Diego del 2026-11-16: **per ora si lavora solo sulla fase 1**. Le assunzioni
che seguono sono vincolanti per tutti i documenti di `sviluppo/`. Il 23-11 Diego ha deciso nomi,
regola, errori e colonne SEW (AS-01…AS-04), il 24-11 i nomi delle colonne, i branch e il primo passo
della fase 1.

**AS-01, nomi e posizione nel tracciato unico** [DECISO, Diego 23-11]. Stile snake_case dell'ICD,
con il prefisso `zonos_`. I nomi provvisori `account_key`, `product_id`, `declaration_id` non si usano più.

```json
{
  "spedizione": [{
    "zonos_account_key": "<52 caratteri>",
    "zonos_declaration_id": null,
    "collo": [{
      "articolo": [
        { "posizione": "1", "codice_taric": "...", "zonos_product_id": "<1-255 caratteri>" }
      ]
    }]
  }]
}
```

- `zonos_account_key` e `zonos_declaration_id` stanno sulla testata di ogni elemento di `spedizione[]`.
- `zonos_product_id` sta su ogni elemento di `spedizione[].collo[].articolo[]`.
- `zonos_declaration_id` è solo **predisposto**: in fase 1 è sempre assente o `null`, e si
  propaga e si salva come gli altri due (è il 3° campo dell'HLD, PA-01).
- Tutti e tre sono **opzionali** nei DTO, `String`, senza default e senza trasformazioni
  (niente trim, niente conversioni; R-04, R-05).
- Su **MongoDB** (validatore e orchestratore: `dichiarato_events`, `enrichment_events`) si salvano
  con gli stessi nomi del tracciato `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id`,
  non camelCase [DECISO, Diego 24-11]. Con nomi Java camelCase serve `@Field("zonos_…")` oltre a
  `@JsonProperty`, come già nel bff.
- Esempi di formato (inventati): `zonos_account_key` `credential_live_<uuid>` (52 caratteri),
  `zonos_declaration_id` `0rtvQg6j865xR` (13), `zonos_product_id` da 1 a 255 caratteri.

**AS-02, riconoscimento delle spedizioni soggette (R-01)** [DECISO, Diego 23-11]. Una spedizione
è soggetta se valgono **tutte** queste condizioni:

- `tipo_merce` diverso da "documenti" (`D`); `tipo_merce` assente = merce;
- la nazione del destinatario è USA: `destinatario.codice_nazione_iso_2` = `US`, oppure
  `destinatario.codice_nazione` in (`US`, `USA`), senza spazi e senza distinzione fra maiuscole e
  minuscole;
- `codice_prodotto` **oppure** `id_servizio` appartiene all'elenco dei prodotti interessati:
  `456,457,458,459,515,516`.

La condizione "cliente business" della versione precedente non c'è più. Per le spedizioni
soggette `zonos_account_key` è obbligatorio (esattamente 52 caratteri) e `zonos_product_id` è
obbligatorio su ogni articolo di ogni collo (1-255); `zonos_declaration_id` non si controlla.

I valori e un flag di attivazione generale stanno in **configurazione** del validatore
(prefisso `compliance-usa`: `abilitata`, `tipi-merce-documenti` = `D`, `nazioni-usa` = `US,USA`,
`prodotti` = `456,457,458,459,515,516`). Con il flag spento la regola non scatta: è il default
(`abilitata: 'false'` anche in `.helm/values.yaml`) finché il builder non manda i campi.

**AS-03, errori.** Seguono il modello delle regole esistenti: `errors.put(codice,
descrizione)` sul `DichiaratoDTO`, con codici numerici di 4 cifre come `1181` e `1182`.
I codici e le descrizioni sono decisi da Diego il 23-11. L'esito è lo **scarto** della
spedizione, come per gli altri campi obbligatori mancanti.
Il nome del campo sta sempre prima dei due punti, perché il monitoring legge così il
"campo in errore". Le occorrenze di più articoli si elencano fra parentesi, separate da
`"; "`: la mappa degli errori ha una sola voce per codice.

| Codice | Errore | Descrizione |
|---|---|---|
| `1320` | Account Key assente | `zonos_account_key: Campo obbligatorio mancante` |
| `1321` | Account Key di lunghezza diversa da 52 | `zonos_account_key: lunghezza non valida (attesi 52 caratteri)` |
| `1322` | Product ID assente | `zonos_product_id: Campo obbligatorio mancante (collo <n> articolo <posizione>; ...)` |
| `1323` | Product ID più lungo di 255 | `zonos_product_id: lunghezza non valida, attesi 1-255 caratteri (collo <n> articolo <posizione>; ...)` |

**AS-04, SEW** [DECISO, Diego 23 e 24-11]. Colonne Informix con gli stessi nomi dei campi:

| Colonna | Tipo | Tabella |
|---|---|---|
| `zonos_account_key` | `char(52) default ''` | tabella della spedizione: lato SDA **solo `sew_spedizioni_work`** (non `sew_spedizioni_work_2` né `sew_spedizioni`, Diego 24-11); lato Poste `sew_spedizioni_poste` |
| `zonos_declaration_id` | `char(13) default ''` | tabella della spedizione |
| `zonos_product_id` | `char(255) default ''` | **tabella articoli** che il consumer scrive già |

I consumer che scrivono le SEW mettono le colonne nuove nella INSERT (e nell'eventuale
UPDATE/MERGE) **solo se il campo arriva valorizzato**. Senza i campi lo statement resta
identico a quello di oggi: così il consumer funziona anche prima delle DDL. Le DDL le esegue il
DBA ([sviluppo/ddl-sew-146073.md](sviluppo/ddl-sew-146073.md)). Chi rilegge le colonne (il producer)
toglie gli spazi di riempimento a destra dei campi `char`: un valore vuoto o di soli spazi vale come
campo assente [DECISO, Diego 24-11].

**AS-05, ingresso.** Il builder, fuori perimetro, e i canali PDB, PDW e ILP (attraverso
l'adapter) pubblicano i campi con i nomi di AS-01. Finché il builder non è pronto, i test si
fanno con messaggi costruiti a mano su `preadvising.pre-enrichment`.

**Branch (decisione di Diego del 2026-11-24, sostituisce quella del 16-11).** Nei repository
dei servizi preadvising (validatore, orchestratore, smistatore, bff, adapter,
`poste-ldv-preadv-consumer`) lo sviluppo va su **`develop`**. Solo `ESITI/sda-ldv-preadv-consumer`
(moduli `consumer-sew_sped` e `producer-sew-sped`) resta sul branch dedicato
`146073_compliance_usa_fase1`, creato da `origin/dev202508_preadvising` (il repo non ha `develop`).
Non si sviluppa mai su `master` né su branch di altre iniziative.

**AS-07, campi assenti.** Un campo assente e un campo `null` si trattano allo stesso modo
in tutta la catena. Ogni servizio serializza i campi nuovi secondo la propria convenzione:
il validatore scrive i `null`, orchestratore e smistatore li omettono (`NON_NULL`). Nessun
consumer deve distinguere i due casi. Nelle SEW un campo assente non entra nello statement e la
colonna resta al default `''` (AS-04).

**AS-06, fuori dalla fase 1.**
- Zonos, valorizzazione del Declaration ID, dazi e fee, verso BEP.
- Stampe.
- Palmari (`sew_sped_pre_adv_online_out_tot`), T&T-Repo e OneTracking.

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
| 09 | Producer dei dati da portali e web service | Il batch invia anche i 3 campi | — | 0,45 | `sda-ldv-preadv-consumer/producer-sew-sped` (certezza alta) |

Per le SEW il Product ID, che è per articolo, va nella **tabella articoli**. Account Key e
Declaration ID vanno nella tabella della spedizione (PA-05).

## Esito dei funzionali della fase 1 (2026-11-16, aggiornato il 2026-11-24)

I funzionali sono in `sviluppo/`, uno per microservizio, ciascuno con il suo prompt. Il codice è
stato letto sui ref `origin/develop` presenti in locale: il `git fetch` del 16-11 è fallito
per un problema di rete, quindi va ripetuto prima di creare i branch. Il 24-11 tutti i funzionali
sono passati alla versione 0.2 (nomi `zonos_*`, regola, colonne SEW, branch).

**Primo passo e punto 2 della fase 1 (decisione di Diego del 2026-11-24).** Nel primo passo si
sviluppano validatore, orchestratore, smistatore e bff (su `develop`) e `sda-ldv-preadv-consumer`
(`consumer-sew_sped` e `producer-sew-sped`, branch dedicato). Stato al 24-11: validatore su
`develop` (`090d037`, verifica spenta di default); `sda-ldv-preadv-consumer` su
`146073_compliance_usa_fase1` (`990503a`, pubblicato; da allineare alla scrittura solo su
`sew_spedizioni_work` e da compilare in Eclipse con i jar di `L:` prima del rilascio); orchestratore,
smistatore e bff restano nel primo passo su `develop` e ripartono il 24-11. L'adapter (int. 05) e `consumer-sew_sped_poste` (int. 08) sono **rimandati al
punto 2 della fase 1**: mancano i nomi dei campi nei messaggi sorgente PDB, PDW e ILP e i dettagli
lato Poste (PA-13). I loro funzionali sono comunque allineati ai nomi `zonos_*`.

| Int. | Servizio | Modifica di codice | Sintesi |
|---|---|---|---|
| 01 | `ce-dichiarato-validatore` | **sì** | I DTO tipizzati oggi perdono i campi: si aggiungono a `SpedizioneDTO` e `ArticoloDTO`, senza annotazioni Bean Validation. La regola R-01 va in un componente Java configurabile (`ComplianceUsaValidator`), chiamato da `SdaFlussoHandler` e `PdbPreadvisingHandler`. I DRL restano come sono. Codici di errore `1320`…`1323` |
| 02 | `ce-dichiarato-orchestratore` | **sì**, piccola | I campi si perdono in 8 punti (ingresso, Mongo, lavorazioni, merge, uscita): si aggiungono ai DTO. I tre campi vanno esclusi dal merge delle lavorazioni tramite `campi-esclusi` |
| 03 | `ce-dichiarato-smistatore` | **sì**, piccola | Stesso `SmistatoreDTO` per Poste e SDA: si aggiungono i campi ai DTO. I palmari restano esclusi senza logica nuova |
| 04 | `ce-event-handler-event-store` | no | `eventData` è un `Object` generico: i campi arrivano su Mongo così come sono. Solo test di non regressione |
| 04 | `ce-event-handler-monitoring` | no (variante A) | Usa solo identificativi, stato ed errori. Gli errori nuovi arrivano già alla console. Variante B (campi nel `Record`) solo se Poste la chiede |
| 04 | `ce-dichiarato-bff` | **sì**, piccola | Le API di dettaglio e di ricerca leggono `dichiarato_events` con DTO tipizzati: si aggiungono i tre campi. Nessuna modifica al front-end |
| 05 | `ce-dichiarato-adapter` | **sì**, **rimandato al punto 2** | Mapping nei 3 consumer, con nomi sorgente provvisori (ADA-01). Su PDB si aggiunge `productId` a `hasValidProperties()` e la testata al merge degli esiti BEP. PDW ha un solo articolo per spedizione |
| 07 | `consumer-sew_sped` | **sì** | `zonos_account_key` e `zonos_declaration_id` **solo su `sew_spedizioni_work`** (non su `_2` né su `sew_spedizioni`, Diego 24-11), nell'insert solo se valorizzati. Il consumer **non scrive una tabella articoli**: `zonos_product_id` non ha dove andare (SEW-02) |
| 08 | `consumer-sew_sped_poste` | **sì**, **rimandato al punto 2** | Account Key e Declaration ID nella MERGE di `SEW_SPEDIZIONI_POSTE`. `ZONOS_PRODUCT_ID` su `SEW_SPEDIZIONI_POSTE_INTER` (e sullo scarto inter), solo nei rami internazionali PRTN |
| 09 | `producer-sew-sped` | **sì** | Batch che rilegge le SEW dei portali (MYSDA, INVIO_WEB) e del web service (SDA_WS). Invia `zonos_account_key` solo se i portali la scrivono in `sew_spedizioni_work`, senza gli spazi di riempimento; `zonos_product_id` non è disponibile per articolo |
| — | DDL (`ddl-sew-146073.md`) | Informix | `ALTER TABLE … ADD`, con query di verifica e rollback. Esegue il DBA, prima del rilascio del codice |

**Rischi emersi oltre l'HLD**

- **Il validatore non controlla tutti i canali.** Le regole girano solo nel flusso SDA (IF,
  IS, IE) e in quello PDB/EUD. I canali dei portali e del web service (MYSDA, SDA_WS,
  INVIO_WEB), l'adapter e TUP passano senza regole: una spedizione USA che arriva da
  lì non verrebbe controllata (VAL-DA-04).
- **Le lavorazioni non conoscono i campi.** `ce-dichiarato-ldv`, `-ldv-pdb` e `-ldv-pdb-sync`
  restituiscono il tracciato senza i campi. In fase 1 l'orchestratore li conserva da Mongo,
  ma in fase 2 servono verso BEP. Questi servizi non sono nell'HLD (PA-10).
- **Due retry li perdono.** `retry-eurodis` e `retry-pread-completo` usano un proprio DTO
  tipizzato (ORC-08).
- **Il merge per indice.** Colli e articoli si fondono per indice nella lista, non per
  `posizione`: oggi non succede, ma se una lavorazione li riordina i Product ID si mescolano
  (ORC-05).
- **Il Product ID lato SDA non ha una tabella.** Né il consumer né il producer hanno una
  sorgente o una destinazione per articolo (SEW-02, PRD-04).
- **L'Account Key dei portali.** Arriva al producer solo se i portali e il web service, fuori
  perimetro, la scrivono nelle SEW (PRD-05).
- **Account Key nei log.** Validatore, event store e monitoring loggano il messaggio intero.
  Se l'Account Key è un dato riservato va mascherata (VAL-AS-11, EVS-03).
- **Il carattere non ASCII.** Il consumer Poste toglie i caratteri non ASCII da tutta
  l'istruzione SQL, Product ID compreso (SWP-08).
- **Base dei branch.** `sda-ldv-preadv-consumer` non ha `develop`: il branch dedicato parte da
  `origin/dev202508_preadvising` (SEW-07, deciso il 24-11). Sul `develop` locale dell'adapter ci
  sono due commit di Diego non pubblicati (`c4a26d1`, `1a6202d`) sugli stessi file: da
  riconsiderare quando parte il punto 2.

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
| PA-01 | **Deciso internamente il 23-11 (Diego)**: `zonos_declaration_id` (13) si predispone in fase 1. Resta la conferma di Poste che i "3 nuovi campi" dell'HLD sono Account Key, Product ID e Declaration ID, e che il Declaration ID si predispone in fase 1 | DTO, DDL, ICD |
| PA-02 | **Chiuso il 23-11 (Diego).** Regola R-01: niente condizione "business"; USA da `codice_nazione_iso_2` / `codice_nazione`; documenti da `tipo_merce` = `D`; prodotti `456,457,458,459,515,516` su `codice_prodotto` o `id_servizio` (resta PA-12) | Validatore |
| PA-03 | **Chiuso il 23-11 (Diego)** per i nomi: `zonos_account_key`, `zonos_product_id`, `zonos_declaration_id`. Resta l'aggiornamento dell'ICD con il team del builder | Tutti |
| PA-04 | **Chiuso il 23-11 (Diego).** Codici `1320`…`1323` con le descrizioni di AS-03, esito scarto | Validatore, scarti |
| PA-05 | DDL: **colonne, tipi e nomi decisi il 23 e 24-11** (AS-04). **Tabelle SDA chiuse il 24-11 (Diego)**: solo `sew_spedizioni_work` (SEW-01). Restano aperti: chi le esegue su Informix SDA e dove va il Product ID lato SDA, che non ha una tabella articoli (SEW-02) | Int. 07, 08 |
| PA-06 | Repo del batch producer dei preavvisi da portali e web service | Int. 09 |
| PA-07 | Fase 2: quali sono i due campi verso BEP, con quale contratto e quale flusso (`ldv-pdb` o `ldv-pdb-sync`) | Int. 06 |
| PA-08 | Fase 2: contratto del microservizio comune Zonos (sincrono o su topic, chiave di idempotenza, formato di dazi e fee, codici di errore) e punto del processo in cui si avvia la lavorazione | Orchestratore fase 2 |
| PA-09 | Fase 2: elenco dei campi che la lavorazione Zonos può sovrascrivere nel preavviso; dazi e fee rientrano? | Orchestratore fase 2 |
| PA-10 | `ce-dichiarato-ldv` e `ce-dichiarato-state-machine-handler` compaiono nella descrizione ma non nell'HLD: chi li fa? | Perimetro |
| PA-11 | Palmari (`sew_sped_pre_adv_online_out_tot`), T&T-Repo e OneTracking: sono fuori perimetro? | Perimetro |
| PA-12 | **Nuovo (23-11).** Diego ha elencato CRONO INTERNAZIONALE quattro volte, ma in `ce_prodotto` di ce-rules risultano solo `515` e `516` (516 = assicurato): l'elenco dei prodotti va confermato. Si cambia in configurazione | Validatore |
| PA-13 | **Nuovo (24-11).** Punto 2 della fase 1: nomi e livello dei campi nei messaggi sorgente PDB, PDW e ILP (adapter, int. 05) e dettagli lato Poste (`consumer-sew_sped_poste`, int. 08) | Int. 05, 08 |

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
