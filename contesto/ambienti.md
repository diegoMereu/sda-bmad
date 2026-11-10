# Ambienti svil e collaudo

Solo nomi e chiavi: **password, token e valori dei secret non si scrivono mai**, nemmeno se
comparsi in una conversazione.

| | Sviluppo (svil) | Collaudo (coll) |
|---|---|---|
| Cluster OpenShift | `https://api.gen3gpazne.cloudsvil.poste.it:6443` | `https://api.gen3gpazne.cloudcoll.poste.it:6443` |
| Namespace | `corriere-espresso-preadvising` | idem |
| Kafka | `kafka-pcl1.svil.kafka.aztestposte:9092`, `kafka-pcl2…:9092` (raggiungibili dalla postazione); nei values porta 9094 con `hostAliases` | vedi values `deploy-coll` |
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
- Una route che risponde 200 su un endpoint e 500 su un altro dello stesso servizio può dipendere
  dalla cache (`@Cacheable`) che maschera un database giù.
