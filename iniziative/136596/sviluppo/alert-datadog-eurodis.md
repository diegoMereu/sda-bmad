# Alert Datadog della catena EURODIS (AS-19)

**Iniziativa**: 136596 — Eurodis autoproduttore · **Versione**: 0.1 (proposta) · **Data**: 2026-11-10
**Autore**: Winston (architect) · **Destinatari**: chi configura i monitor in Datadog, team di sviluppo
**Servizi**: `ce-dichiarato-eurodis-in`, `ce-dichiarato-eurodis-mapper`, `ce-eurodis-send-tracking`

## 1. Come leggere questo documento

- I nomi delle metriche e dei tag sono **verificati nel codice** su `develop`, il 10-11:
  - `-in` al commit `c60e508`, classe `MetricheEurodisIn`;
  - mapper al commit `5b84993`, classe `MetricheMapper`;
  - send-tracking al commit `ec2f65b` (12-11), classe `MetricheSendTracking`.
- Ogni metrica ha il tag comune `service`, uguale al nome del servizio (`MetricsConfig`).
- Le metriche sono esposte su `/actuator/prometheus` (porta 8091) e raccolte dalla componente di piattaforma `otel-for-metrics-app` (`observability.metrics` del chart).
- **Il nome esatto in Datadog dipende da quella pipeline.** Un counter Prometheus `x_total` può comparire come `x_total` oppure come `x.count`. Prima di creare i monitor va verificato in Metrics Explorer, con `eurodis_in_chiamata_total` come esempio. Le query qui sotto usano il nome Prometheus.
- **Tag con caratteri speciali**: Datadog normalizza i valori di tag. Per esempio `campo:collo[].id_ldv` può diventare `collo__.id_ldv`: verificarlo come sopra.
- **Soglie**: i valori proposti tengono conto della frequenza:
  - scarico ed elaborazione ogni 2 minuti in svil e coll, ogni 10 minuti in produzione;
  - le finestre legate al ciclo sono indicate per produzione (P) e per gli altri ambienti (S).
- **Gravità**:
  - **critico**: possibile perdita di spedizioni, intervento subito;
  - **alto**: il flusso è fermo o rotto, intervento in giornata;
  - **medio**: dati o casi da analizzare.
- Tutti i monitor filtrano per `env` (`svil`, `coll`, `prod`) e notificano il canale del team.

## 2. `ce-dichiarato-eurodis-in`

Filtro comune: `{service:ce-dichiarato-eurodis-in,env:<env>}`.

