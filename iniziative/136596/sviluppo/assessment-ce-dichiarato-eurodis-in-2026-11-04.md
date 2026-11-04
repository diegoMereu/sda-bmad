# 136596 — Assessment di `ce-dichiarato-eurodis-in` (04-11, dopo l'implementazione)

**Autrice**: Amelia (dev) · **Destinatari**: Diego, Mary, John
**Repository**: `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in`, branch
`feature/eurodis-base-implementation`, commit **`a53398c`** (sopra `5da28fc` di azzurrazezza)
**Confronto con**: specifica [ce-dichiarato-eurodis-in.md](ce-dichiarato-eurodis-in.md) **0.4** e
`contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md`

## In sintesi

Il servizio è **implementato secondo la specifica 0.4**, con il disegno in due fasi deciso il 04-11:
**53 test automatici verdi**. La specifica è stata aggiornata con tutte le decisioni del 04-11.
Resta aperta una scelta tecnica, la **versione di Spring Boot** (AS-17). Il resto del lavoro
mancante è infrastrutturale o di verifica in ambiente: secret, rete verso EURODIS, service mesh,
estensione del mock.

## Cosa è stato fatto (rispetto all'assessment della mattina)

| # | Rilievo del mattino | Esito |
|---|---|---|
| AS-1 | Consumer Kafka su `preadvising.eud.in` | ✅ Tolto (configurazione, Helm, profilo prod) |
| AS-2 | Spring Boot 3.2.2, logstash 7.4 | ✅ 3.5.14 e 8.0, come blueprint e mapper. Vedi AS-17 |
| AS-3 | Package `it.posteitaliane` | ✅ `it.poste.dichiarato.eurodis.in` |
| AS-4 | Mongo e ShedLock assenti | ✅ `spring-boot-starter-data-mongodb`, ShedLock 6.10.0 con provider Mongo |
| AS-5 | Configurazione EURODIS assente | ✅ `eurodis.in.*` completa; Helm con `EURODIS_API_KEY` e `MONGO_STRING_CONNECTION` dal secret |
| AS-6 | Producer senza `acks=all` e idempotenza | ✅ `acks=all`, `enable.idempotence=true`, invio sincrono |
| AS-8 | `health.show-details: always` | ✅ `never`, probes abilitate |
| AS-12 | Porta 8080 senza endpoint | Lasciata: serve al chart. Nessun endpoint applicativo (D6) |
| AS-13 | Nessun test, `CLAUDE.md` non versionato | ✅ 53 test; `CLAUDE.md` versionato e aggiornato al disegno in due fasi |
| IN-1/IN-2 | Credenziali ServiceNow e retry del template | ✅ Già rimosse da azzurrazezza il 03-11 |

## Conformità alla specifica 0.4

| Area | Stato | Dove |
|---|---|---|
| Fase 1: run + esito HTTP + grezzo su `eurodis_scarichi`, nessun retry, `404` regolare | ✅ | `ScaricoService`, `ReceivePanClient`, `AppConfig` (`disableAutomaticRetries`) |
| Fase 2: record per spedizione con JSON separato, `edReference`, ora di invio, motivo; esito dello scarico | ✅ | `ElaborazioneService`, `SpedizioneService` |
| Nessuna deserializzazione: lettura generica, solo `edReference` | ✅ | `AnalizzatoreSpedizioni`, `EdReference` |
| Corpo del messaggio identico al testo ricevuto | ✅ | divisione dell'array per offset, senza riserializzare |
| Nessun filtro dei duplicati | ✅ | `SpedizioneService` |
| Header del messaggio + `traceparent` | ✅ | `SpedizioneProducer` |
| Grezzo in GridFS sopra 10 MB | ✅ | `GrezzoStore` |
| Non identificabili come record con motivo | ✅ | `registraNonIdentificabile` |
| Ripubblicazione dei fermi; ripresa degli scarichi interrotti | ✅ | `RipubblicazioneService`, `ElaborazioneService.esegui` |
| Recupero e reinvio da configurazione, una volta per valore | ✅ | `RichiesteManualiService` |
| Un solo pod per job | ✅ | ShedLock, 4 lock distinti |
| Metriche e span su tutto | ✅ | `MetricheEurodisIn`, `TraceUtil` (modello `ce-dichiarato-adapter`) |
| Scarico e invio ogni 2 minuti; scarico disabilitato di default | ✅ | `application.yaml` |

## Rilievi aperti

| # | Rilievo | Gravità | Chi |
|---|---|---|---|
| AS-17 | **Versione di Spring Boot.** Il commit `5da28fc` di azzurrazezza portava il parent a **4.1.2** con Jackson 3. Nel merge ho tenuto **3.5.14** (blueprint e mapper); di quel commit è rimasta la dipendenza `jackson-datatype-jsr310`. Passare a Boot 4 vuol dire ShedLock 7.x, adattare la lettura JSON a Jackson 3 e portare anche il mapper: è una scelta da fare per tutta la catena | **alta (da decidere)** | Diego / azzurrazezza |
| AS-7 | `application-prod.yaml`: `ssl.endpoint.identification.algorithm: ""` disattiva la verifica dell'hostname di Kafka. Non l'ho toccato: con gli `hostAliases` di svil potrebbe servire. Da verificare | media (sicurezza) | team piattaforma |
| AS-9 | Profilo `svil`: log in console non JSON (`logback-svil.xml`), quindi in svil Datadog non vede l'MDC | bassa | — |
| AS-10 | `codice_iniziativa_goto: "138972"` in `deploy-svil` e `deploy-coll` | da verificare | Diego |
| AS-11 | Helm `application.properties` ancora il placeholder del template | bassa | — |
| AS-14 | Retry del service mesh verso EURODIS (RNF-03) | alta, da verificare in ambiente | piattaforma |
| AS-15 | Utente SCRAM del secret = quello di `ce-dichiarato-smistatore`: serve permesso di scrittura su `preadvising.eud.pre.build` | alta per il deploy | piattaforma |
| AS-16 | Stringa Mongo verso `ce_preadvising` su un cluster che dal nome sembra di collaudo | media | piattaforma |
| AS-18 | Uscita di rete da OpenShift svil verso `testapi.eurodis.com` | alta per il deploy | Poste / rete |
| AS-19 | **Alert Datadog** da configurare (sezione 9 della specifica): non sono nel codice | media | team / Datadog |
| AS-20 | **Mock da estendere** (`500`, timeout, `.0`, `edReference` assente, campi extra, `401` testuale) per gli end-to-end | media | Amelia |
| AS-21 | Conservazione (TTL) delle collezioni: ogni run viene salvato, anche i `404` (720 al giorno) | bassa | Diego |
| AS-22 | Non verificato: avvio dell'applicazione con Mongo e Kafka veri (i test sono unitari) e test con 2 repliche (AC-13) | media | in svil |

## Per andare in svil

1. Decidere AS-17 (versione di Spring Boot).
2. AS-15, AS-16, AS-18: permessi Kafka, database Mongo, rete verso EURODIS TEST.
3. AS-14: retry del service mesh disattivati per l'host EURODIS.
4. Deploy con `EURODIS_IN_ABILITATO=false`, verifica di avvio, poi abilitazione.
5. Test end-to-end contro il mock esteso (AS-20), poi con EURODIS TEST (PA-29).
