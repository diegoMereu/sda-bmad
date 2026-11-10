# `ce-dichiarato-eurodis-in` — Persistenza su PostgreSQL: DDL e ambiente

**Iniziativa**: 136596 — Eurodis autoproduttore · **Versione**: 0.1 · **Data**: 2026-11-10
**Autore**: Winston (architect) · **Destinatari**: DBA e piattaforma (script e secret), Amelia (dev)
**Specifica di riferimento**: [ce-dichiarato-eurodis-in.md](ce-dichiarato-eurodis-in.md) 0.6, sezione 3.4

**[DECISO 10-11, Diego]** Lo scarico EURODIS passa da MongoDB a PostgreSQL, sul database dedicato
`ce_eud_api_in`. Le tre collezioni Mongo diventano tre tabelle, più la tabella del lock dei job. Le
credenziali sono quelle già usate da `ce-db-sync`, nello stesso secret.

---

## 1. Scelte

| Scelta | Motivo |
|---|---|
| **Accesso con `spring-boot-starter-jdbc` (`NamedParameterJdbcTemplate`)**, niente JPA | È come lavorano tutti i servizi `ce-` su PostgreSQL (`ce-db-sync`, `ce-anagrafica`, `ce-ldv`, `ce-dichiarato-state-machine-handler`). Le query sono poche e note (sezione 6) |
| **Niente Flyway o Liquibase**: le DDL le esegue il DBA | Nessun servizio `ce-` usa uno strumento di migrazione; `ce-db-sync` tiene gli script in `sql/ddl/`. Si fa lo stesso: gli script di questo documento vanno anche nel repository, in `sql/ddl/` |
| **Schema `public`** | Il database `ce_eud_api_in` è dedicato al solo `-in`, quindi uno schema in più non isola niente. La DDL di Diego dà già `USAGE, CREATE` su `public` a `ce_user`, e anche gli script di `ce-db-sync` usano `public`. Così l'URL non ha bisogno di `currentSchema`. Gli script qualificano comunque ogni oggetto con `public.` |
| **Grezzo e JSON per spedizione in `text`**, non `jsonb` | `jsonb` riscrive il testo (spazi, ordine delle chiavi, chiavi duplicate, numeri come `7319003746401.0`). La specifica vuole il testo **identico** a quello ricevuto (RF-06, RF-14) |
| **Niente GridFS** | `text` regge fino a 1 GB ed è compresso dal TOAST di PostgreSQL. Il grezzo sta sempre nella colonna `corpo`. Resta la soglia di guardia a 100 MB (warning e metrica, sezione 9 della specifica) |
| **Identificativo dello scarico `uuid`, generato dal servizio** | Il servizio lo conosce prima dell'`INSERT`, senza leggere chiavi generate e senza dipendere da `gen_random_uuid()` (PostgreSQL 13+). Diventa `idEsecuzione` negli header e la parte finale di `rifGrezzo` (`eurodis_scarichi/<uuid>`) |
| **Stati in `varchar` con `CHECK`** | Leggibili in query e nei log, come gli enum Java. Un nuovo stato richiede un `ALTER` del vincolo, voluto: lo stato è parte del contratto |
| **Tempi in `timestamptz`** | Il servizio lavora in `Instant`, nessuna ambiguità di fuso |
| **Lock dei job con ShedLock JDBC** (`shedlock-provider-jdbc-template`) | Stessa libreria di oggi, cambia solo il provider. Tabella standard di ShedLock (script 5) |

## 2. Script

Ordine di esecuzione: 1 come amministratore del server, sul database `postgres`; dal 2 in poi come
`ce_user`, connessi a `ce_eud_api_in`. Dal 2 in poi gli script si possono rieseguire (`IF NOT EXISTS`).

### Script 1 — Database (Diego)

