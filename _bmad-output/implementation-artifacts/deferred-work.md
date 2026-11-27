# Deferred work

## Deferred from: code review of ce-dichiarato-eurodis-in.md (2026-11-27)

Repo `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in`, `develop` @ `8995ae8`, gruppo A (`src/main` + `sql`).

- **Wiring di ShedLock senza test** (`configuration/SchedulingConfig.java:28`, `scheduler/EurodisScheduler.java`): nessun test verifica `@SchedulerLock` né `withDatabaseProduct(POSTGRES_SQL)` + `usingDbTime()`. Serve PostgreSQL vero (Testcontainers non è nel pom): da coprire con lo smoke test a 2 repliche in svil (AC-13).
- **Conservazione e pulizia assenti** (`sql/ddl/02_ddl_eurodis_scarichi.sql`, `03_ddl_eurodis_spedizioni.sql:23`): nessun job di pulizia per `corpo`, `json` e `eurodis_postazioni`, che contengono dati personali. `fk_eurodis_spedizioni_scarico` è senza `ON DELETE`, quindi una pulizia futura degli scarichi verrebbe bloccata. La decisione è aperta nella specifica (sezione 3.4, [DA DECIDERE]).
- **`ssl.endpoint.identification.algorithm: ""`** (`src/main/resources/application-prod.yaml`): disattiva la verifica dell'hostname del broker. È uguale in tutti i servizi della catena: va deciso a livello di catena, non qui.
- **DDL `eurodis_postazioni` copiata fuori repo**: `ce-dichiarato-eurodis-mapper` (`src/test/resources/sql/07_ddl_eurodis_postazioni.sql`) e `ce-eurodis-send-tracking` (`PostazioniEurodisRepositoryTest.java:19`, create table scritta a mano). Una modifica allo script 07 non fa fallire i loro test.

## Deferred from: code review of ce-dichiarato-eurodis-mapper.md (2026-11-27)

Repo `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper`, `develop` @ `506d71d`, gruppo G1 (`mapper/`, `service/`, `dto/`, `exception/`, `EdReference`, `MapperProperties` e test).

- **Codici nazione senza ISO4, nessun avviso** (`mapper/EurodisToIcdMapper.java:389-392`, `anagrafica/CacheCodiciNazione.java:70`): se `ce-anagrafica` risponde con `codNazione` valorizzato e `codNazionePoste` vuoto, `codice_nazione` (che dal DEF-136596-005 è l'ISO4) esce vuoto senza `anagrafica_ko` e senza default italiano; `valida()` della cache accetta la risposta perché basta l'ISO3. Non verificato: va controllato se in `net_delivery_int` esistono nazioni senza ISO4 Poste. Se sì è medio (BEP 101 / regola 1039 del validatore).
