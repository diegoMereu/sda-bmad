# PACCHI.TRACKING in produzione: lettura completa di 24 ore (12-11)

Mary, 12-11. Analisi della lettura completa di `PACCHI.TRACKING` fatta da Paolo il 12-11 con
`tracking_sample.py` (cartella TOOLS/Kafka del team). Serve a **PA-35**: da dove arrivano le tracce
SDA per `ce-eurodis-send-tracking` (sezione 3.5 di
[`sviluppo/ce-eurodis-send-tracking.md`](sviluppo/ce-eurodis-send-tracking.md)).

Legenda: **[FATTO]** misurato sui dati; **[IPOTESI]** interpretazione non confermata da SDA;
**[DA DECIDERE]**; **[DA VERIFICARE]**. Il significato dei codici `applicativo`, `canale` e `status`
non è documentato: dove non c'è il foglio IN-BOUND non lo si deduce.

## In sintesi

1. **[FATTO] In produzione `PACCHI.TRACKING` porta gli status SDA del foglio IN-BOUND.** Arrivano
   con `header.applicativo = CE`: 9,85 milioni di eventi in 24 ore, 285 status distinti, **65 dei 76**
   status del foglio. Il 59,4% degli eventi `CE` ha uno status traducibile in un codice EURODIS.
2. **La conclusione del 10-11 va corretta.** Era stata ricavata in svil, dove il topic aveva 265
   messaggi della sola rete pacchi Poste. In produzione il topic è condiviso: ci sono `TT` e `CE`.
   `PACCHI.TRACKING` diventa il **primo candidato** per l'opzione A di PA-35.
3. **Gli stessi codici compaiono anche sotto altri applicativi.** 22 status del foglio si vedono anche
   con `TT`, `OMP`, `IPER` o `FS` (`000`, `GGG`, `ING`, `ARP`, `CNP`, `CP0`…). Per riconoscere una
   traccia SDA non basta lo status: servono `applicativo = CE` e l'LDV presente in `eurodis_ldv`.
4. **Il 40,6% degli eventi `CE` ha uno status fuori dal foglio** (220 status, 3.997.303 eventi). In
   testa c'è `THE`, con il 23,8% degli eventi `CE`. Con la regola TR-03 questi eventi non si inviano.
   È coerente con il foglio, ma va confermato che sia voluto.
5. **Per chiudere PA-35 mancano tre verifiche** (V-01..V-03):
   - che le LDV EURODIS (`deliveryPartnerBarcode`) compaiano davvero con `applicativo = CE`;
   - che ci sia il nome di chi ritira per il `1100`;
   - quale sia la chiave Kafka.

## Lettura

| Voce | Valore |
|---|---|
| Topic | `PACCHI.TRACKING`, 15 partizioni |
| Ambiente | **[IPOTESI forte]** produzione: è il bootstrap attivo nel `.env` dello script; quello di collaudo è commentato |
| Finestra | Ultime 24 ore, dal 2026-11-11 circa 10:07 al 2026-11-12 10:39. Offset di partenza da `offsets_for_times`, fine all'high watermark letto all'avvio |
| Eventi | 23.745.112, lettura completa e non campionata: in media circa 275 eventi/s su tutto il topic |
| Modalità | Sola lettura, `assign` manuale, nessun group e nessun commit |
| Campi letti | `header.applicativo`, `payload.canale`, `payload.status` (`<assente>` = campo non presente nel JSON) |
| Dati | [`dati/pacchi-tracking-prod-2026-11-12/`](dati/pacchi-tracking-prod-2026-11-12/), con `tracking_values.csv` (tutti i valori di ogni campo) e `tracking_combos.csv` (576 combinazioni (applicativo, canale, status) con conteggio, primo e ultimo `header.timestamp`, esempio topic/partition/offset). Contengono solo codici, conteggi e coordinate Kafka: nessun dato personale |

Forma dell'evento (esempio anonimizzato fornito con la lettura):

```json
{
  "header":  { "applicativo": "TT", "timestamp": "2026-11-09 15:00:38.663" },
  "payload": { "canale": "TT", "status": "000", "ldv": "...", "dataTrack": "2026-11-09 14:58:24",
               "faseLavorazione": "D", "arealavorazione": "TP", "tipologiaUfficioEvento": "UP",
               "idFrazionarioEvento": "...", "idFrazionarioMittente": "...", "idFrazionarioDestinazione": "...",
               "mazzetto": "...", "tipologiaMazzetto": "MP", "numTentativiDiConsegna": "1" }
}
```