| ID | Nome | Query | Soglia / finestra | Gravità | Runbook |
|---|---|---|---|---|---|
| IN-01 | EURODIS: chiamata fallita senza risposta | `sum(last_10m):sum:eurodis_in_chiamata_total{…,esito:errore}.as_count()` | > 0 | critico | Timeout o connessione caduta su `/shipments/v1`: le spedizioni potrebbero essere già state consegnate da EURODIS (I1). Chiedere a EURODIS di rimetterle nella richiesta successiva, oppure recuperarle con `EURODIS_RECUPERO_ED_REFERENCES` (60 giorni) |
| IN-02 | EURODIS: chiave o partner non validi | `sum(last_10m):sum:eurodis_in_chiamata_total{…,esito:401 OR esito:424 OR esito:451}.as_count()` | > 0 | alto | Verificare il secret `api-key`; per `424`/`451` la configurazione del partner presso EURODIS (Chiapponi). Nessuna spedizione persa |
| IN-03 | EURODIS: errore del server | `sum(last_30m):sum:eurodis_in_chiamata_total{…,esito:500}.as_count()` | ≥ 2 | medio | EURODIS restituisce `500`. Il run successivo riprova da solo; se continua, avvisare EURODIS |
| IN-04 | Scarico fermo | `sum(last_30m):sum:eurodis_in_scarico_total{…}.as_count()` (P), `last_10m` (S) | < 1, più l'opzione "notify if no data" | alto | Nessun run di scarico concluso: pod giù, lock ShedLock bloccato (tabella `shedlock`) o `EURODIS_IN_ABILITATO=false`. Controllare pod e log |
| IN-05 | Salvataggio del grezzo fallito | `sum(last_10m):sum:eurodis_in_grezzo_salvataggio_ko_total{…}.as_count()` | > 0 | critico | Il database non ha preso la risposta EURODIS. Verificare che il buffer locale l'abbia scritta (IN-06): il job di recupero la salverà. Altrimenti usare gli `edReference` del log CRITICO |
| IN-06 | Buffer locale: scrittura fallita | `sum(last_10m):sum:eurodis_in_buffer_scrittura_total{…,esito:ko}.as_count()` | > 0 | critico | Il file di sicurezza del grezzo non è stato scritto (volume pieno o permessi). Controllare `EURODIS_BUFFER_DIR` e lo spazio del volume |
| IN-07 | Buffer locale: file scartati | `sum(last_1h):sum:eurodis_in_buffer_recuperati_total{…,esito:scartato}.as_count()` | > 0 | critico | Un file del buffer era illeggibile ed è stato spostato in `scartati/`. Analizzarlo a mano e recuperare le spedizioni da EURODIS |
| IN-08 | Buffer locale: file in attesa da troppo | `min(last_10m):max:eurodis_in_buffer_eta_file_piu_vecchio_seconds{…}` | > 600 | alto | C'è un file non ancora salvato a database da più di 10 minuti: database giù o recupero in errore. Controllare PostgreSQL e lo span `eurodis.buffer.recupero` |
| IN-09 | Buffer locale: spazio in attesa alto | `avg(last_15m):max:eurodis_in_buffer_byte_pendenti{…}` | > 400 MB (soglia applicativa `EURODIS_BUFFER_SOGLIA_BYTE` 500 MB) | medio | Il buffer cresce: database lento o giù a lungo. Intervenire prima che il volume si riempia |
| IN-10 | Spedizioni in attesa di invio | `min(last_30m):max:eurodis_in_spedizioni_in_attesa{…}` | > 0 | medio | Record `DA_INVIARE` o `ERRORE_INVIO` fermi: Kafka giù o invii in errore. Ripartono da soli (ripubblicazione); dopo 10 tentativi serve `EURODIS_RIPUBBLICA_ED_REFERENCES` |
| IN-11 | Elaborazione senza invii | `sum(last_30m):sum:eurodis_in_elaborazione_total{…,stato:NESSUN_INVIO}.as_count()` | > 0 | alto | Uno scarico non ha inviato nessuna spedizione su `preadvising.eud.pre.build`. Controllare Kafka e i permessi dell'utente SCRAM |
| IN-12 | Spedizioni non identificabili | `sum(last_1h):sum:eurodis_in_spedizioni_non_identificabili_total{…}.as_count()` | > 0 | medio | Spedizione senza `edReference` valido, mai inviata: il JSON è in `eurodis_spedizioni`. Segnalarla a EURODIS |
| IN-13 | Eventi di stato del file non inviati | `sum(last_15m):sum:eurodis_in_evento_total{…,esito:ko}.as_count()` | > 0 | alto | `ST_F0002`/`ST_F0005` non pubblicati su `preadvising.evensource`, quindi lo scarico resta `DA_ELABORARE` e nessuna spedizione parte (RF-21). Controllare topic e permessi |
| IN-14 | Risposta EURODIS molto grande | `sum(last_1h):sum:eurodis_in_risposta_oltre_soglia_total{…}.as_count()` | > 0 | medio | Risposta oltre la soglia di guardia (100 MB). Verificare durata e memoria; segnalarla a EURODIS (nessun limite dichiarato) |

## 3. `ce-dichiarato-eurodis-mapper`

Filtro comune: `{service:ce-dichiarato-eurodis-mapper,env:<env>}`.

