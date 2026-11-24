# `ce-event-handler-event-store` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore dell'event store (Amelia) e test manager
**Intervento HLD**: 04 della fase 1 ("Adeguamento ce-dichiarato-monitoring, event store, bff"), stima TOW 1.2 di 0,40 per i tre servizi insieme
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-event-handler-event-store` (in locale `gitposte/SDA/preadvising/ce-event-handler-event-store`)
**Branch**: `develop` [DECISO, Diego 2026-11-24, sostituisce il branch dedicato del 16-11], **solo se
emerge una modifica**: con le verifiche di questo documento non ne serve nessuna (sezione 3). Non si
sviluppa su `master` né sui branch di altre iniziative.
**Codice letto**: `origin/develop` @ `94bb901` (2026-09-03), con `git show`, senza checkout. Il
`git fetch` del 16-11 è fallito (connessione rifiutata da GitLab): prima di iniziare va rifatto. La
copia locale ha modifiche non committate di altri (`AsyncProcessingConfig` e 4 DTO): non sono
considerate.
**Stack**: Spring Boot 3.5.7, Java 17, Spring Kafka, Spring Data MongoDB
**Generato da**: [prompt-ce-event-handler-event-store.md](prompt-ce-event-handler-event-store.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" (AS-01…AS-06, **vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (int. 04); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`
(§ `ce-event-handler-event-store`); ICD `ce-event-handler-monitoring/icd/ICD_preadvising_eventsource.md`
(non versionato, copia locale del 13-09); [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md) (codici 1320…1323)

Etichette:
- **[FATTO]**: scritto nell'HLD, nella descrizione, nell'ICD o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare il lavoro, con ID e default (sezione 10).

> **Verdetto: nessuna modifica di codice.** L'event store tratta `eventData` come JSON generico e
> lo salva così com'è: `zonos_account_key`, `zonos_declaration_id` e `zonos_product_id` (per articolo) arrivano su
> Mongo senza interventi. L'intervento si riduce a **verifica e test di non regressione**.

---

## 1. Contesto e obiettivo

`ce-event-handler-event-store` consuma il topic degli eventi di stato `preadvising.evensource` e
scrive ogni evento, in sola **insert**, nella collection Mongo `event_store`. Gli eventi sono di due
tipi [FATTO, ICD eventsource §3-§6]:

| `aggregateType` | Chi lo pubblica | `eventData` |
|---|---|---|
| `file` | `ce-dichiarato-builder`, `ce-dichiarato-eurodis-in` | `FileDigest` (dati del file) |
| `ldv`, `collo` | validatore, orchestratore, smistatore, `ce-dichiarato-ldv` | il `DichiaratoDTO` completo del preavviso, con `spedizione[].collo[].articolo[]` |

Con la fase 1 il preavviso porta tre campi nuovi (AS-01): `zonos_account_key` e `zonos_declaration_id` sulla
testata di `spedizione[]`, `zonos_product_id` su ogni `spedizione[].collo[].articolo[]`. La descrizione
chiede all'event store di [FATTO, descrizione]:

1. estendere il modello degli eventi con Account Key e Product ID;
2. conservare la cardinalità per articolo in serializzazione e deserializzazione;
3. garantire che replay, consultazione e recupero dello stato ricostruiscano i nuovi dati;
4. restare compatibile con gli eventi già memorizzati, che non hanno i campi.

Questo documento mostra che i punti 1, 2 e 4 sono già garantiti dal codice e che il punto 3 non
riguarda codice di questo servizio (sezione 3.3). Definisce i test che lo dimostrano.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Mettere i campi nel `DichiaratoDTO` che finisce in `eventData` | i servizi che pubblicano l'evento: validatore (int. 01), orchestratore (int. 02), smistatore (int. 03). `ce-dichiarato-ldv` non è nell'HLD (PA-10) |
| Consultazione dell'event store | `ce-dichiarato-bff` ([ce-dichiarato-bff.md](ce-dichiarato-bff.md)) |
| Esito e stato della lavorazione Zonos, Declaration ID valorizzato | fase 2 (AS-06) |
| Altri consumer di `preadvising.evensource` (T&T-Repo, `ce-event-handler-file-pdb`, scarti) | fuori fase 1 (AS-06) o fuori HLD |

## 2. Interventi HLD coperti

| HLD | Testo | Copertura |
|---|---|---|
| Fase 1, int. 04 | "adeguamento ms per propagazione nuovi campi sul topic": il ms riceve e propaga i nuovi campi | ricezione e salvataggio già garantiti (3.1, 3.2). L'event store non pubblica su nessun topic (3.4) |
| Descrizione, event store fase 1 | modello, cardinalità, replay, eventi storici | sezioni 3 e 4, test della sezione 9 |

