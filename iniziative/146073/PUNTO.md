# 146073 — Compliance USA Entry Type 13 — nuovi campi e controlli sul preadvising

**Data**: 2026-11-24 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: da definire · **PRJ**: da assegnare

## In una riga
La fase 1 (Account Key per spedizione, Product ID per articolo, Declaration ID predisposto) ha
nomi, regola, errori e colonne SEW decisi da Diego. Lo sviluppo del primo passo è in corso:
- validatore su `develop` (`090d037`, `43f5cbe`); orchestratore (`9a96564`), smistatore (`9289aeb`) e bff (`d2f5027`) su `develop`;
- `sda-ldv-preadv-consumer` (`consumer-sew_sped`, `producer-sew-sped`) sul branch dedicato (`990503a` + `ef0a5ce`,
  pubblicati), scrive solo su `sew_spedizioni_work`; da compilare in Eclipse.

Adapter e consumer Poste sono rimandati al punto 2 della fase 1. Da Poste servono ancora l'elenco
dei prodotti CRONO INTERNAZIONALE e i nomi dei campi nelle sorgenti.

## Fatto dall'ultimo punto
- 2026-11-23 — Diego decide nomi, regola, errori e colonne SEW:
  - nomi `zonos_account_key`, `zonos_product_id`, `zonos_declaration_id`;
  - regola senza "cliente business", prodotti 456-459, 515, 516 su `codice_prodotto` o `id_servizio`;
  - errori `1320`…`1323`;
  - colonne `char` con default `''`.
- 2026-11-24 — Partito lo sviluppo del primo passo. Validatore, orchestratore, smistatore e bff vanno su `develop`, `sda-ldv-preadv-consumer` sul branch `146073_compliance_usa_fase1`.
- 2026-11-24 — Analisi 0.3 (contratto AS-01…AS-07 aggiornato, primo passo e punto 2, punti aperti), Mary.
- 2026-11-24 — Funzionali e prompt alla versione 0.2 con le decisioni del 23 e 24-11, Mary. Adapter e `consumer-sew-sped-poste` hanno in testa la nota "rimandato al punto 2 della fase 1".
- 2026-11-24 — DDL 0.2 (`ddl-sew-146073.md`) con le colonne `zonos_*` `char` con default `''`, Mary.
- 2026-11-24 — Validatore su `develop`, commit `090d037`: campi `zonos_*`, regola ed errori `1320`…`1323`, verifica spenta di default. I 153 test `regoledrools/Invio*Test` falliscono già su `develop`: sono preesistenti, da sistemare a parte.
- 2026-11-24 — `sda-ldv-preadv-consumer` sul branch `146073_compliance_usa_fase1`, commit `990503a` e `ef0a5ce` (colonne solo su `sew_spedizioni_work`), pubblicati. Mai compilato con le librerie reali: serve un build in Eclipse con i jar di `L:` prima del rilascio.
- 2026-11-24 — Validatore: chiavi `zonos_*` anche su Mongo (`@Field`), commit `43f5cbe` su `develop`.
- 2026-11-24 — Su `develop`: orchestratore `9a96564` (campi protetti nel merge con le lavorazioni, chiavi `zonos_*` su Mongo), smistatore `9289aeb` (campi su `.completed.poste`/`.sda`, non verso i palmari), bff `d2f5027` (campi in lettura e risottomissione). Lo smistatore ha 4 test `PalmariMapper*` rossi già su `develop` (commit `3d91ac5` del 18-11), non legati alla 146073.
- 2026-11-24 — Documenti aggiornati con le decisioni del giorno (Mary): analisi 0.4, DDL 0.3 (script 2 su `sew_spedizioni_work_2` eliminato), funzionali 0.3 di `consumer-sew_sped`, `producer-sew-sped`, validatore e orchestratore; note su bff ed event store; prompt.

## Prossimi passi
- Segnalare i 4 test `PalmariMapper*` rossi su `develop` dello smistatore all'autore di `3d91ac5` — Diego — fuori dalla 146073
- Build in Eclipse di `consumer-sew_sped` e `producer-sew-sped` con i jar di `L:` — Diego — prima del rilascio
- Sistemare a parte i 153 test `regoledrools/Invio*Test` già rotti su `develop` del validatore — da assegnare — fuori dalla 146073
- Chiedere a Poste la conferma dell'elenco CRONO INTERNAZIONALE (PA-12) — Diego — prossimo passo
- Richiedere al DBA Informix lo script 1 delle DDL in svil, solo `sew_spedizioni_work` — Diego / Winston — prima che il builder mandi i campi
- Test integrati in svil con messaggi costruiti a mano su `preadvising.pre-enrichment`, con il flag `compliance-usa.abilitata` acceso solo per il test — test manager — dopo lo sviluppo
- Punto 2 della fase 1: adapter (int. 05) e `consumer-sew_sped_poste` (int. 08) — Amelia — quando arrivano i nomi dei campi sorgente e i dettagli lato Poste (PA-13)

