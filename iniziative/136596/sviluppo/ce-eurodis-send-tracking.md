# `ce-eurodis-send-tracking` — Documento funzionale per lo sviluppo

**Iniziativa**: 136596 — Eurodis autoproduttore · **Versione**: 0.1 (bozza) · **Data**: 2026-11-05
**Autrice**: Mary (analyst) · **Destinataria**: Amelia (dev) e team di sviluppo
**Repository**: https://posteitaliane.ghe.com/SVILUPPO/CORRIERE-ESPRESSO_PREADVISING_ce-eurodis-send-tracking (branch `feature/eurodis-base-implementation`)
**Generato da**: [prompt-ce-eurodis-send-tracking.md](prompt-ce-eurodis-send-tracking.md)
**Fonte principale**: [eurodis-send-tracking-swagger-v1.json](../eurodis-send-tracking-swagger-v1.json) (scaricato il 05-11)

Etichette usate nel documento:
- **[FATTO]**: scritto nello swagger EURODIS; la fonte è indicata.
- **[IPOTESI]**: non scritto nello swagger, da confermare.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[DA DECIDERE]**: scelta aperta, con proposta e default provvisorio.

> **Stato 05-11**: client implementato da Amelia (`4cba024` su `feature/eurodis-base-implementation`, 34 test verdi), conforme a RF-01…RF-12 e AC-01…AC-13.
>
> **Cosa si sviluppa adesso** (Diego, 05-11): solo il **client verso EURODIS**, cioè le sezioni 3.1, 5 (RF-01…RF-12), 7.1, 8, 9 e 11.1.
> Sorgente degli eventi SDA, traduzione nei codici EURODIS, persistenza e job (sezioni 3.2, 3.3, 4 e 6) sono **DA DECIDERE**. Finché non si decidono non si scrivono consumer né scheduler.

---

## 1. Scopo e responsabilità

`ce-eurodis-send-tracking` restituisce a EURODIS le tracce SDA delle spedizioni che EURODIS ha
affidato a SDA (entrate da `receive-pan`), chiamando l'API EURODIS `send-tracking`.

In pratica:

1. riceve gli eventi di tracciatura SDA delle spedizioni EURODIS (sorgente DA DECIDERE, 3.2);
2. li traduce in eventi EURODIS: codice evento, riferimento della spedizione o del collo, data e luogo;
3. li invia a EURODIS, singolarmente o a lotti;
4. registra l'esito di ogni evento (creato, rifiutato, da riprovare) e lo rende recuperabile.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Scarico delle spedizioni da EURODIS | `ce-dichiarato-eurodis-in` |
| Mapping verso l'ICD e preadvising | `ce-dichiarato-eurodis-mapper` |
| Prove di consegna (immagini, firme) | API EURODIS `send-pod`, non in perimetro oggi |
| Eventi sugli ordini di ritiro (`/event(s)/pickup-order/v1`) | nessuno: EURODIS non ci affida ritiri |
| Eventi sulle transit unit (`/event(s)/transit/v1`) | nessuno per ora (IPOTESI: SDA non riceve transit unit EURODIS, ST-05) |
| Leggere le tracce che EURODIS espone (`receive-tracking`) | nessuno: è l'API del verso opposto |

## 2. Posizione nella catena

```
EURODIS receive-pan → ce-dichiarato-eurodis-in → ce-dichiarato-eurodis-mapper → preadvising.pre-enrichment → … → PDB
                                                                                                                  │
                                                                                         lavorazione SDA (scan, esiti)
                                                                                                                  │
EURODIS send-tracking ← ce-eurodis-send-tracking ← eventi di tracciatura SDA (sorgente DA DECIDERE, 3.2) ←───────┘
```

Il legame tra i due versi è l'**identità della spedizione**:
- EURODIS la riconosce per `edReference` (spedizione) o per barcode (collo);
- SDA la lavora per LDV (`collo.id_ldv` ← `consignorsColloBarcode`, `internazionale.id_ldv_itz` ← `europlateBarcode`).