## 3. Dove si interviene nel codice

Codice di `origin/develop` @ `94bb901` [FATTO, letto il 16-11].

### 3.1 Il percorso di un evento

| Punto | Cosa fa | Effetto sui campi nuovi |
|---|---|---|
| `consumer/KafkaConsumer.consumeEvent` | `@KafkaListener` su `${kafka.consumer.topic.event-store-topic}` (`KAFKA_TOPIC_INPUT` = `preadvising.evensource` in `.helm`, svil, coll e template); passa il record a un executor asincrono | nessuno |
| `KafkaConsumer.processaMessaggio` | `readTree` del valore per il log, `readValue(..., EventStoreDTO.class)`, poi `EventStoreService.handleEvent` in uno span figlio `SalvataggioEventoMongo` | nessuno |
| `service/EventStoreService.handleEvent` | `readValue(record.value(), EventStoreDTO.class)`; se `timestamp` manca mette `Instant.now()`; `mongoTemplate.insert(evento, eventStoreCollection)` | **il punto che conta**: vedi 3.2 |
| `dto/EventStoreDTO` | `id`, `aggregateId`, `aggregateType`, `eventType`, **`Object eventData`**, `Map<String,Object> metadata`, `Instant timestamp` | `eventData` non è tipizzato |
| `config/AppConfig.objectMapper` | `FAIL_ON_UNKNOWN_PROPERTIES = false`, `JavaTimeModule` | campi sconosciuti mai bloccanti |
| `mongo.collection.eventstore` | default `event_store`; nessun override nei values | collection di destinazione |

### 3.2 Perché i campi passano senza modifiche [FATTO]

- `eventData` è dichiarato `Object`: Jackson lo deserializza in `LinkedHashMap` / `ArrayList` /
  `String` / numeri, **qualunque** sia il contenuto. Nessuna classe Java descrive il preavviso in
  questo percorso, quindi un campo nuovo non può essere scartato.
- `MongoTemplate.insert` scrive la mappa come documento BSON annidato con le stesse chiavi e lo
  stesso ordine. Gli array restano array: ogni `zonos_product_id` resta nell'elemento di `articolo[]` in
  cui è arrivato, e ogni `zonos_account_key` nel suo elemento di `spedizione[]` (cardinalità per articolo
  e per spedizione, R-04).
- Le chiavi sono quelle del JSON dell'evento, cioè i nomi del tracciato `zonos_account_key`,
  `zonos_declaration_id`, `zonos_product_id`: gli stessi che, per decisione di Diego del 24-11,
  validatore e orchestratore usano su `dichiarato_events`. L'event store non legge
  `dichiarato_events` (3.3), quindi la decisione non richiede modifiche qui.
- I valori stringa non vengono toccati: niente `trim`, maiuscole, troncamenti (R-04). Lunghezze di
  52 e 255 caratteri non hanno limiti né in Jackson né in Mongo.
- `zonos_declaration_id: null` si salva come `null`; un campo assente resta assente. Per la fase 1 le due
  forme sono equivalenti (AS-01). Il test TC-03 registra quale delle due si ottiene.

### 3.3 DTO tipizzati presenti nel repo, ma fuori dal percorso [FATTO]

Il repo contiene due copie dei DTO del tracciato (`dto/` e `dto/dto/`: `DichiaratoDTO`,
`SpedizioneDTO`, `ColloDTO`, `ArticoloDTO`…) e l'entity `entity/PreadvisingEvents` (collection
`dichiarato_events`). **Non sono usati** nel flusso:

- `PreadvisingEvents` non è referenziata da nessuna classe;
- `DichiaratoDTO` compare solo in `AppConfig.safeRead`, metodo statico che nessuno chiama;
- `KafkaTemplate` è iniettato in `EventStoreService` ma non usato: il servizio non pubblica nulla.

Non vanno estesi con i campi nuovi (EVS-01): sarebbe codice morto in più, senza effetto.

### 3.4 Replay, consultazione, ricostruzione dello stato [FATTO]

- Il servizio **non legge** mai `event_store`: non ha API, non fa replay, non ricostruisce stati.
  Il "replay" dell'ICD è il flag `metadata.replay` dell'evento, che si salva come gli altri campi.
- Un evento ripubblicato con lo stesso `id` va in errore di chiave duplicata sull'`_id`: l'errore è
  loggato e l'evento non si duplica (comportamento attuale, non cambia). Un evento ripubblicato con
  un `id` nuovo diventa un documento in più con tutti i campi.
- La consultazione è nel BFF: `EventStoreEntry` legge `eventData` come `Map<String,Object>`, quindi
  rilegge i campi nuovi così come sono stati scritti ([ce-dichiarato-bff.md](ce-dichiarato-bff.md), 3.3).
