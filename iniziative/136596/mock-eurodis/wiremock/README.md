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
- **Contenuto (17-11).** Una spedizione per chiamata, con destinatario e mittente valorizzati e date di
  oggi (`{{now}}`). Sono casuali a ogni chiamata (`response-template`) tutti gli identificativi che finiscono
  nel tracciato:
  - `edReference` = `88` + 11 cifre: è `spedizione.rif_spedizione`, la chiave Kafka e la chiave della
    spedizione in `-in`;
  - `dispatchPartnersDomesticShipmentNumber` = `30` + 6 cifre: `spedizione.id_ldv_partner_master`;
  - `collis[].europlateBarcode` = `12345` + 19 cifre: `internazionale.id_ldv_itz`;
  - `collis[].deliveryPartnerBarcode` = `3UW2308` + 6 cifre: la LDV, `collo[].id_ldv` (dal 18-11; prima
    `JVGTCRDS` + 14 cifre, che `ce-ldv` non riconosce). È una LDV PDB di 13 caratteri: `[1-8]U` + seme
    di 5 + progressivo di 6 (semantica `PPTT` di `ce-ldv`). Il seme è il `pds_code` del contratto
    `SFA-00633620` per il canale di prenotazione (`contract_ps_data.pds`): `W2308` = `INVIOSYSTEM`
    (gli altri: `W2306` INVIOEASY, `W2307` INVIOFILE, `W2309` WEB, `W2319` WEBSERVICES). Il primo
    tentativo con `W0008` (seme di postazione in `sfa_postazioni_ou`) è stato rifiutato da BEP come
    "barcode non utilizzabile", e così anche `1UW2308` (errore BEP `131`). Il prefisso è `3U`,
    indicato da Poste il 18-11 e coerente con le LDV che BEP restituisce. Un collo figlio PDB ha invece 22 caratteri (9 del figlio + 13 della
    madre): non usare 22 caratteri per un collo singolo;
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
