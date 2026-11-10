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
mancante è infrastrutturale o di verifica in ambiente: verifica di avvio in svil e alert Datadog.

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
| AS-17 | Versione di Spring Boot | ✅ **deciso 04-11 (Diego)**: si resta su **3.5.14**, come blueprint e mapper. Da comunicare ad azzurrazezza (il suo `5da28fc` portava a 4.1.2) | — |
| AS-7 | `application-prod.yaml`: `ssl.endpoint.identification.algorithm: ""` disattiva la verifica dell'hostname di Kafka. Non l'ho toccato: con gli `hostAliases` di svil potrebbe servire. Da verificare | media (sicurezza) | team piattaforma |
| AS-9 | Profilo `svil`: log in console non JSON (`logback-svil.xml`), quindi in svil Datadog non vede l'MDC | bassa | — |
| AS-10 | `codice_iniziativa_goto: "138972"` in `deploy-svil` e `deploy-coll` | da verificare | Diego |
| AS-11 | Helm `application.properties` ancora il placeholder del template | bassa | — |
| AS-14 | Retry del service mesh | ✅ non applicabile: il progetto non usa service mesh (Diego, 04-11) | — |
| AS-15 | Utente SCRAM del secret e scrittura su `preadvising.eud.pre.build` | ✅ confermato che funziona (Diego, 04-11) | — |
| AS-16 | Stringa Mongo | ✅ il servizio la legge dal secret (`mongo-string-connection`); il valore giusto è impostato per ambiente (Diego, 04-11) | — |
| AS-18 | Uscita di rete verso `testapi.eurodis.com` | ✅ aperta (Diego, 04-11) | — |
| AS-19 | **Alert Datadog** (sezione 9 della specifica) | **da fare più avanti** (Diego, 04-11). 10-11: proposta dei monitor per tutta la catena (`-in` con buffer locale, mapper, send-tracking) in [alert-datadog-eurodis.md](alert-datadog-eurodis.md), nomi delle metriche verificati nel codice; resta da configurarli in Datadog | team / Datadog |
| AS-20 | Estensione del mock per gli end-to-end | va bene così per ora (Diego, 04-11): i casi sono coperti dai test unitari | — |
| AS-21 | Conservazione (TTL) delle collezioni: ogni run viene salvato, anche i `404` (720 al giorno) | bassa | Diego |
| AS-22 | Non verificato: avvio dell'applicazione con Mongo e Kafka veri (i test sono unitari) e test con 2 repliche (AC-13) | media | in svil |

### Dockerfile

| # | Rilievo | Esito | Chi |
|---|---|---|---|
| AS-23 | **Dockerfile** confrontato con adapter, orchestratore, mapper e send-tracking. In `-in` mancava `ENV password` (la build in pipeline non si sarebbe autenticata su Nexus), c'era `clean verify` invece di `clean package -DskipTests`, mancavano `--no-check-certificate` sull'agent Datadog, l'aggiornamento dei pacchetti runtime e l'utente 185 | ✅ allineato all'adapter (`db9a56a`) | — |
| AS-24 | Dockerfile degli altri due servizi. **Mapper**: niente download dell'agent Datadog, `clean package` con i test. **send-tracking**: il 05-11 azzurrazezza era già passata a JDK 17 (`58ff5f2`), ma mancavano `ENV password`, `-DskipTests`, `--no-check-certificate`, l'aggiornamento dei pacchetti e l'utente 185 | send-tracking ✅ allineato (`4cba024`, 05-11); mapper da sistemare | Amelia |

## Per andare in svil (aggiornato 04-11 con le risposte di Diego)

1. Deploy con `EURODIS_IN_ABILITATO=false` e verifica di avvio con Mongo e Kafka veri (AS-22).
2. Abilitare lo scarico e provare con EURODIS TEST (PA-29).
3. Più avanti: alert Datadog (AS-19), conservazione delle collezioni (AS-21).

## Aggiornamento del 10-11

Mongo non è più la persistenza: `-in` è passato a **PostgreSQL** (`9acdd77`, DDL in `sql/ddl/` e in `ddl-ce-eurodis-api-in.md`, secret `ce-postgres`). AS-4, AS-5 e AS-16 valgono quindi solo per la versione su Mongo (`a53398c`); AS-22 resta aperto con PostgreSQL al posto di Mongo. Nuovo AS-25: al commit `bd33e8a` `develop` non compila (riparato da `9acdd77`), un build agganciato a quel commit fallisce.

## Aggiornamento del 10-11 (sera): AS-24 chiuso

AS-24 ✅ **mapper** allineato all'adapter (`5b84993` su `develop`): `ENV password`, `clean package -DskipTests` al posto di `clean verify`, `--no-check-certificate` sull'agent Datadog, aggiornamento dei pacchetti runtime con `USER 185`, jar anche in `/deployments/`; esclusioni Sonar di azzurrazezza mantenute, aggiunto il package reale `configuration`. Test del mapper: 94 verdi. **send-tracking** già allineato (`4cba024`), nessuna modifica; 143 test verdi. Java 17 in pom e Dockerfile per entrambi. Spring Boot: send-tracking 3.5.14, **mapper 4.1.2** (portato da azzurrazezza, contro la decisione 3.5.14 per la catena: da chiarire con lei, non modificato). Nota su AS-23: `ENV password` non era indispensabile, perché un `ARG` è comunque visibile come variabile d'ambiente ai `RUN` dello stesso stage; si tiene per coerenza con l'adapter.
