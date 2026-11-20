# Esiti preadvising.completed del 2026-11-19 (25 su 43 scenari completed, più S22 e S05 in errore atteso)

Estratto compatto dei campi rilevanti. Chiave scenario = `rif_spedizione` (edReference del mock, vedi `configmap-wiremock-tutti.yaml`).
Base comune a tutti: numero_colli 1, mittente IT/Berlin "Demo street", destinatario Roma normalizzato OK, valore 0, assicurata S/0, id_partner EURODIS, flag_stampa_ldv N, ora_spedizione 00:00:00, peso collo "15.000", dimensioni "33"/"55"/"44", cliente DECORATION GROUP piva 08890561007.

| Scenario | id_preadvising | rif_spedizione | prodotto / id_servizio | codici_servizi (extra su base) | contrassegno | consegna: accessorio / servizi_spedizione / data-ora | id_ldv_itz | note |
|---|---|---|---|---|---|---|---|---|
| S41 | 115c1d17-4620-4afd-95f5-9972b784d096 | 4400000000041 | PBE/582 | base | N | - / GSP | "" (vuoto) | europlate vuoto |
| S20 | 17362e2e-a717-4828-ba6d-89c543218e6a | 4400000000020 | CBE/583 | +APT000918 | S CON 123.45 | - / CA0\|GSP | 24 cifre | |
| S09-C | 198e27fa-d540-4d70-9e38-fddbeeec23f5 | 4400000000091 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (ragione_sociale XIYEHOGEEZ ZVUEB Y.V.M., piva 33896185242); collo peso "15000.0", lunghezza "33.0", profondita "44.0". **Superato: rieseguito il 20-11, vedi in fondo** |
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
| S08 | be009755-2e86-4b46-9632-8a700a69dca4 | 4400000000008 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (come S09-C); collo "15000.0"/"33.0"/"44.0"; preavviso destinatario (SMS/email/tel) non visibile nel messaggio. **Superato: rieseguito il 20-11, vedi in fondo** |
| S09-X | d0190d76-a1be-4f50-9bd2-fb20fdd47629 | 4400000000092 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S17-D | d4f69655-eafe-40b8-8996-0c1a0f92537a | 4400000000174 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S23 | de4aa897-ff80-4556-b178-cf5a5e4b133a | 4400000000023 | CBE/583 | +APT000918 | S CON 100 | - / CA0\|GSP | 24 cifre | mock in CHF, valuta non presente nel messaggio |
| S21 | de949e04-d841-4eb1-9cdd-e694f2f42e9f | 4400000000021 | CBE/583 | +APT000918 | S ABM 250 | - / CA2\|GSP | 24 cifre | assegno |
| S18-D | e2ed2c31-f133-4ce3-a94e-a0ac68044e51 | 4400000000184 | PBE/582 | base | N | - / GSP | 24 cifre | cliente ANOMALO (come S09-C); ora_spedizione "06:53:55" (tutti gli altri 00:00:00 pur avendo lo stesso entranceTimestamp nel mock). **Superato: rieseguito il 20-11, vedi in fondo** |
| S17-T | e639a100-458d-462f-8c40-047e9784ffe1 | 4400000000173 | PBE/582 | base | N | - / GSP | 24 cifre | |
| S19 | f43c4d61-dde3-4c18-87f0-10cef3c4bdc5 | 4400000000019 | PBE/582 | base | N | - / GSP | 24 cifre | punto di ritiro (Z + pudoID), nessun segno del punto di ritiro |
| S11 | f491428b-4491-41b4-af4c-b23289021691 | 4400000000011 | PBE/582 | +APT000911 | N | SER / SR0\|GSP | 24 cifre | sera (E) |

"base" = APT000916|920|921|923|924|925|927|931|932|933|934|935|936|937|950|951|952|953|954|APT001014.

## Scenari che restituiscono errore: esito atteso (confermato)

Questi due scenari non arrivano a `preadvising.completed`: l'errore è il comportamento corretto, non un difetto.