## Distribuzioni [FATTO]

### `header.applicativo` (10 valori)

| Applicativo | Eventi | % | Status distinti | Status del foglio IN-BOUND | Eventi con status del foglio |
|---|---:|---:|---:|---:|---:|
| `TT` | 13.207.870 | 55,62 | 76 | 19 | 21,3% |
| `CE` | 9.846.227 | 41,47 | 285 | **65** | **59,4%** |
| `OMP` | 397.567 | 1,67 | 10 | 2 | 27,8% |
| `PDA` | 186.206 | 0,78 | 2 | 0 | 0% |
| `IPER` | 89.653 | 0,38 | 35 | 6 | 12,3% |
| `FS` | 11.823 | 0,05 | 4 | 2 | 33,0% |
| `SP1` | 5.510 | 0,02 | 2 | 0 | 0% |
| `SAPEM` | 175 | 0,00 | 2 | 0 | 0% |
| `MDP` | 47 | 0,00 | 1 | 0 | 0% |
| `RTZ` | 34 | 0,00 | 2 | 0 | 0% |

**[IPOTESI]** `CE` è il Corriere Espresso SDA e `TT` il Track & Trace della rete pacchi Poste. Lo
suggeriscono il nome e la copertura del foglio IN-BOUND, ma SDA non l'ha confermato.

### `payload.canale` (11 valori, compreso `<assente>`)

| Canale | Eventi | % |
|---|---:|---:|
| `TT` | 9.635.904 | 40,58 |
| `HUB` | 4.488.704 | 18,90 |
| `<assente>` | 3.100.676 | 13,06 |
| `PDT` | 2.270.942 | 9,56 |
| `DOL` | 2.150.766 | 9,06 |
| `RTZ` | 1.075.373 | 4,53 |
| `MAN` | 851.809 | 3,59 |
| `APT` | 147.173 | 0,62 |
| `FS` | 11.823 | 0,05 |
| `WEB` | 11.074 | 0,05 |
| `OMP` | 868 | 0,00 |

### Applicativo × canale

| Applicativo | Canali (eventi) |
|---|---|
| `TT` | `TT` 9.635.904, `<assente>` 2.337.478, `RTZ` 1.075.373, `APT` 147.173, `WEB` 11.074, `OMP` 868 |
| `CE` | `HUB` 4.488.704, `PDT` 2.270.942, `DOL` 1.964.560, `MAN` 851.809, `<assente>` 270.212 |
| `OMP` | `<assente>` 397.567 |
| `PDA` | `DOL` 186.206 |
| `IPER` | `<assente>` 89.653 |
| `FS` | `FS` 11.823 |
| `SP1`, `SAPEM`, `MDP`, `RTZ` | `<assente>` (5.510, 175, 47, 34) |

Per `CE` la quota di eventi con status del foglio cambia molto da un canale all'altro:

| Canale `CE` | Eventi | Con status del foglio | % |
|---|---:|---:|---:|
| `DOL` | 1.964.560 | 1.685.346 | 85,8 |
| `PDT` | 2.270.942 | 1.814.609 | 79,9 |
| `HUB` | 4.488.704 | 2.149.023 | 47,9 |
| `MAN` | 851.809 | 199.946 | 23,5 |
| `<assente>` | 270.212 | 0 | 0 |

- Su `HUB` l'unico status del foglio è `PPP` (2.149.023 eventi). Il resto di `HUB` è soprattutto
  `THE` (2.339.681).
- `CE` senza canale porta solo status fuori dal foglio: `FTE` 177.242, `ATR` 84.588, `RNT` 3.203,
  `CHI` 2.448, `RCC` 2.186, `IAR` 495, `RII` 50.
- Il canale non serve al filtro: send-tracking non deve dipendere dal canale.

### `payload.status`

328 valori distinti, elenco completo in `tracking_values.csv`. I primi 40:

PPP 11,40% · SCP 10,78% · GGG 10,62% · THE 10,08% · 000 7,43% · PCP 5,46% · ACP 5,07% · CT1 4,39% ·
NCP 4,20% · AMZ 3,40% · VUP 2,57% · FMG 2,02% · CMP 1,65% · RIT 1,59% · AUP 1,53% · MVS 1,48% ·
ING 1,38% · ARP 1,36% · FMZ 1,30% · CNP 1,26% · ANG 1,08% · CP0 1,05% · MAN 0,83% · FTE 0,75% ·
LST 0,64% · TET 0,58% · TVI 0,48% · HBN 0,38% · ATR 0,36% · SF2 0,35% · PAG 0,29% · 008 0,28% ·
HBS 0,27% · PPV 0,23% · PMZ 0,17% · GIU 0,15% · 003 0,14% · ARV 0,13% · RMZ 0,12% · POM 0,12%

