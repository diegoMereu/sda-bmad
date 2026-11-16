# 146073 — Compliance USA Entry Type 13 — nuovi campi e controlli sul preadvising

**Data**: 2026-11-16 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: da definire · **PRJ**: da assegnare

## In una riga
La fase 1 (Account Key per spedizione, Product ID per articolo, Declaration ID predisposto)
ha i funzionali per tutti gli 8 interventi dell'HLD, in `sviluppo/`, con le DDL Informix.
Lo sviluppo può partire sul branch `146073_compliance_usa_fase1` con le assunzioni dichiarate.
Per chiudere servono da Poste:
- la regola esatta che riconosce le spedizioni soggette;
- i nomi dei campi nelle sorgenti;
- la conferma dei codici di errore.

## Fatto dall'ultimo punto
- 2026-11-16 — HLD fase 1 e 2 e descrizione generale "Compliance USA Entry Type 13" in `cliente/`.
- 2026-11-16 — Analisi 0.2 con il contratto della fase 1 (AS-01…AS-07), l'esito dei funzionali e i rischi emersi.
- 2026-11-16 — Funzionali 0.1 della fase 1 con i prompt, Mary:
  - `ce-dichiarato-validatore`, `ce-dichiarato-orchestratore`, `ce-dichiarato-smistatore`, `ce-dichiarato-adapter`;
  - `ce-event-handler-event-store`, `ce-event-handler-monitoring`, `ce-dichiarato-bff`;
  - `consumer-sew-sped`, `consumer-sew-sped-poste`, `producer-sew-sped`.
- 2026-11-16 — DDL Informix delle tabelle SEW (`ddl-sew-146073.md`), Winston.
- 2026-11-16 — Verdetto per l'int. 04: event store e monitoring senza modifiche di codice (solo test); bff con una modifica piccola.

## Prossimi passi
- Rifare il `git fetch` dei repo (fallito il 16-11 per un problema di rete) e ricontrollare i ref letti — Amelia — prima dei branch
- Sviluppo della fase 1 sul branch `146073_compliance_usa_fase1` in ogni repo, a partire da validatore, orchestratore e adapter — Amelia — dopo il fetch
- Inviare a Poste le domande della fase 1 (vedi sotto) — Diego — prossimo passo
- Richiedere al DBA Informix le DDL in svil — Diego / Winston — dopo la conferma delle tabelle
- Test integrati in svil con messaggi costruiti a mano su `preadvising.pre-enrichment` — test manager — dopo lo sviluppo

## Blocchi e rischi
- 🟡 Il validatore controlla solo i flussi SDA e PDB/EUD: portali e web service (MYSDA, SDA_WS, INVIO_WEB), adapter e TUP passano senza regole.
- 🟡 `ce-dichiarato-ldv`, `-ldv-pdb` e `-ldv-pdb-sync` non conoscono i campi e non sono nell'HLD. In fase 1 basta l'orchestratore, in fase 2 servono.
- 🟡 Lato SDA il Product ID non ha una tabella articoli (né consumer né producer): va deciso con Poste.
- 🟡 L'Account Key dei portali arriva solo se i portali, fuori perimetro, la scrivono nelle SEW.
- 🟡 Due retry (`retry-eurodis`, `retry-pread-completo`) perderebbero i campi.
- 🟡 `git fetch` fallito il 16-11: i funzionali sono scritti sui ref locali di `origin/develop`.

## Serve dal cliente
- Regola di riconoscimento: "business" (`importi.cliente_business` o `cliente.tipo_cliente`?), "documenti" (`tipo_merce` o `collo.codice_contenuto`?) ed elenco dei prodotti.
- Nomi e livello di Account Key e Product ID nei messaggi PDB, PDW e ILP; PDW avrà più articoli?
- Conferma dei codici di errore `1320`…`1323` e del formato delle descrizioni.
- Il validatore deve controllare anche portali, web service, adapter e TUP?
- Dove va il Product ID lato SDA (nuova tabella `sew_spedizioni_work_art`?) e chi adegua i portali per l'Account Key.
- L'Account Key è un dato riservato? Se sì va mascherata nei log.
- La console di monitoraggio deve ricevere i campi (variante B)?
- Chi adegua `ce-dichiarato-ldv`, `-ldv-pdb`, `-ldv-pdb-sync` e i retry?
- PRJ e owner cliente.

## Serve da Diego
- I due commit locali sull'adapter (`c4a26d1`, `1a6202d`, 30-10), non pubblicati e sugli stessi file: vanno pubblicati prima o inclusi nel branch?
- Base del branch per `sda-ldv-preadv-consumer` (senza `develop`): va bene `origin/dev202508_preadvising`?
- Istanze Informix di svil e collaudo, referente DBA e modalità di richiesta delle DDL; valori delle properties esterne del producer (topic, query, schedule).

## Decisioni prese
- 2026-11-16 — Il perimetro di Accenture è quello degli interventi negli HLD; la descrizione generale serve da contesto (Diego).
- 2026-11-16 — Si lavora solo sulla fase 1 (Diego).
- 2026-11-16 — Sviluppo su branch dedicato `146073_compliance_usa_fase1` in ogni repo, mai su develop/master o branch di altre iniziative (Diego).
- 2026-11-16 — Nelle descrizioni degli errori il nome del campo va prima dei due punti, con le occorrenze fra parentesi, perché la console le legge così.
