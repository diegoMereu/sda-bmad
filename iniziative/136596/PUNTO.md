# 136596 — Eurodis autoproduttore

**Data**: 2026-10-26 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: Piergentili · **PRJ**: non ancora assegnato

## In una riga
Analisi e mapping in bozza; per chiudere il design aspettiamo le risposte di EURODIS (via Chiapponi) sul comportamento dell'API `receive-pan`.

## Fatto dall'ultimo punto
- 2026-10-23 — Analisi e mapping EURODIS → ICD v11 in bozza; 20 dubbi funzionali (DF-01…DF-20), 9 di gravità alta.
- 2026-10-23 — Recepiti i commenti di Diego sul mapping; letto lo swagger `receive-pan` (solo ambiente TEST).
- 2026-10-26 — Registro punti aperti allineato agli appunti (PA-01…PA-27).
- 2026-10-26 — Inviata a Chiapponi la mail con 12 domande: comportamento API, errori e tracking, ambiente di produzione, payload reale, volumi, dogana/ADR.
- 2026-10-26 — Follow up a Chiapponi con la domanda 13: roll out incrementale senza big bang, perimetro filtrato lato EURODIS (PA-28).

## Prossimi passi
- Risposte alle 13 domande EURODIS — Chiapponi (Poste) — da definire
- Call con Tagliente (Poste) sulle repliche del ms di raccolta (PA-01) — da assegnare — da definire
- Chiudere i dubbi di gravità alta sul mapping (canale, LDV e multicollo, contrassegno, assicurazione, centro di costo, ISO4, lunghezze BEP) — Mary / Diego — da definire
- Completare i campi ancora DA DEFINIRE del mapping (PA-04) — Azzurra / Diego — da definire
- Decidere se servono due livelli di ms per l'ingestione (PA-26) — da assegnare — da definire

## Blocchi e rischi
- 🟡 Perimetro e PRJ non definiti: non si può stimare né pianificare.
- 🟡 `receive-pan` non ha ack: se EURODIS considera consegnata una spedizione quando la restituisce, un errore prima del salvataggio la fa perdere. Da confermare con EURODIS (domanda 1).
- 🟡 Esiste solo l'ambiente TEST: senza chiave e payload di produzione i campi opzionali restano non verificati.
- 🟡 9 dubbi funzionali di gravità alta ancora aperti.

## Serve dal cliente
- Codice PRJ.
- Risposte di EURODIS alle 13 domande (via Chiapponi).
- Chiave API di produzione e payload di esempio con dati reali, dati sensibili oscurati.
- Conferma se `centro_costo` e `rif_prodotto_cliente` sono costanti di contratto (F1).
- Perimetro: dogana, ADR, volumi e frequenza del batch.

## Decisioni prese
- 2026-10-22 — Si parte con l'analisi (Mary) prima di qualsiasi PRD o stima.
- 2026-10-22 — Il ms tracking (`ce-eurodis-send-tracking`) è un task a parte, fuori da questa analisi.
- 2026-10-22 — Il ms di raccolta salva lo storico (con stato).
- 2026-10-22 — Prodotto e servizi accessori si derivano dalla LDV con ce-rules.
- 2026-10-22 — Contratto, codice cliente e AUC si reperiscono da F1.
- 2026-10-22 — Nessun troncamento dei campi lunghi: si passa il valore intero.
- 2026-10-22 — LDV: `consignorsColloBarcode` → `collo.id_ldv`; `europlateBarcode` → `internazionale.id_ldv_itz`.
- 2026-10-22 — `id_preadvising` = UUID generato dal servizio.
