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
  (rilettura). Dal 17-11 `-in` chiama `/shipments/v2` (configurabile con `EURODIS_PATH_SCARICO`) e la mappatura risponde sia su `/receive-pan/shipments/v1` sia su `v2` (`urlPathPattern`). La rilettura puntuale
  non è mappata: WireMock risponde 404.
- **Contenuto (19-11).** Due spedizioni per chiamata, mittente con `countryCode: IT` (come la ConfigMap del
  cluster del 18-11), date di oggi (`{{now}}`):
  1. con contrassegno, 1 collo, LDV `4UW2308` + 6 cifre;
  2. senza contrassegno (`cashOnDeliveryService: null`), **3 colli** (`numberOfHandlingUnits: 3`, peso 45):
     il primo collo ha la LDV madre `3UW2308` + 6 cifre (13 caratteri), gli altri due il barcode figlio di
     22 caratteri = figlio di 9 + la stessa madre (regola dell'ICD BEP Mediation v2.5 per INVIOSYSTEM: "in
     caso di multicollo il primo conterra' il barcode a 13 digit della madre, mentre i successivi
     conterranno i barcode a 22 digit dei figli"). Il figlio di 9 segue la regola verificata su 667 figli
     reali in collaudo ([../../ldv-figlia-multicollo-pdb.md](../../ldv-figlia-multicollo-pdb.md)):
     `2308` + contatore `[M-Z][0-9A-Z]{3}` + `W`. Il contatore ha una radice casuale di 3 caratteri
     (`{{#assign 'radice'}}`, prima lettera fra M e Z) e un ultimo carattere `1`, `2` per i colli 2 e 3:
     figli consecutivi e mai uguali, es. `2308MK71W` + madre, `2308MK72W` + madre. Madre e radice sono
     una sola per spedizione grazie a `{{#assign}}`.

  Identificativi casuali a ogni chiamata (`response-template`):
  - `edReference` = `88` + 11 cifre: è `spedizione.rif_spedizione`, la chiave Kafka e la chiave della
    spedizione in `-in`;
  - `dispatchPartnersDomesticShipmentNumber` = `30` + 6 cifre: `spedizione.id_ldv_partner_master`;
  - `collis[].europlateBarcode` = `12345` + 19 cifre: `internazionale.id_ldv_itz`;
  - `collis[].deliveryPartnerBarcode`: la LDV, `collo[].id_ldv`. LDV PDB di 13 caratteri: prefisso + seme
    di 5 + 6 cifre (semantica `PPTT` di `ce-ldv`). Prefisso `4U` con il contrassegno, `3U` senza (Poste,
    18-11). Seme = `pds_code` del contratto `SFA-00633620` per canale (`contract_ps_data.pds`): `W2308` =
    `INVIOSYSTEM` (`W2306` INVIOEASY, `W2307` INVIOFILE, `W2309` WEB, `W2319` WEBSERVICES). Rifiutati da BEP
    con `131`: `JVGTCRDS` + 14 cifre, `1UW0008` (seme di postazione), `1UW2308`;
  - `referencedEurodisShipmentNumber`, non mappato.

  Ogni scarico produce quindi due spedizioni nuove, quattro colli (ogni 2 minuti in svil).
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