- La ricostruzione dello stato di un preavviso dall'event store (ordinare per `timestamp` gli eventi
  di un `aggregateId`, ICD §7.3) restituisce quindi anche i campi nuovi, per gli eventi che li hanno.

### 3.5 Eventi storici [FATTO]

L'event store fa solo insert e non migra i documenti. Gli eventi già salvati restano come sono,
senza i campi. Nessun lettore del perimetro li deserializza in classi che richiedono i campi (il BFF
usa una mappa): nessuna incompatibilità.

## 4. Regole

| ID | Regola |
|---|---|
| RE-01 | L'evento si salva com'è arrivato: i tre campi nuovi, se presenti in `eventData`, sono nel documento di `event_store` con lo stesso nome, la stessa posizione e lo stesso valore |
| RE-02 | `zonos_product_id` resta sull'elemento di `articolo[]` in cui è arrivato, con più colli e più articoli |
| RE-03 | Un evento senza i campi (scenari non USA, eventi `file`, eventi storici) si salva come oggi |
| RE-04 | Nessuna validazione dei campi: presenza e lunghezza le controlla solo il validatore (R-02) |
| RE-05 | Nessun cambio a topic, collection, gruppo consumer, metriche |

## 5. Esempi [dati inventati]

### 5.1 Evento `ST_R0004` di una spedizione USA con due articoli

In ingresso su `preadvising.evensource` (ridotto ai campi utili):

```json
{
  "id": "e1000000-0000-4000-8000-000000000001",
  "aggregateId": "99TESTPREADV0001",
  "aggregateType": "ldv",
  "eventType": "ST_R0004",
  "eventData": {
    "id_preadvising": "99TESTPREADV0001",
    "canale": "PDB_INVIOFILE",
    "spedizione": [{
      "rif_spedizione": "99RIF-USA-0001",
      "zonos_account_key": "TESTACCOUNTKEY00000000000000000000000000000000000001",
      "zonos_declaration_id": null,
      "collo": [{
        "id_collo": "99COLLO0001",
        "articolo": [
          { "posizione": "1", "codice_taric": "6109100010", "zonos_product_id": "PRD-TEST-0001" },
          { "posizione": "2", "codice_taric": "6203420000", "zonos_product_id": "PRD-TEST-0002" }
        ]
      }]
    }]
  },
  "metadata": { "timestamp": "2026-11-16T10:00:00Z", "correlation_id": "99TESTPREADV0001",
                "source": "ce-dichiarato-smistatore", "replay": false },
  "timestamp": "2026-11-16T10:00:00Z"
}
```

Documento in `event_store`: stesso contenuto, con `_id` = `id` e `timestamp` come `Date`. In
`eventData.spedizione[0]` ci sono `zonos_account_key` (52 caratteri) e `zonos_declaration_id` (`null`); in
`eventData.spedizione[0].collo[0].articolo[0]` e `[1]` i due `zonos_product_id`, ognuno sul suo articolo.

### 5.2 Scarto `ST_R0006` per Product ID mancante

`eventData.errori` = `{"1322": "zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2)"}` (codice del
validatore), il secondo articolo senza `zonos_product_id`. Si salva com'è: l'articolo senza `zonos_product_id`
resta senza la chiave.

### 5.3 Spedizione non USA

Nessuno dei tre campi in `eventData`: il documento è identico a quello di oggi.

## 6. Configurazione

Nessuna proprietà nuova, nessun cambio ai values (`.helm`, `deploy-svil`, `deploy-coll`,
`deploy-config/values_TEMPLATE.yaml`).

## 7. Requisiti non funzionali e osservabilità

- Volumi e tempi invariati: due stringhe per spedizione e una per articolo, al massimo 255 caratteri.
- **Log** [FATTO]: `processaMessaggio` scrive in INFO l'intero evento (`Evento ricevuto da topic…`) e
  `gestisciErroreTecnico` in ERROR l'intero payload. Con la fase 1 nei log finiscono anche
  `zonos_account_key` e `zonos_product_id`. Oggi ci finiscono già nomi, indirizzi e P.IVA, contro le linee guida:
  è un problema esistente, non di questa iniziativa. Se Poste considera l'Account Key un dato
  riservato serve una modifica (EVS-03).
