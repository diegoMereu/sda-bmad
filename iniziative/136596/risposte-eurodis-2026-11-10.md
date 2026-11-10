# 136596 — Risposte di EURODIS sul comportamento di `receive-pan` (10-11)

**Fonte**: risposte di EURODIS alle domande della mail del 26-10, arrivate via
Gianluca Chiapponi (Poste) il 09-11 e girate da Diego il 10-11. Il dettaglio
domanda per domanda, con le assunzioni che ne derivano, è in
[assunzioni.md](assunzioni.md) (AS-D01…AS-D06).

**Testo originale (inglese)**: non è nel repository. Le risposte sono arrivate
riassunte in italiano. Il testo inglese di EURODIS va incollato qui quando
disponibile: non lo ricostruiamo per non attribuire a EURODIS frasi che non
ha scritto.

Nessun dato personale in questo documento.

## Sintesi in italiano

| # | Tema | Risposta di EURODIS | Effetto per noi | Rif. |
|---|---|---|---|---|
| 1 | Consegna delle spedizioni | `GET /shipments/v1` restituisce solo le spedizioni non ancora ricevute; **nessun ack**. Se abbiamo problemi a trasferire i dati nel nostro database possiamo chiedere a EURODIS di **rimettere tutti i dati** nella richiesta successiva. Consigliano, come fa Post AT, di scrivere in parallelo i dati ricevuti in uno script o log locale prima del database | **I1 confermata** (at-most-once). Nuova via di recupero di un lotto perso: richiesta di rimando a EURODIS (modalità da concordare). Vedi la nota sul log parallelo qui sotto | PA-05, PA-09, AS-D01 |
| 2 | Prima chiamata | Solo le spedizioni non ancora ricevute: nessun arretrato storico | Nessuna gestione speciale della prima chiamata | PA-06, AS-D02 |
| 3 | Modifiche e annullamenti | Possibili solo prima dell'attivazione e della condivisione con il partner di consegna | Non ci arrivano rettifiche né annullamenti | PA-27, AS-D03 |
| 4 | Limiti e frequenza | Nessun limite né paginazione, per ora. Consigliano una chiamata ogni **15-20 minuti** | **Decisione di Diego (10-11)**: in produzione scarico ed elaborazione **ogni 10 minuti**; in svil e coll restano **2 minuti**. Si cambia solo da configurazione | PA-14, PA-27, AS-D04 |
| 5 | Rilettura puntuale | `GET /shipment/{edReference}/v1` disponibile per **60 giorni** | Limite del recupero puntuale (RF-16 di `-in`) | PA-27, AS-D05 |
| 6 | Chiave e fuso orario | Le API key **non ruotano**. Il fuso è quello usato oggi nello scambio file via FTP (flusso EUD esistente) | Nessuna rotazione da gestire. Il valore del fuso si ricava dai dati FTP esistenti (AS-D06); fino ad allora i timestamp passano come arrivano | PA-27, AS-D06; PA-12 resta per la chiave di produzione |

## Nota sul "log parallelo" consigliato da EURODIS (punto 1)

Scrivere il grezzo nei **log applicativi** viola la regola di progetto
"nessun dato personale nei log": le spedizioni contengono nomi, indirizzi,
telefoni ed email.

La nostra contromisura è già nel disegno di `-in`:
- il grezzo si salva **per primo**, prima di qualsiasi elaborazione (RF-06);
- se il salvataggio fallisce si logga solo l'elenco degli `edReference`, che
  serve per il recupero puntuale (RF-16).

**Proposta per Diego**: se vuole comunque il log parallelo, va scritto su un
file o volume dedicato, con accesso ristretto e conservazione limitata, e non
nei log applicativi raccolti da Datadog.
