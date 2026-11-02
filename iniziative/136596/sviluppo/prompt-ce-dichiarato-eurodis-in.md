# Prompt — documento funzionale `ce-dichiarato-eurodis-in`

> Prompt per Mary (analyst): genera il documento funzionale del microservizio
> `ce-dichiarato-eurodis-in` (iniziativa 136596).
> Output: `iniziative/136596/sviluppo/ce-dichiarato-eurodis-in.md`, da passare
> ad Amelia (dev) per lo sviluppo.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per lo
sviluppatore** del microservizio `ce-dichiarato-eurodis-in`, nell'iniziativa
136596 "Eurodis autoproduttore" (Poste Italiane / SDA, Corriere Espresso,
pipeline di preadvising).

EURODIS è un consorzio di corrieri europei che affida spedizioni a SDA. Le
spedizioni arrivano con la LDV già prodotta da EURODIS (autoproduttore) e si
scaricano dall'API EURODIS `receive-pan`.

Il flusso è diviso in tre microservizi (decisione del 30-10, PA-26). Ognuno ha
il suo documento funzionale:

| Microservizio | Responsabilità | Repository |
|---|---|---|
| **`ce-dichiarato-eurodis-in`** (questo) | Interroga `receive-pan`, salva subito la risposta grezza, la divide in una spedizione per messaggio e la consegna al mapper | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in |
| `ce-dichiarato-eurodis-mapper` | Valida e trasforma la spedizione EURODIS nel tracciato unico ICD v11 e la pubblica su `preadvising.pre-enrichment` | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper |
| `ce-eurodis-send-tracking` | Invia a EURODIS le tracce SDA delle sue spedizioni | https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-eurodis-send-tracking |

Catena completa (decisione del 29-10):
`receive-pan` → **`ce-dichiarato-eurodis-in`** → `ce-dichiarato-eurodis-mapper`
→ `preadvising.pre-enrichment` → `ce-dichiarato-ldv-pdb-sync` (esistente) →
PDB `waybillCreate`.

**Questo microservizio non trasforma e non valida il contenuto di business.**
Il suo compito è non perdere nessuna spedizione: scaricare, salvare, dividere,
consegnare, e rendere tutto tracciabile e recuperabile.

Stack di riferimento: Java / Spring Boot, Kafka, MongoDB, PostgreSQL,
OpenShift/Kubernetes, Datadog. Il lettore è uno sviluppatore Java che non
conosce EURODIS né la pipeline di preadvising.

# Fonti (tutte in `iniziative/136596/`)

- `eurodis-receive-pan-swagger-v1.json`: specifica OpenAPI 3.0 di
  `receive-pan`, generata con NSwag. Originale:
  https://testapi.eurodis.com/receive-pan/swagger/Release%20v1/swagger.json
- `analisi.md`: registro dei punti aperti (PA-nn) e note per lo sviluppo.
- `punti-aperti-analisi-2026-10-23.md`: dubbi funzionali (DF-nn).
- `mock-eurodis/`: mock dell'API in Python, con coda "consuma senza ack",
  rilettura puntuale e anomalie iniettabili. È lo strumento per i test di
  sviluppo.
- `PUNTO.md`: stato dell'iniziativa e decisioni prese.

# Fatti verificati (dalla specifica e da prove del 22-10 e 26-10)

1. Ambienti:
   - TEST `https://testapi.eurodis.com/receive-pan`;
   - PROD `https://api.eurodis.com/receive-pan`, raggiungibile (risponde
     `401` senza chiave).
2. Autenticazione: API key del partner nell'header `X-API-Key`. È scritta
   solo nella descrizione della pagina, **non** nei `securitySchemes` dello
   swagger: un client generato non la aggiunge da solo. Una chiave errata
   restituisce `401` con corpo in testo semplice (`Invalid API Key`), non JSON.
3. Endpoint, entrambi GET:
   - `GET /shipments/v1`: *"Deploys all new shipments, that have not already
     been deployed to the partner"*. Nessun parametro: niente paginazione,
     filtri o cursore. `200` array di `GetShipmentResponse2`; `404` *"No new
     shipments available"*, che è un **esito normale**; `401`; `424` (partner
     non determinabile); `451` (partner senza accesso); `500`.
   - `GET /shipment/{edReference}/v1`: una spedizione. Codici: `200`, `400`
     (edReference non valido), `401`, `404`, `424`, `451`, `500`.
