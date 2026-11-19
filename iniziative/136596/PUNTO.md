# 136596 — EURODIS Autoproduttore

**Data**: 2026-11-18 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: Piergentili · **PRJ**: non ancora assegnato

## In una riga
La catena EURODIS `EUD_INVIOSYSTEM` arriva fino a BEP in svil: con la LDV PDB `4UW2308` + 6 cifre e il contrassegno BEP accetta la spedizione. È pronto il rilascio di `-in`, mapper (dati cliente dalla postazione del seme LDV), send-tracking (filtro EURODIS) e monitoraggio; serve prima lo script DB 07. Go-live atteso a fine gennaio 2027.

## Fatto dall'ultimo punto
- 2026-11-18 — **LDV PDB per BEP INVIOSYSTEM**: 13 caratteri, prefisso `4U` con contrassegno e `3U` senza (indicazione Poste), seme = `pds_code` INVIOSYSTEM del contratto (`W2308` in svil). Rifiutati con `131`: seme di postazione (`W0008`), prefisso `1U`, LDV di 22 caratteri. **`4UW2308` + contrassegno passa su BEP**; mock WireMock con due spedizioni per scarico (4U e 3U). Il caso `3U` è ancora da vedere passare.
- 2026-11-18 — **Nazione del mittente estero**: BEP scartava con `101 country` (`GER1`); il contratto EURODIS non ha nazioni estere abilitate e la minuta del 29/07 vuole `ITA1` costante (`bep-nazione-mittente-estero.md`).
- 2026-11-18 — **Sviluppo pronto al rilascio** (`nota-rilascio-eurodis.md`): `-in` con ragione sociale `EURODIS GmbH` negli eventi di stato e file fittizio in Mongo `preadvising_file` (chiuso dalla state machine), script DDL 07 `eurodis_postazioni`; mapper solo LDV PDB (le altre scartate), contratto, centro di costo e dati cliente dalla postazione del seme (cache → `eurodis_postazioni` → `ce-vendite` → upsert), configurazione come riserva; send-tracking con filtro EURODIS su `eurodis_postazioni` (niente più `ce-vendite`); `EUD_INVIOSYSTEM` ammesso dal monitoraggio. Adapter invariato: il canale in Fase 2 funziona già.
- 2026-11-18 — SF 0.6 e DP 0.4 allineati (vincoli 37-38 su LDV e nazione, Open Point 39 su dove applicare `ITA1`, Open Point 30 aggiornato); contesto aggiornato (glossario, catena, ambienti).
- 2026-11-12/17 — Test integrati in svil fino a ldv-pdb (DEF-003/004/005 corretti nel mapper); send-tracking 0.4 su `PACCHI.TRACKING`, senza storico; ADR esclusi (SF 0.5).

## Prossimi passi
- Eseguire lo script `sql/ddl/07_ddl_eurodis_postazioni.sql` su `ce_eud_api_in` (svil e collaudo) — DBA — prima del rilascio del mapper
- Network policy `ce-dichiarato-eurodis-mapper` → `ce-vendite` — piattaforma — prima del rilascio del mapper
- Deploy di mapper e send-tracking (dopo `-in` e script 07), monitoraggio indipendente — Diego — appena pronto lo script
- Verificare in svil l'upsert in `eurodis_postazioni` (riga `W2308` con `eurodis = true`) e il file fittizio in `preadvising_file` chiuso dalla state machine — Diego / Amelia — dopo il deploy
- Decidere dove applicare `ITA1` (ldv-pdb per i canali `EUD_*`, o mapper e builder) e provare il caso `3U` senza contrassegno — Diego / SDA — da definire
- Chiedere a EURODIS conferma che in produzione `deliveryPartnerBarcode` segua la regola 4U/3U + `W2308` — Paolo — alla call
- Call con Chiapponi/EURODIS: errori e rifiuti (A03.2), rimando dei dati, rollout ibrido — Paolo — da fissare
- Elaborazione in parallelo a batch del send-tracking — Amelia — in corso
- Chiarire Spring Boot del mapper (4.1.2 contro 3.5.14) e il Dockerfile del mapper (AS-24) — Diego / Amelia — da definire

## Blocchi e rischi
- 🟡 Nazione del mittente estero: il giro BEP passa (4UW2308 + contrassegno), ma resta da decidere dove applicare `ITA1` per i mittenti esteri, su `EUD_INVIOSYSTEM` ed `EUD_INVIOFILE`; finché non si decide un mittente estero viene scartato da BEP con `101`.
- 🟡 LDV in produzione: se EURODIS non genera le LDV con la regola 4U/3U + seme `pds_code`, BEP risponde `131`; LDV non PDB vengono scartate dal mapper.
- 🟡 Rilascio del mapper legato allo script DB 07 e alla network policy verso `ce-vendite`; l'upsert su PostgreSQL non è mai stato provato.
- 🟡 Errori e rifiuti: EURODIS chiede di non rifiutare; senza chiarimento non si chiude la gestione degli scarti.
- 🟡 Send-tracking: la consegna (`1100`) richiede il nome di chi ritira; in svil `PACCHI.TRACKING` non ha eventi CE.
- 🟡 Perimetro e PRJ non definiti. Go-live a fine gennaio 2027.

