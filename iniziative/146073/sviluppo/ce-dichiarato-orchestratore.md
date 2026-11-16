# `ce-dichiarato-orchestratore` — Documento funzionale per lo sviluppo (fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13, nuovi campi sul preadvising · **Fase**: 1 · **Versione**: 0.1 · **Data**: 2026-11-16
**Autrice**: Mary (analyst) · **Destinataria**: sviluppatrice back-end della catena preadvising
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-orchestratore` (locale `gitposte/SDA/preadvising/ce-dichiarato-orchestratore`)
**Branch**: `146073_compliance_usa_fase1` da `origin/develop`. Mai sviluppo su `develop`/`master` né su branch di altre iniziative
**Codice letto**: `origin/develop` @ `14b0dd6` (2026-11-10), con `git show`. Il `git fetch` del 16-11 è fallito (rete): prima di creare il branch fare `fetch` e ricontrollare i punti della sezione 3. La working copy locale è su `develop` @ `9f996a9` con file non tracciati di altri: lavorare in un `git worktree`
**Stack**: Spring Boot 3.5.14, Java 17, Kafka, MongoDB (vedi [MICROSERVICE_TECHNICAL_BLUEPRINT.md](../../../contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md))
**Generato da**: [prompt-ce-dichiarato-orchestratore.md](prompt-ce-dichiarato-orchestratore.md)
**Fonti**: [analisi.md](../analisi.md), sezione "Contratto della fase 1" (AS-01…AS-06, **vincolante**); HLD `cliente/HLD_146073_dati_preadvising_fase_1.xlsx`, intervento 02; `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`
**Documento gemello**: [ce-dichiarato-smistatore.md](ce-dichiarato-smistatore.md)

Etichette usate nel documento:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default; da confermare (sezione 11).

> **Il contratto della fase 1 (AS-01…AS-06 di `analisi.md`) non si cambia.** Questo documento lo
> dettaglia per l'orchestratore. Buchi e incoerenze trovati sono fra le assunzioni ORC-xx.

---

## 1. Contesto e obiettivo

Per le spedizioni business verso gli USA con merce, il preavviso porta due campi nuovi, più un
terzo solo predisposto (AS-01) [DECISO 16-11, Diego: si lavora solo sulla fase 1]:

| Campo JSON | Posizione | Fase 1 |
|---|---|---|
| `account_key` | testata di ogni `spedizione[]` | valorizzato dal canale (52 caratteri) |
| `declaration_id` | testata di ogni `spedizione[]` | sempre assente o `null`: solo predisposto |
| `product_id` | ogni `spedizione[].collo[].articolo[]` | valorizzato dal canale (1-255 caratteri) |

L'orchestratore riceve il preavviso validato (`preadvising.enrichment`, `tipo_lavorazione =
validato`), lo salva su Mongo, lo manda alle lavorazioni del canale, fonde i loro ritorni e, a
lavorazioni completate, pubblica su `preadvising.completed`.

Obiettivo: i tre campi **arrivano su `preadvising.completed` e su Mongo identici a come sono
entrati**, con `product_id` sul suo articolo, in tutti i rami (salvataggio, fan-out, merge,
retry per conflitto, completamento, KO). L'orchestratore non li valida e non li trasforma (R-02,
R-04): la validazione è del validatore (int. 01).

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Validazione di presenza e lunghezza, riconoscimento delle spedizioni soggette | `ce-dichiarato-validatore` (int. 01) |
| Passaggio dei campi dentro le lavorazioni (`ce-dichiarato-ldv`, `-ldv-pdb`, `-ldv-pdb-sync`, normalizzatore) | nessuno in fase 1 (ORC-06, ORC-07) |
| Nuova lavorazione Zonos, valorizzazione di `declaration_id` | fase 2 (AS-06) |
| Instradamento verso Poste, SDA, palmari | `ce-dichiarato-smistatore` (int. 03, documento gemello) |

## 2. Interventi HLD coperti

| Int. | Cosa chiede l'HLD [FATTO] | Indicazioni dalla descrizione [FATTO] | Dove nel documento |
|---|---|---|---|
| 02 (fase 1) | Modifica del DTO, del salvataggio a DB e del metodo di merge. Stima TOW 1.2: 0,40 gg | Nessuna perdita dei campi nei rami, nei retry e nelle ripartenze; il Product ID non si appiattisce a livello spedizione | sezioni 3, 4, 5 |

## 3. Dove si interviene nel codice

### 3.1 Il modello dati: DTO tipizzati, non `JsonNode` [FATTO, `origin/develop`]

L'orchestratore lavora con **DTO tipizzati**. Tutti i DTO hanno `@JsonIgnoreProperties(ignoreUnknown = true)`
e l'`ObjectMapper` (`AppConfig`) ha `FAIL_ON_UNKNOWN_PROPERTIES=false` e `NON_NULL`: **ogni campo che
non è dichiarato nel DTO si perde senza errori** alla prima deserializzazione. Il merge lavora sì su
alberi JSON (`ObjectNode`), ma li ottiene da DTO tipizzati e li riconverte in DTO tipizzati.

I documenti di uscita e di Mongo riusano **lo stesso `SpedizioneDTO`**: basta aggiungere i campi lì e
in `ArticoloDTO` perché passino in tutti i punti.

### 3.2 Punti in cui i campi oggi si perdono

| # | Punto (classe, metodo) | Cosa succede oggi ai campi nuovi |
|---|---|---|
| P1 | `KafkaConsumer.execute` → `objectMapper.readValue(..., OrchestratoreDTO.class)` | ingresso dal validatore **e** ritorno delle lavorazioni: `account_key`, `declaration_id`, `product_id` scartati |
| P2 | `OrchestratoreMongoService.insertRecord` → `OrchestratoreMapper.toMongoEntity` → `EnrichmentEvents` (`enrichment_events`) | primo salvataggio: campi assenti |
| P3 | `OrchestratoreService.avviaLavorazioni` → `Utils.serialize(dto)` verso i topic delle lavorazioni | le lavorazioni ricevono il preavviso **senza** i campi |
| P4 | `manageMerge` → `findByIdPreadvising` (lettura tipizzata `EnrichmentEvents`) → `merge` (`convertValue` → `mergeNodes` → `treeToValue`) → `saveMerged` (`repository.save`, sovrascrive il documento intero con `@Version`) | anche se il documento Mongo avesse i campi, la rilettura tipizzata li toglie e il `save` li cancella |
| P5 | `manageMerge`, ramo `OptimisticLockingFailureException`: rilettura `fresh` e secondo merge | come P4 |
| P6 | completamento: `OrchestratoreMapper.toOutputDTOEnrichemtEvents` → `OrchestratoreOutputDTO` → `Utils.serialize` (+ canary) → `preadvising.completed` | uscita senza i campi |
| P7 | completamento e KO: `toOutputDTOPreadvisingEvents` (`convertValue` → `PreadvisingEvents`, `dichiarato_events`) → `OrchestratoreMongoService.save` | documento finale senza i campi; è quello che leggono i retry (sezione 5.4) |
| P8 | `MacchinaStatiService.inviaEventoLdv(outputDTO, …)` (event store, stati `PREAD_COMPLETO`, `PREADVISING_PARZIALE_E_BLOCCATO`, `PREAD_DUPLICATO`) | evento di stato senza i campi |

### 3.3 Cosa si fa

| Punto | Modifica |
|---|---|
| `dto/SpedizioneDTO.java` | due campi `String` nuovi: `account_key`, `declaration_id` (nomi Java snake_case come gli altri campi della classe). Copre P1-P8 per la testata |
| `dto/ArticoloDTO.java` | campo `String` nuovo: `product_id`. Copre P1-P8 per l'articolo |
| `OrchestratoreDTO`, `OrchestratoreOutputDTO`, `EnrichmentEvents`, `PreadvisingEvents` | **nessuna modifica**: contengono `List<SpedizioneDTO> spedizione` (AS-01: i campi stanno nella spedizione, non nella radice) |
| `OrchestratoreMapper` | nessuna modifica: copia la lista `spedizione` per riferimento in `toMongoEntity` e `toOutputDTOEnrichemtEvents`. Verificarlo coi test (TC-02, TC-06) |
| `OrchestratoreMongoService.merge` e sottometodi | **nessuna modifica di codice** (sezione 5.2). Si aggiungono solo test |
| `src/main/resources/application.yaml`, sezione `merge.policies` | protezione dei tre campi dalle lavorazioni (5.3, ORC-02) |
| Mongo (`enrichment_events`, `dichiarato_events`) | nessuna DDL: i campi compaiono nei documenti nuovi; quelli vecchi restano senza (R-05) |
| `src/test/.../OrchestratoreMongoServiceMergeTest`, `OrchestratoreMapperTest`, test del service | casi della sezione 10. Modello per i campi nuovi: `dto/NuoviCampiPdwTest` (stesso schema di un'iniziativa precedente) |

Regole sui campi nuovi (AS-01, R-04, R-05):
- `String`, senza default, senza `@JsonProperty` diverso dal nome, senza trasformazioni (niente `trim`, maiuscole, troncamenti);
- **nessun vincolo Bean Validation** (`@Size`, `@NotNull`): `processEvento` fa `validator.validate(dto)` e,
  con una violazione, scarta il messaggio con un WARN. Un vincolo qui farebbe perdere il preavviso
  invece di scartarlo con l'errore del validatore (ORC-03);
- serializzazione `NON_NULL` come il resto (`ObjectMapper` di `AppConfig`): un campo assente o `null`
  non compare nel JSON. Per `declaration_id`, sempre `null` in fase 1, l'uscita non ha la chiave (ORC-04).

## 4. Esempi [dati inventati]

### 4.1 Ingresso dal validatore (`tipo_lavorazione = validato`), estratto

```json
{
  "id_preadvising": "a1460730-0000-4000-8000-000000000001",
  "canale": "PDB_INVIOSYSTEM",
  "tipo_lavorazione": "validato",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-USA-0001",
    "codice_prodotto": "TST01",
    "account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "declaration_id": null,
    "destinatario": { "codice_nazione_iso_2": "US" },
    "collo": [{
      "id_collo": "COLLO-TEST-001",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": "2", "product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": "1", "product_id": "PRD-TEST-0002" }
      ]
    }]
  }]
}
```

### 4.2 Ritorno di una lavorazione (es. `check-ldv`), estratto

Le lavorazioni oggi **non** restituiscono i campi (5.1): il messaggio torna così.

```json
{
  "id_preadvising": "a1460730-0000-4000-8000-000000000001",
  "tipo_lavorazione": "check-ldv",
  "result": "OK",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-USA-0001",
    "collo": [{
      "id_ldv": "TST0000000146",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": "2" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": "1" }
      ]
    }]
  }]
}
```

### 4.3 Uscita su `preadvising.completed`, estratto

```json
{
  "id_preadvising": "a1460730-0000-4000-8000-000000000001",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-USA-0001",
    "account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "collo": [{
      "id_ldv": "TST0000000146",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": "2", "product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": "1", "product_id": "PRD-TEST-0002" }
      ]
    }]
  }]
}
```

`declaration_id` non compare perché `null` (`NON_NULL`, ORC-04). Lo stesso contenuto della spedizione
va in `enrichment_events`, in `dichiarato_events` e nell'`eventData` degli eventi di stato.

## 5. Regole funzionali

### 5.1 Cosa restituiscono le lavorazioni [FATTO, codice letto il 16-11]

| Lavorazione | Repo e ref letti | Riceve | Restituisce |
|---|---|---|---|
| `check-ldv` | `ce-dichiarato-ldv`, `origin/develop` @ `d86a491` | `TracciatoUnicoDTO` tipizzato (`ignoreUnknown`, `FAIL_ON_UNKNOWN_PROPERTIES=false`) | lo **stesso** `TracciatoUnicoDTO` riserializzato (`KafkaProducer`, `tipo_lavorazione=check-ldv`). Il suo `ArticoloDTO` ha solo `posizione`, `codice_taric`, `valore`, `quantita`, `peso_totale`, `paese_origine` |
| `ldv-pdb` | `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-ldv-pdb`, `origin/develop` @ `c8b94db` (la cartella `ce-dichiarato-ldv-pdb` non è un repo git) | `TracciatoUnicoDTO` tipizzato (`ignoreUnknown`, `NON_NULL`) | lo stesso DTO riserializzato; verso BEP una richiesta mappata (`BepRequestMapper`) |
| `ldv-bep-sync` | `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-ldv-pdb-sync`, `origin/develop` @ `e3e2157` | come sopra | come sopra; verso PDB `waybillCreate` (`PdbRequestMapper`) |
| `normalizzazione` | **codice non disponibile**: `ce-normalization-starter` è il chart di un building block Redis, non il normalizzatore (ORC-07) | — | il merge accetta solo i campi `*_normalizzato` della policy (5.3) |

Conseguenze:
- nessuna lavorazione oggi conosce i tre campi: restituisce il preavviso **intero ma senza i campi nuovi**
  (e senza ogni altro campo che non dichiara);
- anche se l'orchestratore li mandasse (P3 risolto), le lavorazioni non li ripasserebbero: la fonte
  dei campi resta **solo** il documento Mongo dell'orchestratore, e il merge deve conservarli (5.2);
- LDV e richieste BEP/PDB non portano i campi: in fase 1 non servono (AS-06), in fase 2 sì (int. 06, PA-07).

### 5.2 Merge: perché i campi non si cancellano [FATTO, `OrchestratoreMongoService`]

Il merge parte dal documento esistente e ci applica il ritorno della lavorazione, campo per campo:

1. `mergeField` **salta** i valori in ingresso `null`, stringa vuota o di soli spazi, array o oggetto
   vuoti, e i campi protetti. Un campo assente nel ritorno non tocca l'esistente. Quindi il ritorno
   di 4.2 lascia intatti `account_key` e `product_id`, **a condizione che siano nel DTO** (altrimenti
   si perdono a P4 indipendentemente dal merge).
2. `spedizione[]` si fonde per `rif_spedizione` (`mergeSpedizioneArrayByRifSpedizione`); se il ritorno
   non ha `rif_spedizione`, per posizione. Una spedizione nuova nel ritorno viene aggiunta.
3. `collo[]` e `articolo[]` si fondono **per indice** (`mergeArrays`), non per `posizione` dell'articolo
   né per `id_collo`. L'elemento i-esimo del ritorno si fonde con l'i-esimo dell'esistente; gli
   elementi in più si aggiungono in coda.
4. Un array assente nell'esistente viene copiato intero dal ritorno, **senza** applicare la policy
   (`mergeArrayField`, ramo `existingValue == null`).

`product_id` resta sul suo articolo finché le lavorazioni restituiscono `collo[]` e `articolo[]`
nello stesso ordine e numero in cui li hanno ricevuti. Le tre lavorazioni lette deserializzano e
riserializzano le liste così come sono (nessun ordinamento rilevato), ma non è garantito in tutti i
rami (andata/ritorno in `ldv-pdb`, multicollo `IS`/`IF`): rischio ORC-05.

Lo stesso indirizzamento per indice si ha a P5 (retry per conflitto di versione): il secondo merge
riparte dal documento riletto, che con i DTO aggiornati contiene i campi.

### 5.3 Protezione dei campi dalle lavorazioni [ASSUNTO ORC-02]

Oggi solo `normalizzazione` (lista `campi-inclusi`) ed `enrichment_bep` (`campi-esclusi`) hanno una
policy; `check-ldv`, `ldv-pdb`, `ldv-bep-sync` sono in **wildcard**: un loro ritorno con un valore non
vuoto **sovrascriverebbe** i campi. Oggi non succede (5.1), ma R-04 chiede che nessun servizio li
cambi. In fase 1 nessuna lavorazione è fonte dei campi, quindi:

```yaml
merge:
  policies:
    # normalizzazione: invariata (lista campi-inclusi, i campi nuovi non ci sono)
    check-ldv:
      campi-esclusi: [account_key, declaration_id, product_id]
    ldv-pdb:
      campi-esclusi: [account_key, declaration_id, product_id]
    ldv-bep-sync:
      campi-esclusi: [account_key, declaration_id, product_id]
    enrichment_bep:
      campi-esclusi:
        - mittente.indirizzo
        - destinatario.indirizzo
        - mittente.codice_nazione
        - destinatario.codice_nazione
        - account_key
        - declaration_id
        - product_id
