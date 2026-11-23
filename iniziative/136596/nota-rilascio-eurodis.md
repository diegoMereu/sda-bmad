# Nota di rilascio progetto

### Release EURODIS INVIOSYSTEM (136596)

### Lista iniziative

**ce-dichiarato-eurodis-in**: ragione sociale del cliente (`EURODIS GmbH`) negli eventi di stato del file; file fittizio registrato nella collection Mongo `preadvising_file` come ce-dichiarato-builder (chiusura del file dalla state machine); script DDL 07 della tabella `eurodis_postazioni`
**ce-dichiarato-eurodis-mapper**: solo LDV PDB (le altre si scartano); cliente, contratto, centro di costo, ragione sociale, partita IVA e codice fiscale dalla postazione del seme LDV (cache → tabella `eurodis_postazioni` → ce-vendite → upsert), configurazione solo come fallback; un record per collo verso il pre-enrichment (`id_record_multicollo` comune), figli LDV PDB a 22 caratteri accettati e divisi in madre e figlio come nel validatore, `id_collo` = LDV; prodotto BEP (`rif_prodotto_cliente`) dalla LDV madre: ce-rules (spento di default), poi regole locali sul prefisso, poi configurazione (`APT000901`)
**ce-eurodis-send-tracking**: filtro EURODIS prima dell'invio: LDV PDB, seme in lista, postazione registrata in `eurodis_postazioni` con `eurodis = true`; LDV figlia a 22 caratteri riconosciuta dalla madre
**ce-event-handler-monitoring**: canale `EUD_INVIOSYSTEM` tra i canali ammessi dal filtro di monitoraggio

### Ambienti

| **Componente**       | **Certificazione**                                                                       | **Produzione**                                                                                                                               |
|----------------------|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **OCP Gen3 Console** | https://console.gen3gpazwe.cloudcert.poste.it                                            | https://console.gen3gpazwe.cloud.poste.it                                                                                                    |
| **OCP Gen3 Api**     | https://api.gen3gpazwe.cloudcert.poste.it:6443                                           | https://api.gen3gpazwe.cloud.poste.it:6443                                                                                                   |
| **DB OL**            | jdbc:postgresql://ctrkevoldb01azwe.postgres.database.azure.com:5432/                     | jdbc:postgresql://ptrkevoldb01azwe.postgres.database.azure.com:5432/  e jdbc:postgresql://ptrkevoldb02azwe.postgres.database.azure.com:5432/ |
| **Kafka**            | CLOGKAF01A, CLOGKAF02A, CLOGKAF03A                                                       | PLOGKAF01A, PLOGKAF02A, PLOGKAF03A                                                                                                           |

### Microservizi

| **Namespace**                     | **Microservizio**                 | **Commit develop** | **Note**                                              |
|-----------------------------------|-----------------------------------|--------------------|-------------------------------------------------------|
| **corriere-espresso-preadvising** | ce-dichiarato-eurodis-in          | 8995ae8            | include 27bbe54 (ragione sociale), ad4e5d8 (DDL 07), 8ce7666 (preadvising_file) |
| **corriere-espresso-preadvising** | ce-dichiarato-eurodis-mapper      | aac007f | include 5a5faf1, 507736a, 253fd0d, 97242eb, 8a796f4; rilasciare dopo lo script 07 |
| **corriere-espresso-preadvising** | ce-eurodis-send-tracking          | b472297            | include c592058, 438c1fe; rilasciare dopo il mapper   |
| **corriere-espresso-preadvising** | ce-event-handler-monitoring       | 4f85f74            | solo values                                           |

### Repository

| **Nome**                          | **Repository di sviluppo**                                                                                  |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------|
| **ce-dichiarato-eurodis-in**      | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in               |
| **ce-dichiarato-eurodis-mapper**  | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper           |
| **ce-eurodis-send-tracking**      | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-eurodis-send-tracking               |
| **ce-event-handler-monitoring**   | https://gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-event-handler-monitoring                       |

Repository di certificazione e produzione: da indicare (i tre servizi EURODIS sono su GitHub Enterprise).

### Attivita' propedeutiche