## Serve dal cliente
- Codice PRJ.
- Conferma che le LDV EURODIS di produzione seguono la regola 4U/3U + `pds_code` INVIOSYSTEM, e che `deliveryPartnerBarcode` è sempre valorizzato.
- Decisione su dove applicare la nazione `ITA1` del mittente estero e conferma della provincia `EE` (BEP).
- Call con Chiapponi/EURODIS su errori e rifiuti, rimando dei dati e rollout ibrido; data della chiave API di produzione.
- Data di spedizione: `entranceTimestamp` arriva sempre? (DF-01)
- Conferma che i valori di riserva del cliente (contratto, centro di costo, codice login, AUC) valgono in produzione.
- Presenza del nome di chi ritira (`acceptorName`) nelle tracce SDA.
- Conferma dei valori del contrassegno e di come arriva il nome del Punto Poste.

## Decisioni prese
- 2026-11-18 — LDV del collo: solo LDV PDB (le altre si scartano nel mapper); per BEP INVIOSYSTEM prefisso `4U` con contrassegno e `3U` senza, seme = `pds_code` del contratto per canale di prenotazione.
- 2026-11-18 — Dati del cliente dalla postazione del seme LDV (`ce-vendite`, tabella `eurodis_postazioni` scritta dal mapper), configurazione solo come riserva; `codice_login_cliente` e `codice_auc` restano di configurazione. Send-tracking legge `eurodis_postazioni` e non chiama `ce-vendite`.
- 2026-11-18 — `-in` registra il file fittizio in `preadvising_file` come il builder (Mongo dal secret di ce-dichiarato-validatore, `8995ae8`); ragione sociale `EURODIS GmbH` negli eventi di stato.
- 2026-11-12 — Send-tracking su `PACCHI.TRACKING`, senza storico; filtro su status e spedizione `EUD_INVIOSYSTEM`. ADR fuori perimetro.
- 2026-11-10 — Persistenza di `-in` su **PostgreSQL** (database `ce_eud_api_in`, JDBC senza JPA né Flyway, script DDL eseguiti dal DBA), con gli stessi secret di `ce-db-sync` (`ce-postgres`, `ssl-secrets`).
- 2026-11-10 — Frequenza: in produzione scarico ed elaborazione ogni 10 minuti (EURODIS consiglia 15-20), in svil e coll restano 2 minuti. LDV del collo = `deliveryPartnerBarcode`. Stati di tracking tradotti con il foglio "Decodifica Eurodis IN-BOUND", eventi di collo.
- 2026-11-09 — Scarico ogni 2 minuti, nonostante EURODIS consigli 15-20. Storico arretrato della prima chiamata elaborato tutto. Rilettura per `edReference` solo come recupero manuale (già implementata). Chiave API in secret OpenShift.
- 2026-11-09 — Scarti: mail come in `EUD_INVIOFILE` tramite il ms esistente dell'altro gruppo, insieme agli errori di `INVIOFILE`; **da riconsiderare** dopo la risposta di EURODIS.
- 2026-11-06 — Mapper senza F1 (cliente da configurazione, superato il 18-11 dalla postazione), codici nazione da `ce-anagrafica`, ce-rules a valle. Ogni scarico è un file fittizio con `idFile`.
- 2026-11-05 — Canale `EUD_INVIOSYSTEM`. Tracking nel perimetro: tre ms, un documento funzionale ciascuno.
- 2026-11-04 — Spring Boot 3.5.14 per tutta la catena. `-in` in due fasi, nessun filtro duplicati, nessun endpoint applicativo. Contratto su `preadvising.eud.pre.build`: corpo = spedizione così com'è, chiave `edReference`.
- 2026-10-30 — Due livelli di ingestione: `-in` legge, salva e scompone; il mapper converte nell'ICD. Il mapping vive solo nel mapper.
- 2026-10-29 — Mock dell'API in Python (FastAPI). Test integrati solo su `receive-pan`. Catena: lettura API → mapping → ms sync → PDB `waybillCreate`.
- 2026-10-22 — Analisi prima di PRD e stima. Il ms di raccolta salva lo storico. Nessun troncamento dei campi lunghi. `id_preadvising` = UUID. `europlateBarcode` → `internazionale.id_ldv_itz`.
