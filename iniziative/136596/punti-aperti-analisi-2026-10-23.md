# 136596 — Eurodis autoproduttore · Punti aperti di analisi (dubbi funzionali)

**Data**: 2026-10-23 · **Analista**: Mary · **Microservizio**: `ce-dichiarato-eurodis-in`

Qui ci sono solo i **dubbi funzionali** emersi dal mapping EURODIS → tracciato
unico (ICD v11). I punti tecnici (repliche, persistenza, ack, chiave API,
volumi) restano nel registro di [analisi.md](analisi.md).

Riferimenti: foglio "Mapping inverso EURODIS" di
`ICD_PREADVISING_LDV_EVENT_SOURCE_v11.xlsx` (colonna "Punto aperto" = DF-nn),
swagger `eurodis-receive-pan-swagger-v1.json`.

Gravità: **alta** = blocca il mapping o rischia dati sbagliati in produzione;
**media** = serve prima dei test; **bassa** = si può rimandare.

| ID | Gravità | Dubbio | Campi EURODIS → ICD | Come è mappato oggi | Rif. PA | Stato |
|---|---|---|---|---|---|---|
| DF-01 | alta | `entranceTimestamp` è facoltativo in EURODIS: se manca, che data spedizione usiamo? | `entranceTimestamp` → `data_spedizione`, `ora_spedizione` | `yyyy-MM-dd` e `HH:mm:ss` da `entranceTimestamp`; `clearanceTimestamp` ignorato | — | aperto |
| DF-02 | alta | Lo swagger descrive `consignorsColloBarcode` come barcode di **reso** del partner di consegna, oppure barcode del cliente o del partner mittente. Nelle spedizioni normali contiene davvero la LDV? | `collis[].consignorsColloBarcode` → `collo.id_ldv` | Diretto (decisione 22-Oct) | PA-11 | aperto |
| DF-03 | alta | Multicollo: `id_ldv_itz` è un campo unico di spedizione, ma `europlateBarcode` esiste su ogni collo: quale si usa? Come si valorizzano madre e figlio? Da dove arriva `collo.id_collo`? | `collis[].europlateBarcode` → `internazionale.id_ldv_itz`; `collo.id_ldv_madre`, `id_ldv_figlio`, `tipo_collo`, `id_collo` | `id_ldv_itz` diretto; il resto da definire | PA-11 | aperto |
| DF-04 | alta | Canale: il nuovo flusso usa `"EURODIS"` (valore già nell'ICD) o un valore sul modello di `"EUD_INVIOFILE"` del flusso esistente? Indizio dal mapper BEP: `collo.id_ldv` arriva a BEP **solo per il canale INVIOSYSTEM**, e la cartella di progetto è "INBOUND INVIOSYSTEM". Quindi `EUD_INVIOSYSTEM`? Va verificato anche che `BepChannel.fromCanale` lo riconosca | → `canale` | Da definire | PA-15 | aperto |
| DF-05 | media | Il servizio di consegna EURODIS (D giorno, T a orario, M mattina, A pomeriggio, E sera, 6 sabato, 7 domenica, B su prenotazione, W finestra, F entro le 10, Z PUDO) come si traduce in servizi accessori SDA? Prodotto e servizi li ricava ce-rules dalla LDV: va comunque passato qualcosa? | `deliveryService.deliveryService` → `codici_servizi`? | Non mappato | PA-03 | aperto |
| DF-06 | media | Consegna a data (finestra di date EURODIS): esiste un servizio di consegna dedicato da attivare, per esempio la consegna programmata? | `deliveryService.deliveryDateWindowStart` → `consegna.data_consegna` | `yyyy-MM-dd` | — | aperto |
| DF-07 | alta | Contrassegno: **BEP ignora la sezione `contrassegno` e legge solo `codici_servizi`**. Quale codice di servizio accessorio va inserito? Come si codifica il tipo di incasso (3 contanti / 5 assegno) nei valori ICD (`CON`, `ACM`, ...)? Conto di accredito e valuta non hanno un campo ICD | `cashOnDeliveryService.*` → `contrassegno.*`, `codici_servizi` | `flag` S/N, importo diretto, tipo pagamento da definire | PA-19 | aperto |
| DF-08 | alta | Assicurazione: **anche la sezione `assicurata` è ignorata da BEP, conta solo `codici_servizi`**. Lo swagger dice che il valore merce serve "per motivi assicurativi". Lo usiamo come importo assicurato? Se presente, la spedizione è assicurata (`"S"`)? | `customsService.commercialValueOfGoods` → `assicurata.importo_assicurata`, `assicurata.spedizione_assicurata` | Importo diretto; flag da definire | — | aperto |
| DF-09 | media | Preavviso: l'abbiamo mappato così, va confermato. Il preavviso telefonico EURODIS non ha un campo nel tracciato | `consigneePreAdvice.smsPreAdvice` → `notifiche_sms`; `eMailPreAdvice` → `notifiche_email`; `telephonePreAdvice` → nessuno | `true` → `"S"`, `false` → `"N"` | PA-18 | aperto |
| DF-10 | media | Resi: `referencedEuroplateBarcode` va in `id_ldv_associata`, ma nell'ICD questo campo è di spedizione e di 3 caratteri, mentre il barcode è per collo e di 24. Più in generale: ignorando `shipmentTypeIndicator`, come riconosciamo resi e rettifiche? | `collis[].referencedEuroplateBarcode` → `id_ldv_associata`; `referencedEurodisShipmentNumber`, `returnAddress` → nessuno | Diretto, valore intero | PA-17 | aperto |
| DF-11 | alta | `rif_prodotto_cliente` (`APT000902`) e `centro_costo` (`CDC-00000014`) del flusso EUD_INVIOFILE: sono costanti di contratto da replicare? **`centro_costo` è obbligatorio per BEP** (`costCenterCode`) | → `rif_prodotto_cliente`, `centro_costo` | Da definire | PA-23 | aperto |
| DF-12 | alta | Codice nazione: ora `countryCode` (ISO2) va solo in `codice_nazione_iso_2`. Nell'esempio EUD_INVIOFILE invece l'ISO2 sta in `codice_nazione`. **BEP vuole obbligatoriamente paese in ISO4 e nome paese** per mittente e destinatario: chi li valorizza, il normalizzatore a valle o il nostro microservizio? | `countryCode` → `codice_nazione_iso_2` | Diretto, solo lì | — | aperto |
| DF-13 | media | Dogana e ADR: le spedizioni extra-UE e con merci pericolose rientrano nel perimetro? Se sì, molti campi EURODIS non hanno destinazione | `customsService.*`, `hazardousADRServices[]`, `hazardousCollis[]` | Descrizione, valore, TARIC mappati; ADR no | PA-13 | aperto |
| DF-14 | bassa | PUDO: la consegna in punto di ritiro non è mappata, il tracciato non ha un campo generico | `consigneeAddress.pudoID` | Non mappato | PA-20 | aperto |
| DF-15 | bassa | Il tracciato non ha un secondo numero di telefono: chiedere se serve | `alternativeContactTelephone` (mittente e destinatario) | Non mappato | — | aperto |
| DF-16 | bassa | `region` EURODIS è testo libero, `provincia` ICD è una sigla di 2 lettere | `region` → `provincia` | Da definire | PA-22 | aperto |
| DF-17 | bassa | Nello swagger la descrizione di `descriptionOfGoods` parla di "camion di trasporto, es. per la Svizzera", non della merce: errore di documentazione EURODIS? | `customsService.descriptionOfGoods` → `descrizione_contenuto`, `internazionale.descrizione` | Diretto | — | aperto |
| DF-18 | bassa | `europlateBarcode` vale `0` nel neighbourhood business: in quel caso `id_ldv_itz` resta vuoto? | `collis[].europlateBarcode` → `internazionale.id_ldv_itz` | Diretto | PA-11 | aperto |
| DF-19 | alta | Abbiamo deciso di non troncare (PA-16), ma BEP ha limiti suoi: città 30, nome 35, indirizzo 40, civico 4, telefono 15 cifre. Chi adegua i valori più lunghi prima di BEP, o BEP li rifiuta? | indirizzi e contatti → `mittente.*`, `destinatario.*` | Valori interi | PA-16 | aperto |
| DF-20 | media | Per le spedizioni internazionali BEP vuole obbligatoriamente `receiverType` (da `internazionale.b2b_b2c`) e gli articoli completi (posizione, TARIC, valore, quantità, peso, paese di origine). EURODIS non dà B2B/B2C né quantità, peso e paese di origine dell'articolo. Una spedizione AT → IT è "internazionale" per BEP? | → `internazionale.b2b_b2c`, `collo.articolo[]` | Solo TARIC, valore, valuta e descrizione | PA-13 | aperto |

## Impatti dal mapping TracciatoUnico → BEP

Fonte: `mapping-tracciatoDTO-bep.md` (cartella EURODIS su SharePoint), che
descrive come il tracciato unico viene trasformato nella richiesta LDV verso
BEP. Hanno cambiato gravità DF-07, DF-08, DF-11 e DF-12, DF-04 ha un indizio
forte, e sono nati DF-19 e DF-20. In sintesi, per BEP:

- sono obbligatori `canale`, `codice_contratto`, `centro_costo`, `progressivo`,
  `data_spedizione`, `codice_prodotto`, `codici_servizi` e, per ogni collo,
  peso (grammi) e dimensioni (cm);
- contrassegno, assicurazione e consegna **non** vengono letti dalle loro
  sezioni: i servizi passano solo da `codici_servizi`;
- `collo.id_ldv` arriva a BEP solo per il canale INVIOSYSTEM;
- `progressivo` è obbligatorio (`fileRecordOrder`): nel mapping EURODIS oggi è
  N/A e va rivisto (una riga per spedizione nel batch?).

## Commenti di Diego del 23-10 e come sono stati recepiti

I commenti sono nella colonna "Commenti" del foglio "Mapping inverso EURODIS"
e restano lì a ogni rigenerazione.

| Campo EURODIS | Commento | Recepito |
|---|---|---|
| `shipmentTypeIndicator`, `lineHaulIndicator` | Da ignorare | Non mappati; tolti anche da `verso` e dagli input di ce-rules |
| `clearanceTimestamp` | Da ignorare | Non mappato (anche `data_ordine`) |
| `entranceTimestamp` | Va in data e ora spedizione | `data_spedizione`, `ora_spedizione` → DF-01 |
| `truckLicensePlate`, `termsOfDeliveryText`, `gatewayAssigned` | Da non mappare | Non mappati (tolti anche `codice_servizio_pagamento` e `addebito_oneri`) |
| `consigneeAddress.contactSMS` | Tutto su cellulare | `prefisso_cellulare` non più valorizzato |
| `consigneeAddress.pudoID` | Non mappare, punto aperto di gravità bassa | DF-14 |
| `alternativeContactTelephone` | Segnalare che manca il secondo numero | DF-15 |
| `shipperAddress.countryCode` | ISO2: solo in `codice_nazione_iso_2` | Tolto da codice/descrizione nazione, nazionalità e `importi`; stessa regola per il destinatario → DF-12 |
| `shipperAddress.countryCode` → `tipo_spedizione` | Sbagliato | Tolto |
| `additionalConsigneeInfo` | Note anche in consegna | `consegna.note` = concatenazione destinatario + mittente |
| `deliveryService.deliveryService` | Prodotto e servizio sono interni, ce-rules con `id_ldv`; codici servizi punto aperto | Tutti i campi CE-RULES hanno come ingresso `id_ldv` → DF-05 |
| `deliveryService.deliveryType` | S/N → no firma | `cliente.no_firma`: S → `"N"`, N → `"S"`, altri valori vuoto |
| `deliveryDateWindowStart` | Chiedere se c'è un servizio dedicato | DF-06 |
| `cashOnDeliveryService` | C'è la sezione contrassegno; aperto il codice accessorio | DF-07 |
| `commercialValueOfGoods` | C'è anche la sezione assicurata | `assicurata.importo_assicurata` → DF-08 |
| `smsPreAdvice`, `eMailPreAdvice` | Tracciare come sono stati mappati | DF-09 |
| `referencedEuroplateBarcode` | Dovrebbe essere `id_ldv_associata` | Mappato → DF-10 |

## Aggiornamento del 29-10: servizi accessori nel formato PDB (proposta)

Fonti: riscontro SDA/Chiapponi del 11-09 (flusso via file: ipotesi per l'API),
`FlussiPreadvisingInfo.csv` e `ce-dichiarato-ldv-pdb-sync`. Il dettaglio è in
[accessori-eurodis-pdb-proposta.md](accessori-eurodis-pdb-proposta.md). La
colonna "Stato" della tabella sopra non è stata toccata: qui sotto cosa cambia.

| DF | Proposta | Esito |
|---|---|---|
| DF-01 | Conflitto: il riscontro SDA mappa `clearanceTimestamp` → `shipmentDate`, noi usiamo `entranceTimestamp` | da confermare |
| DF-05 | Servizi confermati da SDA: `6`, `E`, `F`, `M`, `B`, `Z`; lacune `D`, `W`, `7`, `T` | in parte chiuso → DF-21 |
| DF-06 | `T` non ha APT: nessun servizio per la data di consegna | aperto → DF-21 |
| DF-07 | Contrassegno in perimetro: `APT000918`, `amount`, `3`→`CON`, `5`→`ABM`; non ammesso con Punto Poste | da confermare → DF-24 |
| DF-08 | Assicurazione fuori perimetro: non valorizzare `assicurata` | chiuso (proposta) |
| DF-09 | Pre-avviso non mappato dal riscontro SDA | da rivedere |
| DF-10 | Reso = rientro al mittente; tipo P via FTP; C, X, A come normali | in parte chiuso → DF-25 |
| DF-11 | Fallback in config del ms sync per prodotto (`APT000901`), contratto e centro di costo | ridimensionato |
| DF-12 | Destinatario `ITA1`; il ms sync non risolve ISO4 | aperto → DF-27 |
| DF-13, DF-20 | Prodotto unico trattato come nazionale: campi internazionali BEP non richiesti; dogana e ADR da confermare | ridimensionato |
| DF-14 | PUDO in perimetro, solo Punto Poste | chiuso (proposta) → DF-23 |
| DF-19 | Il ms sync non tronca | aperto → DF-26 |

### Nuovi dubbi

| ID | Gravità | Dubbio | Chi |
|---|---|---|---|
| DF-21 | media | Valori `deliveryService` non coperti (`D`, `7`, `T`): servizio, scarto o normale? `W` risulta APP nella matrice di test, da confermare | Chiapponi / EURODIS |
| DF-22 | media | Valori fuori perimetro che arrivano dall'API (`A`, Locker, assicurazione, tipo P): scarto o ignorati? | Chiapponi / EURODIS |
| DF-23 | alta | Nome del Punto Poste (`name` di `APT000947`, obbligatorio): nel flusso via file è in `RT_30_030`, opzionale e non garantito. Cosa si fa se manca? | Chiapponi / EURODIS |
| DF-24 | media | Contrassegno: formato e valuta dell'importo, `3`→`CON`, `5`→`ABM` | Chiapponi / EURODIS |
| DF-25 | media | Reso: serve `APT000930`? Valore di `return` e semantica di `R` e `A` | SDA |
| DF-26 | alta | Peso e dimensioni a 0 (default 1/1/1) e troncamento: chi li applica. Nel flusso file li fa il validatore (VR-30, VR-31): verificare se la nostra catena ci passa | Diego / responsabile ms sync |
| DF-27 | alta | ISO4 non risolto e canale `POU` / `WEBSERVICE` nel ms sync | responsabile ms sync |
| DF-29 | alta | LDV generata da EURODIS: regole di validità secondo SDA e univocità; ogni ripetizione dei test richiede LDV nuove; indirizzi, CAP e nazioni reali. Chiesto con la mail del 29-10 | Chiapponi / EURODIS |
| DF-28 | media | Scarto: l'unica causa confermata è il nome mittente assente. Vale per l'API? Come si traccia? | Diego |
