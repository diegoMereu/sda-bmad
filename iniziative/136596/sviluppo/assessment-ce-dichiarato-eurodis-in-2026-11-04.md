# 136596 — Assessment di `ce-dichiarato-eurodis-in` (stato al 04-11)

**Autrice**: Amelia (dev) · **Destinatari**: Diego, Mary
**Repository**: `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in`, branch
`feature/eurodis-base-implementation`, commit `eb53b49` (03-11, azzurrazezza, "impostazione progetto")
**Confronto con**: specifica `ce-dichiarato-eurodis-in.md` 0.3 e
`contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md`

## In sintesi

L'impostazione infrastrutturale è fatta: Kafka SASL, secret, Helm, log JSON, metriche.
**Non c'è ancora codice applicativo**: solo `Application.java`. L'impostazione sembra
derivata da un servizio che *consuma* da Kafka, mentre `-in` interroga un'API HTTP: va
corretta prima di partire. Mancano Spring Boot 3.5.14, MongoDB, il lock distribuito e tutta
la configurazione EURODIS.

## Cosa c'è ✅

| Area | Stato | Rif. |
|---|---|---|
| Credenziali ServiceNow (`snowcore`) del template | **Rimosse** (`application.yml` cancellato): risolve IN-1 e IN-2 per `-in` | rapporto 02-11 |
| groupId | `it.poste.ce` | blueprint |
| Kafka produzione | SASL_SSL / SCRAM-SHA-512, truststore, credenziali da `ce-dichiarato-eurodis-in-secret` | blueprint |
| Topic in uscita | `preadvising.eud.pre.build` | decisione 30-10 |
| Log | logstash JSON con `mdc` e `stackTrace` (meglio del blueprint, che non dichiara `stackTrace`) | blueprint §10 |
| Metriche | actuator su 8091, prometheus | specifica §9 |
| Helm | values base, svil e coll; env da secret; hostAliases Kafka svil | — |
| Pipeline | deploy svil su `corriere-espresso-preadvising` | — |

## Incongruenze e mancanze

| # | Rilievo | Gravità | Rif. |
|---|---|---|---|
| AS-1 | **È configurato un consumer Kafka** (`group-id`, `ack-mode`, deserializer) con topic in ingresso `preadvising.eud.in` (anche in Helm: `KAFKA_TOPIC_INPUT`, "nomi topic provvisori"). Secondo la specifica `-in` **non consuma da Kafka**: il trigger è lo scheduler che chiama `receive-pan`. O è un residuo copiato dal mapper, o c'è un'intenzione che la specifica non conosce (un topic di comando?) | **alta** | specifica §2, §4 |
| AS-2 | Spring Boot **3.2.2** (blueprint e mapper: 3.5.14); `logstash-logback-encoder` 7.4 (blueprint: 8.0) | media | blueprint §3 |
| AS-3 | Package ancora `it.posteitaliane` | media | blueprint §5: `it.poste.dichiarato.eurodis.in` |
| AS-4 | Mancano le dipendenze `spring-boot-starter-data-mongodb` (D1) e ShedLock con provider Mongo (D3, pattern già usato in `ce-dichiarato-state-machine-handler`) | — (da fare) | specifica §3.3, RF-02 |
| AS-5 | Manca tutta la configurazione EURODIS: URL per ambiente, chiave API da secret (`EURODIS_API_KEY` in `ce-dichiarato-eurodis-in-secret`), cron, timeout, flag `eurodis.in.abilitato`, elenchi di recupero; e la stringa Mongo (`MONGO_STRING_CONNECTION`, come l'orchestratore) | — (da fare) | specifica §8 |
| AS-6 | Producer: mancano `acks=all` ed `enable.idempotence=true` (c'è solo `send-timeout-ms`) | alta | RF-10 |
| AS-7 | `application-prod.yaml`: `ssl.endpoint.identification.algorithm: ""` disattiva la verifica dell'hostname del broker Kafka. Il mapper non lo fa | media (sicurezza) | — |
| AS-8 | `management.endpoint.health.show-details: always` (mapper e blueprint: `never`) | bassa (sicurezza) | blueprint §12 |
| AS-9 | Con il profilo di default `svil` i log vanno in console **non JSON** (`logback-svil.xml`): in svil Datadog non vede i campi MDC | bassa | specifica §9 |
| AS-10 | `deploy-svil/values.yaml`: `codice_iniziativa_goto: "138972"` (Preadvising Fast) e referente "Alfonso Puttini". Copiati da un altro progetto o voluti (budget GOTO)? | da verificare | — |
| AS-11 | Helm `application.properties` ancora placeholder (`myvar`) | bassa | — |
| AS-12 | `server.port: 8080` con `context-path`: senza endpoint applicativi (04-11) serve solo se il chart lo richiede; l'actuator è su 8091 | bassa | D6 |
| AS-13 | Nessun test, nessun `CLAUDE.md` versionato (il mio è solo locale) | — | — |
| AS-14 | Retry del service mesh verso EURODIS: niente in Helm (né `VirtualService` né `ServiceEntry`) | da verificare in ambiente | RNF-03 |

## Cosa serve per partire con l'implementazione

**Decisioni**
1. **AS-1**: il consumer Kafka su `preadvising.eud.in` va tolto o ha un ruolo? È l'unica
   domanda che cambia il disegno.
2. AS-10: codice iniziativa GOTO corretto per questo servizio.

**Lavoro di impostazione (storia S1)**: AS-2, AS-3, AS-4, AS-5, AS-6, AS-7, AS-8, AS-11,
`CLAUDE.md`. Allineamento sul modello del mapper, senza logica applicativa.

**Secret** `ce-dichiarato-eurodis-in-secret` (svil, verificato il 04-11 sulla struttura, non sui valori):
chiavi `kafka-scram-username`, `kafka-scram-password`, `mongo-string-connection`, `api-key`.
Nell'Helm vanno mappate su `KAFKA_SCRAM_*` (già fatto), `MONGO_STRING_CONNECTION` e
`EURODIS_API_KEY` (da aggiungere). Due verifiche:
- **AS-15**: l'utente SCRAM è quello di `ce-dichiarato-smistatore`, e il secret risulta creato
  il 28-07-2025, prima del progetto: sembra copiato da quello dello smistatore. Serve un utente
  Kafka dedicato, con ACL di scrittura su `preadvising.eud.pre.build`, oppure è voluto?
- **AS-16**: la stringa Mongo punta al database `ce_preadvising` su un cluster che dal nome
  sembra di collaudo, anche se il secret è in svil. Confermare database e cluster per il grezzo (D1).

**Richieste esterne (tempi lunghi)**: topic e ACL in svil; uscita di rete da svil verso `testapi.eurodis.com`;
verifica dei retry del service mesh (AS-14).

**Mock**: estensioni per AC-04, 05, 10, 11, 12 (storia S0).

Dopo S0 e S1 si parte con S2 (client + scheduler + lock).
