# Mock di test EURODIS (S01-S61)

Un file per scenario, stesso formato del mock base. Generati da `../genera_mock_test.py`.

| File | Scenario |
|---|---|
| S01.json | Standard, un collo |
| S02.json | Multi-collo (3 colli, pesi 3/5/7) |
| S03.json | Multi-collo, pesi decimali 1.5/2.25/0.4 |
| S04.json | Senza contatti (telefono, SMS, e-mail) su mittente e destinatario |
| S05.json | Valori al limite (civico 4, citta 30, ragione sociale 40) |
| S06.json | Peso 0, senza dimensioni |
| S07.json | Mittente con citta e CAP austriaci (countryCode IT: BEP rifiuta altrimenti) |
| S08.json | Preavviso destinatario (SMS, e-mail, telefono) |
| S09-C.json | shipmentTypeIndicator = C |
| S09-X.json | shipmentTypeIndicator = X |
| S10.json | Sabato (6) |
| S11.json | Sera (E) |
| S12.json | Entro le 12 (M) |
| S13.json | Entro le 10 (F) |
| S14.json | Su appuntamento (B, bookIn true, telefono valorizzato) |
| S15.json | Finestra di consegna (W) [da confermare] |
| S16.json | Pomeriggio (A) |
| S17-D.json | deliveryService = D [da confermare] |
| S17-7.json | deliveryService = 7 [da confermare] |
| S17-T.json | deliveryService = T [da confermare] |
| S18-S.json | Gestione firma, deliveryType = S, nessun altro servizio |
| S18-N.json | Gestione firma, deliveryType = N, nessun altro servizio |
| S18-D.json | Gestione firma, deliveryType = D, nessun altro servizio |
| S19.json | Punto di ritiro (Z + pudoID) [da confermare] |
| S20.json | Contrassegno contanti 123.45 EUR (id 3) |
| S21.json | Contrassegno assegno 250.00 EUR (id 5) |
| S22.json | Contrassegno importo 0 |
| S23.json | Contrassegno in CHF 100.00 |
| S30.json | Entro le 12 + contrassegno |
| S31.json | Entro le 10 + contrassegno |
| S32.json | Appuntamento + contrassegno |
| S33.json | Entro le 12 + multi-collo |
| S34.json | Contrassegno + multi-collo |
| S35.json | Entro le 10 + contrassegno + multi-collo |
| S36.json | Appuntamento + multi-collo |
| S37.json | Punto di ritiro + contrassegno [da confermare] |
| S40.json | consignorsColloBarcode vuoto |
| S41.json | europlateBarcode vuoto |
| S42.json | europlateBarcode = "0" |
| S43.json | Multi-collo, primo europlate vuoto |
| S44.json | Multi-collo, consignor ed europlate vuoti |
| S45.json | entranceTimestamp assente |
| S60.json | Dogana 500.00 EUR, mittente con citta e CAP svizzeri (countryCode IT) |
| S61.json | Dogana 500.00 CHF, mittente con citta e CAP svizzeri (countryCode IT) |
