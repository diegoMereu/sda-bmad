# `ce-dichiarato-bff` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del BFF (Amelia) e test manager
**Intervento HLD**: 04 della fase 1 ("Adeguamento ce-dichiarato-monitoring, event store, bff"), stima TOW 1.2 di 0,40 per i tre servizi insieme
**Repository**: `posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-bff` (in locale
`gitposte/SDA/preadvising/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-bff`). È il **repo vivo**: ha git,
`develop` e `master` aggiornati al 02-11. La cartella `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-bff-master`
è una copia senza git del 17-06: non si usa.
**Branch**: `develop` [DECISO, Diego 2026-11-24: sostituisce il branch dedicato `146073_compliance_usa_fase1`
deciso il 16-11]. `origin/HEAD` punta a `master`. Non si sviluppa su `master` né sui branch di altre
iniziative (es. `ce-dichiarato-fe`, che contiene il front-end dell'harness).
**Codice letto**: `origin/develop` @ `2335cff` (2026-11-02), con `git show`, senza checkout.
**Stack**: Spring Boot 3.5.14, Java 17, Spring Data MongoDB, Spring Kafka, springdoc-openapi
**Generato da**: [prompt-ce-dichiarato-bff.md](prompt-ce-dichiarato-bff.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" (AS-01…AS-06, **vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (int. 04); [ce-event-handler-event-store.md](ce-event-handler-event-store.md)

Etichette:
- **[FATTO]**: scritto nell'HLD o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default (sezione 10).

> **Verdetto: modifica di codice necessaria, piccola.** Le API di consultazione dei preavvisi
> (`/api/v1/preadvising/dettaglio` e `/api/v1/preadvising`) leggono `dichiarato_events` in DTO
> tipizzati, che **scartano** i campi che non conoscono: oggi i tre campi nuovi non si vedrebbero.
> Si aggiungono `zonos_account_key` e `zonos_declaration_id` a `SpedizioneDTO` e `zonos_product_id` ad `ArticoloDTO`.
> Le altre API (risottomissione, enrichment, event store, harness) trattano i dati come JSON generico
> e restano come sono: per loro basta il test di non regressione.

---

## 1. Contesto e obiettivo

`ce-dichiarato-bff` espone in REST i dati della catena preadvising salvati su MongoDB
(`dichiarato_db`): preavvisi (`dichiarato_events`), enrichment (`enrichment_events`), file, event
store (`event_store`). Permette inoltre di risottomettere un preavviso su un topic della catena e,
solo in svil con `test-harness.enabled`, di iniettare messaggi di test.

La fase 1 aggiunge al preavviso `zonos_account_key`, `zonos_declaration_id` (testata di `spedizione[]`) e
`zonos_product_id` (ogni `spedizione[].collo[].articolo[]`) (AS-01). L'HLD chiede al BFF di "ricevere e
propagare" i campi [FATTO, HLD int. 04]: per un BFF vuol dire **restituirli** nelle API che espongono
il preavviso, e **non perderli** quando il preavviso viene risottomesso (R-04).

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Scrivere i campi in `dichiarato_events` | validatore e orchestratore (int. 01, 02): il BFF mostra solo ciò che trova su Mongo |
| Validare presenza e lunghezza | validatore (R-02) |
| Mostrare i campi a video | nessun front-end in fase 1 (BFF-02) |
| Filtri di ricerca per Account Key o Product ID | non richiesti (BFF-03) |

## 2. Interventi HLD coperti

| HLD | Testo | Copertura |
|---|---|---|
| Fase 1, int. 04 | il ms riceve e propaga i nuovi campi | API di consultazione dei preavvisi: 3.2; risottomissione e altre API: 3.3 |

## 3. Dove si interviene nel codice

Codice di `origin/develop` @ `2335cff` [FATTO, letto il 16-11].

### 3.1 Le API e come leggono i dati

| API | Collection | Modello di lettura | I campi nuovi passano? |
|---|---|---|---|
| `GET /api/v1/preadvising/dettaglio?id_ldv=…\|rif_spedizione=…` | `dichiarato_events` | `entity/PreadvisingEvents` con `List<SpedizioneDTO>` → `List<ColloDTO>` → `List<ArticoloDTO>` | **no**: 3.2 |
| `GET /api/v1/preadvising` (ricerca paginata) | `dichiarato_events` | `PreadvisingEvents`, come sopra | **no**: 3.2 |
| `POST /api/v1/preadvising/{id}/resubmit?topic=…` | `dichiarato_events` | `org.bson.Document` generico (`ResubmitService`), serializzato com'è | sì |
| `GET /api/v1/enrichment`, `/{idPreadvising}`, `/by-id-file/{idFile}` | `enrichment_events` | `EnrichmentEvent` con `Map<String,Object> spedizione` | sì |
| `GET /api/v1/files`, `/{idFile}` | file | `PreadvisingFile`, dati del file | non pertinente |
| `POST /api/v1/test/inject`, `GET /api/v1/test/inject/{id}/esito` (harness) | topic, `dichiarato_events` | `JsonNode` in ingresso, `Document` in lettura | sì |
| event store (`EventStoreService.search`, `timeline`) | `event_store` | `EventStoreEntry` con `Map<String,Object> eventData` | sì; nessun controller lo espone oggi |

### 3.2 La modifica: DTO del preavviso

Spring Data MongoDB, leggendo un documento in una classe, **ignora** le chiavi che la classe non
mappa. `SpedizioneDTO` e `ArticoloDTO` non hanno i campi nuovi, quindi `dettaglio` e la ricerca
li perdono [FATTO].

| Classe | Campo nuovo | Annotazioni (stile esistente) |
|---|---|---|
| `dto/SpedizioneDTO` | `private String zonosAccountKey;` | `@Field("zonos_account_key")` `@JsonProperty("zonos_account_key")` |
| `dto/SpedizioneDTO` | `private String zonosDeclarationId;` | `@Field("zonos_declaration_id")` `@JsonProperty("zonos_declaration_id")` |
| `dto/ArticoloDTO` | `private String zonosProductId;` | `@Field("zonos_product_id")` `@JsonProperty("zonos_product_id")` |

- Nessuna annotazione di validazione (`@Size`, `@NotNull`): il BFF legge, non valida (R-02, BFF-04).
- Tipo `String`, senza default e senza trasformazioni (AS-01, R-04).
- `ColloDTO` non cambia: contiene già `List<ArticoloDTO> articolo`.
- L'`ObjectMapper` di `config/AppConfig` non esclude i `null`: i campi assenti escono come `null`
  nella risposta (stessa forma per documenti nuovi e storici).
- L'OpenAPI si aggiorna da sola: lo schema delle risposte è `PreadvisingEvents`.

### 3.3 Nessuna modifica, solo verifica [FATTO]

- **Risottomissione** (`ResubmitService`): legge il documento come `Document`, toglie `_class`,
  converte `ObjectId` e `Date`, e pubblica il resto com'è. I tre campi, con la cardinalità per
  articolo, arrivano sul topic di destinazione (R-04: reinvii senza perdita).
- **Enrichment** (`EnrichmentEvent.spedizione` è una mappa), **event store** (`EventStoreEntry.eventData`
  è una mappa), **harness** (`JsonNode` e `Document`): JSON generico.
- L'harness (`POST /api/v1/test/inject`, solo con `test-harness.enabled`) può iniettare in svil
  preavvisi con i campi nuovi su `preadvising.pre-enrichment`: è uno strumento utile per i test di
  AS-05 finché il builder non è pronto.

### 3.4 Front-end [FATTO]

- `ce-monitoraggio-fe-develop` (in locale) è una cartella vuota.
- Il branch `origin/ce-dichiarato-fe` di questo repo contiene un front-end React solo per l'harness
  (simulazione, iniezione, esito con il JSON grezzo): non usa `/api/v1/preadvising`. Nessuna modifica.
- Chi consuma `/api/v1/preadvising` non risulta dal codice letto (BFF-02).

## 4. Regole

| ID | Regola |
|---|---|
| RB-01 | `dettaglio` e la ricerca restituiscono `zonos_account_key` e `zonos_declaration_id` in ogni elemento di `spedizione[]` e `zonos_product_id` in ogni elemento di `collo[].articolo[]`, con il valore letto da Mongo, senza trasformazioni |
| RB-02 | Un campo assente su Mongo esce come `null` (documenti storici, scenari non USA) |
| RB-03 | La risottomissione pubblica i campi così come sono su Mongo, ognuno nella sua posizione |
| RB-04 | Nessun filtro, parametro o API nuova; nessun cambio di path, codici HTTP, metriche |
| RB-05 | Nei log del BFF non si scrivono i valori dei campi nuovi (oggi il BFF non logga il contenuto dei preavvisi: resta così) |

## 5. Esempi [dati inventati]

### 5.1 `GET /api/v1/preadvising/dettaglio?rif_spedizione=99RIF-USA-0001`

Documento su `dichiarato_events` scritto dalla catena (fase 1), risposta `200` (ridotta):

```json
[{
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
  }],
  "stato": 1
}]
```

### 5.2 Documento storico

Stesso endpoint su un preavviso salvato prima della fase 1: risposta come oggi, con in più
`"zonos_account_key": null`, `"zonos_declaration_id": null` e `"zonos_product_id": null` su ogni articolo.

### 5.3 Risottomissione

`POST /api/v1/preadvising/99TESTPREADV0001/resubmit?topic=preadvising.enrichment`: il messaggio
pubblicato (chiave `99TESTPREADV0001`) contiene i tre campi nelle stesse posizioni del documento Mongo.

## 6. Configurazione

Nessuna proprietà nuova, nessun cambio ai values.

## 7. Requisiti non funzionali e osservabilità

- Tempi e dimensioni delle risposte invariati (tre stringhe in più per spedizione e una per articolo).
- Metriche (`bff_dettaglio_*`, `bff_list_*`, `bff_resubmit_*`) e span invariati.
- Sonar: tre campi Lombok `@Data`, nessun codice nuovo da coprire oltre ai test della sezione 9.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato su Mongo il documento di 5.1, `dettaglio?rif_spedizione=99RIF-USA-0001` risponde `200` con `zonos_account_key`, `zonos_declaration_id` e i due `zonos_product_id` come in 5.1 |
| AC-02 | Lo stesso documento, cercato con `dettaglio?id_ldv=…` e con la ricerca paginata (`/api/v1/preadvising?id_file=…`), ha gli stessi campi |
| AC-03 | Con due colli e tre articoli ciascuno, ogni `zonos_product_id` è sull'articolo di partenza |
| AC-04 | Un documento storico senza i campi risponde come oggi, con i tre campi a `null` |
| AC-05 | `zonos_account_key` di 52 caratteri e `zonos_product_id` di 255 caratteri escono interi, senza `trim` |
| AC-06 | La risottomissione del documento 5.1 pubblica un messaggio con i tre campi nelle stesse posizioni |
| AC-07 | Le API di enrichment, file, harness e la risottomissione di un documento storico danno le stesse risposte di prima |
| AC-08 | L'OpenAPI (`/v3/api-docs`) mostra i tre campi negli schemi `SpedizioneDTO` e `ArticoloDTO` |

## 9. Casi di test

Oggi `src/test` ha un solo test (`AtlasSchemaInspectorTest`). Si aggiungono test unitari con dati
inventati; poi verifica in svil.

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit | `MappingMongoConverter.read(PreadvisingEvents.class, Document)` sul documento 5.1 | i tre campi valorizzati nei DTO | AC-01, AC-03 |
| TC-02 | unit | stesso test con un documento senza i campi | campi `null`, nessuna eccezione | AC-04 |
| TC-03 | unit | serializzazione JSON di `PreadvisingEvents` con l'`ObjectMapper` di `AppConfig` | nomi `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id`; `null` presenti | AC-01, AC-04 |
| TC-04 | unit | valori di 52 e 255 caratteri, con spazi iniziali e finali | valori identici | AC-05 |
| TC-05 | unit | `ResubmitService` con `MongoTemplate` e `KafkaTemplate` mock, documento 5.1 | payload pubblicato con i tre campi | AC-06 |
| TC-06 | integrato svil | preavviso USA iniettato con l'harness o con un messaggio a mano su `preadvising.pre-enrichment` (AS-05), dopo i rilasci di validatore e orchestratore | `dettaglio` e ricerca come AC-01, AC-02 | AC-01, AC-02 |
| TC-07 | regressione svil | `dettaglio` su un preavviso storico; enrichment; file; risottomissione su un topic ammesso di svil | come prima | AC-04, AC-07 |
| TC-08 | svil | `/v3/api-docs` | schemi aggiornati | AC-08 |

TC-06 dipende dagli altri interventi: se il campo non c'è nella risposta, si guarda prima il
documento su `dichiarato_events`. Se manca lì, il difetto è di chi lo scrive, non del BFF.

## 10. Assunzioni e domande aperte

Valgono AS-01…AS-06 di [analisi.md](../analisi.md). Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| BFF-01 | "Ricevere e propagare" per il BFF vuol dire esporre i campi nelle API di consultazione del preavviso e non perderli nella risottomissione | modifica di 3.2; risottomissione invariata | Diego |
| BFF-02 | Chi consuma `/api/v1/preadvising`? Nessun front-end del perimetro la usa (3.4). Un front-end deve mostrare i campi in fase 1? | nessuna modifica a front-end | Poste, Diego |
| BFF-03 | Servono filtri di ricerca per `zonos_account_key` o `zonos_product_id`? | no | Poste |
| BFF-04 | I DTO del BFF hanno annotazioni di validazione (`@Size`) che in lettura non scattano | i campi nuovi senza annotazioni | — |
| BFF-05 | I campi si vedono solo se validatore e orchestratore li scrivono in `dichiarato_events` (int. 01, 02: salvataggio a DB e merge) | dipendenza dichiarata, verificata da TC-06 | Diego |
| BFF-06 | La stima di 0,40 dell'int. 04 copre tre servizi: event store e monitoring si riducono a verifica, il BFF ha l'unica modifica di codice | quota BFF = 3 campi + test 3.2 e 9 | Diego |

## 11. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1.
- [ce-event-handler-event-store.md](ce-event-handler-event-store.md), [ce-event-handler-monitoring.md](ce-event-handler-monitoring.md): gli altri due servizi dell'int. 04.
- [contesto/test-integrati.md](../../../contesto/test-integrati.md): regole per l'iniezione in svil.
