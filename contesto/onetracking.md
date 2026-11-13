# OneTracking (OT)

Portale degli operatori SDA/Poste (assistenza clienti, filiali, SDA) che mostra **in un'unica vista
lo stato di una spedizione** leggendo da molti back-end: dichiarato, tracking, giacenze, ritiri,
contrassegni, POD, reclami NFEA, immagini, alert proattivi. Nessun database proprio per i dati di
spedizione: aggrega in lettura.

Repository in `C:\Users\diego.mereu\gitposte\SDA\ONETRACKING` (GitLab
`gitlab.alm.poste.it/ONETRACKING/...`), namespace OpenShift **`onetracking`**. Assessment del
13-11-2026: prima di usare un dettaglio in un documento ricontrolla il codice su `origin/develop`.

## Repository

| Repo | Ruolo | Stack | Branch di riferimento |
|---|---|---|---|
| `PRESENTATION/portal-pages` | Front-end del portale | Nuxt **3.14** / Vue 3 su `develop` (Nuxt 2 sui vecchi `gen3`, ormai cancellato su origin) | `develop`, `master` (release `AA.MM.NN`) |
| `PRESENTATION/shipment-info` | BFF: espone `/api/**` al FE e chiama tutti i sistemi | Spring Boot 2.7.18, Java 11 | `develop`, `master` |
| `SHIPMENT/sda-wrapper` | Gateway JDBC verso i DB Informix SDA (ermes, pacchi, poste, billings), 50+ endpoint REST | Spring Boot | `develop` |
| `SHIPMENT/alert-proattivo-wrapper` | Alert proattivi (cambio stato, cambio frazionario, dashboard NPS) | Spring Boot | `master` |
| `CE-FILIALI/ce-filiali-wrapper` | Immagini LdV e configurazione filiali (con CE Blob Interface) | Spring Boot | `gen3` |
| `USER/management` | Utenti, azioni, ultime ricerche (management-onetracking, IAM) | Spring Boot, script SQL in `ScriptSql/` | `develop` |
| `MONITORING/onetracking-otel` | Collector OpenTelemetry del namespace | config OTel | `develop` |

I README dei repo sono stati scritti nell'assessment (non committati nei repo).

## Flusso di una richiesta

```
operatore (browser) -> SiteMinder (header sm_user, ruolo, frazionario, filiale, ...)
  -> portal-pages (Nuxt, proxy /api -> shipment-info, /user -> management)
  -> shipment-info -> sda-wrapper (Informix) | Ermes Full-Tracking (DataPower) | Solr T&T-Repo
                   | alert-proattivo-wrapper | ce-filiali-wrapper | NFEA | SAP | Contract Manager ...
```

- **Autenticazione**: nessun login applicativo, solo header SiteMinder. Ruoli con prefisso `CE_`
  (default `CE_BASE`). Tipologia utente da `x-forwarded-server`: `-SDA`, `-FILIALI`, altrimenti
  ASSISTENZA (alcuni tab, es. Costo spedizione e Dati cliente, solo per ASSISTENZA).
- **Funzionalità**: chiavi `OTR_*` (es. `OTR_RICERCA`, `OTR_RISTAMPA_LV`, `OTR_RICERCA_IMMAGINI`,
  `OTR_GESTIONE_ALERT_PROATTIVI`) da `api/profilazione` (JWT) e da `USER/management`.
- In locale: shipment-info su `8083`, management su `8091`, header SiteMinder simulati con ModHeader
  (`shipment-info/AVVIO_LOCALE.txt`).

## Da dove legge shipment-info

