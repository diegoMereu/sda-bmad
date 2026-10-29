# 136596 — Eurodis autoproduttore

**Data**: 2026-10-29 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: Piergentili · **PRJ**: non ancora assegnato

## In una riga
Analisi e mapping in bozza, con i servizi accessori tradotti nel formato PDB; pronto un mock dell'API `receive-pan` per i test, ma la sintassi delle LDV è provvisoria in attesa di Marzilli, e restiamo in attesa delle risposte di EURODIS alle 13 domande e sui test integrati.

## Fatto dall'ultimo punto
- 2026-10-29 — Realizzato in Python un mock dell'API `receive-pan` (`mock-eurodis/`, 9 test verdi): configurabile per prodotto, con indirizzi e nazioni reali e dati generati, coda "consuma senza ack" come EURODIS, anomalie iniettabili per i test negativi.
- 2026-10-29 — Chiesta a Marzilli (team) la sintassi delle LDV autoproduttore EURODIS: nel mock è provvisoria (11 cifre + check Luhn, inventata) e si cambia da configurazione.
- 2026-10-29 — Servizi accessori EURODIS tradotti nel formato PDB (proposta da validare): sabato, sera, ore 10 e 12, appuntamento, Punto Poste, contrassegno. L'assicurazione risulta fuori perimetro.
- 2026-10-29 — Mapping ICD rigenerato e registro aggiornato: nuovi dubbi funzionali DF-21…DF-29 e punti aperti PA-29 e PA-30.
- 2026-10-29 — Letto il ms esistente `ce-dichiarato-ldv-pdb-sync` (in test): emerse osservazioni da segnalare al suo responsabile (canale, codici paese ISO4, default di peso e dimensioni).
- 2026-10-29 — Inviata a Gianluca Chiapponi la mail per organizzare i test integrati su `receive-pan` (PA-29): scenari proposti da EURODIS, LDV valide e univoche, indirizzi e nazioni reali, modalità operative.

## Prossimi passi
- Risposta di Marzilli sulla sintassi LDV, poi inserirla in `ldv_default` del mock — Marzilli / Paolo — da definire
- Risposte alle 13 domande EURODIS — Chiapponi (Poste) — da definire
- Risposta alla mail sui test integrati (scenari, date, modalità) — Chiapponi / EURODIS — da definire
- Validare con Diego la proposta sui servizi accessori e i nuovi dubbi — Mary / Diego — da definire
- Segnalare al responsabile del ms sync le osservazioni (PA-30) — da assegnare — da definire
- Call con Tagliente (Poste) sulle repliche del ms di raccolta (PA-01) — da assegnare — da definire
- Chiudere i dubbi di gravità alta sul mapping — Mary / Diego — da definire

## Blocchi e rischi
- 🟡 La sintassi delle LDV non è nota: finché non arriva, il mock genera LDV inventate e non prova che SDA le accetti.
- 🟡 Perimetro e PRJ non definiti: non si può stimare né pianificare.
- 🟡 `receive-pan` non ha ack: se EURODIS considera consegnata una spedizione quando la restituisce, un errore prima del salvataggio la fa perdere. Da confermare con EURODIS (domanda 1).
- 🟡 Esiste solo l'ambiente TEST: senza chiave e payload di produzione i campi opzionali restano non verificati.
- 🟡 Il ms `ce-dichiarato-ldv-pdb-sync` è ancora in fase di test e può contenere bug: alcune osservazioni toccano i nostri dati (paese, peso e dimensioni).
- 🟡 Diversi dubbi funzionali di gravità alta ancora aperti (canale, LDV e multicollo, nome del Punto Poste, centro di costo, lunghezze).

## Serve dal cliente
- Codice PRJ.
- Risposte di EURODIS alle 13 domande (via Chiapponi).
- Regola di validità e univocità delle LDV SDA (chiesta a Marzilli; se non la conosce, a chi la governa in SDA).
- Scenari di test proposti da EURODIS, con LDV valide e univoche e dati reali (via Chiapponi).
- Chiave API di produzione e payload di esempio con dati reali, dati sensibili oscurati.
- Conferma dei valori del contrassegno (3 → contanti, 5 → assegno bancario) e di come arriva il nome del Punto Poste.
- Conferma se `centro_costo` e `rif_prodotto_cliente` sono costanti di contratto.
- Perimetro: dogana, ADR, volumi e frequenza del batch.

## Decisioni prese
- 2026-10-29 — Mock dell'API in Python con FastAPI, configurazione per prodotto in YAML; la sintassi LDV è un parametro, non codice.
- 2026-10-29 — Test integrati: solo ingestione `receive-pan`, in parallelo alle risposte, con scenari proposti da EURODIS.
- 2026-10-29 — Catena: lettura API → nostro mapping verso l'ICD → ms sync `ce-dichiarato-ldv-pdb-sync` → PDB `waybillCreate` sincrono.
- 2026-10-22 — Si parte con l'analisi (Mary) prima di qualsiasi PRD o stima.
- 2026-10-22 — Il ms tracking (`ce-eurodis-send-tracking`) è un task a parte, fuori da questa analisi.
- 2026-10-22 — Il ms di raccolta salva lo storico (con stato).
- 2026-10-22 — Prodotto e servizi accessori si derivano dalla LDV con ce-rules (rivista il 29-10: proposta di tradurli nel nostro mapping, da validare).
- 2026-10-22 — Contratto, codice cliente e AUC si reperiscono da F1.
- 2026-10-22 — Nessun troncamento dei campi lunghi: si passa il valore intero.
- 2026-10-22 — LDV: `consignorsColloBarcode` → `collo.id_ldv`; `europlateBarcode` → `internazionale.id_ldv_itz`.
- 2026-10-22 — `id_preadvising` = UUID generato dal servizio.