| ID | Nome | Query | Soglia / finestra | Gravità | Runbook |
|---|---|---|---|---|---|
| MAP-01 | Messaggi illeggibili | `sum(last_15m):sum:eurodis_mapper_spedizioni_total{…,esito:non_mappabile,motivo:json OR motivo:ed_reference}.as_count()` | > 0 | alto | Corpo non JSON o `edReference` non intero: problema del contratto con `-in`. Il messaggio è nella DLT, se configurata (`MAPPER_DLT_TOPIC`), altrimenti nel log |
| MAP-02 | Spedizioni senza destinatario | `sum(last_1h):sum:eurodis_mapper_spedizioni_total{…,esito:non_mappabile,motivo:destinatario_assente}.as_count()` | > 0 | medio | EURODIS ha mandato una spedizione senza `consigneeAddress`, o senza cap o località (RF-14): non pubblicata. Segnalarla a EURODIS e ripubblicarla da `-in` dopo la correzione |
| MAP-03 | Errori tecnici | `sum(last_10m):sum:eurodis_mapper_spedizioni_total{…,esito:errore_tecnico}.as_count()` | > 0 | alto | `preadvising.pre-enrichment` non raggiungibile o errore inatteso, dopo 3 tentativi. Controllare Kafka; i messaggi sono nella DLT o da ripubblicare da `-in` |
| MAP-04 | `ce-anagrafica` non risponde | `sum(last_15m):sum:eurodis_mapper_avvisi_total{…,motivo:anagrafica_ko}.as_count()` | ≥ 3 | medio | I codici nazione ISO3/ISO4 sono pubblicati vuoti (RF-15) e PDB potrebbe rifiutare. Controllare `ce-anagrafica` (`ANAGRAFICA_URL`) |
| MAP-05 | LDV del collo mancante | `sum(last_1h):sum:eurodis_mapper_campo_mancante_total{…,campo:collo[].id_ldv}.as_count()` | > 0 | medio | `deliveryPartnerBarcode` assente: la LDV del collo arriva vuota a valle. Chiedere conferma a EURODIS (CLS) |
| MAP-06 | Data di spedizione di ripiego | `sum(last_1h):sum:eurodis_mapper_avvisi_total{…,motivo:fallback_data}.as_count()` | > 0 | medio | `entranceTimestamp` assente: usato `clearanceTimestamp` (DF-01). Informativo finché DF-01 è aperto |
| MAP-07 | Header di `-in` mancanti | `sum(last_1h):sum:eurodis_mapper_avvisi_total{…,motivo:header_mancante}.as_count()` | > 0 | medio | Senza `idFile`/`ricevutoIl`/`rifGrezzo` il tracciato non è collegato al file fittizio. Controllare la versione di `-in` in esercizio |

## 4. `ce-eurodis-send-tracking`

Filtro comune: `{service:ce-eurodis-send-tracking,env:<env>}`.

Flusso dal 12-11 (Diego): consumer di `PACCHI.TRACKING` → filtro sullo status abilitato → filtro
applicativo (opzionale, default spento) → LDV di una spedizione `EUD_INVIOSYSTEM` su Mongo
`dichiarato_events` con cache → invio diretto a EURODIS. **Nessuno storico**: un errore temporaneo o
di configurazione non conferma l'offset e il consumer riprova con backoff; oltre la durata massima
(default 24 ore) l'evento si abbandona. Quindi un consumer fermo sui retry si vede come **lag** e come
`retry_total` in crescita.

**Metriche** (verificate nel codice, `ec2f65b`):

