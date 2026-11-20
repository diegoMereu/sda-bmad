# Esiti preadvising.completed del 2026-11-19 (25 su 43 scenari)

Estratto compatto dei campi rilevanti. Chiave scenario = `rif_spedizione` (edReference del mock, vedi `configmap-wiremock-tutti.yaml`).
Base comune a tutti: numero_colli 1, mittente IT/Berlin "Demo street", destinatario Roma normalizzato OK, valore 0, assicurata S/0, id_partner EURODIS, flag_stampa_ldv N, ora_spedizione 00:00:00, peso collo "15.000", dimensioni "33"/"55"/"44", cliente DECORATION GROUP piva 08890561007.

| Scenario | id_preadvising | rif_spedizione | prodotto / id_servizio | codici_servizi (extra su base) | contrassegno | consegna: accessorio / servizi_spedizione / data-ora | id_ldv_itz | note |
|---|---|---|---|---|---|---|---|---|
| S41 | 115c1d17-4620-4afd-95f5-9972b784d096 | 4400000000041 | PBE/582 | base | N | - / GSP | "" (vuoto) | europlate vuoto |
| S20 | 17362e2e-a717-4828-ba6d-89c543218e6a | 4400000000020 | CBE/583 | +APT000918 | S CON 123.45 | - / CA0\|GSP | 24 cifre | |
| S09-C | 198e27fa-d540-4d70-9e38-fddbeeec23f5 | 4400000000091 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (ragione_sociale XIYEHOGEEZ ZVUEB Y.V.M., piva 33896185242); collo peso "15000.0", lunghezza "33.0", profondita "44.0" |
| S14 | 1ab400f7-5e5d-41db-8882-4f09a4cdc974 | 4400000000014 | PBE/582 | +APT000908 | N | APP / PP0\|GSP / nessuna data | 24 cifre | appuntamento (B, bookIn true) |
| S17-7 | 1d69d17e-f7b4-47a5-9514-e64548f32118 | 4400000000172 | PBE/582 | base | N | - / GSP | 24 cifre | nessun servizio mappato |
| S18-S | 2990d5de-e7b1-4760-9c43-1bbda98d94b0 | 4400000000181 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S37 | 29ec5d49-a0ce-4d9d-b5fb-41d903d7d149 | 4400000000037 | CBE/583 | +APT000918 | S CON 123.45 | - / CA0\|GSP | 24 cifre | punto di ritiro + contrassegno, nessun segno del punto di ritiro |
| S10 | 2e0a4234-c677-47c8-b62d-8da694a3de9d | 4400000000010 | PBE/582 | +APT000910 | N | SAB / SB0\|GSP | 24 cifre | sabato |
| S04 | 31e15568-8546-458d-a389-d45fef3ab793 | 4400000000004 | PBE/582 | base | N | - / GSP | 24 cifre | contatti vuoti: telefono/cellulare/email "", *_tipo "vuoto" |
| S32 | 39ec969d-d66f-4abd-abb4-8b688b46bf24 | 4400000000032 | CBE/583 | +APT000908 +APT000918 | S CON 123.45 | APP / PP0\|CA0\|GSP | 24 cifre | appuntamento + contrassegno |
| S18-N | 3e2da169-0417-4b73-9f6b-59f2a8c916aa | 4400000000182 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S16 | 542d44bc-9397-466c-97c1-cd65243e97fe | 4400000000016 | PBE/582 | base | N | - / GSP | 24 cifre | pomeriggio (A), nessun servizio mappato |
| S45 | 54494e54-43ee-48cf-bf05-1afe029b50a9 | 4400000000045 | PBE/582 | base | N | - / GSP | 24 cifre | entranceTimestamp assente nel mock |
| S42 | 66f84f91-ea5b-4ace-aa24-9ed783b7d319 | 4400000000042 | PBE/582 | base | N | - / GSP | "" (vuoto) | europlate = "0" |
| S15 | 703d79b4-2ed1-4a43-8d57-c5b5817b0e89 | 4400000000015 | PBE/582 | +APT000908 | N | APP / PP0\|GSP / 2026-11-21 09:00-13:00 | 24 cifre | finestra di consegna (W) |
| S40 | 95b4a693-a95f-473a-8734-612b2a1242a4 | 4400000000040 | PBE/582 | base | N | - / GSP | 24 cifre | consignorsColloBarcode vuoto |
| S08 | be009755-2e86-4b46-9632-8a700a69dca4 | 4400000000008 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (come S09-C); collo "15000.0"/"33.0"/"44.0"; preavviso destinatario (SMS/email/tel) non visibile nel messaggio |
| S09-X | d0190d76-a1be-4f50-9bd2-fb20fdd47629 | 4400000000092 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S17-D | d4f69655-eafe-40b8-8996-0c1a0f92537a | 4400000000174 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S23 | de4aa897-ff80-4556-b178-cf5a5e4b133a | 4400000000023 | CBE/583 | +APT000918 | S CON 100 | - / CA0\|GSP | 24 cifre | mock in CHF, valuta non presente nel messaggio |
| S21 | de949e04-d841-4eb1-9cdd-e694f2f42e9f | 4400000000021 | CBE/583 | +APT000918 | S ABM 250 | - / CA2\|GSP | 24 cifre | assegno |
| S18-D | e2ed2c31-f133-4ce3-a94e-a0ac68044e51 | 4400000000184 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (come S09-C); ora_spedizione "06:53:55" (tutti gli altri 00:00:00 pur avendo lo stesso entranceTimestamp nel mock) |
| S17-T | e639a100-458d-462f-8c40-047e9784ffe1 | 4400000000173 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S19 | f43c4d61-dde3-4c18-87f0-10cef3c4bdc5 | 4400000000019 | PBE/582 | base | N | - / GSP | 24 cifre | punto di ritiro (Z + pudoID), nessun segno del punto di ritiro |
| S11 | f491428b-4491-41b4-af4c-b23289021691 | 4400000000011 | PBE/582 | +APT000911 | N | SER / SR0\|GSP | 24 cifre | sera (E) |

"base" = APT000916|920|921|923|924|925|927|931|932|933|934|935|936|937|950|951|952|953|954|APT001014.