Per risalire da una LDV SDA a `edReference` e barcode serve una correlazione (3.3, ST-03).

## 3. Interfacce

### 3.1 In uscita: API EURODIS `send-tracking`

**Ambienti** [FATTO, `servers`]:
- TEST: `https://testapi.eurodis.com/send-tracking`.
- PROD: per analogia con `receive-pan` sarà `https://api.eurodis.com/send-tracking` [IPOTESI].

**Autenticazione** [FATTO, `info.description`]: API key del partner nell'header `X-API-Key`.
- Come in `receive-pan`, non è dichiarata nei `securitySchemes`: un client generato non la aggiunge da solo.
- [IPOTESI] È la stessa chiave di `receive-pan`, perché la chiave identifica il partner. Va confermato (ST-08); default: stesso secret, chiave configurabile a parte.

**Endpoint** [FATTO, `paths`]. Tutti POST, con corpo JSON:

| Endpoint | Cosa crea | Si usa |
|---|---|---|
| `POST /event/shipment/v1` | un evento di spedizione | **sì** |
| `POST /events/shipment/v1` | più eventi di spedizione (lotto) | **sì** |
| `POST /event/parcel/v1` | un evento di collo | **sì** |
| `POST /events/parcel/v1` | più eventi di collo (lotto) | **sì** |
| `POST /event(s)/transit/v1` | eventi su transit unit | no (sezione 1) |
| `POST /event(s)/pickup-order/v1` | eventi su ordini di ritiro | no (sezione 1) |

Quale livello usare (spedizione, collo o entrambi) dipende dai codici evento (ST-01). Il client li offre tutti e quattro.

**Richiesta: evento di spedizione** (`AddShipmentEventRequest`) [FATTO]:

| Campo | Tipo e vincoli | Obbligatorio | Note |
|---|---|---|---|
| `eventCode` | string, **esattamente 3** caratteri | sì | catalogo non nello swagger (ST-01) |
| `edReference` | int64 | no (nullable) | numero di spedizione EURODIS. Di fatto serve per individuarla |
| `acceptorName` | string ≤ 50 | per i codici **100 e 101** | nome di chi ritira: **dato personale** |
| `numberOfParcels` | int 0..999 | **sì** | |
| `numberOfPallets` | int 0..999 | **sì** | |
| `alternateShipmentReference` | string ≤ 50 | no | oltre 50 viene troncato con un warning, senza errore (esempio `02050E`) |
| `eventTimestamp` | string, **10..26** caratteri | sì | ISO 8601, `yyyy-MM-dd'T'HH:mm:ss.SSSZ` (vedi RF-05) |
| `freeTextInformation` | string ≤ 50 | no | |
| `locationCode` | string 1..10 | sì | esempio `CN-CC`; semantica non descritta (ST-04) |
| `countryCode` | string 1..2 | sì | ISO 3166 alpha-2 del luogo dell'evento |
| `bilateralInformation`, `bilateralInformation2` | string ≤ 50 | no | informazioni concordate tra i partner |

**Richiesta: evento di collo** (`AddParcelEventRequest`) [FATTO]. Ha gli stessi campi, con queste differenze:
- `eventCode` ha **esattamente 4** caratteri.
- `acceptorName` è obbligatorio per il codice **1100**.
- `numberOfParcels` e `numberOfPallets` sono facoltativi.
- C'è un riferimento del collo. Almeno uno tra questi è obbligatorio, salvo il setup "neighbourhood business":