| Scenario | Mock | Input | Esito | Motivo |
|---|---|---|---|---|
| S22 | `S22.json` | contrassegno con `amount` = 0 | errore: **atteso, OK** | un contrassegno a importo 0 non è valido (il CSV vuole `amount` > 0, vedi `accessori-eurodis-pdb-proposta.md` S6) |
| S05 | `S05.json` | valori al limite: civico 4, citta 30, ragione sociale 40 | errore: **atteso, OK** | i valori al limite non sono accettati a valle |

Da completare: codice/messaggio d'errore effettivo e punto della catena in cui si ferma (non riportati qui, non verificati).
Gli altri 16 scenari dei 43 non sono ancora censiti in questo esito.

## Rieseguiti il 2026-11-20: S08, S09-C, S18-D

Ripetuti con `edReference` `5500…` (mock aggiornato: `S08.json`, `S09-C.json`, `S18-D.json`). Sostituiscono le righe del 19-11.

| Scenario | id_preadvising | rif_spedizione | id_ldv_tt | id_ldv_itz | esito |
|---|---|---|---|---|---|
| S08 | 2a3ea629-8bfd-409a-b628-9884c398203b | 5500000000008 | 3UW2308154190 | 123453395681584539330762 | OK, con riserva su `ora_spedizione` |
| S09-C | 0cbfd092-c8be-451b-a389-015b335340a5 | 5500000000091 | 3UW2308393186 | 123455357862373091363944 | OK, con riserva su `ora_spedizione` |
| S18-D | 63aefd66-c6f1-4d19-8c7d-8b2b1e83c4f1 | 5500000000184 | 3UW2308880401 | 123451946304470206162474 | OK, con riserva su `ora_spedizione` |

Campi comuni ai tre: PBE/582, `codici_servizi` base, contrassegno N, `consegna` `- / GSP`, `data_spedizione` 2026-11-20.

**Risolto rispetto al 19-11**
- Cliente DECORATION GROUP (piva 08890561007) in tutti e tre: l'anomalia dipendeva dalla chiave `4400…`.
- Collo `peso "15.000"`, dimensioni `"33"/"55"/"44"` (prima `"15000.0"/"33.0"/"44.0"`).
- `ora_spedizione` di S18-D non è più diversa dagli altri.

**Aperto**
- `ora_spedizione` è `00:00:00` in tutti e tre, ma il mock ha `entranceTimestamp` `T06:53:55`. La specifica (`sviluppo/ce-dichiarato-eurodis-mapper.md`, riga `ora_spedizione`, AC-01) vuole `06:53:55`. Da correggere; causa non ancora verificata.

**Conformi alla specifica (assenza di effetto voluta)**
- S08: `consigneePreAdvice` non mappato (DF-09).
- S09-C: `shipmentTypeIndicator` ignorato (DF-15); messaggio identico a S08 salvo gli id.
- S18-D: `deliveryType D` deve dare `no_firma ""` (AC-05). Nel messaggio il campo non compare: non distinguibile da "assente". Il caso discriminante è S18-S / S18-N (da verificare).

**Non verificati**
- `consegna.contactless "S"` e `consegna.modifica_modalita "S"` sono valorizzati in tutti e tre; nella specifica non c'è la regola che li produce. Da chiarire.
- Campo `x_canary_<hex>` in ogni messaggio: non è nel mock né nella specifica; atteso, non si tratta.

## Risolti il 2026-11-20: S12, S13, S30

Mock con `edReference` `5500…`, mittente Milano (Via Montenapoleone, normalizzato OK), cliente DECORATION GROUP.

| Scenario | id_preadvising | rif_spedizione | prodotto / id_servizio | codici_servizi (extra su base) | contrassegno | consegna: accessorio / servizi_spedizione | id_ldv_tt | esito |
|---|---|---|---|---|---|---|---|---|
| S12 | 3eb16dc7-c2a4-4794-9039-c9d89a2c0815 | 5500000000012 | PBE/582 | +APT000907 | N | T12 / TD3\|GSP | 3UW2308060914 | RISOLTO |
| S13 | 542cdb33-2978-4d86-abe6-fe591ffe84c3 | 5500000000013 | PBE/582 | +APT000906 | N | T10 / TD0\|GSP | 3UW2308226647 | RISOLTO |
| S30 | 91dcc748-e0df-4286-ab0a-9d13699cb810 | 5500000000030 | CBE/583 | +APT000907 +APT000918 | S CON 123.45 | T12 / TD3\|CA0\|GSP | 4UW2308866454 | RISOLTO |

