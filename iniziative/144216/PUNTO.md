# 144216 — Assistenza Clienti — Customer Journey preavviso

**Data**: 2026-11-13 · **Stato**: in_corso · **Semaforo**: 🟡
**Owner cliente**: Raimondo Malatesta · **PRJ**: PRJ0049429

## In una riga
La sezione "Informazioni preavviso" del dettaglio LdV di OneTracking è sviluppata su BE (shipment-info, API `/preavviso/{ldv}` sul T&T-Repo, 56 test verdi) e FE (portal-pages, build ok), committata in locale sul branch `144216_preavviso_onetracking` di entrambi i repo, ma **non pushata**: GitLab risponde 403 all'utenza. SF in stesura, DP a seguire.

## Fatto dall'ultimo punto
- 2026-11-13 — Materiale del cliente in `cliente/`: mock up v0.8 (DREQ0062862, DREQ0062864, DREQ0062865, DREQ0062866), ICD `pacchi_anagrafica` (138975) e `pacchi_file`.
- 2026-11-13 — Analisi (`analisi.md`): tre sezioni (preavviso sempre, dati file solo con `id_file`, errori solo se presenti), regola di scelta del preavviso, mapping dei campi, contratto JSON, assunzioni.
- 2026-11-13 — Funzionali 0.1 di `shipment-info` e `portal-pages` con i prompt (`sviluppo/`), Mary.
- 2026-11-13 — BE: `GET /preavviso/{ldv}` (il FE la chiama `/api/preavviso/{ldv}` via proxy), letture Solr su `pacchi_anagrafica` (LdV e preavvisi) e `pacchi_file`, decodifica stati file, parsing tollerante degli errori, 503 se il T&T-Repo non risponde; 56 test verdi (commit `ee9df14`). Amelia.
- 2026-11-13 — FE: componente `InfoPreavviso.vue` fra "Informazioni LV" e "Cliente/Mittente/Destinatario", tre casi del mock up, assenza di preavviso, 503 senza bloccare il dettaglio; `nuxi build` ok (commit `abc49718`). Amelia.
- 2026-11-13 — Assessment di OneTracking: `contesto/onetracking.md` e README dei 7 repo (non committati nei repo).

## Prossimi passi
- Ottenere il permesso di push su `ONETRACKING/PRESENTATION/shipment-info` e `portal-pages` e pushare i branch — Diego — prossimo passo
- SF 0.1 per Poste (`/sf 144216`) — Mary — in corso
- DP 0.1 (`/dp 144216`) sulla SF 0.1 — Winston — dopo la SF
- Prova integrata in svil (BE + FE, LdV di test con preavviso da file con scarto, da file ok, da web service) — Amelia / Diego — dopo il push
- Confermare con Poste le assunzioni AS-02…AS-05 (numero ordine, canale del preavviso non da file, formato di `preadv_errori`, data stato del file) — Diego — da definire

## Blocchi e rischi
- 🟡 Push negato (403) su entrambi i repo OneTracking: senza permessi lo sviluppo non arriva in svil.
- 🟡 Formato di `preadv_errori` non descritto nell'ICD: il parsing è tollerante, ma la tabella errori va verificata su dati veri.
- 🟡 Canale del preavviso non da file (caso 3 del mock up): nessun campo nell'ICD, oggi il BE legge un campo configurabile e mostra "-" se manca.
- 🟡 Build Maven di shipment-info: la dipendenza `ce-common-utils` richiede le credenziali Nexus nelle variabili d'ambiente; i test sono stati eseguiti con un pom senza quella dipendenza (il codice non la usa).

## Serve dal cliente
- Formato del campo `preadv_errori` di `pacchi_anagrafica` (campo, codice, descrizione).
- Campo del T&T-Repo con il canale del preavviso quando non viene da file.
- Conferma: numero ordine = `code_externalId`; data stato del file = `_lastupdate_` di `pacchi_file`.
- Visibilità per tipologia di utente ed eventuale export PDF/Excel della sezione.
- LdV di test in svil per i tre casi del mock up.

## Decisioni prese
- 2026-11-13 — La sezione parte dalla LdV; "Dati file preavviso" solo se il preavviso ha `id_file`, "Dettaglio errori" solo se ci sono errori (Diego).
- 2026-11-13 — Con più preavvisi per la LdV si sceglie quello con `event_type` = `COMPLETED` (fra più `COMPLETED` il più recente), altrimenti il penultimo per `event_ts` (Diego).
- 2026-11-13 — Sviluppo su branch `144216_preavviso_onetracking` da `origin/develop` in shipment-info e portal-pages (FE su Nuxt 3).