| Campo | Vincolo | Quando |
|---|---|---|
| `edReference` | int64 | vuoto solo per scan sul barcode della transit unit |
| `transitUnitBarcode` | ≤ 24 | se il collo è consolidato in una transit unit EURODIS |
| `europlateBarcode` | ≤ 24 | obbligatorio se `deliveryPartnerBarcode` e `dispatchPartnerBarcode` sono entrambi vuoti |
| `deliveryPartnerBarcode` | ≤ 50 | barcode del partner di consegna dal Central Label Service (CLS) |
| `dispatchPartnerBarcode` | ≤ 50 | barcode del partner mittente dal CLS |
| `alternativeBarcode` | ≤ 50 | obbligatorio nel setup neighbourhood business (SOP 02-11) |

Proposta per la correlazione: `europlateBarcode` del collo ricevuto da `receive-pan`, più `edReference`.
- Lo stesso `europlateBarcode` è oggi la base di `internazionale.id_ldv_itz` nel mapper.
- Non sappiamo se SDA è "delivery partner" nel CLS né quale barcode EURODIS si aspetta da noi (ST-03).

**Risposte** [FATTO]:

| Codice | Endpoint singolo | Endpoint a lotti |
|---|---|---|
| `201` | evento creato. Corpo `Add…EventResponse`: echo di `edReference`, barcode, `eventCode`, `warnings[]` | richiesta accolta. Corpo: un `Add…EventsResponse` per evento, con `errors[]` e `warnings[]`. **Se `errors` non è vuoto, quell'evento NON è stato creato** |
| `400` | validazione fallita: `ValidationFailureResponse { errors: [{code, message}] }`, per esempio `02060 Invalid event code` | non documentato: gli errori arrivano per elemento dentro il `201` |
| `401` | API key mancante o errata | idem |
| `424` | partner non determinabile | idem |
| `500` | errore inatteso | idem |

Note sullo swagger:
- Il corpo dei lotti è dichiarato `*/*` invece di `application/json`. Si invia `application/json` [IPOTESI: accettato].
- Non c'è `451`, che invece esiste in `receive-pan`.
- Gli esempi con `eventCode` di 5 caratteri (parcel) o 4 (shipment) sono esempi di errore: la risposta d'esempio li rifiuta con `02060`.
- Per `401` [IPOTESI], come in `receive-pan`, il corpo è testo semplice (`Invalid API Key`), non JSON.
- Non è dichiarato un massimo di elementi per lotto (ST-06).
- Non è dichiarato che la risposta a lotti mantenga l'ordine della richiesta [IPOTESI: stesso ordine e stesso numero di elementi, ST-06].

**Idempotenza** [FATTO, per assenza]: non c'è chiave di idempotenza né un endpoint per leggere gli eventi già creati. Una POST ripetuta dopo una risposta persa **può creare un evento doppio**. Se EURODIS scarti i doppioni (stesso `edReference`/barcode, `eventCode`, `eventTimestamp`) è una domanda (ST-07).

### 3.2 In ingresso: eventi di tracciatura SDA [DA DECIDERE]

Non sappiamo ancora da dove arrivano le tracce SDA delle LDV EURODIS né in che formato (PA-07, ST-02). Candidati da verificare:
- un topic dedicato, per esempio `preadvising.eud.send-tracking` (il nome già messo da azzurrazezza in `application.yaml`), alimentato da chi possiede il tracking SDA;
- un topic o archivio del tracking SDA esistente (track & trace), filtrato sulle LDV EURODIS.

**Default per lo sviluppo**: nessun consumer. Il client ha un'interfaccia Java chiara, così che il consumer, quando la sorgente è decisa, la chiami senza toccare il client.

### 3.3 Persistenza e correlazione [DA DECIDERE]

Proposta, da confermare quando si decide la sorgente:
- **Correlazione LDV → spedizione EURODIS** (ST-03). Per tradurre un evento SDA (per LDV) in un evento EURODIS servono `edReference` e il barcode del collo. Si possono ricavare:
  - dal JSON della spedizione salvato da `-in` in `eurodis_spedizioni` (oggi senza indice sui barcode);
  - oppure da un indice LDV → (`edReference`, `europlateBarcode`) che il mapper scrive quando pubblica.
  - Decide l'Architect.