- `APT000906` per `F` (entro le 10) e `APT000907` per `M` (entro le 12): conformi alla specifica.
- Con contrassegno la LDV parte da `4U`, senza da `3U`: coerente con la regola di `id_ldv`.
- Ancora aperti, come per gli altri scenari: `ora_spedizione` `00:00:00` (atteso `06:53:55`); `no_firma` non visibile nel messaggio (qui `deliveryType S` darebbe `"N"`).
- Non verificati: la corrispondenza `deliveryService` M/F con accessorio `T12`/`T10` e servizi `TD3`/`TD0` non l'ho trovata nella specifica.

## In errore il 2026-11-20: S02, S60

| Scenario | rif_spedizione | dove si ferma | errore |
|---|---|---|---|
| S02 | 5500000000002 | mapper (offset 1450, nessuna pubblicazione) | `ldv_non_pdb`: `collis[].deliveryPartnerBarcode (non PDB nei colli [2, 3] di 3) -> spedizione.collo[].id_ldv` |
| S60 | 5500000000060 | BEP | `BEP:101`: "Dati non conformi: zipCode" |

**S02: conflitto fra specifica e mock, da decidere.**
- Il mock (`genera_mock_test.py`, righe 147-154) segue la regola multicollo dell'ICD BEP: collo 1 con la LDV madre di 13 caratteri, colli 2 e 3 con il figlio di 22 caratteri (9 casuali + madre).
- RF-17 (`ce-dichiarato-eurodis-mapper.md`, sezione 6.2.1 passo 1) considera PDB solo la LDV di 13 caratteri `[1-8]U[A-Z0-9]{5}[0-9A-Z]{6}` e la applica a ogni collo: i figli di 22 caratteri vengono scartati.
- Il mapper si comporta come da specifica; il difetto è nella specifica, se i figli a 22 caratteri sono validi (da confermare con Diego).

**S60: errore del mock, non del mapper.**
- Il messaggio ha superato il mapper; l'errore viene da BEP.
- Il mittente ha CAP svizzero `8001` / Zurich con `countryCode IT`. Stessa causa già corretta per S12/S13/S30 (mittente Milano, riga 158 di `genera_mock_test.py`).
- Il destinatario ha CAP `00144`, valido: il `zipCode` rifiutato è quello del mittente (dedotto, non letto nel log di BEP).
- Stessa struttura in S61 (CHF): atteso lo stesso errore, non ancora verificato.

## Riepilogo esiti test mock (indicazione di Azzurra, 2026-11-23)

Su 44 scenari del mock (`INDICE.md`): **36 andati a buon fine**, **8 non andati a buon fine**.

**Andati a buon fine (36)**: S01, S04, S05, S06, S07, S08, S09-C, S09-X, S10, S11, S12, S13, S14, S15, S16, S17-D, S17-7, S17-T, S18-S, S18-N, S18-D, S19, S20, S21, S22, S23, S30, S31, S32, S37, S40, S41, S42, S45, S60, S61.

**Non andati a buon fine (8)**: S02, S03, S33, S34, S35, S36, S43, S44 (tutti multi-collo).

Note sullo stato precedente, superato da questa indicazione:
- S05 e S22: l'errore è il comportamento atteso, quindi il test è OK.
- S60 e S61: nel report del 20-11 S60 era in errore `BEP:101` per il CAP svizzero del mittente (errore del mock). Ora risultano OK sulla base della correzione del mock; il rerun non è documentato in questo file.
- S02: errore `ldv_non_pdb` sui colli 2 e 3 (figli da 22 caratteri), vedi la sezione "In errore il 2026-11-20". Il conflitto fra specifica RF-17 e mock resta da decidere.

## Rilasci mancanti

| Servizio | Motivo | Stato |
|---|---|---|
| `ce-dichiarato-ldv-pdb` | fix su `ORA_CONSEGNA` | **MANCANTE**: da rilasciare |
