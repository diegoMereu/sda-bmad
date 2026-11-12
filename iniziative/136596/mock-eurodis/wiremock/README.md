# Mock di `receive-pan` con WireMock (OpenShift)

Manifesti di Diego (12-11) per un mock dell'endpoint EURODIS da cui `ce-dichiarato-eurodis-in` scarica
le spedizioni: ConfigMap con le risposte, Deployment WireMock, Service interno.
File: [wiremock-receive-pan.yaml](wiremock-receive-pan.yaml). Dati della spedizione: quelli di fantasia
dell'ambiente TEST EURODIS.

## Uso

1. `oc -n corriere-espresso-preadvising apply -f wiremock-receive-pan.yaml`
2. In `-in` (values dell'ambiente): `EURODIS_BASE_URL: 'http://wiremock-mock:8080/receive-pan'`.
3. Le risposte si cambiano modificando la ConfigMap (e riavviando il pod WireMock) oppure a caldo con
   l'API di amministrazione di WireMock (`POST /__admin/mappings`).

## Da sapere prima di usarlo

- **Path.** `-in` chiama `EURODIS_BASE_URL + /shipments/v1` (scarico) e `+ /shipment/{edReference}/v1`
  (rilettura). La mappatura qui risponde su `/receive-pan/shipments/v2`: con il base URL sopra va
  messo `"urlPath": "/receive-pan/shipments/v1"`, altrimenti WireMock risponde 404 (che per `-in` vuol
  dire "nessuna spedizione").
- **Consegna una volta sola.** EURODIS restituisce ogni spedizione una volta e poi `404`. Questa
  mappatura statica restituisce sempre la stessa risposta: per simulare il consumo servono gli scenari
  di WireMock (`scenarioName`, `requiredScenarioState`, `newScenarioState`) o una seconda mappatura
  con `404`.
- **Immagine.** `wiremock/wiremock` è un'immagine di terzi: in svil va presa dal registry Poste e deve
  passare il gate CVE.
- **Alternativa già presente.** Su `develop` di `-in` c'è un mock di `receive-pan` dentro il servizio
  (commit `16475e3`, `dd2c8fa`: generazione delle spedizioni e interruttore da Bruno); oggi svil e coll
  puntano lì (`EURODIS_BASE_URL: 'http://localhost:8080/ce-dichiarato-eurodis-in/receive-pan'`).
- Il mock Python per i test in locale è in [../README.md](../README.md).
