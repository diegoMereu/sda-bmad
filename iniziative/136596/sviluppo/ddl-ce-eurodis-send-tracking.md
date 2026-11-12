# `ce-eurodis-send-tracking` — Persistenza su PostgreSQL: DDL e ambiente

> **Superato il 12-11: lo storico non serve, nessuna DDL per send-tracking.** Decisione di Diego:
> send-tracking invia ogni evento direttamente a EURODIS, senza database `ce_eud_tracking`, tabella
> `eurodis_tracce` né ShedLock. Architettura attuale: sezione 14 di
> [ce-eurodis-send-tracking.md](ce-eurodis-send-tracking.md) 0.4 (implementazione `ec2f65b`). Il
> documento resta come riferimento se servisse uno storico minimo (ST-07).

**Iniziativa**: 136596 — Eurodis autoproduttore · **Versione**: 0.1 · **Data**: 2026-11-12
**Autore**: Winston (architect) · **Destinatari**: DBA e piattaforma (script e secret), Amelia (dev)
**Specifica di riferimento**: [ce-eurodis-send-tracking.md](ce-eurodis-send-tracking.md) 0.3, sezioni 3.3 e 14

Lo storico degli invii di send-tracking va su PostgreSQL, sullo stesso server di `-in`, in un
**database dedicato `ce_eud_tracking`**. Credenziali: secret `ce-postgres`, come `ce-db-sync` e `-in`.
Le LDV EURODIS **non** si salvano qui: il filtro 3 le cerca nel MongoDB del preadvising
(`dichiarato_events`, specifica 3.3).

---

## 1. Scelte

| Scelta | Motivo |
|---|---|
| **Database dedicato `ce_eud_tracking`**, non le tabelle nel database di `-in` | Servizi con cicli di vita, volumi e conservazione diversi; nessuna dipendenza fra i due schemi. Stesso server e stesso utente: per il DBA cambia solo il nome del database |
| **JDBC con `NamedParameterJdbcTemplate`**, niente JPA né Flyway | Convenzione dei servizi `ce-` ([linee guida](../../../contesto/linee-guida-sviluppo.md)); script nel repo in `sql/ddl/`, eseguiti dal DBA |
| **Schema `public`** | Database dedicato, come `ce_eud_api_in` |
| **Idempotenza con vincolo `UNIQUE (ldv, status_sda, data_traccia)`** e `INSERT ... ON CONFLICT DO NOTHING` | Kafka consegna almeno una volta: una traccia ripetuta non crea righe né invii (RF-18) |
| **`data_traccia` in `timestamptz`** | `dataTrack` arriva in ora italiana senza fuso (V-04): il servizio la converte da `Europe/Rome` e salva l'istante; il testo originale resta in `data_traccia_testo` |
| **Traccia ricevuta in `text`** | Testo dell'evento così com'è, per audit e ripresa. Può contenere dati personali: si legge solo per analisi, non va nei log |
| **Stati in `varchar` con `CHECK`** | Come in `-in` |
| **ShedLock JDBC** con `DatabaseProduct.POSTGRES_SQL` dichiarato e `usingDbTime()` | Il riconoscimento automatico fallisce senza connessione e blocca i job (lezione di `-in`, 10-11) |

## 2. Script

Ordine: 1 come amministratore sul database `postgres`; il resto come `ce_user`, connessi a
`ce_eud_tracking`. Dal 2 in poi si possono rieseguire.

### Script 1 — Database

```sql
CREATE DATABASE ce_eud_tracking
    WITH
    OWNER = ce_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'it_IT.utf8'
    LC_CTYPE = 'it_IT.utf8'
    CONNECTION LIMIT = -1
    TEMPLATE = template0;
GRANT ALL PRIVILEGES ON DATABASE ce_eud_tracking TO ce_user;
-- connessi a ce_eud_tracking (\c ce_eud_tracking):
GRANT USAGE, CREATE ON SCHEMA public TO ce_user;
```

Il `GRANT ... ON SCHEMA public` va eseguito **connessi a `ce_eud_tracking`**, altrimenti agisce sul
database `postgres`.

### Script 2 — `eurodis_tracce`

Una riga per ogni traccia SDA che ha superato i tre filtri (specifica 3.2), con l'esito dell'invio.