4. Non esiste un endpoint di acknowledge o commit.
5. Due schemi spedizione: `GetShipmentResponse2`, l'unico referenziato dagli
   endpoint, e `GetShipmentResponse`, non referenziato, con campi in più:
   `initiatingPartnerId`, `routingCode`, `shipmentFlexField1..4` e, sui colli,
   `deliveryPartnerBarcode`, `dispatchPartnerBarcode`, `pudoOpeningCode`,
   `colloFlexField1..3`.
6. `edReference` è `number`/`decimal` (1..9999999999999), mentre
   `referencedEurodisShipmentNumber` è `int64`.
7. I timestamp sono `date-time`, descritti con suffisso `Z`
   (`2000-01-31T18:30:00.000Z`).
8. `consigneeAddress` è `nullable`. Obbligatori della spedizione:
   `edReference`, `shipmentTypeIndicator`, `lineHaulIndicator`,
   `clearanceTimestamp`, `numberOfHandlingUnits`, `shipmentWeight`,
   `dispatchPartnersDomesticShipmentNumber`, `consigneePreAdvice`, `collis`.
9. Lo swagger **non contiene esempi** di payload.

# Ipotesi da trattare come tali

- **I1 (forte)**: EURODIS segna le spedizioni come consegnate nel momento in
  cui le restituisce, quindi la consegna è at-most-once. Una risposta persa
  (timeout, crash, retry di client, proxy o sidecar) significa spedizioni
  perse, recuperabili solo con la GET puntuale e solo se si conosce
  l'`edReference`. Domande a EURODIS: PA-05, PA-09.
- **I2**: la GET puntuale non ha effetti collaterali e funziona anche su
  spedizioni già scaricate.
- **I3**: l'array di risposta può essere grande (nessun limite dichiarato,
  PA-27).

# Decisioni prese

- Si salva lo storico (PA-02).
- Un messaggio per spedizione verso il mapper, mai un unico messaggio con
  tutta la lista: messaggi sovradimensionati sono già stati visti in
  produzione.
- Il ms di tracking e il mapping sono fuori da questo microservizio.
- Rilascio incrementale, non big bang (PA-28).
- `id_preadvising` (UUID) lo genera il mapper, non questo microservizio.

# Decisioni da prendere (da marcare DA DECIDERE, con una proposta)

- **D1. Dove si salva il grezzo.** Staging su MongoDB oppure topic Kafka
  dedicato con `acks=all`. La proposta del 26-10 era Mongo, poi coda verso il
  mapper. Decide l'Architect.
- **D2. Contratto del messaggio verso il mapper.** Nome del topic, chiave
  (`edReference`?), corpo (JSON grezzo della singola spedizione così come
  arriva, più metadati: id esecuzione, istante di ricezione, ambiente,
  riferimento al grezzo salvato).
- **D3. Una sola istanza attiva** con più repliche: meccanismo di lock o
  leader election (PA-01, call con Tagliente da fissare).
- **D4. Frequenza di polling** e finestra oraria (PA-14).
- **D5. Duplicati.** Se arriva un `edReference` già visto (I2, rettifiche):
  si scarta, si ripubblica o si versiona?
- **D6. Recupero.** Rilettura per `edReference` e ripubblicazione dal grezzo
  salvato: endpoint amministrativo, job o procedura manuale?

# Punti aperti che toccano questo microservizio

PA-01 (repliche), PA-05/PA-09 (stato e perdita delle spedizioni), PA-06
(prima chiamata: arretrato?), PA-12 (chiave di produzione), PA-14 (frequenza),
PA-27 (limiti, aggiornamenti e annullamenti), PA-29 (test integrati). Più le
domande a EURODIS: c'è un ack o una riconsegna su richiesta? La marcatura
avviene prima o dopo la trasmissione completa? C'è un massimo di spedizioni
per chiamata? Quale dei due schemi arriva? Che fuso orario hanno i timestamp?
Quando `consigneeAddress` è null? Qual è la frequenza consigliata e il rate
limit?

Per ognuno indica il **default provvisorio** con cui lo sviluppo può partire e
cosa cambia quando arriva la risposta.

# Requisiti non funzionali da formalizzare (RNF-nn, misurabili)

- Salvataggio del corpo grezzo della risposta **prima** di qualsiasi parsing di
  business, validazione o pubblicazione.
- **Nessun retry automatico** su `GET /shipments/v1`, compresi client HTTP,
  Spring Retry, proxy e sidecar: un fallimento è un incidente (alert e log),
  non si ripete alla cieca. Sulla GET puntuale il retry è ammesso.
