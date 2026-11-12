# Codici status SDA → EURODIS (IN-BOUND)

Trascrizione del foglio **"Decodifica Eurodis IN-BOUND"** di `Elenco codici status.xlsx` (stessa cartella), righe 3-78. Gli altri fogli ("Decodifica Eurodis OUT-BOUND", "Status Fedex") sono fuori perimetro e non sono riportati.

Fonte di verità resta l'Excel: se cambia, rigenerare questo file. Decisione d'uso: Diego, 10-11 (PA-34); regole di traduzione TR-01..TR-04 in [`sviluppo/ce-eurodis-send-tracking.md`](../../sviluppo/ce-eurodis-send-tracking.md), sezione 3.4.

## Come leggere la tabella

- **Direzione**: da SDA verso EURODIS. La chiave è lo **status SDA**; il valore è il **codice evento EURODIS**.
- **76 status SDA**, ognuno compare **una sola volta**; vanno su **24 codici EURODIS**. Più status SDA possono dare lo stesso codice EURODIS: la traduzione inversa (EURODIS → SDA) non è univoca e non va fatta.
- **Status SDA**: stringa di 3 caratteri alfanumerici, maiuscoli. Gli zeri iniziali sono significativi (`000`, `003`, `083` sono stringhe, non numeri). Confronto esatto, senza spazi.
- **Codice EURODIS**: 4 cifre, codice evento a livello di **collo** (parcel), da inviare con le API eventi parcel di EURODIS (A03.2).
- Le **descrizioni** sono informative. Quelle EURODIS hanno piccole differenze di testo per lo stesso codice (es. `1200`, `1306`): conta il codice.
- Status SDA **non presente** in tabella: comportamento in TR-03 (default proposto: non si invia, warning e metrica).

Pulizia rispetto all'Excel: rimossi spazi non separabili e spazi in coda nelle descrizioni (`CNP`, `ARP`, `013`, `ZNR`); `CAL` "Calamit?" nel file sorgente (carattere corrotto) reso come "Calamità". Nessun codice modificato.

## Tabella di traduzione

Ordine e contenuto del foglio. La colonna "Riga" è la riga dell'Excel, per tracciabilità.

