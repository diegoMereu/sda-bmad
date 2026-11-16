# 146073 — Dazi USA — nuovi campi e controlli sul preadvising

**Data**: 2026-11-16 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: da definire · **PRJ**: da assegnare

## In una riga
Abbiamo letto i due HLD (fase 1 e fase 2) e preparato l'analisi 0.1. Gli interventi sono
su 8 punti della catena ce-dichiarato. I campi però non sono ancora definiti: l'HLD parla
di 3 campi e ne nomina 2 (Account Key, Product ID), mancano formato e regola di
riconoscimento delle spedizioni USA. Senza questi dati non si scrivono i funzionali.

## Fatto dall'ultimo punto
- 2026-11-16 — HLD v.1 del 09/11/2026 in `cliente/` (fase 1: 22.388,73 €, fase 2: 12.969,62 €).
- 2026-11-16 — Analisi 0.1 (`analisi.md`):
  - interventi per fase e microservizio, con i repo da toccare;
  - stime;
  - campi doganali già presenti nel tracciato unico;
  - 11 punti aperti e le incongruenze degli HLD.

## Prossimi passi
- Chiedere a Poste la definizione dei campi e la regola di riconoscimento (PA-01…PA-05) — Diego — prossimo passo
- Aggiornare l'ICD del tracciato unico con i nuovi campi, appena definiti — Mary — dopo le risposte
- Funzionali per microservizio della fase 1 (`sviluppo/`), partendo dal validatore — Mary — dopo l'ICD
- Chiarire con Poste il perimetro della fase 2 (lavorazione orchestratore, SOROS, contratto BEP, campo del sistema integrato) — Diego — da definire

## Blocchi e rischi
- 🟡 Campi non definiti (nome, tipo, terzo campo): blocca DTO, DDL e ICD.
- 🟡 Regola "spedizione USA soggetta a dazi" non descritta negli HLD: è il cuore della validazione.
- 🟡 Fase 2: l'HLD presume che il campo del nuovo sistema integrato sia predisposto già in fase 1, ma il suo nome non è noto.
- 🟡 Producer dei preavvisi da portali e web service (int. 09): repo non ancora individuato.

## Serve dal cliente
- Definizione dei campi: nome, tipo, lunghezza, obbligatorietà e posizione nel tracciato unico. Qual è il terzo campo?
- Regola che individua le spedizioni soggette (destinazione USA? clienti, canali, prodotti, soglie).
- Esito se i campi mancano: scarto con codice errore o warning.
- Come arrivano i campi da file, PDB, PDW, ILP, portali e web service.
- Fase 2: cos'è SOROS, contratto verso BEP, nuova lavorazione e campi sovrascrivibili, campo del sistema integrato.
- PRJ e owner cliente.

## Decisioni prese
- Nessuna per ora.
