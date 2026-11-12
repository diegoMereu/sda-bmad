# 136596 — EURODIS Autoproduttore

**Data**: 2026-11-10 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: Piergentili · **PRJ**: non ancora assegnato

## In una riga
I tre microservizi sono implementati su `develop` (`-in` su PostgreSQL con eventi di stato, mapper con il tracciato completo, send-tracking con la traduzione degli stati), ma nessuno è stato ancora avviato in svil: le DDL di PostgreSQL sono state eseguite, manca il deploy. Restano da chiarire con EURODIS errori e rifiuti, rimando dei dati e `deliveryPartnerBarcode`. Go-live atteso a fine gennaio 2027.

## Fatto dall'ultimo punto
- 2026-11-12 — **ADR non gestiti** (conferma di Chiapponi): tolti dalla test list UAT (C088-C091) e dalla richiesta dati a EURODIS (S62-S65, ora 44 spedizioni); Excel della test list rigenerato. Registrato in `assunzioni.md` (AS-D12), PA-13 e SF 0.5 (esclusione 18, Open Point 36 sulla dogana); la SF recepisce anche i dati cliente e i codici nazione del mapper 0.5.
- 2026-11-10 — **DDL PostgreSQL eseguite dal DBA** (database `ce_eud_api_in`, script di `sql/ddl/` di `-in`), secondo Diego.
- 2026-11-10 — **Sviluppo completato sui tre repository** (`develop`, push con bypass della regola "solo pull request"):
  - `-in`: persistenza da Mongo a **PostgreSQL** (JDBC, script DDL in `sql/ddl/`, secret `ce-postgres` di `ce-db-sync`), file fittizio per scarico con eventi `ST_F0002`/`ST_F0005` su `preadvising.evensource` e header `idFile`, cron 10 min in prod e 2 altrove; 74 test verdi (`1c1e79b`…`b012d89`). Al commit `bd33e8a` `develop` non compila (riparato in `9acdd77`).
  - mapper: tracciato completo nella forma EUD, `EUD_INVIOSYSTEM`, LDV da `deliveryPartnerBarcode`, destinatario obbligatorio, codici nazione da `ce-anagrafica`, header di `-in`, error handler con DLT, metriche e span; 94 test verdi (`dbb3b59`, `474c8ef`).
  - send-tracking: client EURODIS e traduzione degli stati IN-BOUND (76 status SDA → 24 codici EURODIS); 143 test verdi (`4cba024`, `591767d`).
  - Documenti: DDL PostgreSQL (`sviluppo/ddl-ce-eurodis-api-in.md`, Winston), specifica di `-in` 0.6.1, mapper 0.4, send-tracking 0.2.
- 2026-11-10 — **Decisioni e risposte di Diego**: la LDV del collo è `deliveryPartnerBarcode` (`consignorsColloBarcode` non si mappa, `europlateBarcode` vuoto o `0` → `""`), destinatario in `consigneeAddress` confermato (DF-02, DF-18, DF-30 chiusi); traduzione degli stati SDA → EURODIS per send-tracking dal foglio "Decodifica Eurodis IN-BOUND" (PA-34 chiuso); risposte EURODIS registrate in `risposte-eurodis-2026-11-10.md` (PA-05, PA-06, PA-09, PA-27 chiusi). Mapping Excel rigenerato, mapper 0.4, send-tracking 0.2.
- 2026-11-09 — **Risposte di EURODIS (via Chiapponi) e documento A03.2**: si riceve solo il non ancora ricevuto; modifiche e annullamenti non rilevano; nessun limite di chiamata; rilettura per `edReference` a 60 giorni; chiavi API senza rotazione; produzione = cambio di endpoint e chiave; dogana e ADR nel perimetro; rollout ibrido, settimana per settimana. Tutto in `assunzioni.md` (13 assunzioni, stato per ciascuna).
- 2026-11-09 — **EURODIS chiede di non rifiutare le spedizioni** e di riprendere il suo sistema di errori e rifiuti (A03.2): la mail di scarto concordata oggi è da riconsiderare.
- 2026-11-06 — Specifica di `-in` 0.5 (file fittizio per scarico, eventi ST_F0002/ST_F0005, header `idFile`) e del mapper 0.2/0.3 (LDV confermate, destinatario obbligatorio, codici nazione da `ce-anagrafica`, cliente da configurazione). Figure di SF e DP.
- 2026-11-05 — SF 0.2 e DP 0.1 per il cliente; client di `ce-eurodis-send-tracking` implementato; canale `EUD_INVIOSYSTEM` confermato da Diego.
- 2026-11-04 — `ce-dichiarato-eurodis-in` implementato (53 test verdi, `a53398c` su `feature/eurodis-base-implementation`); Dockerfile allineato.