| Area del portale | Sistema | Proprietà |
|---|---|---|
| Ricerche (LdV, ID ritiro, codice prenotazione, ordine, mancata consegna, dossier, avanzata), mittente/destinatario, caratteristiche, costi, giacenza/svincolo, ritiri, contrassegno, BIC, firma | `sda-wrapper` → Informix | `onetracking.wrapperUrl` |
| Tracking, full tracking, POD | Ermes Full-Tracking (EJB su WebSphere via DataPower, XML) | `ermes.datapower.url`, `*.path` |
| Tab TUP, anagrafica LdV | **Solr T&T-Repo** (AppGW): `pacchi_tracking`, `pacchi_anagrafica`, `sda_anagldv`, `pacchi_stato`, `pacchi_blacklist`, `postazioni_di_stampa`; `ce-transcodifiche-event` | `solrappgw.endpoint`, `solr.username`/`solr.password` |
| Alert proattivo | `alert-proattivo-wrapper` | `onetracking.alert.wrapperUrl` |
| Immagini | `ce-filiali-wrapper` + CE Blob Interface | `onetracking.images.wrapperUrl`, `ce-blob-interface.url` |
| Reclami | NFEA + token Microsoft Entra | `nfea.url`, `microsoft.url` |
| Ristampa LdV / DHL | SOAP RISTAMPA-LDV; Contract Manager (c4logistic) | `ristampa.ldv.endpoint`, `contract.manager.endpoint` |
| Resi Amazon | SAP (SOAP RFC), Amazon WS | `amazon.endpoint`, `amazon.ws.*` |
| Regole/anomalie | CE Rules | `ce-rules.endpoint` |

Client Solr: `rest/RestClientSolr.java` (RestTemplate, query costruite a mano con `build(true)`).

## T&T-Repo e preavviso

Le collection Solr del T&T-Repo che servono al preavviso (ICD in `iniziative/144216/cliente/`):
- **`pacchi_anagrafica`**: un documento per LdV (`id` = LdV) e, dall'iniziativa 138975, uno per
  preavviso (`id` = `id_preadvising`/`aggregate_id`, con `ldv`, `id_file`, `event_type`
  `PRE_ENRICHMENT|COMPLETED|ERROR`, `event_ts`, `preadv_errori`). Sul documento LdV: `id_preadvising`
  (preavviso valido), `stato_LdV` (`LDV SENZA PREAVVISO`, `LDV ON TIME`, `LDV IN RITARDO`),
  `timestamp_firstscan`.
- **`pacchi_file`**: un documento per file di preavviso (`idfile`, `nomefile`, `upload_time_stamp`,
  `idStato`/`status` `ST_F0001`…`ST_F0008`, `channel`, errori di file), alimentato da
  `preadvising.evensource`.

## Dismissione di sda-wrapper (analisi in corso)

`OT_Analisi_Impatto_SDA_Wrapper_v7.2.docx` (SharePoint `07. Iniziative/2026/02.Documenti/Dismissione
sda-wrapper e migrazione vs tup`): sda-wrapper ed Ermes Full-Tracking da dismettere.
- Tracciatura → `ce-transcodifiche-event` (`/api/onetracking/recupera-tup`, Solr TUP); test
  comparativo obbligatorio fra le 10 UNION di Ermes FT e Solr TUP.
- Dati spedizione (dettaglio, mittente/destinatario, caratteristiche, costi, BIC) → **AnagraficaTT**
  (ICD draft v1.0.0, client da scrivere).
- Ricerca avanzata bloccata (nessun target); giacenze, ritiri, prenota ritiro, contrassegno, POD PDB
  oltre 45 giorni in fase 2. Open point OP-01…OP-14 nel documento.
- Flussi già indipendenti da sda-wrapper: alert proattivo, immagini, NFEA, TUP, ristampe, Amazon,
  login/permessi, tracking, POD.

## Deploy

- Jenkins (`build.jenkinsFile`, `deploy.jenkinsFile`), `pipeline.yaml` con `NAMESPACE: onetracking`,
  immagini `postesviluppo.azurecr.io` (svil) e `palmcreg01a.azurecr.io` (coll/cert/prod).
- Route svil `<servizio>-onetracking.cloudsvil.poste.it`, coll `...cloudcoll.poste.it`.
- Values: `deploy-svil/`, `deploy-coll/`, template di cert/prod `deploy-config/values_TEMPLATE.yaml`.

## Attenzioni

- portal-pages: SAS token Azure in chiaro in `urlRistampaDhl` (nuxt.config, values), plugin axios con
  `NODE_TLS_REJECT_UNAUTHORIZED='0'` e log delle request intere. Da segnalare, non copiare.
- shipment-info: `application-test.properties` contiene credenziali Solr di test versionate.
- Iniziative che toccano OT: 144216 (sezione preavviso), 138130 (causale reso mittente), 126278
  (autenticazione NFEA), 131176 (digipod), 138151 (blacklist indirizzi), 141077 (POD).