```sql
CREATE DATABASE ce_eud_api_in
    WITH
    OWNER = ce_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'it_IT.utf8'
    LC_CTYPE = 'it_IT.utf8'
    CONNECTION LIMIT = -1
    TEMPLATE = template0;
GRANT ALL PRIVILEGES ON DATABASE ce_eud_api_in TO ce_user;
GRANT USAGE, CREATE ON SCHEMA public TO ce_user;
```

Nota: `GRANT ... ON SCHEMA public` agisce sul database a cui si è connessi. Va eseguito **dopo**
essersi connessi a `ce_eud_api_in` (`\c ce_eud_api_in`), altrimenti dà i permessi sullo schema
`public` del database `postgres`. Da PostgreSQL 15 `public` non concede più `CREATE` a tutti: il
grant serve.

### Script 2 — `eurodis_scarichi`

Un record per ogni chiamata a EURODIS (scarico o rilettura): run, esito HTTP, grezzo e, dopo la
fase 2, esito dell'invio e file fittizio.

```sql
CREATE TABLE IF NOT EXISTS public.eurodis_scarichi (
    id                          uuid          NOT NULL,
    tipo                        varchar(10)   NOT NULL,
    ed_reference_richiesto      varchar(20),
    istanza                     varchar(255),
    avviato_il                  timestamptz   NOT NULL,
    ricevuto_il                 timestamptz,
    http_status                 smallint,
    durata_ms                   bigint,
    errore                      varchar(300),
    corpo                       text,
    dimensione_byte             bigint,
    sha256                      char(64),
    stato                       varchar(20)   NOT NULL,
    numero_spedizioni           integer,
    numero_inviate              integer,
    numero_non_inviate          integer,
    elaborazione_iniziata_il    timestamptz,
    elaborazione_conclusa_il    timestamptz,
    id_file                     uuid,
    nome_file                   varchar(100),
    evento_preso_in_carico_il   timestamptz,
    evento_in_elaborazione_il   timestamptz,
    CONSTRAINT pk_eurodis_scarichi PRIMARY KEY (id),
    CONSTRAINT uq_eurodis_scarichi_id_file UNIQUE (id_file),
    CONSTRAINT ck_eurodis_scarichi_tipo CHECK (tipo IN ('SCARICO', 'RILETTURA')),
    CONSTRAINT ck_eurodis_scarichi_stato CHECK (stato IN (
        'CHIAMATA_IN_CORSO', 'ERRORE_CHIAMATA', 'NESSUNA_SPEDIZIONE', 'DA_ELABORARE',
        'IN_ELABORAZIONE', 'NON_ELABORABILE', 'INVIATO_TUTTO', 'INVIO_PARZIALE', 'NESSUN_INVIO')),
    CONSTRAINT ck_eurodis_scarichi_rilettura CHECK (tipo <> 'RILETTURA' OR ed_reference_richiesto IS NOT NULL)
);

-- Job di elaborazione: scarichi da elaborare e scarichi rimasti in elaborazione (riavvio a meta')
CREATE INDEX IF NOT EXISTS ind_eurodis_scarichi_da_elaborare
    ON public.eurodis_scarichi (avviato_il)
    WHERE stato IN ('DA_ELABORARE', 'IN_ELABORAZIONE');
-- Consultazione per periodo e pulizia (sezione 4)
CREATE INDEX IF NOT EXISTS ind_eurodis_scarichi_avviato_il
    ON public.eurodis_scarichi (avviato_il);
CREATE INDEX IF NOT EXISTS ind_eurodis_scarichi_stato
    ON public.eurodis_scarichi (stato);

COMMENT ON TABLE  public.eurodis_scarichi IS 'Una riga per ogni chiamata a EURODIS receive-pan (scarico o rilettura): run, esito HTTP, grezzo, esito della fase 2';
COMMENT ON COLUMN public.eurodis_scarichi.id IS 'Generato dal servizio; header idEsecuzione e parte finale di rifGrezzo';
COMMENT ON COLUMN public.eurodis_scarichi.tipo IS 'SCARICO = GET /shipments/v1, RILETTURA = GET /shipment/{edReference}/v1';
COMMENT ON COLUMN public.eurodis_scarichi.ed_reference_richiesto IS 'Solo per le riletture';
COMMENT ON COLUMN public.eurodis_scarichi.istanza IS 'Pod che ha eseguito il run';
COMMENT ON COLUMN public.eurodis_scarichi.errore IS 'Esito non 200 o eccezione, senza dati personali';
COMMENT ON COLUMN public.eurodis_scarichi.corpo IS 'Risposta grezza esattamente come ricevuta (text, non jsonb)';
COMMENT ON COLUMN public.eurodis_scarichi.sha256 IS 'Hash esadecimale del grezzo, per verificarne l''integrita''';
COMMENT ON COLUMN public.eurodis_scarichi.stato IS 'Ciclo di vita, sezione 6 della specifica';
COMMENT ON COLUMN public.eurodis_scarichi.id_file IS 'File fittizio: idFile degli eventi ST_F0002/ST_F0005 e dell''header verso il mapper; assegnato una volta sola';
COMMENT ON COLUMN public.eurodis_scarichi.nome_file IS 'Nome del file fittizio negli eventi di stato';
COMMENT ON COLUMN public.eurodis_scarichi.evento_preso_in_carico_il IS 'Invio confermato di ST_F0002: alla ripresa non si ripete';
COMMENT ON COLUMN public.eurodis_scarichi.evento_in_elaborazione_il IS 'Invio confermato di ST_F0005: alla ripresa non si ripete';
```