- **Storico degli invii**: collezione `eurodis_tracce` con un documento per evento. Contiene:
  - evento SDA di origine ed evento EURODIS inviato;
  - stato (sezione 6), tentativi, codici di errore e warning EURODIS;
  - istante di invio.
  - Serve per audit, ripresa e per non reinviare un evento già creato.

## 4. Flusso di elaborazione (proposta, quando la sorgente è decisa)

```mermaid
sequenceDiagram
    participant S as Sorgente eventi SDA
    participant T as ce-eurodis-send-tracking
    participant M as MongoDB
    participant E as EURODIS send-tracking
    S->>T: evento SDA (LDV, codice, data, luogo)
    T->>M: correlazione LDV → edReference, barcode
    T->>T: traduzione nel codice EURODIS (tabella da configurazione)
    T->>M: salva evento DA_INVIARE
    T->>E: POST /events/{shipment|parcel}/v1 (lotto)
    E-->>T: 201 con errors/warnings per elemento
    T->>M: CREATO / RIFIUTATO / DA_RIPROVARE per evento
```

## 5. Regole funzionali del client

| # | Regola |
|---|---|
| RF-01 | Ogni chiamata porta l'header `X-API-Key` con la chiave letta dalla configurazione (secret). La chiave non compare mai nei log |
| RF-02 | Il client espone quattro operazioni: evento di spedizione singolo e a lotto, evento di collo singolo e a lotto |
| RF-03 | Il client non solleva eccezioni sugli stati HTTP: restituisce un esito per evento. Gli errori di rete (timeout, connessione rifiutata) diventano anch'essi un esito, `ERRORE_TEMPORANEO`, non un'eccezione verso il chiamante |
| RF-04 | Classificazione degli esiti: `201` senza `errors` → **CREATO** (con eventuali warning); `400` o `errors` non vuoto nel lotto → **RIFIUTATO** (definitivo, non si riprova); `401`/`424` → **ERRORE_CONFIGURAZIONE** (chiave o partner: si riprova solo dopo l'intervento); `500`, `5xx` non documentati, timeout, I/O → **ERRORE_TEMPORANEO** (si può riprovare); altri codici → **ERRORE_TEMPORANEO** con log del codice |
| RF-05 | `eventTimestamp` si invia in UTC nel formato `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'` (24 caratteri). Il pattern con offset numerico (`+0100`) è lungo 28 caratteri e supera il massimo di 26. Il fuso atteso da EURODIS è una domanda (ST-09) |
| RF-06 | Prima dell'invio il client verifica i vincoli dello swagger che EURODIS rifiuterebbe comunque: lunghezza di `eventCode` (3 spedizione, 4 collo), obbligatori, `countryCode` ≤ 2, `locationCode` 1..10, `numberOfParcels`/`numberOfPallets` 0..999, almeno un riferimento del collo, `acceptorName` per 100/101 (spedizione) e 1100 (collo). Un evento non valido diventa **RIFIUTATO** con motivo locale, senza chiamata |
| RF-07 | I campi testuali oltre la lunghezza massima **non si troncano** (regola di progetto PA-16): l'evento è rifiutato localmente (RF-06). Fa eccezione `alternateShipmentReference`, che EURODIS tronca da sé con un warning |
| RF-08 | Lotti: un lotto oltre `lotto-max` elementi si divide in più chiamate. Gli esiti si restituiscono nell'ordine della richiesta. Se una risposta ha un numero di elementi diverso dalla richiesta, tutti gli eventi di quella chiamata diventano **ERRORE_TEMPORANEO** con motivo "risposta non correlabile" |
| RF-09 | Correlazione nel lotto: l'esito i-esimo corrisponde all'evento i-esimo. Se `edReference` o `eventCode` dell'esito non coincidono con l'evento, l'esito si accetta lo stesso ma si registra un warning (metrica e log senza dati personali) |
| RF-10 | Nessun retry automatico nel client HTTP. La politica di retry sta nel chiamante, che decide sugli `ERRORE_TEMPORANEO` (sezione 7.2). Così il client resta prevedibile e una POST non si ripete di nascosto (rischio di doppioni, 3.1) |
| RF-11 | I warning EURODIS (per esempio `02050E`) non bloccano: si registra il codice nei log e nelle metriche |
| RF-12 | Log senza dati personali: si registrano `edReference`, `eventCode`, codici di errore e warning, esito, durata. Mai `acceptorName`, `freeTextInformation`, `bilateralInformation*` né i barcode completi |

## 6. Stati di un evento (proposta, per lo storico 3.3)

`DA_INVIARE` → `CREATO` | `RIFIUTATO` | `DA_RIPROVARE` → (tentativi) → `CREATO` | `RIFIUTATO` | `ABBANDONATO` (oltre il massimo dei tentativi, con alert).

`ERRORE_CONFIGURAZIONE` non consuma tentativi: blocca gli invii e manda un alert finché la chiave non torna valida.

## 7. Errori e recupero

### 7.1 Nel client

| Scenario | Esito | Note |
|---|---|---|
| `400` con `errors` | RIFIUTATO, con codici EURODIS | non si riprova; il codice va nei log e nella metrica |
| Lotto `201` con alcuni `errors` | quegli eventi RIFIUTATO, gli altri CREATO | successo parziale |
| `401` (corpo testo, non JSON) | ERRORE_CONFIGURAZIONE | il corpo non si interpreta come JSON |
| `424` | ERRORE_CONFIGURAZIONE | |
| `500` | ERRORE_TEMPORANEO | |
| Timeout di connessione / connessione rifiutata | ERRORE_TEMPORANEO | la richiesta non è partita: riprovare è sicuro |
| Timeout di lettura / connessione caduta dopo l'invio | ERRORE_TEMPORANEO, motivo "esito incerto" | l'evento potrebbe essere stato creato: riprovare può creare un doppione (ST-07) |
| Corpo `201` non leggibile | ERRORE_TEMPORANEO, motivo "esito incerto" | come sopra |

### 7.2 Politica di retry [DA DECIDERE]

Proposta: si riprova sugli ERRORE_TEMPORANEO con backoff (1, 5, 15 minuti, poi ogni ora), fino a 24 ore, poi ABBANDONATO con alert. Anche gli "esiti incerti" si riprovano, per due motivi:
- un evento di tracking doppio è meno grave di un evento perso;
- EURODIS potrebbe scartare i doppioni (ST-07).

Se EURODIS risponde che i doppioni sono un problema, gli esiti incerti vanno a verifica manuale invece che al retry automatico.

## 8. Configurazione (client)

| Proprietà (`eurodis.tracking.*`) | Variabile | Default | Note |
|---|---|---|---|
| `base-url` | `EURODIS_TRACKING_BASE_URL` | `https://testapi.eurodis.com/send-tracking` | per ambiente |
| `api-key` | `EURODIS_API_KEY` | vuoto | dal secret `ce-eurodis-send-tracking-secret`, chiave `api-key` |
| `timeout.connect` | `EURODIS_TIMEOUT_CONNECT` | `10s` | |
| `timeout.read` | `EURODIS_TIMEOUT_READ` | `30s` | |
| `lotto-max` | `EURODIS_TRACKING_LOTTO_MAX` | `100` | massimo EURODIS non dichiarato (ST-06) |

## 9. Osservabilità

Metriche (Micrometer/Prometheus, tag comune `service=ce-eurodis-send-tracking`), sul modello di `-in`:

| Metrica | Tipo | Tag |
|---|---|---|
| `eurodis_tracking_chiamata_total` | counter | `endpoint` (shipment, shipments, parcel, parcels), `esito` (codice HTTP o `io`) |
| `eurodis_tracking_chiamata_durata` | timer | `endpoint` |
| `eurodis_tracking_eventi_total` | counter | `livello` (spedizione, collo), `esito` (CREATO, RIFIUTATO, ERRORE_CONFIGURAZIONE, ERRORE_TEMPORANEO) |
| `eurodis_tracking_errori_eurodis_total` | counter | `codice` (codice errore EURODIS, `locale` per RF-06) |
| `eurodis_tracking_warning_total` | counter | `codice` |
| `eurodis_tracking_lotto_non_correlabile_total` | counter | — |
| `eurodis_tracking_esito_non_coincidente_total` | counter | — (RF-09) |

Span OpenTelemetry: uno per chiamata HTTP, kind CLIENT, nome `eurodis.send-tracking <endpoint>`. Attributi: `http.status_code`, `eurodis.eventi`, `eurodis.creati`, `eurodis.rifiutati`. Il tracing non deve mai far fallire l'invio (principio di `TraceUtil`).

Alert (più avanti, come AS-19 di `-in`):
- qualsiasi `401`/`424`;
- tasso di ERRORE_TEMPORANEO oltre soglia;
- eventi ABBANDONATO.

## 10. Requisiti non funzionali

| # | Requisito |
|---|---|
| RNF-01 | Chiave API solo da secret, mai in `application*.yaml` né nei log |
| RNF-02 | Nessun dato personale nei log (RF-12) |
| RNF-03 | Nessun retry automatico nascosto nel client HTTP (RF-10) |
| RNF-04 | DTO tolleranti: le proprietà sconosciute nelle risposte si ignorano; `edReference` è `Long`, mai `double` |
| RNF-05 | Timeout espliciti su connessione e lettura |
| RNF-06 | Stack della catena: Java 17, Spring Boot 3.5.14, Dockerfile allineato a `ce-dichiarato-adapter` |

## 11. Criteri di accettazione

### 11.1 Client (si sviluppa ora; test con server HTTP finto e dati inventati)

| # | Given / When / Then |
|---|---|
| AC-01 | Dato un evento di spedizione valido, quando lo invio, allora parte `POST /event/shipment/v1` con `X-API-Key` e il JSON atteso; con `201` l'esito è CREATO |
| AC-02 | Dato un `201` con `warnings`, l'esito è CREATO e i codici dei warning sono riportati |
| AC-03 | Dato un `400` con `errors [02060]`, l'esito è RIFIUTATO con il codice `02060` |
| AC-04 | Dato un lotto di due eventi e un `201` con `errors` solo sul primo, il primo è RIFIUTATO e il secondo CREATO |
| AC-05 | Dato un `401` con corpo testo `Invalid API Key`, l'esito è ERRORE_CONFIGURAZIONE senza errori di parsing |
| AC-06 | Dato un `500`, l'esito è ERRORE_TEMPORANEO e la richiesta parte **una sola volta** |
| AC-07 | Dato un timeout di lettura, l'esito è ERRORE_TEMPORANEO con motivo "esito incerto", senza eccezione verso il chiamante |
| AC-08 | Dato un lotto più grande di `lotto-max`, partono più chiamate e gli esiti tornano nell'ordine della richiesta |
| AC-09 | Dato un `201` a lotto con un numero di elementi diverso dalla richiesta, tutti gli eventi della chiamata sono ERRORE_TEMPORANEO "risposta non correlabile" |
| AC-10 | Dato un evento con `eventCode` di lunghezza errata, o con codice 100 senza `acceptorName`, o di collo senza riferimenti, l'esito è RIFIUTATO locale senza chiamata HTTP |
| AC-11 | `eventTimestamp` è serializzato come `2026-11-05T13:45:00.000Z` |
| AC-12 | Nei log del client non compaiono `acceptorName` né la chiave API |
| AC-13 | Le metriche della sezione 9 si incrementano con i tag attesi |

### 11.2 End-to-end (quando la sorgente è decisa)

Da scrivere: evento SDA → evento EURODIS creato in TEST, rifiuto con codice errato, ripresa dopo un errore temporaneo.

## 12. Punti aperti e default provvisori

| # | Punto | Default per partire | Impatto quando arriva la risposta | Rif. |
|---|---|---|---|---|
| ST-01 | Catalogo dei codici evento EURODIS (3 cifre spedizione, 4 collo) e traduzione degli eventi SDA. Lo swagger non li elenca: rimanda al manuale di rete EURODIS | il client accetta qualsiasi codice della lunghezza giusta; la traduzione sarà una tabella da configurazione | si compila la tabella; si decide spedizione o collo | PA-34 (nuovo), PA-07 |
| ST-02 | Sorgente degli eventi SDA delle LDV EURODIS (topic, archivio T&T, formato) | nessun consumer | si scrivono consumer e storico | PA-35 (nuovo), PA-07 |
| ST-03 | Correlazione LDV SDA → `edReference` e barcode; quale barcode EURODIS si aspetta da SDA (europlate, delivery partner CLS, alternative) | proposta `edReference` + `europlateBarcode` | indice di correlazione nel mapper o in `-in` | PA-35, PA-11 |
| ST-04 | Significato di `locationCode` (es. `CN-CC`) e di `countryCode` per gli eventi SDA | campi passati dal chiamante | regola di derivazione (deposito SDA? codice EURODIS?) | PA-36 (nuovo) |
| ST-05 | SDA riceve transit unit EURODIS? Servono gli eventi transit? | no | eventuali endpoint transit | PA-36 |
| ST-06 | Massimo di eventi per lotto; ordine e numero degli elementi nella risposta | 100; stesso ordine | `lotto-max`; correlazione diversa se l'ordine non è garantito | PA-36 |
| ST-07 | EURODIS scarta i doppioni? Una POST ripetuta crea due eventi? | retry anche sugli esiti incerti | se i doppioni sono un problema, esiti incerti a verifica manuale | PA-36 |
| ST-08 | Chiave API di send-tracking: la stessa di receive-pan? | stesso secret | secret separato | PA-12 |
| ST-09 | Fuso orario atteso in `eventTimestamp` | UTC con `Z` | formato locale se richiesto | PA-27 |
| ST-10 | Errori verso EURODIS (spedizioni scartate dal mapper): passano da un evento di eccezione? | fuori dal client | eventuale codice evento di scarto | PA-08 |

## 13. Riferimenti

- Swagger: [eurodis-send-tracking-swagger-v1.json](../eurodis-send-tracking-swagger-v1.json); originale https://testapi.eurodis.com/send-tracking/swagger/Release%20v1/swagger.json
- [ce-dichiarato-eurodis-in.md](ce-dichiarato-eurodis-in.md): convenzioni, collezione `eurodis_spedizioni`
- [analisi.md](../analisi.md): PA-07, PA-08, PA-11, PA-12, PA-27, PA-34…PA-36
- Repository: CORRIERE-ESPRESSO_PREADVISING_ce-eurodis-send-tracking
- Modello di metriche e tracing: `ce-dichiarato-adapter`, `ce-dichiarato-eurodis-in` (`TraceUtil`, `MetricheEurodisIn`)

## Domande per Diego

1. **Sorgente degli eventi SDA** (ST-02): sai chi possiede le tracce SDA delle LDV EURODIS e su quale topic o archivio passano? Il placeholder `preadvising.eud.send-tracking` di azzurrazezza è un topic che esiste o un'idea?
2. **Catalogo dei codici evento** (ST-01): lo chiediamo a Chiapponi/EURODIS insieme alla tabella di traduzione? Serve il manuale di rete EURODIS.
3. **Retry sugli esiti incerti** (7.2): va bene la proposta "meglio un doppione che un evento perso" finché EURODIS non risponde su ST-07?
4. **Livello degli eventi**: spedizione, collo o entrambi? Dipende da ST-01, ma se hai già un'indicazione la mettiamo come default.