1. **Database `ce_eud_api_in`** (DBA), script in `sql/ddl/` del repository ce-dichiarato-eurodis-in:
   - dove il database esiste già (script 01-06 eseguiti): eseguire `07_ddl_eurodis_postazioni.sql` come `ce_user`, e la riga nuova di `06_permessi.sql` (`ALTER TABLE public.eurodis_postazioni OWNER TO ce_user`) se le tabelle non le crea `ce_user`;
   - dove il database non esiste: eseguire in ordine `01` (come amministratore, connessi a `postgres`), poi `02`…`07` come `ce_user` connessi a `ce_eud_api_in`, poi `06_permessi.sql`.
   - Mapper e send-tracking si collegano con lo stesso `ce_user` del secret `ce-postgres`: nessun grant aggiuntivo. Con un altro utente: `SELECT, INSERT, UPDATE` su `eurodis_postazioni` per il mapper, `SELECT` per il send-tracking.
2. **Secret**:
   - `ce-postgres` (`datasource-name`, `data-source-password`) e `ssl-secrets` disponibili anche per ce-dichiarato-eurodis-mapper e ce-eurodis-send-tracking;
   - ce-dichiarato-eurodis-in legge Mongo (collection `preadvising_file`) dal secret di ce-dichiarato-validatore: `ce-dichiarato-validatore-secret`, chiave `mongo-string-connection`. Nessun secret nuovo.
3. **Network policy**: ce-dichiarato-eurodis-mapper → `ce-vendite.corriere-espresso-preadvising.svc.cluster.local:8080`. Verso `ce-rules.corriere-espresso-core.svc.cluster.local:8080` solo se si accende `PRODOTTO_CE_RULES_ABILITATO` (spento di default).
4. **Values per ambiente**: `DATASOURCE_URL` verso `ce_eud_api_in` per mapper e send-tracking (in `deploy-config/values_TEMPLATE.yaml` è un segnaposto); `EURODIS_TRACKING_SEMI` del send-tracking con i `pds_code` INVIOSYSTEM del contratto EURODIS dell'ambiente (svil: `W2308`).

### Modalità di rilascio microservizi

Ordine: script DB → ce-dichiarato-eurodis-in → ce-dichiarato-eurodis-mapper → ce-eurodis-send-tracking; ce-event-handler-monitoring indipendente.

1. Eseguire su Jenkins le seguenti **pipeline di release**:

| **Microservizio**                     | **Upstream di release**                   |
|---------------------------------------|-------------------------------------------|
| **ce-dichiarato-eurodis-in**          | ce-dichiarato-eurodis-in-release          |
| **ce-dichiarato-eurodis-mapper**      | ce-dichiarato-eurodis-mapper-release      |
| **ce-eurodis-send-tracking**          | ce-eurodis-send-tracking-release          |
| **ce-event-handler-monitoring**       | ce-event-handler-monitoring-release       |

2. Eseguire su Jenkins i seguenti **upstream di deploy**:

| **Microservizio**                     | **Upstream di deploy**                        | MERGE REQUEST |
|---------------------------------------|-----------------------------------------------|---------------|
| **ce-dichiarato-eurodis-in**          | deploy-ce-dichiarato-eurodis-in-upstream      | NO            |
| **ce-dichiarato-eurodis-mapper**      | deploy-ce-dichiarato-eurodis-mapper-upstream  | NO            |
| **ce-eurodis-send-tracking**          | deploy-ce-eurodis-send-tracking-upstream      | NO            |
| **ce-event-handler-monitoring**       | deploy-ce-event-handler-monitoring-upstream   | NO            |

### Verifiche dopo il rilascio

- dopo il primo scarico: riga del seme INVIOSYSTEM in `eurodis_postazioni` con `eurodis = true` (verifica dell'upsert, non provato su PostgreSQL);
- `rif_prodotto_cliente` coerente con il prefisso della LDV (3U/4U → `APT000901`) e `eurodis_mapper_prodotto_total{sorgente="regole"}` in crescita;
- spedizione multicollo: un record per collo nel pre-enrichment, nessuno scarto 317;
- documento del file fittizio in `preadvising_file` con `stato` 0, poi chiuso dalla state machine;
- tracce delle LDV EURODIS inviate a EURODIS; tracce di altre LDV scartate (`postazione_non_eurodis`, `ldv_non_pdb`).