Lunga coda: circa 200 status sotto lo 0,01%, molti con 1-10 occorrenze.

## Copertura del foglio IN-BOUND [FATTO]

Eventi nelle 24 ore per ogni status del foglio
([`documenti/eurodis/elenco-codici-status-inbound.md`](documenti/eurodis/elenco-codici-status-inbound.md))
e per applicativo. "-" significa mai visto.

| Status SDA | Descrizione SDA | Codice EURODIS | CE | TT | Altri applicativi |
|---|---|---|---:|---:|---|
| `000` | OK | `1100` | 847.500 | 912.779 | IPER 2.875 |
| `CP0` | CONSEGNATA AL PUNTOPOSTE | `1100` | 21.103 | 229.183 | - |
| `CNP` | CONSEGNATA DA UFI AL CLIENTE | `1100` | 6 | 245.321 | OMP 52.859 |
| `083` | CONSEGNATA A KIPOINT | `1100` | 2 | - | - |
| `085` | CONSEGNATA UFFICIO POSTALE | `1100` | 10.990 | - | - |
| `009` | Danneggiata | `1105` | 4.712 | 4.142 | - |
| `018` | Manomessa | `1105` | 415 | - | - |
| `FTO` | Furto | `1106` | 269 | - | FS 20 |
| `FTV` | Furto Vettore | `1106` | - | - | - |
| `SMA` | Smarrimento | `1106` | 159 | 2.013 | FS 3.878 |
| `SMV` | Smarrimento Vettore | `1106` | 60 | - | - |
| `021` | Chiusura Settimanale | `1200` | 2.400 | 2.270 | - |
| `029` | Consegne Particolari | `1200` | 13.174 | - | - |
| `APC` | Appuntamento concordato | `1200` | 152 | - | - |
| `APP` | Appuntamento da concordare | `1200` | 2.459 | - | - |
| `CON` | Consegna Concordata | `1200` | 34 | - | - |
| `EDO` | Entrata in dogana | `1201` | 11 | - | - |
| `AGT` | Arrivo al Gateway. In attesa di lavorazione | `1203` | - | - | - |
| `007` | Rifiutata | `1300` | 17.304 | 855 | - |
| `008` | Destinatario Assente | `1304` | 29.221 | 37.131 | - |
| `010` | Festa Patronale | `1305` | 610 | 23 | - |
| `042` | Ferie fino al | `1305` | 872 | 42 | - |
| `013` | INCOMPLETA PER MANCANZA/DANNEGGIAMENTO | `1306` | 7.985 | - | - |
| `023` | Fuori Standard | `1306` | 30 | - | - |
| `024` | Ispezione Postale | `1306` | 3 | - | - |
| `041` | Zona non servita | `1306` | 4.139 | - | - |
| `003` | Indirizzo Errato/Incompleto | `1307` | 27.111 | 5.815 | IPER 303 |
| `017` | FDP Concordato | `1308` | 3.994 | - | - |
| `FDB` | Fermo Deposito Punto Blu | `1308` | 38 | - | - |
| `FDP` | Fermo Deposito Concordato | `1308` | 8.187 | - | - |
| `SFP` | Servizio Fermo Deposito | `1308` | 14 | - | - |
| `ARP` | ARRIVATA UFI | `1308` | 190 | 265.126 | OMP 57.672, IPER 246 |
| `AFK` | LA SPEDIZIONE E' IN FERMO DEPOSITO PRESSO KIPOINT | `1308` | 17.783 | - | - |
| `006` | Mancanza B.A.M. | `1309` | 160 | - | - |
| `027` | Mancato Pagamento | `1310` | 7.087 | 8 | - |
| `093` | Mancato importo contrassegno | `1310` | 164 | - | - |
| `095` | Importo contrassegno non leggibile | `1310` | 3 | - | - |
| `096` | Importo contrassegno discordante | `1310` | 10 | - | - |
| `098` | Mittente contrassegno non leggibile | `1310` | - | - | - |
| `001` | Mancanza di tempo | `1402` | 1.130 | - | - |
| `012` | Smistamento Errato | `1406` | 312 | - | - |
| `DID` | Disguido colpa SDA | `1406` | - | - | - |
| `DIL` | Disguido | `1406` | 2.023 | 3.306 | - |
| `DIS` | Disguido | `1406` | 6.798 | 8.576 | - |
| `015` | Sciopero | `1408` | 17 | 12 | - |
| `053` | Causa forza maggiore hub | `1408` | - | - | - |
| `084` | Causa forza maggiore | `1408` | 1.218 | - | IPER 347 |
| `CAL` | Calamità Naturale | `1408` | 1 | - | - |
| `RAL` | Rallentamenti sindacali | `1408` | - | - | - |
| `SIN` | Agitazione Sindacale | `1408` | - | - | - |
| `DNR` | Destinatario chiuso causa ordinanza Covid-19 | `1408` | - | - | - |
| `ZNR` | Zona non raggiungibile per ordinanza Covid-19 | `1408` | 7 | - | - |
| `090` | Spedizione abbandonata | `1416` | 497 | - | - |
| `SML` | Smaltita | `1416` | 147 | - | - |
| `RRR` | Ritorno al mittente | `1600` | 15.253 | 4.344 | - |
| `STA` | L/V Stampata | `1740` | 14.234 | - | - |
| `PPP` | Partita | `1750` | 2.707.044 | - | - |
| `ARR` | Arrivata in filiale | `1766` | 8.783 | - | - |
| `GGG` | In consegna al mattino | `1767` | 1.739.973 | 777.467 | IPER 4.209 |
| `POM` | In consegna al pomeriggio | `1767` | 28.344 | - | - |
| `019` | Ritardo Linea | `1785` | 7.418 | - | - |
| `022` | Non uscita | `1785` | 4.553 | - | - |
| `035` | Giacenza Problemi linee | `1785` | 2 | - | - |
| `036` | Giacenza Problemi hub | `1785` | 174 | - | - |
| `037` | Giacenza Problemi impianto | `1785` | 1 | - | - |
| `038` | Ritardo linee (partenza) | `1785` | 130 | - | - |
| `044` | Giacenza esubero spedizioni | `1785` | 33 | - | - |
| `ANG` | Arrivata non messa a giro | `1785` | 255.358 | - | - |
| `ATC` | Attesa partenza colpa Cliente | `1785` | 628 | - | - |
| `ATP` | Attesa In Partenza | `1785` | 156 | - | - |
| `GIA` | Giacenza | `1785` | 9.996 | - | - |
| `ING` | Entrata in giacenza | `1785` | 13.699 | 313.398 | - |
| `NGG` | Consegna al mattino annullata | `1785` | - | - | - |
| `NPO` | Consegna al pomeriggio annullata | `1785` | - | - | - |
| `RUS` | Status Precedente | `1785` | - | - | - |
| `UDO` | Uscita: Mag. Temp. Custodia | `1785` | 2.644 | - | IPER 3.045 |

