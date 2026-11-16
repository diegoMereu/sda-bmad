# 146073 — Compliance USA Entry Type 13 — nuovi campi e controlli sul preadvising

**Data**: 2026-11-16 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: da definire · **PRJ**: da assegnare

## In una riga
Analisi 0.2 sugli HLD (che restano il nostro perimetro) e sulla descrizione generale. I
due campi della fase 1 sono definiti:
- Account Key: per spedizione, 52 caratteri;
- Product ID: per articolo, 1–255 caratteri.

Mancano ancora la regola esatta che riconosce le spedizioni soggette (business, USA, merce,
prodotti), i nomi JSON nel tracciato e i codici di errore.

## Fatto dall'ultimo punto
- 2026-11-16 — HLD v.1 del 09/11/2026 in `cliente/` (fase 1: 22.388,73 €, fase 2: 12.969,62 €).
- 2026-11-16 — Descrizione generale "Compliance USA Entry Type 13" in `cliente/`: campi, regole, flusso Zonos, casi di test.
- 2026-11-16 — Analisi 0.2 (`analisi.md`):
  - campi e regole;
  - interventi HLD per fase, con le indicazioni della descrizione e i repo;
  - differenze fra descrizione e HLD;
  - 11 punti aperti.

## Prossimi passi
- Chiedere a Poste la regola di riconoscimento (PA-02), i nomi JSON concordati col builder (PA-03) e i codici di errore (PA-04) — Diego — prossimo passo
- Allineare con Poste le differenze fra descrizione e HLD: `ce-dichiarato-ldv`, state-machine-handler, dazi e fee (PA-10) — Diego — prossimo passo
- Funzionali della fase 1 per microservizio (`sviluppo/`), partendo dal validatore — Mary — dopo PA-02…PA-04
- Fase 2: contratto del microservizio Zonos e del verso BEP (PA-07…PA-09) — Diego — da definire

## Blocchi e rischi
- 🟡 La regola "business, USA, merce, prodotti interessati" non è ancora tradotta nei campi del tracciato: è il cuore della validazione.
- 🟡 La descrizione assegna attività a `ce-dichiarato-ldv` e allo state-machine-handler, che non sono nell'HLD: rischio di lavoro fuori stima, oppure di campi persi nella creazione della LDV.
- 🟡 Il "3° campo" dell'HLD sembra essere il Declaration ID, da predisporre in fase 1: va confermato.
- 🟡 Producer dei preavvisi da portali e web service (int. 09): repo non ancora individuato.

## Serve dal cliente
- Valori dei campi del tracciato che identificano business, USA, merce e prodotti interessati.
- Nomi JSON di Account Key e Product ID nel tracciato unico (dal team del builder) e ICD aggiornato.
- Codici e descrizioni dei nuovi errori di validazione.
- Conferma dei 3 campi SEW (Account Key, Product ID, Declaration ID) e delle DDL.
- Perimetro di `ce-dichiarato-ldv` e `ce-dichiarato-state-machine-handler`.
- Fase 2: contratto del microservizio Zonos, contratto verso BEP, campi sovrascrivibili.
- PRJ e owner cliente.

## Decisioni prese
- 2026-11-16 — Il perimetro di Accenture è quello degli interventi negli HLD; la descrizione generale serve da contesto (Diego).