| Riga | Status SDA | Descrizione SDA | Codice EURODIS | Descrizione EURODIS |
|---:|---|---|---|---|
| 3 | `000` | OK | `1100` | The item was delivered completely and accepted by the consignee |
| 4 | `CP0` | CONSEGNATA AL PUNTOPOSTE | `1100` | The item was delivered completely and accepted by the consignee |
| 5 | `CNP` | CONSEGNATA DA UFI AL CLIENTE | `1100` | The item was delivered completely and accepted by the consignee |
| 6 | `083` | CONSEGNATA A KIPOINT | `1100` | The item was delivered completely and accepted by the consignee |
| 7 | `085` | CONSEGNATA UFFICIO POSTALE | `1100` | The item was delivered completely and accepted by the consignee |
| 8 | `009` | Danneggiata | `1105` | Damaged |
| 9 | `018` | Manomessa | `1105` | Damaged |
| 10 | `FTO` | Furto | `1106` | Item Lost |
| 11 | `FTV` | Furto Vettore | `1106` | Item Lost |
| 12 | `SMA` | Smarrimento | `1106` | Item Lost |
| 13 | `SMV` | Smarrimento Vettore | `1106` | Item Lost |
| 14 | `021` | Chiusura Settimanale | `1200` | Special Delivery times - booking in - appointments |
| 15 | `029` | Consegne Particolari | `1200` | Special delivery times - booking in - appointments |
| 16 | `APC` | Appuntamento concordato | `1200` | Special delivery times - booking in - appointments |
| 17 | `APP` | Appuntamento da concordare | `1200` | Special delivery times - booking in - appointments |
| 18 | `CON` | Consegna Concordata | `1200` | Special delivery times - booking in - appointments |
| 19 | `EDO` | Entrata in dogana | `1201` | The item was taken out of the transportation flow, custom clearance process started |
| 20 | `AGT` | Arrivo al Gateway. In attesa di lavorazione | `1203` | Customs clearance documents missing or wrong |
| 21 | `007` | Rifiutata | `1300` | Delivery of the item was refused by the consignee without any reason |
| 22 | `008` | Destinatario Assente | `1304` | First delivery attempt, notification card was left |
| 23 | `010` | Festa Patronale | `1305` | Consignee was closed - holiday |
| 24 | `042` | Ferie fino al | `1305` | Consignee was closed - holiday |
| 25 | `013` | INCOMPLETA PER MANCANZA/DANNEGGIAMENTO | `1306` | Delivery problem |
| 26 | `023` | Fuori Standard | `1306` | Delivery problems caused by customer (i.e. local bank holidays) |
| 27 | `024` | Ispezione Postale | `1306` | Delivery problems caused by customer (i.e. local bank holidays) |
| 28 | `041` | Zona non servita | `1306` | Delivery problems caused by customer (i.e. local bank holidays) |
| 29 | `003` | Indirizzo Errato/Incompleto | `1307` | The address of the consignee is incorrect or incomplete |
| 30 | `017` | FDP Concordato | `1308` | The consignee will pick up the item at the delivery depot himself |
| 31 | `FDB` | Fermo Deposito Punto Blu | `1308` | The consignee will pick up the item at the delivery depot himself |
| 32 | `FDP` | Fermo Deposito Concordato | `1308` | The consignee will pick up the item at the delivery depot himself |
| 33 | `SFP` | Servizio Fermo Deposito | `1308` | The consignee will pick up the item at the delivery depot himself |
| 34 | `ARP` | ARRIVATA UFI | `1308` | The consignee will pick up the item at the delivery depot himself |
| 35 | `AFK` | LA SPEDIZIONE E' IN FERMO DEPOSITO PRESSO KIPOINT | `1308` | The consignee will pick up the item at the delivery depot himself |
| 36 | `006` | Mancanza B.A.M. | `1309` | The delivery documents are missing or wrong |
| 37 | `027` | Mancato Pagamento | `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete |
| 38 | `093` | Mancato importo contrassegno | `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete |
| 39 | `095` | Importo contrassegno non leggibile | `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete |
| 40 | `096` | Importo contrassegno discordante | `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete |
| 41 | `098` | Mittente contrassegno non leggibile | `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete |
| 42 | `001` | Mancanza di tempo | `1402` | Delivery problems caused by the haulier (i.e vehicle breakdown) |
| 43 | `012` | Smistamento Errato | `1406` | No delivery - the item was misrouted or missorted |
| 44 | `DID` | Disguido colpa SDA | `1406` | No delivery - the item was misrouted or missorted |
| 45 | `DIL` | Disguido | `1406` | No delivery - the item was misrouted or missorted |
| 46 | `DIS` | Disguido | `1406` | No delivery - the item was misrouted or missorted |
| 47 | `015` | Sciopero | `1408` | Force Majeure |
| 48 | `053` | Causa forza maggiore hub | `1408` | Force Majeure |
| 49 | `084` | Causa forza maggiore | `1408` | Force Majeure |
| 50 | `CAL` | Calamità Naturale | `1408` | Force Majeure |
| 51 | `RAL` | Rallentamenti sindacali | `1408` | Force Majeure |
| 52 | `SIN` | Agitazione Sindacale | `1408` | Force Majeure |
| 53 | `DNR` | Destinatario chiuso causa ordinanza Covid-19 | `1408` | Force Majeure |
| 54 | `ZNR` | Zona non raggiungibile per ordinanza Covid-19 | `1408` | Force Majeure |
| 55 | `090` | Spedizione abbandonata | `1416` | Disposal of goods |
| 56 | `SML` | Smaltita | `1416` | Disposal of goods |
| 57 | `RRR` | Ritorno al mittente | `1600` | Return Item |
| 58 | `STA` | L/V Stampata | `1740` | Inbound Gateway Scan |
| 59 | `PPP` | Partita | `1750` | Delivery Partner Scan |
| 60 | `ARR` | Arrivata in filiale | `1766` | Delivery depot arrival |
| 61 | `GGG` | In consegna al mattino | `1767` | Out for delivery |
| 62 | `POM` | In consegna al pomeriggio | `1767` | Out for delivery |
| 63 | `019` | Ritardo Linea | `1785` | On Hold |
| 64 | `022` | Non uscita | `1785` | On Hold |
| 65 | `035` | Giacenza Problemi linee | `1785` | On Hold |
| 66 | `036` | Giacenza Problemi hub | `1785` | On Hold |
| 67 | `037` | Giacenza Problemi impianto | `1785` | On Hold |
| 68 | `038` | Ritardo linee (partenza) | `1785` | On Hold |
| 69 | `044` | Giacenza esubero spedizioni | `1785` | On Hold |
| 70 | `ANG` | Arrivata non messa a giro | `1785` | On Hold |
| 71 | `ATC` | Attesa partenza colpa Cliente | `1785` | On Hold |
| 72 | `ATP` | Attesa In Partenza | `1785` | On Hold |
| 73 | `GIA` | Giacenza | `1785` | On Hold |
| 74 | `ING` | Entrata in giacenza | `1785` | On Hold |
| 75 | `NGG` | Consegna al mattino annullata | `1785` | On Hold |
| 76 | `NPO` | Consegna al pomeriggio annullata | `1785` | On Hold |
| 77 | `RUS` | Status Precedente | `1785` | On Hold |
| 78 | `UDO` | Uscita: Mag. Temp. Custodia | `1785` | On Hold |

## Riepilogo per codice EURODIS

Vista inversa, solo di consultazione (in ordine di codice).

| Codice EURODIS | Descrizione EURODIS | Status SDA |
|---|---|---|
| `1100` | The item was delivered completely and accepted by the consignee | `000`, `CP0`, `CNP`, `083`, `085` |
| `1105` | Damaged | `009`, `018` |
| `1106` | Item Lost | `FTO`, `FTV`, `SMA`, `SMV` |
| `1200` | Special Delivery times - booking in - appointments | `021`, `029`, `APC`, `APP`, `CON` |
| `1201` | The item was taken out of the transportation flow, custom clearance process started | `EDO` |
| `1203` | Customs clearance documents missing or wrong | `AGT` |
| `1300` | Delivery of the item was refused by the consignee without any reason | `007` |
| `1304` | First delivery attempt, notification card was left | `008` |
| `1305` | Consignee was closed - holiday | `010`, `042` |
| `1306` | Delivery problem | `013`, `023`, `024`, `041` |
| `1307` | The address of the consignee is incorrect or incomplete | `003` |
| `1308` | The consignee will pick up the item at the delivery depot himself | `017`, `FDB`, `FDP`, `SFP`, `ARP`, `AFK` |
| `1309` | The delivery documents are missing or wrong | `006` |
| `1310` | The payment information:terms of delivery, COD amounts are wrong or incomplete | `027`, `093`, `095`, `096`, `098` |
| `1402` | Delivery problems caused by the haulier (i.e vehicle breakdown) | `001` |
| `1406` | No delivery - the item was misrouted or missorted | `012`, `DID`, `DIL`, `DIS` |
| `1408` | Force Majeure | `015`, `053`, `084`, `CAL`, `RAL`, `SIN`, `DNR`, `ZNR` |
| `1416` | Disposal of goods | `090`, `SML` |
| `1600` | Return Item | `RRR` |
| `1740` | Inbound Gateway Scan | `STA` |
| `1750` | Delivery Partner Scan | `PPP` |
| `1766` | Delivery depot arrival | `ARR` |
| `1767` | Out for delivery | `GGG`, `POM` |
| `1785` | On Hold | `019`, `022`, `035`, `036`, `037`, `038`, `044`, `ANG`, `ATC`, `ATP`, `GIA`, `ING`, `NGG`, `NPO`, `RUS`, `UDO` |