### Script 3 — `eurodis_spedizioni`

Un record per spedizione, con il suo JSON. La chiave è `edReference` normalizzato: una spedizione
ricevuta di nuovo aggiorna lo stesso record (nessun filtro duplicati, si reinvia comunque).

```sql
CREATE TABLE IF NOT EXISTS public.eurodis_spedizioni (
    id                      varchar(64)   NOT NULL,
    ed_reference            varchar(20),
    id_scarico              uuid          NOT NULL,
    id_file                 uuid,
    posizione               integer       NOT NULL,
    fonte                   varchar(40)   NOT NULL,
    rif_grezzo              varchar(100)  NOT NULL,
    ricevuto_il             timestamptz   NOT NULL,
    json                    text          NOT NULL,
    stato_invio             varchar(20)   NOT NULL,
    inviata_il              timestamptz,
    tentativi_invio         integer       NOT NULL DEFAULT 0,
    ultimo_errore           varchar(300),
    numero_ricezioni        integer       NOT NULL DEFAULT 1,
    prima_ricezione_il      timestamptz   NOT NULL,
    ultima_ricezione_il     timestamptz   NOT NULL,
    CONSTRAINT pk_eurodis_spedizioni PRIMARY KEY (id),
    CONSTRAINT fk_eurodis_spedizioni_scarico FOREIGN KEY (id_scarico)
        REFERENCES public.eurodis_scarichi (id),
    CONSTRAINT ck_eurodis_spedizioni_stato_invio CHECK (stato_invio IN (
        'DA_INVIARE', 'INVIATA', 'ERRORE_INVIO', 'NON_IDENTIFICABILE')),
    CONSTRAINT ck_eurodis_spedizioni_identificata CHECK (
        stato_invio = 'NON_IDENTIFICABILE' OR ed_reference IS NOT NULL)
);

-- Job di ripubblicazione: record DA_INVIARE fermi da piu' di N minuti
CREATE INDEX IF NOT EXISTS ind_eurodis_spedizioni_da_inviare
    ON public.eurodis_spedizioni (ultima_ricezione_il)
    WHERE stato_invio = 'DA_INVIARE';
-- Gauge eurodis_in_spedizioni_in_attesa
CREATE INDEX IF NOT EXISTS ind_eurodis_spedizioni_in_attesa
    ON public.eurodis_spedizioni (stato_invio)
    WHERE stato_invio IN ('DA_INVIARE', 'ERRORE_INVIO');
-- Consultazione per periodo e pulizia
CREATE INDEX IF NOT EXISTS ind_eurodis_spedizioni_ultima_ricezione_il
    ON public.eurodis_spedizioni (ultima_ricezione_il);
-- Chiave esterna: le spedizioni di uno scarico
CREATE INDEX IF NOT EXISTS ind_eurodis_spedizioni_id_scarico
    ON public.eurodis_spedizioni (id_scarico);

COMMENT ON TABLE  public.eurodis_spedizioni IS 'Una riga per spedizione EURODIS, con il JSON identico al ricevuto e l''esito dell''invio su preadvising.eud.pre.build';
COMMENT ON COLUMN public.eurodis_spedizioni.id IS 'edReference normalizzato (senza decimali); per le non identificabili <idScarico>#<posizione>';
COMMENT ON COLUMN public.eurodis_spedizioni.id_scarico IS 'Scarico dell''ultima ricezione';
COMMENT ON COLUMN public.eurodis_spedizioni.id_file IS 'idFile dello scarico dell''ultima ricezione; va nell''header idFile anche nei reinvii';
COMMENT ON COLUMN public.eurodis_spedizioni.fonte IS 'receive-pan/shipments/v1 oppure receive-pan/shipment/v1';
COMMENT ON COLUMN public.eurodis_spedizioni.json IS 'JSON della singola spedizione, identico al testo ricevuto (text, non jsonb)';
COMMENT ON COLUMN public.eurodis_spedizioni.inviata_il IS 'Ora dell''invio confermato dal broker';
COMMENT ON COLUMN public.eurodis_spedizioni.ultimo_errore IS 'Motivo del mancato invio, senza dati personali';
```