## Prossimi passi
- **Deploy di `-in`, mapper e send-tracking in svil** (scarico disabilitato), poi prima verifica con PostgreSQL e Kafka veri e prova end-to-end con EURODIS TEST — Diego / Amelia — prossimo passo
- Fissare la call con Chiapponi/EURODIS: errori e rifiuti (A03.2), come si chiede il rimando dei dati, rollout ibrido, `consigneeAddress` e LDV in produzione — Paolo — da fissare
- Verificare il fuso orario sui dati EURODIS del flusso FTP — Paolo — da definire
- Ricavare i volumi giornalieri dal flusso FTP — da assegnare — da definire
- Confermare che l'utente del secret `ce-postgres` è `ce_user`, proprietario di `ce_eud_api_in` — Diego / DBA — da definire
- Dare all'utente SCRAM di `-in` il permesso di scrittura su `preadvising.evensource` — piattaforma — da definire
- Chiarire con azzurrazezza Spring Boot: il mapper è a 4.1.2, la decisione è 3.5.14 per tutta la catena — Diego — da definire
- Decidere se su `develop` si passa da pull request (oggi i push scavalcano la regola) — Diego — da definire
- Togliere `mongo-string-connection` dal secret di `-in` dopo il rilascio — piattaforma — dopo il deploy
- Decidere se tenere una copia locale del grezzo e un interruttore di pubblicazione separato in `-in` — Diego / Amelia — da definire
- Chiedere all'altro gruppo come consegnare gli scarti al ms di invio mail e come funziona `send-pod` — Paolo — da definire
- Aggiornare i registri PA con le risposte di EURODIS (PA-05, 06, 09, 12, 13, 24, 27, 28) — Mary — da definire
- Decidere la sorgente delle tracce SDA per send-tracking (PA-35): senza, niente consumer né storico — Diego — da definire
- Sistemare il Dockerfile del mapper (AS-24) — Amelia — da definire
- Risposta di Marzilli sulla sintassi LDV — Marzilli — da definire

## Blocchi e rischi
- 🟡 Errori e rifiuti: EURODIS dice di non rifiutare, ma non è chiaro cosa significhi «riprendere» il loro sistema; senza chiarimento non si chiude PA-32 né la mail di scarto.
- 🟡 Perdita di un lotto tra la risposta HTTP e il salvataggio su PostgreSQL: il recupero è un rimando totale su richiesta a EURODIS, ma il modo di chiederlo è da concordare.
- 🟡 Nessuno dei tre servizi è mai stato avviato con PostgreSQL e Kafka veri; i repository di `-in` sono provati su H2 (CHECK e indici parziali non coperti). Prima verifica reale: il deploy in svil (DDL già eseguite).
- 🟡 Send-tracking: la consegna (`1100`) richiede il nome di chi ritira (`acceptorName`); se la sorgente SDA non lo ha, l'evento viene scartato.
- 🟡 Il destinatario (`consigneeAddress`) è `null` in TEST e LDV del collo vuota: EURODIS non ha detto se in produzione sono valorizzati.
- 🟡 Fuso orario dei timestamp non noto; sintassi LDV non nota (il mock genera LDV inventate).
- 🟡 Perimetro e PRJ non definiti: non si può stimare né pianificare. Go-live a fine gennaio 2027.
- 🟡 Il ms `ce-dichiarato-ldv-pdb` è ancora in test e alcune osservazioni toccano i nostri dati.

