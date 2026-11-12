# Linee guida per lo sviluppo (Amelia e ogni istanza dev)

## Stack e convenzioni dei servizi `ce-`

- Base: [MICROSERVICE_TECHNICAL_BLUEPRINT.md](MICROSERVICE_TECHNICAL_BLUEPRINT.md). Java 17,
  **Spring Boot 3.5.14** (decisione per la catena: segnala chi porta un servizio a un'altra versione).
- PostgreSQL come `ce-db-sync`: `spring-boot-starter-jdbc` + `NamedParameterJdbcTemplate`, niente
  JPA né Flyway; DDL in `sql/ddl/` del repo, eseguite dal DBA. Testi da conservare identici in
  colonne `text`, non `jsonb`.
- ShedLock JDBC: dichiarare `withDatabaseProduct(DatabaseProduct.POSTGRES_SQL)` con `usingDbTime()`;
  il riconoscimento automatico fallisce senza connessione e blocca tutti i job.
- Dockerfile come `ce-dichiarato-adapter` (credenziali Nexus da ARG, `clean package -DskipTests`,
  agent Datadog, pacchetti runtime aggiornati, `USER 185`).
- Helm: `.helm/values.yaml` completo; `deploy-svil` e `deploy-coll` con i soli override; template di
  prod `deploy-config/values_TEMPLATE.yaml` con segnaposto `_#VAR` e commento per certificazione e
  produzione; secret solo via `secretKeyRef`.
- Chiamate REST ripetitive a parità di parametro (es. `ce-anagrafica`): cache in memoria con TTL,
  errori non in cache, default esplicito se il servizio non risponde.

## Qualità prima del push (Sonar ha bloccato rilasci)

- Letterali ripetuti 3+ volte nello stesso file → costante (S1192), anche nei test.
- Complessità cognitiva ≤ 15: estrarre metodi; prima test di caratterizzazione, poi refactoring.
- Nessun accesso a valori che possono essere null senza controllo.
- Nessun campo, import o metodo inutilizzato.
- Nessun riferimento a punti aperti (PA/DF) o documenti di analisi nei commenti del codice.

## Osservabilità e dati

- Metriche Micrometer e span OpenTelemetry su ogni job, chiamata esterna e invio Kafka, sul modello
  di `TraceUtil` e `MetricheEurodisIn` (`ce-dichiarato-eurodis-in`): l'instrumentation non deve mai
  far fallire la lavorazione. Pensare le metriche per gli alert Datadog.
- **Log nel formato standard dei ms, per tutti i servizi** (Diego, 12-11), per poterli analizzare in
  Datadog. JSON su console con `LoggingEventCompositeJsonEncoder` di logstash in `logback-spring.xml`
  (provider timestamp, level, threadName, loggerName, message, mdc, stackTrace), come
  `ce-dichiarato-orchestratore` e i servizi EURODIS; l'adapter usa la variante con pattern esplicito.
  In ambiente il profilo è sempre `prod` (`SPRING_PROFILES_ACTIVE` in Helm), quindi JSON anche in svil
  e coll; `logback-svil.xml` (console in chiaro) serve solo per l'esecuzione in locale. MDC con gli
  identificativi di correlazione, con gli stessi nomi dei servizi a valle: `partition`, `offset`,
  `id_preadvising`, `id_file`, più quelli di dominio (es. `ed_reference`, `id_scarico`,
  `id_esecuzione`); `MDC.clear()` a fine messaggio o job. Il contesto di trace lo aggiunge l'agent.
- Mai dati personali nei log, nelle metriche o negli attributi degli span; mai chiavi o password.
- Test con dati inventati, mai di produzione. I test su H2 in modalità PostgreSQL non coprono
  CHECK, indici parziali e comportamenti specifici del driver: dirlo nel report.

## Come lavorare

- Prima di toccare un repo: `git fetch`/`pull`; se la working copy ha modifiche di altri, lavorare in
  un `git worktree` separato nello scratchpad e rimuoverlo alla fine.
- Commit piccoli, uno per blocco verde, push man mano; `pull --rebase` prima di ogni push; mai
  riscrivere commit altrui.
- Repo della catena dell'iniziativa: `develop`. Repo di altri team: branch `feature/...` e merge
  request, salvo indicazione di Diego.
- Maven: `mvn -o test` con le impostazioni Maven dell'utente (`settings.xml` del progetto chiede
  credenziali Nexus).
- Report finale breve: commit, numero di test, scostamenti dalla specifica, servizi da rilasciare.
- La specifica di riferimento sta in `iniziative/<id>/sviluppo/<microservizio>.md`; esempio
  completo: `iniziative/136596/sviluppo/`.