| Metrica | Tipo | Tag | Significato |
|---|---|---|---|
| `eurodis_tracking_tracce_lette_total` | counter | — | eventi letti da `PACCHI.TRACKING` |
| `eurodis_tracking_tracce_total` | counter | `esito` | esito per evento: `evento_non_valido`, `status_non_abilitato`, `applicativo`, `ldv_non_eurodis`, `acceptor_name_mancante`, `invio_disabilitato`, `inviato`, `rifiutato` |
| `eurodis_tracking_scartati_total` | counter | `filtro` | solo gli scarti, stessi valori di `esito` esclusi `inviato` e `rifiutato` |
| `eurodis_tracking_stato_non_mappato_total` | counter | `status` | status SDA non presente in tabella (in `PACCHI.TRACKING` sono la maggioranza, per esempio `THE`): **informativa, non da alert** |
| `eurodis_tracking_cache_ldv_total` | counter | `esito` (`hit_trovata`, `hit_non_trovata`, `miss`) | cache del filtro 3 |
| `eurodis_tracking_mongo_ricerca_durata` | timer | `esito` (`trovata`, `non_trovata`, `errore`) | durata della ricerca su Mongo (solo i miss di cache) |
| `eurodis_tracking_mongo_errori_total` | counter | — | ricerche Mongo fallite (il consumer riprova) |
| `eurodis_tracking_retry_total` | counter | `esito` (`errore_temporaneo`, `errore_configurazione`) | invii a EURODIS da ripetere |
| `eurodis_tracking_tracce_abbandonate_total` | counter | — | eventi abbandonati dopo la durata massima dei tentativi |
| `eurodis_tracking_chiamata_total` / `_durata` | counter / timer | `endpoint`, `esito` (codice HTTP o `io`) | chiamate a EURODIS (client) |
| `eurodis_tracking_eventi_total` | counter | `livello`, `esito` (`CREATO`, `RIFIUTATO`, `ERRORE_CONFIGURAZIONE`, `ERRORE_TEMPORANEO`) | esiti degli eventi inviati (client) |
| `eurodis_tracking_errori_eurodis_total`, `_warning_total` | counter | `codice` | codici di errore e warning EURODIS |
| `eurodis_tracking_acceptor_name_mancante_total` | counter | `codice` | `1100` senza nome di chi ritira |
| `kafka_consumer_fetch_manager_records_lag_max` | gauge | `client_id`, `topic` | lag del consumer (metriche Kafka collegate da Spring Boot a Micrometer): da verificare il nome in Datadog |

**Span**: `eurodis.tracking.traccia` (CONSUMER, uno per evento, figlio del `traceparent` se presente;
attributi `status_sda`, `ldv` mascherata, `codice_eurodis`, `esito`, partizione e offset),
`eurodis.tracking.lookup_ldv` (CLIENT, solo i miss di cache; attributi `esito`, `cache`),
`eurodis.send-tracking parcel` (CLIENT, chiamata EURODIS; `http.status_code`, numero di eventi, creati,
rifiutati). Nei log JSON gli stessi identificativi sono nell'MDC (`traceId`, `spanId`, `ldv`,
`status_sda`, `codice_eurodis`, `esito`).