- **Visti con `CE`: 65 status.** 43 compaiono solo con `CE` (fra cui `PPP` 2.707.044, `ANG` 255.358,
  `POM`, `AFK`, `STA`, `ARR`, `FDP`). 22 compaiono anche con altri applicativi. Nessuno status del
  foglio compare fuori da `CE` senza comparire anche con `CE`.
- **Mai visti in 24 ore: 11 status** (`FTV`, `AGT`, `098`, `DID`, `053`, `RAL`, `SIN`, `DNR`, `NGG`,
  `NPO`, `RUS`). Sono eventi rari (furto del vettore, scioperi, Covid, annullamenti) e 24 ore non
  bastano per dire che non esistono: restano nella tabella di traduzione.
- **Codici prevalenti fuori da `CE`.** `CNP` (6 con `CE`, 245.321 con `TT`) e `ARP` (190 con `CE`,
  265.126 con `TT`) arrivano quasi solo da `TT`. **[IPOTESI]** Con `TT` lo stesso codice potrebbe avere
  un significato diverso da quello SDA. È un motivo in più per filtrare su `applicativo = CE`.

### Status `CE` fuori dal foglio (sopra lo 0,2% degli eventi `CE`)

| Status `CE` | Eventi | % su `CE` |
|---|---:|---:|
| `THE` | 2.342.017 | 23,79 |
| `CMP` | 392.372 | 3,98 |
| `RIT` | 191.437 | 1,94 |
| `FTE` | 177.242 | 1,80 |
| `TET` | 137.744 | 1,40 |
| `TVI` | 115.000 | 1,17 |
| `HBN` | 90.158 | 0,92 |
| `ATR` | 84.588 | 0,86 |
| `PAG` | 68.698 | 0,70 |
| `HBS` | 63.409 | 0,64 |
| `PPV` | 55.068 | 0,56 |
| `ARV` | 30.301 | 0,31 |
| `ANN` | 24.126 | 0,25 |
| `CGD` | 20.964 | 0,21 |