- Metriche e span invariati (`kafka_eventstore_message_*`, span `ce-event-handler-event-store` e
  `SalvataggioEventoMongo`).

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato l'evento 5.1 su `preadvising.evensource`, il documento in `event_store` con `_id` = `e1000000-…0001` ha `eventData.spedizione[0].zonos_account_key` uguale al valore inviato (52 caratteri, identico) |
| AC-02 | Nello stesso documento `articolo[0].zonos_product_id` = `PRD-TEST-0001` e `articolo[1].zonos_product_id` = `PRD-TEST-0002`: nessuno spostamento né accorpamento |
| AC-03 | `zonos_declaration_id` è `null` o assente nel documento; nessun errore nei log |
| AC-04 | Con due colli e tre articoli ciascuno, ogni `zonos_product_id` è sull'articolo di partenza; un `zonos_product_id` di 255 caratteri è salvato intero |
| AC-05 | L'evento 5.2 (articolo senza `zonos_product_id`) si salva senza la chiave sull'articolo e con `errori` invariato |
| AC-06 | L'evento 5.3 (non USA) e un evento `file` si salvano come prima: confronto con un evento equivalente salvato da `94bb901` senza i campi |
| AC-07 | Il BFF legge con `EventStoreEntry` sia un documento della fase 1 sia uno storico, senza errori |
| AC-08 | Nessuna modifica a codice, values, topic, collection, metriche (diff vuoto sul repo) |

## 9. Casi di test

Nessun test automatico nel repo oggi (`src/test` contiene solo un segnaposto). Non si aggiungono
test al repo se non emerge una modifica: le verifiche si fanno in svil. Regole di
[test-integrati.md](../../../contesto/test-integrati.md): iniezione solo in svil, chiavi con prefisso
`99`, header del contratto (`source`, `eventTime`, `traceId`).

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | integrato svil | evento 5.1 iniettato su `preadvising.evensource` | documento in `event_store` con i tre campi al posto giusto | AC-01, AC-02 |
| TC-02 | integrato svil | 2 colli × 3 articoli, `zonos_product_id` di 1 e di 255 caratteri | cardinalità e valori invariati | AC-04 |
| TC-03 | integrato svil | evento con `zonos_declaration_id: null` e uno senza la chiave | `null` o assente (annotare quale), nessun errore | AC-03 |
| TC-04 | integrato svil | evento 5.2 | articolo senza chiave, `errori` invariato | AC-05 |
| TC-05 | regressione svil | evento non USA, evento `file` | come prima | AC-06 |
| TC-06 | integrato svil, catena | preavviso USA vero da `preadvising.pre-enrichment` (AS-05), dopo i rilasci di validatore, orchestratore e smistatore | gli eventi `ST_R0002` e `ST_R0004` di quell'`aggregateId` hanno i campi in `event_store` | AC-01, AC-02 |
| TC-07 | integrato svil | lettura dal BFF dei documenti di TC-01 e di un evento storico | nessun errore, campi presenti dove c'erano | AC-07 |
| TC-08 | unit locale, facoltativo | `ObjectMapper` di `AppConfig` + `MongoTemplate` mock: `handleEvent` con l'evento 5.1, cattura dell'argomento di `insert` | la mappa `eventData` contiene i tre campi annidati | AC-01…AC-04 |

TC-06 dipende dagli altri interventi: se il campo manca in `event_store` ma c'è nel messaggio in
ingresso al servizio che pubblica l'evento, il difetto è di quel servizio, non dell'event store.

## 10. Assunzioni e domande aperte

Valgono AS-01…AS-06 di [analisi.md](../analisi.md). Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| EVS-01 | I DTO tipizzati di `dto/`, `dto/dto/` e `entity/PreadvisingEvents` non sono nel percorso dell'evento | non si estendono; nessuna modifica di codice | Diego |
| EVS-02 | La "ricostruzione dello stato dall'event store" della descrizione: nel perimetro non c'è un servizio che rilegge `event_store` per ricostruire lo stato, salvo la consultazione del BFF | la ricostruzione è la lettura degli eventi di un `aggregateId` ordinati per `timestamp` (ICD §7.3), verificata da TC-06 e TC-07 | Poste |
| EVS-03 | L'Account Key è un dato riservato? Il servizio logga l'intero evento in INFO e in ERROR | non è riservata: nessuna modifica. Se lo è, serve mascherare `zonos_account_key` nei due log (modifica piccola, con branch) | Poste |
| EVS-04 | La stima di 0,40 dell'int. 04 copre tre servizi. Per l'event store resta solo la verifica | quota event store = test di non regressione in svil (TC-01…TC-07) | Diego |
| EVS-05 | I campi arrivano in `event_store` solo se ci sono nel `DichiaratoDTO` dei servizi che pubblicano l'evento, `ce-dichiarato-ldv` compreso (non è nell'HLD, PA-10) | dipendenza dichiarata, verificata da TC-06 | Diego |

## 11. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1.
- [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md): codici di errore e forma dell'evento `ST_R0006`.
- [ce-dichiarato-bff.md](ce-dichiarato-bff.md), [ce-event-handler-monitoring.md](ce-event-handler-monitoring.md): gli altri due servizi dell'int. 04.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md), [contesto/test-integrati.md](../../../contesto/test-integrati.md).
