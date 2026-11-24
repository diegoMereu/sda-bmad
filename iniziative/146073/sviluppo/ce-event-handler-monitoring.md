# `ce-event-handler-monitoring` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del monitoring (Amelia) e test manager
**Intervento HLD**: 04 della fase 1 ("Adeguamento ce-dichiarato-monitoring, event store, bff"), stima TOW 1.2 di 0,40 per i tre servizi insieme; nel foglio Impatti "Adeguamento ce-dichiarato-monitoring", impatto M50
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-event-handler-monitoring` (in locale `gitposte/SDA/preadvising/ce-event-handler-monitoring`)
**Branch**: `develop` [DECISO, Diego 2026-11-24, sostituisce il branch dedicato del 16-11], **solo se
emerge una modifica**: nella variante di default (A, sezione 3) non ne serve nessuna. `origin/develop`
= `origin/master`, tag `26.09.26` (16-11). Non si sviluppa su `master` né sui branch di altre
iniziative (es. `develop_pdb`).
**Codice letto**: `origin/develop` @ `9dce7cf` (2026-10-19), con `git show`, senza checkout. Il
`git fetch` del 16-11 è fallito (connessione rifiutata da GitLab): prima di iniziare va rifatto. La
copia locale ha una modifica non committata di altri a `deploy-config/values_TEMPLATE.yaml` e le
cartelle non versionate `icd/` e `console di monitoraggio/`: il codice non le considera; le ICD di
`icd/` sono usate come fonte.
**Stack**: Spring Boot 3.5.7, Java 17, Spring Kafka, Spring Data MongoDB
**Generato da**: [prompt-ce-event-handler-monitoring.md](prompt-ce-event-handler-monitoring.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" (AS-01…AS-06, **vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (int. 04, foglio Impatti);
`ce-event-handler-monitoring/icd/ICD_preadvising_eventsource.md`; [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md)
(codici 1320…1323 e forma delle descrizioni)

Etichette:
- **[FATTO]**: scritto nell'HLD, nell'ICD o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare il lavoro, con ID e default (sezione 10).

> **Verdetto: nessuna modifica di codice nella variante di default (A).** Il monitoring legge
> l'evento in un DTO tipizzato, ma ne usa solo identificativi, stato, cliente ed errori: i campi
> nuovi non servono a nulla di ciò che produce, e gli errori nuovi del validatore passano già. Resta
> **verifica e test di non regressione**. Se Poste vuole i campi sul topic di cambio stato
> (MON-01) si applica la variante B, una modifica piccola descritta in 3.4.

---

## 1. Contesto e obiettivo

`ce-event-handler-monitoring` consuma `preadvising.evensource` (gruppo `ce-event-handler-monitoring-group`)
e trasforma ogni evento di stato in un messaggio per la console di monitoraggio sul topic
`PRE-ADV.MONITORAGGIO-CAMBIO-STATO` [FATTO, values e `application.yaml`]. Registra anche metriche
di stato per Datadog.

La fase 1 aggiunge al preavviso `zonos_account_key`, `zonos_declaration_id` (testata di `spedizione[]`) e
`zonos_product_id` (ogni `spedizione[].collo[].articolo[]`) (AS-01), e quattro errori di validazione nuovi
(AS-03, codici `1320`…`1323` proposti dal validatore). L'HLD chiede di "ricevere e propagare i nuovi
campi sul topic" [FATTO, HLD int. 04].

Obiettivo del documento: dire che cosa il monitoring fa oggi con questi dati, perché non serve
modificarlo, quali errori nuovi arrivano alla console e come, e che cosa cambierebbe se Poste
volesse i campi sul topic di cambio stato.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Mettere i campi nell'evento su `preadvising.evensource` | validatore, orchestratore, smistatore (int. 01-03) |
| Salvare l'evento | `ce-event-handler-event-store` ([ce-event-handler-event-store.md](ce-event-handler-event-store.md)) |
| Mostrare i dati nella console di monitoraggio | sistema consumatore di `PRE-ADV.MONITORAGGIO-CAMBIO-STATO` (M50?), non nostro |

## 2. Interventi HLD coperti

| HLD | Testo | Copertura |
|---|---|---|
| Fase 1, int. 04 | il ms riceve e propaga i nuovi campi sul topic | ricezione: già garantita (3.2). Propagazione: il contratto di `PRE-ADV.MONITORAGGIO-CAMBIO-STATO` non ha dati di spedizione né di articolo; default A senza campi nuovi, variante B se Poste la chiede (MON-01) |
| Fase 1, int. 04 (implicito) | gli scarti nuovi arrivano alla console | già garantito (4.2) |

## 3. Dove si interviene nel codice

Codice di `origin/develop` @ `9dce7cf` [FATTO, letto il 16-11].

### 3.1 Il percorso di un evento

| Punto | Cosa fa |
|---|---|
| `consumer/KafkaConsumer.consumeEvent` | `@KafkaListener` su `${kafka.consumer.topic.event-store-topic}` = `preadvising.evensource`; lavorazione asincrona su executor |
| `service/MonitoringService.handleEvent` | `readValue(..., EventStoreDTO.class)` (`eventData` `Object`); smista per `aggregateType`: `LDV`/`COLLO` → `gestisciLDV`, `FILE` → `gestisciFile` |
| `MonitoringService.gestisciLDV` | `objectMapper.convertValue(eventData, DichiaratoDTO.class)`, metriche (`registraMetricheRecord`, `recordStateMetric`), filtro per canale (`MonitoringFiltroProperties`), poi `MacchinaStatiService.mapToMonitoraggio` e invio su `PRE-ADV.MONITORAGGIO-CAMBIO-STATO` |
| `service/MacchinaStatiService.mapToMonitoraggio` | un `Record` **per collo** con: `idFile`, `idRecord`, `identificativoCollo`, `codiceLdv`, `rifSpedizione`, `idStato`, `stato`, `dataStato`, `codiceCliente`, `codiceLoginCliente`, `canale`, `errore[]`, `esito`, `numeroColli`, `flagAutoproduttore`, `partitaIVA`, `ragioneSociale` |
| `MacchinaStatiService.getErrore` | da ogni voce di `errori` un `Errore`: `codiceErrore` = chiave, `nomeCampoInErrore` = testo prima del **primo** `:`, `descrizioneErrore` = il resto, `ownerErrore` `CLIENTE`, `tipologiaErrore` `BLOCCANTE` |
| `config/AppConfig.objectMapper` | `FAIL_ON_UNKNOWN_PROPERTIES = false` |

### 3.2 Perché i campi nuovi non danno problemi [FATTO]

- `DichiaratoDTO`, `SpedizioneDTO`, `ColloDTO`, `ArticoloDTO` del monitoring non hanno i campi nuovi.
  Con `FAIL_ON_UNKNOWN_PROPERTIES = false`, `convertValue` li **ignora** senza errori.
- Nessuna parte del messaggio in uscita né delle metriche usa dati della testata di spedizione
  diversi da `rif_spedizione` e `numero_colli`, né dati degli articoli. Perdere i campi nuovi nella
  conversione non cambia nulla di ciò che il servizio produce.
- Gli eventi storici e quelli non USA non hanno i campi: stesso trattamento di oggi.
- `Validator` è iniettato ma non usato: le annotazioni `@Size` e `@Digits` dei DTO non scattano.

### 3.3 Variante A (default): nessuna modifica

Nessun file cambia. Si verifica con i test della sezione 9 che:
- gli eventi della fase 1 (con i campi) producono gli stessi `Record` di oggi;
- gli scarti con i codici nuovi arrivano alla console come in 4.2.

### 3.4 Variante B (solo se Poste la chiede, MON-01): i campi sul topic di cambio stato

| Punto | Cosa si fa |
|---|---|
| `dto/SpedizioneDTO` | `zonos_account_key`, `zonos_declaration_id` (`String`, nessuna validazione), stesso stile snake_case dei campi esistenti |
| `dto/ArticoloDTO` | `zonos_product_id` (`String`) |
| `dto/producerDTO/Record` | `zonosAccountKey`, `zonosDeclarationId` (`String`) e `articoli` (`List<ArticoloMonitoraggio>` con `posizione`, `zonosProductId`), stile camelCase dei campi del `Record`. Il `Record` è per collo: gli articoli sono quelli del collo |
| `MacchinaStatiService.mapToMonitoraggio` | valorizza i tre campi da `sped` e `collo`, senza trasformazioni (R-04); con i campi assenti restano `null` / lista vuota |
| ICD della console | nuova versione, da Poste |

Stima indicativa: tre campi in tre DTO, un metodo di mapping, test unitari in
`MacchinaStatiServiceTest`. La forma esatta del `Record` la decide l'ICD della console: quella sopra
è una proposta.

## 4. Regole

### 4.1 Regole generali

| ID | Regola |
|---|---|
| RM-01 | Gli eventi con i campi nuovi producono su `PRE-ADV.MONITORAGGIO-CAMBIO-STATO` gli stessi `Record` di un evento equivalente senza i campi (variante A) |
| RM-02 | Gli eventi storici, non USA e `FILE` si trattano come oggi |
| RM-03 | Nessuna validazione dei campi nuovi (R-02) |
| RM-04 | Nessun cambio a topic, gruppo consumer, filtri, metriche |

### 4.2 Errori nuovi verso la console [FATTO, codice; codici dal validatore]

L'evento di scarto `ST_R0006` porta `eventData.errori`. Ogni voce diventa un `Errore` di ogni
`Record` (cioè di ogni collo) della spedizione, con `esito` `KO`:

| `errori` (chiave: valore) | `codiceErrore` | `nomeCampoInErrore` | `descrizioneErrore` |
|---|---|---|---|
| `1320: zonos_account_key: Campo obbligatorio mancante` | `1320` | `zonos_account_key` | `Campo obbligatorio mancante` |
| `1321: zonos_account_key: lunghezza non valida (attesi 52 caratteri)` | `1321` | `zonos_account_key` | `lunghezza non valida (attesi 52 caratteri)` |
| `1322: zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2)` | `1322` | `zonos_product_id` | `Campo obbligatorio mancante (collo 1 articolo 2)` |
| `1323: zonos_product_id: lunghezza non valida, attesi 1-255 caratteri (collo 2 articolo 1)` | `1323` | `zonos_product_id` | `lunghezza non valida, attesi 1-255 caratteri (collo 2 articolo 1)` |
| `1322: zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 1; collo 2 articolo 3)` | `1322` | `zonos_product_id` | `Campo obbligatorio mancante (collo 1 articolo 1; collo 2 articolo 3)` |

Il taglio al primo `:` è il comportamento di oggi e non cambia. Le descrizioni del validatore
(AS-03) mettono il nome del campo prima dei due punti e le occorrenze (collo e articolo) fra
parentesi: il "campo in errore" è quindi `zonos_product_id` e la descrizione le contiene tutte (MON-02). Inoltre ogni collo riceve tutti gli errori della
spedizione, anche quelli di un altro collo: è il comportamento attuale per tutti gli errori.

## 5. Esempi [dati inventati]

### 5.1 `ST_R0004` di una spedizione USA, un collo, due articoli

Ingresso (ridotto): l'evento 5.1 di [ce-event-handler-event-store.md](ce-event-handler-event-store.md),
con in più `id_file` e `cliente`: `aggregateType` `ldv`, `canale` `PDB_INVIOFILE`, `zonos_account_key` di
52 caratteri, due `zonos_product_id`.

Uscita su `PRE-ADV.MONITORAGGIO-CAMBIO-STATO`, variante A (identica a oggi):

```json
{
  "filePreAdvising": null,
  "recordList": [{
    "idFile": "99TESTFILE00001",
    "idRecord": "99TESTPREADV0001",
    "identificativoCollo": "99COLLO0001",
    "codiceLdv": null,
    "rifSpedizione": "99RIF-USA-0001",
    "idStato": "ST_R0004",
    "stato": "PREAD_COMPLETO",
    "dataStato": "2026-11-16T11:00:00+01:00",
    "codiceCliente": "99CLI0000001",
    "canale": "PDB_INVIOFILE",
    "errore": null,
    "esito": "OK",
    "numeroColli": 1
  }]
}
```

(Ridotto: i campi omessi, come `codiceLoginCliente`, seguono le regole attuali. L'esempio mostra
solo che non compare nessun campo nuovo.)

Variante B: lo stesso `Record` con in più `"zonosAccountKey": "TESTACCOUNTKEY…0001"`,
`"zonosDeclarationId": null`, `"articoli": [{"posizione": "1", "zonosProductId": "PRD-TEST-0001"}, {"posizione": "2", "zonosProductId": "PRD-TEST-0002"}]`.

### 5.2 Scarto `ST_R0006` con Account Key corta e Product ID mancante

`errori` = `{"1321": "zonos_account_key: lunghezza non valida (attesi 52 caratteri)", "1322": "zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2)"}`.

Uscita: un `Record` con `esito` `KO` e due `errore` come nelle righe 2 e 3 della tabella 4.2.

## 6. Configurazione

Variante A: nessuna proprietà nuova, nessun cambio ai values. Variante B: nessuna proprietà nuova.

## 7. Requisiti non funzionali e osservabilità

- Volumi e tempi invariati.
- **Log** [FATTO]: `KafkaConsumer` scrive in INFO l'intero evento ricevuto e `gestisciLDV` l'intero
  payload in uscita; `gestisciErroreTecnico` scrive il payload in ERROR. Con la fase 1 nei log va
  anche `zonos_account_key` (e in variante B anche nel payload in uscita). Oggi ci vanno già P.IVA e
  ragione sociale: problema esistente, fuori iniziativa. Se l'Account Key è riservata serve
  mascherarla (MON-03, come EVS-03).
- Metriche invariate: i codici nuovi compaiono nelle metriche di stato esistenti senza tag nuovi.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato l'evento 5.1, il messaggio su `PRE-ADV.MONITORAGGIO-CAMBIO-STATO` è uguale, campo per campo, a quello di un evento identico senza i tre campi |
| AC-02 | Dato un evento con `zonos_account_key` di 52 caratteri, `zonos_declaration_id: null` e `zonos_product_id` di 255 caratteri, non ci sono eccezioni né incrementi di `business_monitoring_error_total` |
| AC-03 | Dato l'evento 5.2, il `Record` ha `esito` `KO` e gli `Errore` della tabella 4.2 (codice, campo, descrizione, `CLIENTE`, `BLOCCANTE`) |
| AC-04 | Dato uno scarto con `1322` su più articoli (descrizioni concatenate con `"; "`), `nomeCampoInErrore` è `zonos_product_id` e `descrizioneErrore` contiene tutte le occorrenze (collo e articolo), senza eccezioni |
| AC-05 | Dato uno scarto `1322` su una spedizione con due colli, entrambi i `Record` hanno l'errore |
| AC-06 | Eventi non USA, `FILE` e storici producono gli stessi messaggi di prima (test esistenti verdi) |
| AC-07 | Variante A: nessuna modifica a codice e values (diff vuoto). Variante B: AC-08…AC-10 |
| AC-08 | (B) Dato l'evento 5.1, il `Record` ha `zonosAccountKey` uguale all'ingresso, `zonosDeclarationId` `null`, `articoli` con i due `zonosProductId` nell'ordine di ingresso |
| AC-09 | (B) Dato un evento con due colli, ogni `Record` ha solo gli articoli del proprio collo |
| AC-10 | (B) Dato un evento senza i campi, `zonosAccountKey` e `zonosDeclarationId` sono `null` e `articoli` è vuota; il resto del `Record` è invariato |

## 9. Casi di test

I test esistenti (`MacchinaStatiServiceTest`, 16 test; `MonitoringServiceTest`, 3 test) sono la base
di regressione. In variante A non si aggiungono test al repo; si verifica in svil (regole di
[test-integrati.md](../../../contesto/test-integrati.md): consumer in sola lettura su
`PRE-ADV.MONITORAGGIO-CAMBIO-STATO` senza group id o con un group id nuovo, chiavi `99`).

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | integrato svil | evento 5.1 su `preadvising.evensource`, e lo stesso senza i campi | due messaggi in uscita uguali (a parte gli identificativi) | AC-01 |
| TC-02 | integrato svil | campi alle lunghezze massime, `zonos_declaration_id: null` | nessun errore, metriche di errore ferme | AC-02 |
| TC-03 | integrato svil | evento 5.2 | `Record` KO con gli `Errore` di 4.2 | AC-03 |
| TC-04 | integrato svil | scarto `1322` concatenato, due colli | AC-04 e AC-05 | AC-04, AC-05 |
| TC-05 | regressione | `mvn -o test` su `origin/develop` | 19 test verdi | AC-06 |
| TC-06 | integrato svil, catena | preavviso USA da `preadvising.pre-enrichment` (AS-05), valido e con Account Key mancante, dopo i rilasci di validatore, orchestratore e smistatore | stati `ST_R0002`/`ST_R0004` e scarto `ST_R0006` arrivano alla console | AC-01, AC-03 |
| TC-07 | unit, solo variante B | `MacchinaStatiServiceTest`: 1 collo 2 articoli; 2 colli; nessun campo | AC-08…AC-10 | AC-08…AC-10 |

## 10. Assunzioni e domande aperte

Valgono AS-01…AS-06 di [analisi.md](../analisi.md). Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| MON-01 | L'HLD dice "propagazione dei nuovi campi sul topic" e il foglio Impatti cita il monitoring con impatto M50. Il topic del monitoring è `PRE-ADV.MONITORAGGIO-CAMBIO-STATO`, verso la console, e il suo contratto non ha dati di spedizione né di articolo. Il contratto della fase 1 (AS-01…AS-06) non lo cita. La console deve ricevere Account Key, Product ID e Declaration ID? Che cos'è M50? | variante A: nessun campo nuovo sul topic. Se sì, variante B (3.4) con nuova versione dell'ICD della console | Poste |
| MON-02 | [DECISO 2026-11-16, testi decisi da Diego il 23-11] Le descrizioni del validatore (AS-03) mettono il nome del campo prima dei due punti: `zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2; collo 2 articolo 3)`. La console mostra quindi `zonos_product_id` come campo in errore e tutte le occorrenze nella descrizione | nessuna modifica al monitoring | — |
| MON-03 | L'Account Key è un dato riservato? Il servizio logga l'evento intero | non riservata: nessuna modifica | Poste |
| MON-04 | La stima di 0,40 dell'int. 04 copre tre servizi | quota monitoring = test di non regressione (A); la variante B non è stimata nell'HLD come modifica di DTO | Diego |

## 11. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1.
- [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md): codici e descrizioni degli errori.
- [ce-event-handler-event-store.md](ce-event-handler-event-store.md), [ce-dichiarato-bff.md](ce-dichiarato-bff.md).
- ICD: `ce-event-handler-monitoring/icd/ICD_preadvising_eventsource.md` (§6, §7.4), `ICD_Event_Store (2).xlsx`.
