# Mock di `receive-pan` con WireMock (OpenShift)

Manifesti di Diego (12-11, ConfigMap aggiornata il 16-11 come in svil) per un mock dell'endpoint EURODIS da cui `ce-dichiarato-eurodis-in` scarica
le spedizioni: ConfigMap con le risposte, Deployment WireMock, Service interno.
File: [wiremock-receive-pan.yaml](wiremock-receive-pan.yaml). Dati della spedizione: quelli di fantasia
dell'ambiente TEST EURODIS.

## Uso

Per rigenerare il file dal cluster (lo facciamo insieme, con una sessione `oc` di sola lettura):
`oc -n corriere-espresso-preadvising get configmap wiremock-config -o yaml`, e lo stesso per
`deployment/wiremock-mock` e `service/wiremock-mock`. Poi si tolgono i campi del cluster
(`uid`, `resourceVersion`, `creationTimestamp`, `managedFields`, `namespace`, `status`,
`clusterIP(s)`, `generation`, annotazioni `deployment.kubernetes.io/*`) e si sostituisce la sezione
corrispondente di `wiremock-receive-pan.yaml`. Dopo una modifica alla ConfigMap va riavviato il pod:
`oc -n corriere-espresso-preadvising rollout restart deployment/wiremock-mock`.

1. `oc -n corriere-espresso-preadvising apply -f wiremock-receive-pan.yaml`
2. In `-in` (values dell'ambiente): `EURODIS_BASE_URL: 'http://wiremock-mock:8080/receive-pan'`.
3. Le risposte si cambiano modificando la ConfigMap (e riavviando il pod WireMock) oppure a caldo con
   l'API di amministrazione di WireMock (`POST /__admin/mappings`).

## Da sapere prima di usarlo

- **Path.** `-in` chiama `EURODIS_BASE_URL + /shipments/v1` (scarico) e `+ /shipment/{edReference}/v1`
  (rilettura). Dal 16-11 la mappatura risponde su `/receive-pan/shipments/v1`. La rilettura puntuale
  non è mappata: WireMock risponde 404.
- **Contenuto (17-11).** Una spedizione per chiamata, con destinatario e mittente valorizzati e date di
  oggi (`{{now}}`). Sono casuali a ogni chiamata (`response-template`) tutti gli identificativi che finiscono
  nel tracciato:
  - `edReference` = `88` + 11 cifre: è `spedizione.rif_spedizione`, la chiave Kafka e la chiave della
    spedizione in `-in`;
  - `dispatchPartnersDomesticShipmentNumber` = `30` + 6 cifre: `spedizione.id_ldv_partner_master`;
  - `collis[].europlateBarcode` = `12345` + 19 cifre: `internazionale.id_ldv_itz`;
  - `collis[].deliveryPartnerBarcode` = `JVGTCRDS` + 14 cifre: la LDV, `collo[].id_ldv`;
  - `referencedEurodisShipmentNumber`, non mappato.

  Ogni scarico produce quindi una spedizione nuova (ogni 2 minuti in svil).
- **Consegna una volta sola.** EURODIS restituisce ogni spedizione una volta e poi `404`. Questa
  mappatura statica restituisce sempre la stessa risposta: per simulare il consumo servono gli scenari
  di WireMock (`scenarioName`, `requiredScenarioState`, `newScenarioState`) o una seconda mappatura
  con `404`.
- **Immagine.** `wiremock/wiremock` è un'immagine di terzi: in svil va presa dal registry Poste e deve
  passare il gate CVE.
- **Dove punta svil.** Il mock interno a `-in` è stato tolto (revert del 12-11): su `develop` svil usa il
  default di `.helm/values.yaml`, `https://testapi.eurodis.com/receive-pan`. Per usare questo mock va
  messo `EURODIS_BASE_URL: 'http://wiremock-mock:8080/receive-pan'` nei values di svil.
- Il mock Python per i test in locale è in [../README.md](../README.md).