## Serve dal cliente
- Codice PRJ.
- Call con Chiapponi/EURODIS su errori e rifiuti, rimando dei dati e rollout ibrido.
- Data di consegna della chiave API di produzione.
- Conferma che `deliveryPartnerBarcode` (la LDV del collo, schema non referenziato) è valorizzato in produzione e nei dati di test. `consigneeAddress` confermato lato Poste il 10-11 (DF-30 chiuso).
- Data della spedizione: `entranceTimestamp` arriva sempre? Se manca, quale data (DF-01).
- Dati del cliente EURODIS per svil (codice login, ragione sociale, partita IVA, contratto, centro di costo) per mapper ed eventi di stato.
- Sorgente delle tracce SDA delle LDV EURODIS (PA-35) e presenza del nome di chi ritira (`acceptorName`).
- Regola di validità e univocità delle LDV SDA (chiesta a Marzilli).
- Conferma dei valori del contrassegno e di come arriva il nome del Punto Poste.
- Conferma se `centro_costo` e `rif_prodotto_cliente` sono costanti di contratto.
- Dall'altro gruppo: come si consegnano gli scarti al ms di invio mail e come funziona `send-pod`.

## Decisioni prese
- 2026-11-10 — Persistenza di `-in` su **PostgreSQL** (database `ce_eud_api_in`, JDBC senza JPA né Flyway, script DDL eseguiti dal DBA), con gli stessi secret di `ce-db-sync` (`ce-postgres`, `ssl-secrets`); Mongo abbandonato.
- 2026-11-10 — Frequenza: in produzione scarico ed elaborazione ogni 10 minuti (EURODIS consiglia 15-20), in svil e coll restano 2 minuti. LDV del collo = `deliveryPartnerBarcode`. Stati di tracking tradotti con il foglio "Decodifica Eurodis IN-BOUND", eventi di collo.
- 2026-11-09 — Scarico ogni 2 minuti, nonostante EURODIS consigli 15-20. Storico arretrato della prima chiamata elaborato tutto. Rilettura per `edReference` solo come recupero manuale (già implementata). Chiave API in secret OpenShift.
- 2026-11-09 — Scarti: mail come in `EUD_INVIOFILE` tramite il ms esistente dell'altro gruppo, insieme agli errori di `INVIOFILE`; **da riconsiderare** dopo la risposta di EURODIS.
- 2026-11-06 — Mapper senza F1: cliente e contratto da configurazione per ambiente, codici nazione da `ce-anagrafica`, ce-rules a valle (chiude PA-33). `consignorsColloBarcode` → `collo.id_ldv` confermato (superato il 10-11: la LDV è `deliveryPartnerBarcode`). Ogni scarico è un file fittizio con `idFile`.
- 2026-11-05 — Canale `EUD_INVIOSYSTEM`. Tracking nel perimetro: tre ms, un documento funzionale ciascuno.
- 2026-11-04 — Spring Boot 3.5.14 per tutta la catena. `-in` in due fasi, grezzo su Mongo, nessun filtro duplicati, nessun endpoint applicativo. Contratto su `preadvising.eud.pre.build`: corpo = spedizione così com'è, chiave `edReference`.
- 2026-10-30 — Due livelli di ingestione: `-in` legge, salva e scompone; il mapper converte nell'ICD. Il mapping vive solo nel mapper.
- 2026-10-29 — Mock dell'API in Python (FastAPI). Test integrati solo su `receive-pan`. Catena: lettura API → mapping → ms sync → PDB `waybillCreate`.
- 2026-10-22 — Analisi prima di PRD e stima. Il ms di raccolta salva lo storico. Prodotto e servizi dalla LDV con ce-rules (rivista il 29-10). Contratto, codice cliente e AUC da F1 (rivisto il 06-11). Nessun troncamento dei campi lunghi. `id_preadvising` = UUID. `europlateBarcode` → `internazionale.id_ldv_itz`.
