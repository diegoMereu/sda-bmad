# 136596 — Risposte di EURODIS sul comportamento di `receive-pan` (10-11)

**Fonte**: risposte di EURODIS alle domande della mail del 26-10, arrivate via
Gianluca Chiapponi (Poste) il 09-11 e girate da Diego il 10-11. Il dettaglio
domanda per domanda, con le assunzioni che ne derivano, è in
[assunzioni.md](assunzioni.md) (AS-D01…AS-D06).

**Testo originale (inglese)**: in fondo al documento, così come l'ha girato
Diego (domande nostre e risposte di EURODIS, refusi compresi).

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

## Testo originale (inglese)

> receive-pan API behaviour
>
> 1. Shipment delivery → Does GET /shipments/v1 return only shipments that have not yet been delivered to the partner, and is there no acknowledgement endpoint? Does EURODIS therefore consider a shipment data delivered as soon as it is returned by the API? If our service fails after receiving the response, how can we recover those shipments?
>    - You just receive the data for shipments, which you dont receive yet. This doesnt change. If you recognize, that you have issues in transferring this data into your database, you can request always that we are putting all the data again into your next request. I would recommend you (Post AT is doing like this) to write all the data you receive paralelly into a local script/log and then transfer to your database. This supports you, if something going wrong in the process of transferring.
> 2. Initial call → Does the first call return the entire historical backlog, or only shipments from a specific date onward?
>    - You just receive the data for shipments, which you dont receive yet.
> 3. Updates and cancellations → If EURODIS modifies or cancels a shipment that has already been delivered to us, will it be sent again in a subsequent batch? How can we identify it? Will it use the same edReference?
>    - Modification or cancellation is only possible, if the data is not acitvated and not shared with the respective delivery partner. This topic is not necessary to consider.
> 4. Call limits → What is the maximum number of shipments returned by a single call? Is pagination supported? Are there any rate limits or timeout constraints that must be respected?
>    - There is no limit. For now. If this is necessary in future, we can try to find a solution. I would recommend you to request every 15-20min. The number of shipments will be absolutely feasible to process.
> 5. Individual retrieval → For how long does GET /shipment/{edReference} keep a previously delivered shipment available?
>    - 60 days.
> 6. Time zone and access → Which time zone is used for timestamps? How is API key rotation managed?
>    - API keys are not rotating. Standard timezone which you use today for file exchange based on the FTP environment.