### Script 4 — `eurodis_richieste_manuali`

Traccia dei recuperi (RF-16) e dei reinvii (RF-17) già eseguiti: un valore in configurazione si
esegue una volta sola.

```sql
CREATE TABLE IF NOT EXISTS public.eurodis_richieste_manuali (
    tipo            varchar(10)   NOT NULL,
    ed_reference    varchar(20)   NOT NULL,
    eseguita_il     timestamptz   NOT NULL,
    esito           varchar(30)   NOT NULL,
    id_scarico      uuid,
    CONSTRAINT pk_eurodis_richieste_manuali PRIMARY KEY (tipo, ed_reference),
    CONSTRAINT fk_eurodis_richieste_manuali_scarico FOREIGN KEY (id_scarico)
        REFERENCES public.eurodis_scarichi (id) ON DELETE SET NULL,
    CONSTRAINT ck_eurodis_richieste_manuali_tipo CHECK (tipo IN ('RECUPERO', 'RIPUBBLICA'))
);

COMMENT ON TABLE  public.eurodis_richieste_manuali IS 'Recuperi (RECUPERO, RF-16) e reinvii (RIPUBBLICA, RF-17) gia'' eseguiti dalle liste in configurazione';
COMMENT ON COLUMN public.eurodis_richieste_manuali.esito IS 'Stato dello scarico di rilettura (RECUPERO) o esito del reinvio (RIPUBBLICA)';
COMMENT ON COLUMN public.eurodis_richieste_manuali.id_scarico IS 'Scarico di rilettura, solo per RECUPERO';
```

### Script 5 — `shedlock`

Tabella standard di ShedLock per `JdbcTemplateLockProvider`. Il servizio ha quattro lock (scarico,
elaborazione, ripubblicazione, richieste manuali).

```sql
CREATE TABLE IF NOT EXISTS public.shedlock (
    name        varchar(64)    NOT NULL,
    lock_until  timestamp(3)   NOT NULL,
    locked_at   timestamp(3)   NOT NULL,
    locked_by   varchar(255)   NOT NULL,
    CONSTRAINT pk_shedlock PRIMARY KEY (name)
);

COMMENT ON TABLE public.shedlock IS 'Lock dei job schedulati (ShedLock): ogni job gira su un solo pod';
```