## Blocchi e rischi
- 🟡 Il validatore controlla solo i flussi SDA e PDB/EUD: portali e web service (MYSDA, SDA_WS, INVIO_WEB), adapter e TUP passano senza regole.
- 🟡 `ce-dichiarato-ldv`, `-ldv-pdb` e `-ldv-pdb-sync` non conoscono i campi e non sono nell'HLD. In fase 1 basta l'orchestratore, in fase 2 servono.
- 🟡 Lato SDA il Product ID non ha una tabella articoli (né consumer né producer): va deciso con Poste.
- 🟡 L'Account Key dei portali arriva solo se i portali, fuori perimetro, la scrivono nelle SEW.
- 🟡 Due retry (`retry-eurodis`, `retry-pread-completo`) perderebbero i campi.
- 🟡 `sda-ldv-preadv-consumer` non è mai stato compilato con le librerie reali (`sdaKafkaLibrary`, driver Informix): un errore di build si vedrebbe solo in Eclipse.
- 🟡 Le DDL vanno eseguite prima che il builder mandi i campi. Prima di allora i consumer funzionano, perché le colonne entrano nello statement solo se i campi arrivano valorizzati.

## Serve dal cliente
- Elenco dei prodotti CRONO INTERNAZIONALE: in `ce_prodotto` ci sono solo `515` e `516` (PA-12).
- Nomi e livello di Account Key e Product ID nei messaggi PDB, PDW e ILP; PDW avrà più articoli? Serve per il punto 2 (PA-13).
- Il validatore deve controllare anche portali, web service, adapter e TUP?
- Dove va il Product ID lato SDA (nuova tabella `sew_spedizioni_work_art`?) e chi adegua i portali per l'Account Key.
- L'Account Key è un dato riservato? Se sì va mascherata nei log.
- La console di monitoraggio deve ricevere i campi (variante B)?
- Chi adegua `ce-dichiarato-ldv`, `-ldv-pdb`, `-ldv-pdb-sync` e i retry?
- Aggiornamento dell'ICD con i nomi `zonos_*` (team del builder).
- PRJ e owner cliente.

## Serve da Diego
- Istanze Informix di svil e collaudo, referente DBA e modalità di richiesta delle DDL; valori delle properties esterne del producer (topic, query, schedule).
- Per il punto 2: i due commit locali sull'adapter (`c4a26d1`, `1a6202d`, 30-10), non pubblicati e sugli stessi file.

## Decisioni prese
- 2026-11-16 — Il perimetro di Accenture è quello degli interventi negli HLD; la descrizione generale serve da contesto (Diego).
- 2026-11-16 — Si lavora solo sulla fase 1 (Diego).
- 2026-11-16 — Nelle descrizioni degli errori il nome del campo va prima dei due punti, con le occorrenze fra parentesi, perché la console le legge così.
- 2026-11-23 — Nomi nel tracciato `zonos_account_key` (spedizione, 52), `zonos_product_id` (articolo, 1-255), `zonos_declaration_id` (spedizione, 13, solo predisposto) (Diego).
- 2026-11-23 — Soggette le spedizioni con merce (`tipo_merce` diverso da `D`), destinatario USA e prodotto `456,457,458,459,515,516` su `codice_prodotto` o `id_servizio`. Niente condizione "cliente business". Flag spento di default (Diego).
- 2026-11-23 — Errori `1320`…`1323` con le descrizioni dell'analisi (AS-03), esito scarto (Diego).
- 2026-11-23 — Colonne SEW `char(52)`, `char(13)` e `char(255)` con default `''`. I consumer le mettono nello statement solo se il campo arriva valorizzato (Diego).
- 2026-11-24 — Nomi `zonos_*` sia nel tracciato sia nelle colonne SEW: niente prefisso `z_` (Diego).
- 2026-11-24 — Branch: `develop` nei repo dei servizi preadvising (validatore, orchestratore, smistatore, bff, adapter, `poste-ldv-preadv-consumer`). Solo `sda-ldv-preadv-consumer` resta sul branch dedicato `146073_compliance_usa_fase1`, da `origin/dev202508_preadvising`. Sostituisce la decisione del 16-11 (Diego).
- 2026-11-24 — Adapter (int. 05) e `consumer-sew_sped_poste` (int. 08) rimandati al punto 2 della fase 1, perché mancano i dettagli (Diego).
- 2026-11-24 — `consumer-sew_sped` scrive `zonos_account_key` e `zonos_declaration_id` solo su `sew_spedizioni_work`: non su `sew_spedizioni_work_2` né su `sew_spedizioni`. DDL SDA solo sulla work (SEW-01 chiusa) (Diego).
- 2026-11-24 — Il producer toglie gli spazi di riempimento a destra dei campi `char`: un valore vuoto o di soli spazi vale come campo assente (PRD-02) (Diego).
- 2026-11-24 — Su MongoDB validatore e orchestratore salvano i campi con i nomi del tracciato `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id`, non camelCase (Diego).
- 2026-11-24 — Orchestratore, smistatore e bff restano nel primo passo su `develop`; lo sviluppo riparte oggi (Diego).