```

- `MergePolicy.allows` confronta il percorso completo o il suffisso `.<campo>`: `product_id` copre
  `spedizione.collo.articolo.product_id` (gli indici di array non entrano nel percorso).
- Con `campi-esclusi` la policy resta wildcard per tutti gli altri campi: il comportamento attuale
  non cambia.
- I nomi delle chiavi devono essere quelli di `tipo_lavorazione` restituiti dalle lavorazioni (minuscolo,
  come in `azioni.mappings`): verificarli in `application.yaml` prima di scriverli.
- In fase 2 la lavorazione Zonos dovrà poter scrivere `declaration_id`: la sua policy si definisce allora (PA-09).
- Se ORC-02 non viene accettata, la sezione `merge` non si tocca e AC-07 si toglie.

### 5.4 Retry e ripartenze [FATTO, working tree locale; le cartelle `ce-preadvising-retry-*` non sono repo git]

| Strumento | Legge | Tipo di lettura | Ripubblica su | Beneficia della modifica? |
|---|---|---|---|---|
| `ce-preadvising-retry-099` | `dichiarato_events` | entity con `spedizione` di tipo `Object` (non tipizzata) | `preadvising.pre-enrichment` | **sì**, i campi passano così come salvati (P7) |
| `ce-preadvising-retry-normalizzazione` | `dichiarato_events` ed `enrichment_events` | `Map` | `Preadvising.enrichment.normalizzatore` | **sì** |
| `ce-preadvising-retry-id-cliente` | messaggi Kafka, non Mongo | `record.value()` grezzo | `preadvising.completed.sda` | sì: ripubblica il messaggio così com'è |
| `ce-preadvising-retry-eurodis` | `dichiarato_events` | `PreadvisingEvents` con `List<SpedizioneDTO>` propria | `preadvising.completed.poste` | **no**: il suo DTO perde i campi (ORC-08) |
| `ce-preadvising-retry-pread-completo` | `dichiarato_events` | `PreadvisingEvents` con `List<SpedizioneDTO>` propria | `preadvising.evensource` | **no**, come sopra (ORC-08) |

Ripartenze interne all'orchestratore:
- evento `validato` già presente su Mongo: `PREAD_DUPLICATO`, nessuna sovrascrittura del documento (invariato);
- conflitto di versione: un retry con rilettura (P5), coperto dai DTO.

## 6. Regole riassuntive

| ID | Regola |
|---|---|
| RO-01 | `account_key` e `declaration_id` stanno in `SpedizioneDTO`; `product_id` in `ArticoloDTO`. `String`, opzionali, senza default, senza vincoli né trasformazioni |
| RO-02 | I tre campi attraversano P1-P8 senza perdita, con la cardinalità del contratto (spedizione / articolo) |
| RO-03 | Un ritorno di lavorazione senza i campi non li cancella (merge 5.2) |
| RO-04 | Nessuna lavorazione della fase 1 li sovrascrive (policy 5.3, ORC-02) |
| RO-05 | Preavvisi senza i campi (non USA, eventi storici, documenti Mongo vecchi) si lavorano come oggi e l'uscita non ha le chiavi nuove |
| RO-06 | Nessun log del valore dei campi, nessuna metrica o attributo di span con i valori (ORC-09) |

## 7. Configurazione

| Proprietà | Default | Uso |
|---|---|---|
| `merge.policies.<lavorazione>.campi-esclusi` | sezione 5.3 | protezione dei campi (ORC-02). In `application.yaml`; se `application-test.yaml` ha una sezione `merge` propria, allinearla |

Nessuna variabile d'ambiente, nessuna modifica Helm.

## 8. Requisiti non funzionali e osservabilità

- **Prestazioni**: nessun impatto misurabile (tre stringhe in più nel documento).
- **Log**: i log esistenti non cambiano. Non aggiungere log con i valori di `account_key` o
  `product_id`: sono identificativi del cliente verso la dogana USA (ORC-09). Ammesso, se serve, un DEBUG
  con la sola presenza (`account_key=presente`, numero di articoli con `product_id`).
- **Metriche e span**: nessuna metrica nuova; nessun valore dei campi negli attributi.
- **Sonar**: nessun letterale ripetuto nei test (costanti per i valori d'esempio), nessun commento con riferimenti a PA/AS.

## 9. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato l'ingresso 4.1, dopo `insertRecord` il documento `enrichment_events` ha `account_key` sulla spedizione e i due `product_id` sui rispettivi articoli, con gli stessi valori |
| AC-02 | Dato 4.1, i messaggi di fan-out verso le lavorazioni contengono i tre campi valorizzati (non `declaration_id`, che è `null`) |
| AC-03 | Dato il documento di AC-01 e il ritorno 4.2, dopo il merge `account_key` e i due `product_id` sono invariati e `id_ldv` è stato aggiunto |
| AC-04 | Dato AC-03 per tutte le lavorazioni del canale, il messaggio su `preadvising.completed` è quello di 4.3 per i campi nuovi |
| AC-05 | Dato AC-04, `dichiarato_events` (stato 1) e l'`eventData` dell'evento `PREAD_COMPLETO` hanno gli stessi campi |
| AC-06 | Dato un ritorno con `result=KO`, `dichiarato_events` (stato 2) e l'evento `PREADVISING_PARZIALE_E_BLOCCATO` hanno i campi |
| AC-07 | (ORC-02) Dato un ritorno `check-ldv`, `ldv-pdb` o `ldv-bep-sync` con `account_key` o `product_id` diversi e non vuoti, dopo il merge restano i valori originali |
| AC-08 | Dato un `OptimisticLockingFailureException` al primo `saveMerged`, il secondo tentativo salva i campi invariati |
| AC-09 | Dato un ingresso con tre colli e articoli in ciascuno, ogni `product_id` resta sul proprio collo e sulla propria posizione dopo il merge di tutte le lavorazioni |
| AC-10 | Dato un ingresso senza i campi (spedizione non USA), documento e uscita non hanno le chiavi `account_key`, `declaration_id`, `product_id` e sono uguali a quelli di oggi |
| AC-11 | Dato un documento `enrichment_events` creato prima del rilascio (senza i campi), il merge e la pubblicazione funzionano come oggi |
| AC-12 | Dato un `account_key` di lunghezza diversa da 52 o un `product_id` di 300 caratteri, l'orchestratore li propaga identici, senza scarti né WARN di validazione |
| AC-13 | Dato `declaration_id: null` in ingresso, nessun punto lo scrive come stringa `"null"` |
| AC-14 | I test esistenti (fra cui `OrchestratoreMongoServiceMergeTest`, `OrchestratoreMapperTest`, `NuoviCampiPdwTest`) restano verdi |

## 10. Casi di test

Unitari con `ObjectMapper` reale (come `OrchestratoreMongoServiceMergeTest`) e Mongo simulato; poi test
integrato in svil con un messaggio costruito a mano su `preadvising.pre-enrichment` (AS-05).

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit | deserializzazione di 4.1 in `OrchestratoreDTO` e riserializzazione | campi presenti, valori identici | AC-01, AC-02 |
| TC-02 | unit | `toMongoEntity`, `toOutputDTOEnrichemtEvents`, `toOutputDTOPreadvisingEvents` | campi presenti in tutti e tre | AC-01, AC-04, AC-05 |
| TC-03 | unit (merge) | esistente con campi + ritorno 4.2 per `check-ldv`, `ldv-pdb`, `ldv-bep-sync`, `normalizzazione` | campi invariati | AC-03 |
| TC-04 | unit (merge) | ritorno con valori diversi dei campi, una lavorazione per volta | con ORC-02 valori originali; senza, valori del ritorno (comportamento da documentare) | AC-07 |
| TC-05 | unit (merge) | 3 colli × 2 articoli, ritorno con le stesse liste senza i campi | ogni `product_id` al suo posto | AC-09 |
| TC-06 | unit (service) | flusso completo con mock di Kafka: `validato`, poi tutti i ritorni | payload su `preadvising.completed` come 4.3 | AC-04 |
| TC-07 | unit (service) | conflitto di versione simulato al primo `saveMerged` | secondo salvataggio con i campi | AC-08 |
| TC-08 | unit | ritorno `result=KO` | `PreadvisingEvents` stato 2 con i campi | AC-06 |
| TC-09 | unit | ingresso senza campi; documento esistente senza campi | nessuna chiave nuova in uscita | AC-10, AC-11 |
| TC-10 | unit | lunghezze fuori regola, `declaration_id` `null` | propagazione identica, nessuna violazione | AC-12, AC-13 |
| TC-11 | regressione | suite esistente | verde | AC-14 |
| TC-12 | integrato svil | preavviso USA con 2 articoli su un canale PDB e su un canale SDA | campi su `preadvising.completed` e su `dichiarato_events` | AC-04, AC-05 |

Caso da annotare per la caratterizzazione (ORC-05): ritorno con gli articoli in ordine diverso. Oggi i
campi degli articoli si mescolano per indice; il test documenta il comportamento, non lo cambia.

## 11. Assunzioni e domande aperte

Dal contratto della fase 1 (`analisi.md`, vincolanti): AS-01 nomi e posizione, AS-05 ingresso con i nomi
di AS-01, AS-06 Zonos, BEP, palmari fuori fase 1.

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| ORC-01 | I tre campi vanno solo in `SpedizioneDTO` e `ArticoloDTO`: radice del messaggio, `OrchestratoreDTO` e documenti Mongo non cambiano perché riusano `SpedizioneDTO` | come detto | — |
| ORC-02 | **Protezione dal merge**: in fase 1 nessuna lavorazione può scrivere i tre campi (`campi-esclusi` per `check-ldv`, `ldv-pdb`, `ldv-bep-sync`, `enrichment_bep`). È un'estensione di R-04, non chiesta in modo esplicito dall'HLD | adottata, solo configurazione | Diego |
| ORC-03 | Nessun vincolo Bean Validation sui campi nell'orchestratore: la regola di lunghezza è del validatore | nessun vincolo | — |
| ORC-04 | Con `NON_NULL` un `declaration_id` `null` non compare in uscita né su Mongo. AS-01 ammette "assente o `null`" | chiave assente | Diego |
| ORC-05 | **Rischio merge per indice**: `collo[]` e `articolo[]` si fondono per posizione nella lista, non per `posizione` dell'articolo. Se una lavorazione restituisce gli articoli riordinati, filtrati o un collo in meno, `product_id` resta sull'indice e i dati dell'articolo si mescolano. Nel codice letto non succede, ma non è un vincolo dichiarato delle lavorazioni (rami andata/ritorno di `ldv-pdb`, multicollo `IS`/`IF` non verificati in dettaglio) | nessuna modifica del merge; test di caratterizzazione | Diego, team delle lavorazioni |
| ORC-06 | **Le lavorazioni non passano i campi**: `ce-dichiarato-ldv`, `-ldv-pdb`, `-ldv-pdb-sync` hanno DTO tipizzati con `ignoreUnknown` e restituiscono il tracciato senza i campi. Per la fase 1 basta il merge; la descrizione però chiede a `ce-dichiarato-ldv` di "mantenere i campi nell'associazione della LDV" e la fase 2 (int. 06) li vuole verso BEP. Chi aggiorna i DTO delle lavorazioni e quando? (si collega a PA-10) | in fase 1 nessuna modifica alle lavorazioni | Diego / Poste |
| ORC-07 | **Normalizzatore**: il codice non è fra i repo locali (`ce-normalization-starter` è un chart Redis). La policy `campi-inclusi` lo rende innocuo per i campi nuovi qualunque cosa restituisca. Serve il repo per confermare | nessuna modifica | Diego |
| ORC-08 | **Retry `eurodis` e `pread-completo`** leggono `dichiarato_events` con un `SpedizioneDTO` proprio: ripubblicherebbero senza i campi. Sono strumenti locali, non servizi in catena | da aggiornare solo se si usano su preavvisi USA | Diego |
| ORC-09 | Valori dei campi mai nei log, metriche, span: trattati come identificativi del cliente | come detto | — |
| ORC-10 | Il `git fetch` del 16-11 è fallito: i riferimenti sono a `origin/develop` @ `14b0dd6` | ricontrollare dopo il fetch | sviluppatrice |

## 12. Riferimenti

- [analisi.md](../analisi.md), "Contratto della fase 1" e tabella degli interventi.
- [ce-dichiarato-smistatore.md](ce-dichiarato-smistatore.md): propagazione a valle di `preadvising.completed`.
- [contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md](../../../contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md): §6.5 DTO, §16 flussi.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md), [contesto/linee-guida-sviluppo.md](../../../contesto/linee-guida-sviluppo.md).
