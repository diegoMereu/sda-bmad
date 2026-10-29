# 136596 — Eurodis autoproduttore · Accessori EURODIS → formato PDB (proposta)

**Data**: 2026-10-29 · **Analista**: Mary · **Stato**: proposta, da validare con Diego

Non sostituisce `analisi.md` né i DF del 23-10: raccoglie cosa serve per
portare i servizi accessori dal formato EURODIS (API `receive-pan`) al formato
PDB che il ms sync si aspetta. Dopo la validazione si riversa in mapping, DF e
punti aperti.

## Catena e responsabilità

```
receive-pan (API EURODIS)
  -> [NOSTRO] mapping verso ICD v11: codici_servizi + campi delle sottochiavi
  -> ce-dichiarato-ldv-pdb-sync (esistente, in test)  ->  PDB waybillCreate (sincrono)
```

Il nostro compito è consegnare al ms sync un TracciatoUnicoDTO corretto. Per
ogni accessorio EURODIS dobbiamo scrivere quello che il builder PDB scriverebbe
partendo da un JSON con `APTxxxxxx` e le sue sottochiavi.

Fonti:
- `FlussiPreadvisingInfo.csv` (specifica accessori per i JSON PDB: codici,
  sottochiavi, controlli).
- Riscontro SDA/Chiapponi del 11-09-2026 (perimetro e valori EURODIS), che
  descrive il flusso via file: i valori sono ipotesi per l'API finché non
  confermati.
- `APT_analysis.md` (catena JSON PDB → tracciato unico → BEP).
- `PdbRequestMapper.java` di `ce-dichiarato-ldv-pdb-sync`.

## 1. Mapping accessori: EURODIS → APT → ICD

`codici_servizi` è una stringa separata da pipe, es. `APT000910|APT000918`.

| Servizio | Da API EURODIS | In `codici_servizi` | Campi ICD per le sottochiavi | Stato |
|---|---|---|---|---|
| Consegna al sabato | `deliveryService` = `6` | `APT000910` | nessuno (`{}`) | confermato SDA |
| Consegna di sera | `deliveryService` = `E` | `APT000911` | nessuno | confermato SDA |
| Time Definite ore 10 | `deliveryService` = `F` | `APT000906` | nessuno | confermato SDA |
| Time Definite ore 12 | `deliveryService` = `M` | `APT000907` | nessuno | confermato SDA (per EURODIS `M` è "Morning") |
| Consegna su appuntamento | `deliveryService` = `B` (e `W`) | `APT000908` | nessuno; serve il telefono del destinatario | `B` confermato SDA; `W` → APP dalla matrice di test (da confermare) |
| Punto Poste | `deliveryService` = `Z` + `consigneeAddress.pudoID` | `APT000947` | `consegna.codice_frazionario` = PUDO ID (`node`); `consegna.denominazione_frazionario` = nome del punto (`name`, non vuoto) | da confermare (PA-01 del riscontro: sorgente del nome) |
| Contrassegno | presenza di `cashOnDeliveryService` | `APT000918` | `contrassegno.importo_contrassegno` = `amount` (2 decimali, > 0, max 999999.99); `contrassegno.tipo_pagamento_contrassegno`: `3` → `CON`, `5` → `ABM`; `contrassegno.flag` = `S` | da confermare (3→CON, 5→ABM, formato importo) |
| Multicollo | più di un elemento in `collis[]` | **non scriverlo** | nessuno | il ms sync aggiunge `APT000945` se i colli sono più di uno |
| Pre-avviso | `consigneePreAdvice` | nessuno | nessuno | SDA notifica da sola se ci sono i contatti: non si mappa |
| Pomeriggio | `deliveryService` = `A` | nessuno | nessuno | spedizione normale (SDA) |

Regole di combinazione note: il contrassegno non è ammesso con consegna a
Punto Poste o di prossimità. `deliveryService` è un valore unico, quindi una
spedizione ha al massimo un servizio di consegna, combinabile con contrassegno
e multicollo.

### Non coperti dal riscontro SDA (lacune)

| `deliveryService` | Significato EURODIS | Domanda |
|---|---|---|
| `D` | Day | servizio, scarto o normale? |
| `7` | domenica | idem |
| `T` | a orario definito | SDA: "consegna a giorno e orario definito", senza APT (PA-05 del riscontro) |

### Fuori perimetro (da non mappare)

Assicurazione (APT000955/956/919): non valorizzare `assicurata` né i codici
copertura, anche se `commercialValueOfGoods` arriva valorizzato. Locker
(APT000948), Uffici Postali (APT000949), Time Definite ore 9 (APT000905),
reverse a domicilio (APT000928), abbandono. Spedizioni di tipo P (pickup): via
FTP, non devono arrivare dall'API. Tipi C, X e A si trattano come N.

### Reso

Per EURODIS "reso" è il rientro al mittente di una spedizione non consegnata
(indirizzo RT_30 tipo R, `returnAddress` in API). Non si mappa finché non si
decide se serve `APT000930` (sottochiave `return`: `A` o `R` secondo il CSV).

## 2. ms sync `ce-dichiarato-ldv-pdb-sync`: osservazioni (da segnalare al responsabile)

Il ms è in test. Rilevanti per EURODIS:

| # | Osservazione | Effetto |
|---|---|---|
| S1 | Canale: la costante `PDB_CHANNEL_POU = "POU"`, ma README e Javadoc dicono `WEBSERVICE` | da chiarire quale vale |
| S2 | ISO4: esiste `AnagraficaClient.resolveIso4` ma non è chiamato da nessuno; il paese passa come `codice_nazione` | PDB vuole ISO4: o lo scriviamo noi in `codice_nazione`, o va corretto il ms |
| S3 | Peso assente → `"0"`; dimensioni assenti → `null`. Nessun default (1/1/1 previsto nel riscontro) | EURODIS può inviare 0: rischio KO. Nel flusso file i default li applica il validatore (VR-31): da verificare se la nostra catena passa dal validatore |
| S4 | Nessun troncamento (civico 4, città 30, indirizzo 40, nome 35) | rischio KO su valori lunghi, vedi DF-19. Nel flusso file tronca il validatore (test EUD_007): da verificare come per S3 |
| S5 | Punto Poste con nome vuoto: `name` omesso | il controllo CSV lo rifiuta: il nome del punto è obbligatorio |
| S6 | Contrassegno con importo 0 non scartato in locale | il CSV vuole `amount` > 0 |
| S7 | `rif_prodotto_cliente` vuoto → prodotto da config (`APT000901`); `contractCode` e `costCenterCode` hanno fallback in config | DF-11 si ridimensiona |

Non rilevanti per EURODIS ma da riferire: ascensore `APT000917` (nell'async è
`913`), copertura gestita solo per `APT000919` (non 955/956), `deliveryDate`
dei servizi LMD letto da `data_appuntamento` (bug B6 corretto solo nell'async),
`APT000930` con `return=R` non escluso (nell'async sì).

## 3. Effetto sui dubbi funzionali (proposta)

| DF | Proposta |
|---|---|
| DF-01 | Conflitto: il riscontro mappa `clearanceTimestamp` → `shipmentDate`; noi usiamo `entranceTimestamp` (commento Diego). Da confermare |
| DF-05 | Tabella sopra; restano le lacune D, W, 7, T |
| DF-06 | `T` senza APT: nessuna mappatura della data di consegna finché non chiarito |
| DF-07 | Contrassegno in perimetro: `APT000918` + `amount` + `CON`/`ABM`; confermare 5→ABM e formato importo |
| DF-08 | Assicurazione fuori perimetro: non valorizzare `assicurata` |
| DF-09 | Pre-avviso non mappato (SDA notifica da sola): rivedere `notifiche_sms` / `notifiche_email` |
| DF-10 | Reso = rientro al mittente; P fuori; C, X, A come normali |
| DF-11 | Prodotto `APT000901` e fallback di contratto e centro di costo in config del ms |
| DF-12 | Destinatario sempre ITA1; mittente ISO2 → ISO4: chi lo fa (S2) |
| DF-13, DF-20 | Prodotto unico trattato come nazionale: i campi internazionali BEP non servono; dogana e ADR da confermare |
| DF-14 | PUDO in perimetro, solo Punto Poste |
| DF-19 | Il ms non tronca (S4): chi adegua i valori |

### Nuovi dubbi proposti

| ID | Dubbio | Chi |
|---|---|---|
| DF-21 | Valori `deliveryService` non coperti (`D`, `7`, `T`); `W` risulta APP nella matrice di test, da confermare | Chiapponi / EURODIS |
| DF-22 | Valori fuori perimetro che arrivano dall'API (`A`, Locker, assicurazione, tipo P): scarto o ignorati? | Chiapponi / EURODIS |
| DF-23 | Nome del Punto Poste: `name` è obbligatorio, ma nel flusso via file è in `RT_30_030`, opzionale e non garantito (`RT_30_080` è il destinatario effettivo). Cosa si fa se manca? | Chiapponi / EURODIS |
| DF-24 | Formato e valuta del contrassegno: `amount` con 2 decimali, solo EUR? `3`→`CON`, `5`→`ABM` | Chiapponi / EURODIS |
| DF-25 | Reso (`APT000930`): serve? valore di `return`, semantica di `R` e `A` | SDA |
| DF-26 | Peso e dimensioni a 0: default 1/1/1 e peso (S3), chi li applica | Diego / responsabile ms sync |
| DF-27 | ISO4 e canale `POU` / `WEBSERVICE` (S1, S2) | responsabile ms sync |
| DF-29 | LDV generata da EURODIS: regole di validità secondo SDA, e univocità. Ogni ripetizione dei test richiede LDV nuove; indirizzi, CAP e nazioni devono essere reali. Richiesto a EURODIS nella mail del 29-10 | Chiapponi / EURODIS |
| DF-28 | Scarto: l'unica causa confermata è il nome del mittente assente. Vale anche per l'API? Come si traccia? | Diego |

## 4. Scenari da chiedere a EURODIS per i test

Un esempio per scenario, con le combinazioni più frequenti. Perimetro
inbound: destinatario IT, mittente anche estero.

- Nessun accessorio (`services{}` vuoto).
- Consegna sabato, sera, ore 10 (`F`), ore 12 (`M`), appuntamento (`B`).
- Punto Poste (`Z` + PUDO ID).
- Contrassegno in contanti (`3`) e con assegno (`5`).
- Singolo collo e multicollo, anche combinati con i servizi sopra.
- Mittente estero (più paesi) verso destinatario IT.
- Pre-avviso SMS, email e telefono.
- Reso (rientro al mittente).
- Casi limite: peso e dimensioni a 0, telefono ed email assenti, nome mittente
  assente, civico oltre 4 caratteri, città oltre 30, `entranceTimestamp` assente.
- Se in produzione transitano anche valori fuori perimetro (`A`, `D`, `W`, `7`,
  `T`, contrassegno su PUDO, assicurazione, dogana, ADR), esempi anche per questi.