| ID | Nome | Query | Soglia / finestra | Gravità | Runbook |
|---|---|---|---|---|---|
| TRK-01 | EURODIS: chiave o partner non validi | `sum(last_10m):sum:eurodis_tracking_chiamata_total{…,esito:401 OR esito:424 OR esito:451}.as_count()` | > 0 | alto | Verificare la chiave API di send-tracking e la configurazione del partner presso EURODIS. Il consumer resta fermo sull'evento e riprova |
| TRK-02 | Invii fermi per errore di configurazione | `sum(last_10m):sum:eurodis_tracking_retry_total{…,esito:errore_configurazione}.as_count()` | > 0 | alto | Gli eventi non partono per URL o chiave: non si risolve riprovando, serve l'intervento |
| TRK-03 | Errori temporanei frequenti | `sum(last_30m):sum:eurodis_tracking_retry_total{…,esito:errore_temporaneo}.as_count()` | ≥ 10 | medio | Timeout o `5xx` di EURODIS: il consumer riprova con backoff. Se continua, avvisare EURODIS |
| TRK-04 | Eventi rifiutati da EURODIS | `sum(last_1h):sum:eurodis_tracking_eventi_total{…,esito:RIFIUTATO}.as_count()` | > 0 | medio | Il codice è in `eurodis_tracking_errori_eurodis_total{codice}`. Analizzare barcode e codice evento |
| TRK-05 | Eventi abbandonati | `sum(last_1h):sum:eurodis_tracking_tracce_abbandonate_total{…}.as_count()` | > 0 | alto | Un evento è stato abbandonato dopo 24 ore di tentativi: la traccia non è arrivata a EURODIS. Recuperarla dai log (topic, partizione, offset) |
| TRK-06 | Consegne senza nome di chi ritira | `sum(last_1h):sum:eurodis_tracking_acceptor_name_mancante_total{…}.as_count()` | > 0 | medio | Evento `1100` scartato: manca `acceptorName` nella sorgente (V-02) e non c'è un valore di default |
| TRK-07 | Risposta di lotto incoerente | `sum(last_1h):sum:eurodis_tracking_lotto_non_correlabile_total{…}.as_count() + sum:eurodis_tracking_esito_non_coincidente_total{…}.as_count()` | > 0 | medio | Esito incerto, rischio di doppioni (PA-36) |
| TRK-08 | Mongo non disponibile per il filtro 3 | `sum(last_10m):sum:eurodis_tracking_mongo_errori_total{…}.as_count()` | > 0 | alto | La ricerca delle LDV su `dichiarato_events` fallisce: il consumer è fermo e riprova. Verificare Mongo e il secret `ce-dichiarato-validatore-secret` |
| TRK-09 | Consumer in ritardo | `max(last_15m):max:kafka_consumer_fetch_manager_records_lag_max{…,topic:PACCHI.TRACKING}` | > 50.000 (P), da tarare | alto | Il consumer non tiene il passo o è fermo sui retry (TRK-02, TRK-03, TRK-08) |
| TRK-10 | Nessuna traccia letta | `sum(last_30m):sum:eurodis_tracking_tracce_lette_total{…}.as_count()` | = 0 (solo dove il consumer è abilitato) | alto | Il consumer è spento, non ha l'ACL di lettura su `PACCHI.TRACKING` o il pod non gira |
| TRK-11 | Ricerche Mongo lente | `avg(last_15m):avg:eurodis_tracking_mongo_ricerca_durata.avg{…}` | > 200 ms | medio | Probabile indice mancante su `dichiarato_events` (`spedizione.collo.id_ldv`, `canale`; V-06) |

## 5. Monitor di piattaforma consigliati (non sono metriche applicative)

| ID | Nome | Cosa | Gravità |
|---|---|---|---|
| PL-01 | Pod non pronto | Readiness/restart dei pod dei tre servizi (integrazione Kubernetes di Datadog) | alto |
| PL-02 | Lag del consumer del mapper | Lag del gruppo `ce-dichiarato-eurodis-mapper-group` su `preadvising.eud.pre.build`, se l'integrazione Kafka di Datadog è attiva sul cluster | medio |
| PL-03 | Log CRITICO di `-in` | Log monitor su `service:ce-dichiarato-eurodis-in` con il testo `CRITICO` | critico |

## 6. Esempio JSON di un monitor (IN-01)

Da adattare al nome della metrica com'è in Datadog (sezione 1) e ai canali di notifica.

```json
{
  "name": "[EURODIS][-in] Chiamata receive-pan fallita senza risposta ({{env.name}})",
  "type": "query alert",
  "query": "sum(last_10m):sum:eurodis_in_chiamata_total{service:ce-dichiarato-eurodis-in,esito:errore} by {env}.as_count() > 0",
  "message": "Timeout o connessione caduta su GET /shipments/v1: possibili spedizioni perse (I1).\nRunbook: chiedere a EURODIS di rimetterle nella richiesta successiva oppure recuperarle con EURODIS_RECUPERO_ED_REFERENCES.\n@<canale-team>",
  "tags": ["iniziativa:136596", "service:ce-dichiarato-eurodis-in"],
  "options": {
    "thresholds": { "critical": 0 },
    "notify_no_data": false,
    "require_full_window": false,
    "renotify_interval": 60
  },
  "priority": 1
}
```

## 7. Punti aperti

- Nome delle metriche in Datadog, cioè `_total` oppure `.count` (sezione 1): verificarlo al primo deploy in svil.
- Canali di notifica e chi è reperibile per gravità: da definire con il team.
- Soglie di IN-03, IN-09, MAP-04 e TRK-03: da tarare dopo le prime settimane di traffico reale.