```sql
CREATE TABLE IF NOT EXISTS public.eurodis_tracce (
    id                      uuid           NOT NULL,
    ldv                     varchar(50)    NOT NULL,
    status_sda              varchar(3)     NOT NULL,
    data_traccia            timestamptz    NOT NULL,
    data_traccia_testo      varchar(30)    NOT NULL,
    codice_eurodis          varchar(4)     NOT NULL,
    ed_reference            bigint,
    europlate_barcode       varchar(24),
    numero_colli            integer,
    location_code           varchar(10),
    country_code            varchar(2),
    id_preadvising          varchar(64),
    id_file                 varchar(64),
    stato                   varchar(25)    NOT NULL,
    motivo                  varchar(300),
    tentativi               integer        NOT NULL DEFAULT 0,
    prossimo_tentativo_il   timestamptz,
    errori_eurodis          varchar(500),
    warning_eurodis         varchar(500),
    inviato_il              timestamptz,
    traccia_json            text           NOT NULL,
    kafka_partizione        integer,
    kafka_offset            bigint,
    ricevuto_il             timestamptz    NOT NULL,
    aggiornato_il           timestamptz    NOT NULL,
    CONSTRAINT pk_eurodis_tracce PRIMARY KEY (id),
    CONSTRAINT uk_eurodis_tracce_traccia UNIQUE (ldv, status_sda, data_traccia),
    CONSTRAINT ck_eurodis_tracce_stato CHECK (stato IN
        ('DA_INVIARE', 'DA_RIPROVARE', 'CREATO', 'RIFIUTATO', 'SCARTATO', 'ABBANDONATO', 'ERRORE_CONFIGURAZIONE')),
    CONSTRAINT ck_eurodis_tracce_codice CHECK (codice_eurodis ~ '^[0-9]{4}$')
);

-- job di invio: candidati da inviare o riprovare, in ordine per collo
CREATE INDEX IF NOT EXISTS ix_eurodis_tracce_da_inviare
    ON public.eurodis_tracce (prossimo_tentativo_il, ldv, data_traccia)
    WHERE stato IN ('DA_INVIARE', 'DA_RIPROVARE');
-- ordine degli eventi dello stesso collo e ricerca per LDV
CREATE INDEX IF NOT EXISTS ix_eurodis_tracce_ldv_data
    ON public.eurodis_tracce (ldv, data_traccia);
-- conservazione
CREATE INDEX IF NOT EXISTS ix_eurodis_tracce_ricevuto
    ON public.eurodis_tracce (ricevuto_il);

COMMENT ON TABLE  public.eurodis_tracce IS 'Tracce SDA delle LDV EURODIS e invio a EURODIS send-tracking (una riga per traccia)';
COMMENT ON COLUMN public.eurodis_tracce.ldv IS 'LDV SDA (payload.ldv), inviata come deliveryPartnerBarcode';
COMMENT ON COLUMN public.eurodis_tracce.data_traccia IS 'payload.dataTrack convertita da Europe/Rome';
COMMENT ON COLUMN public.eurodis_tracce.traccia_json IS 'Evento PACCHI.TRACKING come ricevuto: puo contenere dati personali';
COMMENT ON COLUMN public.eurodis_tracce.stato IS 'Sezione 6 della specifica';
```

### Script 3 — `shedlock`

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

### Script 4 — Permessi (solo se gli oggetti li crea un utente diverso da `ce_user`)

```sql
ALTER TABLE public.eurodis_tracce OWNER TO ce_user;
ALTER TABLE public.shedlock       OWNER TO ce_user;
```

### Script 5 — MongoDB del preadvising (owner di `dichiarato_events`, non questo database)

Il filtro 3 cerca l'LDV in `dichiarato_events` (specifica 3.3, V-06). Nel codice dei servizi non è
dichiarato un indice su `spedizione.collo.id_ldv`: va verificato sul database e, se manca, creato
dall'owner della collezione:

```js
db.dichiarato_events.createIndex(
  { "spedizione.collo.id_ldv": 1, "canale": 1 },
  { name: "ix_dichiarato_events_ldv_canale", background: true }
)
```

## 3. Dimensioni attese

| Tabella | Righe al giorno | Note |
|---|---|---|
| `eurodis_tracce` | ~5-8 tracce del foglio per collo EURODIS × colli EURODIS al giorno (volumi EURODIS ancora da chiedere, PA-14) | solo le tracce delle LDV EURODIS: i 9,85 milioni di eventi `CE` al giorno si filtrano prima |
| `shedlock` | 1-2 righe fisse (job di invio, job di pulizia) | |

## 4. Conservazione

**[DA DECIDERE]** Proposta: job di pulizia giornaliero che cancella le righe in stato finale
(`CREATO`, `RIFIUTATO`, `SCARTATO`, `ABBANDONATO`) più vecchie di 90 giorni
(`eurodis.tracking.conservazione-giorni`). Le righe ancora da inviare non si cancellano mai.

## 5. Ambiente

| Variabile | svil | coll | Fonte |
|---|---|---|---|
| `DATASOURCE_URL` | `jdbc:postgresql://strkevoldb01azwe.postgres.database.azure.com:5432/ce_eud_tracking` | `jdbc:postgresql://ttrkevoldb01azwe.postgres.database.azure.com:5432/ce_eud_tracking` | values per ambiente; template prod `_#DATASOURCE_URL` |
| `DATASOURCE_USERNAME` / `DATASOURCE_PASSWORD` | secret `ce-postgres`, chiavi `datasource-name` / `data-source-password` | idem | `secretKeyRef` |
| `DATASOURCE_HIKARI_*` | `MINIMUM_IDLE` 1, `MAXIMUM_POOL_SIZE` 5 | idem | come `-in` |
| `MONGO_STRING_CONNECTION` | secret `ce-dichiarato-validatore-secret`, chiave `mongo-string-connection` | idem | come `ce-dichiarato-adapter` |

Maven: `spring-boot-starter-jdbc`, `org.postgresql:postgresql`, `shedlock-spring` e
`shedlock-provider-jdbc-template` 6.10.0, `spring-boot-starter-data-mongodb` (solo lettura),
`com.github.ben-manes.caffeine:caffeine` per la cache delle LDV; H2 solo nei test (non copre
`ON CONFLICT`, indici parziali e `CHECK` con espressioni regolari: dirlo nel report).

## 6. Cosa serve dal DBA e dalla piattaforma

1. Script 1-3 su svil e collaudo (database `ce_eud_tracking`).
2. Indice su `dichiarato_events` (script 5), o conferma che esiste.
3. ACL Kafka: lettura di `PACCHI.TRACKING` per l'utente SCRAM di send-tracking, consumer group
   `ce-eurodis-send-tracking`; in produzione va chiesto all'owner del topic.
4. Secret `ce-eurodis-send-tracking-secret`: `api-key` EURODIS e credenziali SCRAM, come oggi.