Il provider va configurato con `usingDbTime()`: i tempi del lock li decide il database, non
l'orologio dei pod.

### Script 6 — Permessi

Gli oggetti sono creati da `ce_user`, che ne è proprietario: non servono altri grant. Se il DBA li
crea con un altro utente:

```sql
ALTER TABLE public.eurodis_scarichi          OWNER TO ce_user;
ALTER TABLE public.eurodis_spedizioni        OWNER TO ce_user;
ALTER TABLE public.eurodis_richieste_manuali OWNER TO ce_user;
ALTER TABLE public.shedlock                  OWNER TO ce_user;
```

## 3. Dimensioni attese

| Tabella | Righe al giorno | Note |
|---|---|---|
| `eurodis_scarichi` | ~720 con il cron a 2 minuti, anche i `404` | il grosso dello spazio è `corpo`, solo nei run con spedizioni |
| `eurodis_spedizioni` | quante sono le spedizioni EURODIS (volumi ancora da chiedere, PA-14) | il JSON di una spedizione è di qualche KB |
| `eurodis_richieste_manuali` | poche, a mano | |
| `shedlock` | 4 righe fisse | |

Con questi volumi il partizionamento non serve.

## 4. Conservazione

**[DA DECIDERE]** Oggi nessuna riga viene cancellata. Proposta: un job di pulizia nel servizio,
una volta al giorno, con il suo lock ShedLock e i periodi in configurazione.

| Cosa | Proposta |
|---|---|
| Scarichi senza spedizioni (`NESSUNA_SPEDIZIONE`, `ERRORE_CHIAMATA`) | 30 giorni |
| Spedizioni `INVIATA` o `NON_IDENTIFICABILE` | 180 giorni dall'ultima ricezione |
| Spedizioni `DA_INVIARE` o `ERRORE_INVIO` | mai in automatico: richiedono un intervento |
| Scarichi con grezzo | quando nessuna spedizione li referenzia più, e comunque dopo 180 giorni |

```sql
-- Esempio, con i periodi della proposta
DELETE FROM public.eurodis_scarichi
 WHERE stato IN ('NESSUNA_SPEDIZIONE', 'ERRORE_CHIAMATA')
   AND avviato_il < now() - interval '30 days';

DELETE FROM public.eurodis_spedizioni
 WHERE stato_invio IN ('INVIATA', 'NON_IDENTIFICABILE')
   AND ultima_ricezione_il < now() - interval '180 days';

DELETE FROM public.eurodis_scarichi s
 WHERE s.avviato_il < now() - interval '180 days'
   AND NOT EXISTS (SELECT 1 FROM public.eurodis_spedizioni p WHERE p.id_scarico = s.id);
```

La chiave esterna `fk_eurodis_spedizioni_scarico` impedisce di cancellare uno scarico ancora
referenziato: l'ordine è prima le spedizioni, poi gli scarichi.

## 5. Ambiente

**[DECISO 10-11, Diego]** Credenziali e secret di `ce-db-sync`, riusati così come sono. Nessun
valore in questo documento.

### Configurazione Spring (`application.yaml`), come `ce-db-sync`

```yaml
spring:
  datasource:
    driver-class-name: org.postgresql.Driver
    url: ${DATASOURCE_URL:jdbc:postgresql://localhost:5432/ce_eud_api_in}
    username: ${DATASOURCE_USERNAME}
    password: ${DATASOURCE_PASSWORD}
    hikari:
      minimum-idle: ${DATASOURCE_HIKARI_MINIMUM_IDLE:1}
      maximum-pool-size: ${DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE:5}
      idle-timeout: ${DATASOURCE_HIKARI_IDLE_TIMEOUT:30000}
  sql:
    init:
      mode: never
```

Va tolto `spring.data.mongodb.uri`. `spring.sql.init.mode: never`: il servizio non crea tabelle,
le crea il DBA con gli script.

### Variabili e secret (Helm)

