# Prompt — documento funzionale `shipment-info` (API preavviso)

> Prompt per Mary (analyst): genera il documento funzionale del back-end `shipment-info` per
> l'iniziativa 144216.
> Output: `iniziative/144216/sviluppo/shipment-info.md`, da passare alla sviluppatrice back-end.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per la sviluppatrice** del
back-end `shipment-info` di OneTracking, nell'iniziativa 144216 "Assistenza Clienti — Customer
Journey preavviso" (PRJ0049429, Poste Italiane / SDA, filone PCL-127).

OneTracking è il portale degli operatori SDA/Poste per lo stato delle spedizioni. `shipment-info`
(Spring Boot 2.7, Java 11) è il BFF che espone `/api/**` al front-end Nuxt `portal-pages`. Nel
dettaglio LdV si aggiunge la sottosezione "Informazioni preavviso": al back-end si chiede la nuova API
`GET /api/preavviso/{ldv}`, che legge il preavviso nel T&T-Repo (Solr, collection
`pacchi_anagrafica` e `pacchi_file`).

Due sviluppatrici lavorano **in parallelo** su back-end e front-end, sul branch
`144216_preavviso_onetracking` (da `origin/develop`), sul contratto di `analisi.md`. Il contratto e
le regole sono **vincolanti**: il documento li dettaglia, non li cambia. Incoerenze e buchi vanno
fra le domande aperte.

Decisione di Diego del 13-11 (AS-01 chiusa): lo stato della regola di scelta è `event_type` del
record di preavviso (`PRE_ENRICHMENT` = ST_R0002, `COMPLETED` = ST_R0004, `ERROR` =
ST_R0003/ST_R0006); si sceglie il `COMPLETED` (fra più `COMPLETED` il più recente per `event_ts`),
altrimenti il penultimo per `event_ts`. Va riportata come regola confermata.

# Fonti (in `iniziative/144216/`)

- `analisi.md`: regole di scelta, mapping, contratto JSON, assunzioni AS-01…AS-07.
- `cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`: mock up con i tre casi
  (DREQ0062862, DREQ0062864, DREQ0062865, DREQ0062866).
- `cliente/ICD_PACCHI_ANAGRAFICA_138975_v1.0.xlsx`, `cliente/ICD_PACCHI_FILE_v1.xlsx` (leggili con
  openpyxl): campi, tipi, indicizzazione, stored, mappatura con il topic.
- `contesto/onetracking.md`, `contesto/glossario-ce.md`, `contesto/microservizi-preadvising.md`
  (sezione `preadvising.evensource`).
- Codice in sola lettura (non modificare, non fare checkout):
  `gitposte/SDA/ONETRACKING/PRESENTATION/shipment-info`, in particolare `rest/RestClientSolr.java`,
  `controller/TupController.java`, `impl/MittDestServiceImpl.java`, `exception/GenericExceptionHandler.java`,
  `config/RestTemplateConfig.java`. Usalo per dire **dove** si interviene, non per riscrivere il codice.
- Modello di forma: `iniziative/136596/sviluppo/ce-eurodis-send-tracking.md`.

# Cosa ti chiedo

Struttura: contesto e obiettivo, requisiti DREQ coperti, dove si interviene nel codice, sorgenti
dati (collection, campi, query Solr con `fl`), regole (scelta del preavviso, mapping, stato del
preavviso, decodifica dello stato file, parser degli errori, formato delle date, errori e
disponibilità), contratto API (anche nessun preavviso e `503`), casi d'uso con esempi (i tre casi del
mock up, nessun preavviso, T&T-Repo non disponibile, casi della regola di scelta), configurazione,
RNF e osservabilità, criteri di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. la regola di scelta con tutti i casi limite (un documento, parità di `event_ts`, `event_ts` mancante);
2. che cosa dice l'ICD su ogni campo usato (indicizzato, stored: `idfile` di `pacchi_file` non è stored);
3. come distinguere "non trovato" da "T&T-Repo non disponibile" (i metodi attuali di `RestClientSolr`
   restituiscono `null` su errore);
4. la sicurezza delle query costruite senza encoding (`build(true)`): validazione della LdV;
5. i dati personali presenti nelle collection: chiedere solo i campi necessari, niente nei log;
6. coerenza del path `/api/...` con il proxy Nitro di `portal-pages`.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Riprendi AS-01…AS-07 e aggiungi le tue con ID nuovi (da AS-08), in una numerazione comune con il
  documento del front-end.
- Niente dati di produzione: LdV, ordini, file ed errori d'esempio inventati.
- Non cambiare il contratto: le incoerenze fra mock up, ICD e contratto vanno fra le domande aperte.
- Lingua italiana; nomi file e ID ASCII.
