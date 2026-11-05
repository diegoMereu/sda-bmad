# Prompt — documento funzionale `ce-eurodis-send-tracking`

> Prompt per Mary (analyst): genera il documento funzionale del microservizio
> `ce-eurodis-send-tracking` (iniziativa 136596).
> Output: `iniziative/136596/sviluppo/ce-eurodis-send-tracking.md`, da passare
> ad Amelia (dev) per lo sviluppo.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per lo
sviluppatore** del microservizio `ce-eurodis-send-tracking`, nell'iniziativa
136596 "Eurodis autoproduttore" (Poste Italiane / SDA, Corriere Espresso).

EURODIS è un consorzio di corrieri europei che affida spedizioni a SDA. Le
spedizioni entrano da `receive-pan` (microservizi `ce-dichiarato-eurodis-in` e
`ce-dichiarato-eurodis-mapper`). Questo microservizio fa il percorso inverso:
**restituisce a EURODIS le tracce SDA** di quelle spedizioni, con l'API EURODIS
`send-tracking` ("Send Tracking data to EURODIS", prima "Tracking Export").

Il tracking rientra nel perimetro della 136596 dal 02-11. Il repository c'è
(`CORRIERE-ESPRESSO_PREADVISING_ce-eurodis-send-tracking`, branch
`feature/eurodis-base-implementation`), impostato da azzurrazezza: template
`ce-`, Kafka, nessuna logica.

**Priorità di Diego (05-11)**: l'API c'è nello swagger, quindi si parte da
quella. Il documento deve permettere ad Amelia di sviluppare **subito il
client verso EURODIS**. La sorgente degli eventi SDA e la loro traduzione nei
codici EURODIS non sono note: vanno trattate come DA DECIDERE con proposta, e
non devono bloccare il client.

Stack: Java 17, Spring Boot 3.5.14 (deciso per tutta la catena il 04-11),
Kafka, MongoDB, OpenShift, Datadog. Nessun service mesh. Metriche e span sul
modello di `ce-dichiarato-adapter` e `ce-dichiarato-eurodis-in`.

# Fonti (in `iniziative/136596/`)

- `eurodis-send-tracking-swagger-v1.json`: OpenAPI 3.0 di `send-tracking`
  (NSwag), scaricato il 05-11 da
  https://testapi.eurodis.com/send-tracking/swagger/Release%20v1/swagger.json
- `eurodis-receive-pan-swagger-v1.json`: per i campi che arrivano in ingresso
  (`edReference`, barcode dei colli).
- `analisi.md` (PA-07 tracking, PA-08 errori verso EURODIS),
  `punti-aperti-analisi-2026-10-23.md`, `PUNTO.md`.
- `sviluppo/ce-dichiarato-eurodis-in.md`: impostazione del documento,
  convenzioni di metriche e span, collezione `eurodis_spedizioni`.

# Cosa ti chiedo

Stessa struttura del documento di `-in`: scopo e confini, posizione nella
catena, interfacce, flusso, regole RF-nn, stati, errori e recupero,
configurazione, osservabilità, RNF, criteri di accettazione, punti aperti con
default, riferimenti, domande per Diego.

Approfondisci soprattutto il **client**:

1. endpoint, con quali usare subito e quali restano fuori;
2. autenticazione (verifica nello swagger se è `X-API-Key` come in
   `receive-pan`);
3. modello dati di richiesta e risposta, con vincoli di lunghezza e
   obbligatorietà condizionate;
4. codici di risposta e come si classificano (definitivo, temporaneo,
   configurazione);
5. semantica dei lotti (successo parziale);
6. retry ammessi e idempotenza: una POST ripetuta crea un evento doppio?
7. formato di `eventTimestamp`.

# Regole

- Distingui **[FATTO]** (con il campo o l'endpoint dello swagger),
  **[IPOTESI]**, **[DECISO]** (data e riferimento), **[DA DECIDERE]** (con
  proposta e default).
- Non inventare il catalogo dei codici evento EURODIS né la semantica di
  `locationCode`: se lo swagger non li dà, sono domande.
- Nessun dato personale nei log: `acceptorName` è il nome di chi ritira.
- Chiave API solo da secret.
- Aggiungi in `analisi.md` i punti aperti nuovi e aggiorna PA-07.
- Chiudi con le domande per Diego.