| Variabile | Dove | Valore |
|---|---|---|
| `DATASOURCE_URL` | `deploy-svil/values.yaml`, `envFrom` | `jdbc:postgresql://strkevoldb01azwe.postgres.database.azure.com:5432/ce_eud_api_in` |
| `DATASOURCE_URL` | `deploy-coll/values.yaml`, `envFrom` | `jdbc:postgresql://ttrkevoldb01azwe.postgres.database.azure.com:5432/ce_eud_api_in` |
| `DATASOURCE_USERNAME` | `.helm/values.yaml`, `env` | `secretKeyRef`: secret `ce-postgres`, chiave `datasource-name` |
| `DATASOURCE_PASSWORD` | `.helm/values.yaml`, `env` | `secretKeyRef`: secret `ce-postgres`, chiave `data-source-password` |
| `DATASOURCE_HIKARI_MINIMUM_IDLE` / `_MAXIMUM_POOL_SIZE` / `_IDLE_TIMEOUT` | `.helm/values.yaml`, `envFrom` | `1` / `5` / `30000` (quattro job, uno alla volta per pod) |
| `MONGO_STRING_CONNECTION` | `.helm/values.yaml`, `env` | **da togliere** |
| `TRUSTSTORE_PASSWORD`, `TRUSTSTORE_CA_POSTE_LOCATION`, volume `sslsecrets` (`ssl.trustore.sslsecretname: ssl-secrets`) | `.helm/values.yaml` | già presenti in `-in` (servono a Kafka): nessuna modifica |

Nel secret `ce-dichiarato-eurodis-in-secret` la chiave `mongo-string-connection` non serve più;
restano `api-key` e le chiavi di Kafka. Il secret `ce-postgres` esiste già nel namespace
`corriere-espresso-preadvising` (lo usano `ce-db-sync`, `ce-anagrafica`, `ce-ldv`).

Rete: `ce-anagrafica` e `ce-db-sync`, nello stesso namespace, raggiungono già entrambi i server;
non servono `hostAliases`. Come in `ce-db-sync`, l'URL non specifica `sslmode`.

### Maven

| Azione | Dipendenza |
|---|---|
| togliere | `spring-boot-starter-data-mongodb` |
| togliere | `net.javacrumbs.shedlock:shedlock-provider-mongo` |
| aggiungere | `spring-boot-starter-jdbc` |
| aggiungere | `org.postgresql:postgresql` (scope `runtime`, versione dal BOM di Spring Boot) |
| aggiungere | `net.javacrumbs.shedlock:shedlock-provider-jdbc-template` (`${shedlock.version}`, 6.10.0) |
| test | PostgreSQL in Testcontainers se la pipeline lo consente; altrimenti test dei repository con H2 in modalità PostgreSQL, sapendo che non copre i `CHECK` e gli indici parziali |

## 6. Cosa cambia nel codice di `-in` (guida per Amelia)

| Oggi (Mongo) | Con PostgreSQL |
|---|---|
| `dto/mongo/*Document` con `@Document`, `@Indexed` | classi o record senza annotazioni Mongo; si possono spostare in `dto/db` |
| `repository/*Repository` (Spring Data Mongo) | repository con `NamedParameterJdbcTemplate` e `RowMapper`, stessi metodi pubblici così i servizi cambiano poco |
| `id` dello scarico generato da Mongo | `UUID.randomUUID()` prima dell'`INSERT` |
| `GrezzoStore` con GridFS sopra 10 MB | il grezzo va sempre in `corpo`; via GridFS, `gridFsId` e `EURODIS_GREZZO_SOGLIA_GRIDFS`. Resta la soglia di guardia a 100 MB |
| `MongoLockProvider` in `SchedulingConfig` | `new JdbcTemplateLockProvider(Configuration.builder().withJdbcTemplate(jdbcTemplate).usingDbTime().build())` |
| id della richiesta manuale `tipo:edReference` | chiave composta `(tipo, ed_reference)` |

Query dei job, con gli indici che le servono:

```sql
-- Elaborazione: scarichi da elaborare e quelli rimasti in elaborazione oltre la durata del lock
SELECT * FROM public.eurodis_scarichi
 WHERE stato = 'DA_ELABORARE'
    OR (stato = 'IN_ELABORAZIONE' AND elaborazione_iniziata_il < :limite)
 ORDER BY avviato_il;                                    -- ind_eurodis_scarichi_da_elaborare

-- Ripubblicazione: record fermi
SELECT * FROM public.eurodis_spedizioni
 WHERE stato_invio = 'DA_INVIARE' AND ultima_ricezione_il < :limite;   -- ind_eurodis_spedizioni_da_inviare

-- Gauge delle spedizioni in attesa
SELECT count(*) FROM public.eurodis_spedizioni
 WHERE stato_invio IN ('DA_INVIARE', 'ERRORE_INVIO');                 -- ind_eurodis_spedizioni_in_attesa

-- Nuova ricezione di una spedizione: un solo record, aggiornato (RF-08, RF-09)
INSERT INTO public.eurodis_spedizioni (id, ed_reference, id_scarico, id_file, posizione, fonte,
       rif_grezzo, ricevuto_il, json, stato_invio, tentativi_invio, numero_ricezioni,
       prima_ricezione_il, ultima_ricezione_il)
VALUES (:id, :edReference, :idScarico, :idFile, :posizione, :fonte, :rifGrezzo, :ricevutoIl,
        :json, 'DA_INVIARE', 0, 1, :ricevutoIl, :ricevutoIl)
ON CONFLICT (id) DO UPDATE SET
       id_scarico = EXCLUDED.id_scarico, id_file = EXCLUDED.id_file, posizione = EXCLUDED.posizione,
       fonte = EXCLUDED.fonte, rif_grezzo = EXCLUDED.rif_grezzo, ricevuto_il = EXCLUDED.ricevuto_il,
       json = EXCLUDED.json, stato_invio = 'DA_INVIARE', tentativi_invio = 0, ultimo_errore = NULL,
       numero_ricezioni = public.eurodis_spedizioni.numero_ricezioni + 1,
       ultima_ricezione_il = EXCLUDED.ultima_ricezione_il;
```

Il passaggio a uno stato (per esempio `DA_ELABORARE` → `IN_ELABORAZIONE`) si fa con
`UPDATE ... WHERE id = :id AND stato = :statoAtteso`: con il lock ShedLock non serve, ma protegge
da una ripresa concorrente.

**Dati già in Mongo**: in svil e coll sono solo prove. Proposta: non si migrano (domanda 3).

## 7. Cosa serve dal DBA e dalla piattaforma

1. Script 1 sul server svil (`strkevoldb01azwe`) e su quello di collaudo (`ttrkevoldb01azwe`),
   con il `GRANT ... ON SCHEMA public` eseguito connessi a `ce_eud_api_in`.
2. Script 2, 3, 4 e 5 come `ce_user` su `ce_eud_api_in`, in entrambi gli ambienti (lo script 6
   solo se le tabelle le crea un altro utente).
3. Conferma che l'utente nel secret `ce-postgres` (chiave `datasource-name`) è `ce_user`, cioè il
   proprietario del nuovo database.
4. Togliere la chiave `mongo-string-connection` da `ce-dichiarato-eurodis-in-secret`, dopo il rilascio.

## 8. Domande per Diego

1. **Utente.** Il secret `ce-postgres` di `ce-db-sync` contiene proprio `ce_user`? Se è un altro
   utente servono grant su `ce_eud_api_in` per quell'utente (script 6).
2. **Conservazione.** Vanno bene i periodi della sezione 4 (30 giorni per i run vuoti, 180 per il
   resto)? Esiste una regola Poste sulla conservazione dei dati di spedizione?
3. **Dati in Mongo.** I dati di prova in svil si possono abbandonare senza migrarli?
4. **Produzione.** Server e nome del database di produzione: stessi nomi (`ce_eud_api_in`)?