- `404` gestito come "nessuna spedizione": nessuna eccezione, nessun alert,
  nessuna apertura del circuit breaker.
- Elaborazione idempotente su `edReference`.
- DTO tolleranti: proprietà sconosciute ignorate (devono passare anche i
  campi di `GetShipmentResponse`); `edReference` letto come `Long` o
  `BigDecimal`, mai `double`, con test sul formato `7319003746401.0`;
  timestamp letti senza assumere il fuso orario.
- Corpo di errore in testo semplice gestito senza tentare il parsing JSON.
- API key da secret OpenShift, mai nei log.
- Osservabilità Datadog: spedizioni ricevute per chiamata, esito e latenza
  della chiamata, `edReference` ricevuti (nei log, senza dati personali),
  alert su `401`/`424`/`451`/`500`/timeout e sull'assenza di esecuzioni.
- Nessun dato personale (nomi, indirizzi, telefoni, email) nei log.
- **[IPOTESI]** Riconciliazione periodica con altre API EURODIS (Receive
  Tracking, Receive Clearing) per scoprire spedizioni perse. Non abbiamo
  ancora letto quegli swagger: è una proposta da verificare.

# Cosa ti chiedo

Scrivi il documento funzionale in
`iniziative/136596/sviluppo/ce-dichiarato-eurodis-in.md`, in italiano, con
questa struttura:

1. **Scopo e responsabilità**: cosa fa e, esplicitamente, cosa **non** fa
   (validazione di business, mapping, tracking, risposta a EURODIS).
2. **Posizione nella catena**: schema della catena a tre microservizi e
   confini con il mapper.
3. **Interfacce**:
   - in ingresso: `receive-pan` (endpoint, header, codici, modello dati
     essenziale con rimando allo swagger);
   - in uscita: messaggio verso il mapper (D2, con proposta di schema JSON);
   - persistenza: modello del grezzo e dello stato per spedizione (D1, con
     proposta di collezioni o tabelle e indici).
4. **Flusso di elaborazione** passo per passo, con diagramma di sequenza
   Mermaid: trigger → lock → chiamata → salvataggio grezzo → divisione →
   salvataggio per spedizione → pubblicazione → chiusura dell'esecuzione.
5. **Regole funzionali** numerate (RF-nn), una per comportamento verificabile.
6. **Stati**: dell'esecuzione (per esempio AVVIATA, NESSUNA_SPEDIZIONE,
   SALVATA, PUBBLICATA, IN_ERRORE) e della spedizione, con le transizioni.
7. **Gestione errori e recupero**: tabella scenario → comportamento → alert →
   come si recupera. Almeno: timeout o connessione caduta durante la
   risposta, crash dopo la risposta e prima del salvataggio, crash dopo il
   salvataggio e prima della pubblicazione, Kafka non disponibile, JSON non
   valido, spedizione senza `edReference`, `edReference` duplicato,
   `401`/`424`/`451`/`500`, risposta molto grande.
8. **Configurazione**: parametri con default (URL per ambiente, secret della
   chiave, cron, timeout, topic, dimensione massima, flag di attivazione per
   il rilascio incrementale PA-28).
9. **Osservabilità**: metriche, log e alert Datadog, con nomi proposti.
10. **Requisiti non funzionali** (RNF-nn).
11. **Criteri di accettazione e casi di test** in formato
    Given/When/Then, eseguibili contro `mock-eurodis` (coda senza ack,
    `404`, `401`, `451`, anomalie iniettate, riavvio a metà elaborazione).
12. **Punti aperti e default provvisori**: tabella con punto, default per
    partire, impatto quando arriva la risposta, riferimento PA/DF.
13. **Riferimenti**: fonti, repository, documenti degli altri due
    microservizi.

# Regole

- Distingui sempre **[FATTO]** (dalla specifica, con il campo o l'endpoint),
  **[IPOTESI]**, **[DECISO]** (con data e riferimento) e **[DA DECIDERE]**
  (con una proposta).
- Non inventare comportamenti dell'API EURODIS: quello che lo swagger non dice
  è un'IPOTESI o una domanda aperta.
- Non dare per scontati nomi di topic, collezioni o classi: proponili come
  proposta.
- Lo sviluppatore deve poter partire senza aspettare le risposte di EURODIS:
  per ogni punto aperto c'è un default.
- Scrivi un primo draft completo, poi elenca in fondo le domande per cui ti
  serve conferma da Diego.