In tutto sono 220 status e 3.997.303 eventi, il 40,6% di `CE`. Il loro significato non è
documentato. Con TR-03 non si inviano a EURODIS. Se qualcuno di questi dovesse arrivare a EURODIS
(`THE`, per volume), il foglio va esteso da chi lo possiede (Diego/SDA).

## Qualità dei dati [FATTO]

| Osservazione | Dettaglio | Effetto su send-tracking |
|---|---|---|
| Status sospetti | `XXX` 992 (`CE`/`DOL`), `999` 5 (`TT`/`TT`), `?YY` 2 (`CE`/`MAN`, `CE`/`PDT`), `555` 1 (`SAPEM`) | Sono fuori dal foglio e quindi non si inviano (TR-03). `?YY` contiene un carattere non alfanumerico e TR-02 (confronto esatto) lo scarta |
| Canale assente | 3.100.676 eventi (13,06%); per `CE` sono 270.212, tutti con status fuori dal foglio | Nessuno, se il filtro non usa il canale |
| `header.timestamp` precedente alla finestra | 31 combinazioni: `IPER` (25), `FS` (3), `SP1` (2), `SAPEM` (1). Per `IPER`, `FS` e `SP1` il primo timestamp è circa un'ora prima dell'inizio della lettura; `SAPEM` ha un evento del 2026-10-26 07:07:59 | **[IPOTESI]** `IPER`, `FS` e `SP1` scrivono l'ora con un fuso diverso (UTC invece dell'ora locale); l'evento `SAPEM` è un ritardo o un reinvio. Su `CE` non succede. Per EURODIS fa fede `payload.dataTrack`, non `header.timestamp` (da verificare, V-04) |

## Conseguenze per PA-35 e per send-tracking

- **Opzione A su `PACCHI.TRACKING`** [proposta Mary, DA DECIDERE con Winston/Diego]. Consumer con
  group dedicato `ce-eurodis-send-tracking`. Per ogni evento, nell'ordine dal controllo più leggero:
  1. scarta se `header.applicativo != CE` (elimina il 58,5% del traffico);
  2. scarta se `payload.status` non è nel foglio (TR-03): elimina un altro 40,6% degli eventi `CE`;
  3. scarta se `payload.ldv` non è in `eurodis_ldv`;
  4. traduce, salva nello storico e invia.
- **Volumi**: circa 9,85 milioni di eventi `CE` al giorno; i picchi orari vanno misurati. I filtri 1 e 2
  si fanno in memoria. Il filtro 3 va fatto su una cache o con un lookup indicizzato, non con una query
  per ogni evento: dopo i filtri 1 e 2 restano circa 5,8 milioni di eventi al giorno.
- **Ordine degli eventi** [DA VERIFICARE, V-03]: la chiave Kafka non è stata letta. Se la chiave non è
  l'LDV, le tracce di uno stesso collo finiscono su partizioni diverse e possono arrivare in un ordine
  diverso da quello di `dataTrack`.

## Prossime verifiche (letture mirate, sempre in sola lettura)

| # | Verifica | Come |
|---|---|---|
| V-01 | Le LDV EURODIS arrivano con `applicativo = CE`? Con quali status? | Rilettura filtrata su alcune `deliveryPartnerBarcode` note, salvando solo status, applicativo, canale e `dataTrack` |
| V-02 | C'è il nome di chi ritira per lo status `000` (`1100`, `acceptorName`)? | Elenco dei nomi dei campi di `payload` per gli eventi `CE`/`000`, senza i valori |
| V-03 | Chiave Kafka e partizionamento | Rilettura che salva anche la chiave: c'è? è l'LDV? |
| V-04 | Formato e fuso orario di `dataTrack` per `CE` | Confronto fra `header.timestamp` e `dataTrack` su un campione `CE` |
| V-05 | `PACCHI.TRACKING` in collaudo ha traffico `CE`? | Stessa lettura su collaudo: serve per provare send-tracking prima della produzione |

## Domande per Diego/SDA

1. `applicativo = CE` è il Corriere Espresso SDA? Le tracce delle LDV PDB Express di EURODIS passano tutte da lì?
2. Possiamo consumare `PACCHI.TRACKING` di produzione con un group nostro (ACL, owner del topic)?
3. Gli status `CE` fuori dal foglio, a partire da `THE`, sono esclusi per scelta?
