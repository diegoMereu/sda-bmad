# Ambienti svil e collaudo

Solo nomi e chiavi: **password, token e valori dei secret non si scrivono mai**, nemmeno se
comparsi in una conversazione.

| | Sviluppo (svil) | Collaudo (coll) |
|---|---|---|
| Cluster OpenShift | `https://api.gen3gpazne.cloudsvil.poste.it:6443` | `https://api.gen3gpazne.cloudcoll.poste.it:6443` |
| Namespace | `corriere-espresso-preadvising` | idem |
| Kafka | `kafka-pcl1.svil.kafka.aztestposte:9092`, `kafka-pcl2…:9092` (raggiungibili dalla postazione); nei values porta 9094 con `hostAliases` | porta 9094; `hostAliases` `tlogkaf01a` 10.60.35.231 (`kafka-pcl1`), `tlogkaf02a` 10.60.35.232 (`kafka-pcl2`), `tlogkaf03a` 10.60.35.233 (`kafka-pcl3`), dominio `.coll.kafka.aztestposte` |
| PostgreSQL | `strkevoldb01azwe.postgres.database.azure.com:5432` | `ttrkevoldb01azwe.postgres.database.azure.com:5432` |
| EURODIS | TEST `https://testapi.eurodis.com/...` (restituisce sempre gli stessi dati) | TEST |

Database: `ce_cen` (anagrafica, db-sync), `ce_eud_api_in` (eurodis-in). Endpoint privati:
**non raggiungibili dalla postazione** (porta 5432 chiusa). Le DDL le esegue il DBA.

## Secret condivisi (nomi e chiavi)

- `ce-postgres`: `datasource-name`, `data-source-password` (utente `ce_user`) → env
  `DATASOURCE_USERNAME`, `DATASOURCE_PASSWORD`; URL in `DATASOURCE_URL` per ambiente.
- `ssl-secrets`: `trustore-password`; truststore montato in `/custom/ssl/trustore-file`.
- Secret propri del servizio `<servizio>-secret` (chiavi API, ecc.).

## Accesso al cluster

- Il server API spesso non risponde dalla postazione (timeout): in quel caso log e pod li legge
  Diego.
- Quando Diego dà un token: usarlo solo sul momento, con un kubeconfig separato nello scratchpad
  (`oc login --kubeconfig=<scratchpad>/kc-svil ...`) per non interferire con altri agenti; solo
  comandi di lettura (get, logs, exec di sola lettura); `oc logout` alla fine. Mai salvare il token.

## Deploy

Pipeline Jenkins ALM (job `<servizio>-build` e `<servizio>-deploy`) dal branch indicato. I deploy li
lancia Diego: all'agente spetta indicare repo, branch e commit da rilasciare. `develop` dei repo
`ce-` è protetto (richiede pull request; l'utenza di Diego ha il bypass).

## Lezioni dagli ambienti

- Un errore di riconoscimento del database (ShedLock "unknown database product") o "Could not open
  JDBC Connection" in più servizi insieme indica il database irraggiungibile, non un difetto del
  codice.
- `NOT_ENOUGH_REPLICAS`, `NOT_LEADER_OR_FOLLOWER`, "Connection to node 2 ... could not be
  established" su più producer insieme (eurodis-in, smistatore, eurodis-mapper) indicano un broker
  Kafka di collaudo giù (16-11-2026: `tlogkaf02a`/`kafka-pcl2`, 10.60.35.232), non un difetto del
  codice. I servizi riprovano da soli; quando il broker torna, si riprende senza intervento.
- Una route che risponde 200 su un endpoint e 500 su un altro dello stesso servizio può dipendere
  dalla cache (`@Cacheable`) che maschera un database giù.
