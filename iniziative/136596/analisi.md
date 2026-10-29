# 136596 — Eurodis autoproduttore · Analisi

**Aggiornata**: 2026-10-29 · **Analista**: Mary · **Stato**: bozza, in raccolta

## Esigenza

EURODIS è un consorzio di corrieri europei. SDA deve prendere in carico le
spedizioni che EURODIS le affida, ricevendone i dati (PAN) dalla piattaforma
EURODIS invece che dal dichiarato tradizionale: EURODIS è l'"autoproduttore"
del dato di spedizione.

## Flusso atteso: due microservizi

**1. `ce-dichiarato-eurodis-in`**: presa in carico delle spedizioni (nei punti
aperti si chiama "ms collection").

```
batch schedulato
  -> GET testapi.eurodis.com/receive-pan/shipments/v1   (X-API-Key)
  -> persistenza storico (decisione PA-02)
  -> conversione nel tracciato unico ICD v11 (+ ce-rules per prodotto/servizi, PA-03)
  -> pubblicazione su Kafka preadvising.pre-enrichment
```

**2. `ce-eurodis-send-tracking`**: recupera le tracce SDA delle spedizioni
EURODIS e le invia a EURODIS (nei punti aperti si chiama "ms tracking", PA-07).
**È un task a parte** (decisione del 22-Oct) e non rientra in questa analisi,
che copre solo `ce-dichiarato-eurodis-in`.

## Mapping verso l'ICD (PA-04)

Il file di riferimento è `ICD_PREADVISING_LDV_EVENT_SOURCE_v11.xlsx`, in questa
cartella. Il foglio originale "Tracciato unico preadvising" non viene toccato.
Fogli aggiunti:

- **Mapping EURODIS**: una riga per ogni campo ICD, con categoria, sorgente
  EURODIS, regola e punto aperto.
- **Mapping inverso EURODIS**: una riga per ogni campo EURODIS e per ognuna
  delle sue destinazioni ICD, compresi i campi senza destinazione (NON MAPPATO).
- **EURODIS non mappati**: campi EURODIS che non hanno una destinazione nell'ICD.
- **Legenda mapping**: significato delle categorie.

Per rigenerarlo: `python genera_mapping_eurodis.py`. Le regole sono nel
dizionario `R`; i default per famiglia di campi sono in `default()`.

Quadro al 2026-10-29 (553 campi foglia; include la proposta sui servizi
accessori, [accessori-eurodis-pdb-proposta.md](accessori-eurodis-pdb-proposta.md)):

| Categoria | Campi |
|---|---|
| DIRETTO / TRASFORMATO | 40 / 20 |
| COSTANTE / GENERATO | 6 / 7 |
| F1 (cliente) / CE-RULES | 4 / 9 |
| A VALLE (normalizzazione e arricchimento) | 230 |
| N/A (ritiro, pickup, altri vettori) | 94 |
| NON VALORIZZATO | 127 |
| **DA DEFINIRE** | **16** |

### Servizi accessori: dal formato EURODIS al formato PDB (proposta del 29-Oct)

La catena è: API `receive-pan` → **nostro mapping verso l'ICD** → ms esistente
`ce-dichiarato-ldv-pdb-sync` → PDB `waybillCreate` (sincrono). Il ms sync legge
i codici APT da `codici_servizi` (separati da pipe) e le sottochiavi dai campi
ICD (contrassegno, consegna, ecc.), come il ms asincrono della PDB Fase 2. Per
ogni accessorio EURODIS il nostro mapping scrive quindi gli stessi valori che il
builder PDB scriverebbe da un JSON con `APTxxxxxx`: specifica in
`FlussiPreadvisingInfo.csv`, perimetro nel riscontro SDA/Chiapponi del 11-set
(flusso via file: ipotesi per l'API). Dettaglio, osservazioni sul ms sync e
nuovi dubbi (DF-21…DF-28) nel file di proposta.

### Modello di riferimento: il flusso esistente EUD_INVIOFILE

`esempio-eud-inviofile.json` è un tracciato unico reale (con dati di test)
del flusso EURODIS già in esercizio, in cui la LDV la produce SDA (canale
`EUD_INVIOFILE`). Il flusso autoproduttore deve differire di poco: la
differenza principale è che la LDV arriva già da EURODIS. Il mapping è stato
allineato all'esempio:

- `cliente`: si valorizzano solo codice login, id cliente e codice AUC (tutti
  uguali al codice cliente EURODIS) e il contratto SFA, che vengono da F1.
  La ragione sociale del cliente coincide con quella del mittente. Tutto il
  resto è vuoto.
- `codice_nazione` contiene l'ISO2 (`"AT"`, `"IT"`), anche se l'ICD dice ISO3.
- `data_spedizione` è nel formato `yyyy-MM-dd`.
- `collo.peso` è espresso in grammi.
- `id_file` e `id_preadvising` sono UUID, già oggi oltre i 15 caratteri dell'ICD.
- I campi assenti sono stringhe vuote `""`, gli importi assenti sono `0`.

Differenze dall'ICD da segnalare: nell'esempio `codici_servizi` sta alla radice
(nell'ICD è in `spedizione`) e il cliente usa `cod_fiscale` (nell'ICD
`codice_fiscale`).

Due conferme dall'ICD stesso: il canale `"EURODIS"` è già fra i valori ammessi,
e `internazionale.id_ldv_itz` è descritto come "previsto per i casi ERS e
Eurodis". È il candidato naturale per la LDV (PA-11).

## Note per lo sviluppo

Decisioni da girare agli sviluppatori di `ce-dichiarato-eurodis-in`:

1. **`id_preadvising`** si valorizza con `UUID.randomUUID().toString()`.
   L'ICD v11 dichiara per questo campo una dimensione di 15 caratteri, mentre
   un UUID ne ha 36: la validazione a valle va adeguata, altrimenti scarta.
2. **Nessun troncamento.** I campi EURODIS più lunghi del limite ICD (email,
   SMS, civico, nome contatto, note, codice TARIC) si passano interi. Se la
   validazione a valle li rifiuta, si cambia la validazione (PA-16).
3. **LDV** (PA-11): `collo.id_ldv` ← `collis[].consignorsColloBarcode`;
   `internazionale.id_ldv_itz` ← `collis[].europlateBarcode`;
   `spedizione.rif_spedizione` ← `edReference` (numero → stringa senza decimali).
4. **Convenzioni del flusso EUD_INVIOFILE** da replicare: `""` per le
   stringhe assenti e `0` per gli importi, peso del collo in grammi,
   `codice_nazione` in ISO2, date nel formato `yyyy-MM-dd`.

## Cosa dice l'API (fonte: swagger Release v1, letto il 2026-10-22)

Fonte: `https://testapi.eurodis.com/receive-pan/swagger/Release%20v1/swagger.json`
(ambiente TEST). Copia salvata in `eurodis-receive-pan-swagger-v1.json`: da lì
vengono le descrizioni dei campi (in originale e in italiano) del foglio
"Mapping inverso EURODIS". Autenticazione con `X-API-Key` assegnata al partner.

| Endpoint | Uso | Note |
|---|---|---|
| `GET /shipments/v1` | scarico batch | Restituisce **solo le spedizioni non ancora consegnate al partner**. Nessun endpoint di conferma (ack). `404` = nessuna spedizione nuova, **non è un errore**. |
| `GET /shipment/{edReference}/v1` | rilettura puntuale | Rilegge una spedizione se se ne conosce l'`edReference`. |

Codici di errore: `401` chiave non valida, `424` partner non determinabile,
`451` partner senza accesso alla spedizione, `500` errore generico.

### Dati principali di una spedizione (`GetShipmentResponse2`)

- **Identificativi**: `edReference` (numero EURODIS, obbligatorio),
  `dispatchPartnersDomesticShipmentNumber` (numero del partner mittente,
  obbligatorio, max 35), `consignorsReference`, `referencedEurodisShipmentNumber`
  (resi/rettifiche).
- **Tipo**: `shipmentTypeIndicator` (N/A/P/R/X/B/D/E/C/Y/L/M/W),
  `lineHaulIndicator` (N/D/L), `termsOfDeliveryText` (Incoterms).
- **Quantità**: `numberOfHandlingUnits`, `shipmentWeight`, array `collis` con
  dimensioni, peso, tipo (P/C) e barcode (`europlateBarcode`,
  `consignorsColloBarcode`).
- **Indirizzi**: `consigneeAddress` (con `pudoID` per consegna in punto di
  ritiro), `shipperAddress`, `returnAddress`, `remunerationAddress`,
  `bookingInAddress`. Contatti: telefono, SMS (`+XX…`), email.
- **Preavviso**: `consigneePreAdvice` obbligatorio, con flag `smsPreAdvice`,
  `eMailPreAdvice`, `telephonePreAdvice` (ognuno richiede il contatto relativo).
- **Servizi**: `deliveryService` (servizio, tipo, finestre data/ora, consegna
  completa, prenotazione), `cashOnDeliveryService` (contrassegno: importo,
  valuta, IBAN, contanti/assegno), `customsService` (dogana),
  `hazardousADRServices` / `hazardousCollis` (merci pericolose ADR).

Altre API EURODIS disponibili: send-pan, PUDO, send-tracking,
receive-tracking, send-pod, receive-pod, get-label, pickup, receive-clearing.

## Evidenze che pesano sui punti aperti

1. **Lettura "consumante" senza ack (PA-05, PA-06, PA-09).** Da come è
   descritto `/shipments/v1`, EURODIS considera consegnata una spedizione nel
   momento in cui la restituisce. Se il servizio va in errore dopo la risposta
   e prima di salvare, quelle spedizioni non tornano più nel batch
   successivo. Si possono recuperare solo una per una con `edReference`, che
   però non si conosce. Va confermato con EURODIS. Se è così, la regola è
   **salvare la risposta grezza prima di qualsiasi trasformazione**. La
   decisione PA-02 (servizio con stato) va già in questa direzione.
2. **Repliche (PA-01).** Con più istanze schedulate, due chiamate
   contemporanee si dividerebbero le spedizioni, senza duplicarle. Il rischio
   vero è il punto 1 moltiplicato per il numero di istanze: il batch dovrebbe
   girare su **una sola istanza attiva**. Questa è una mia proposta, da
   portare alla call con Tagliente.
3. **Prima chiamata (PA-06).** Lo swagger non dice se la prima chiamata
   restituisce tutto lo storico arretrato o solo da una certa data in poi.
4. **Errori verso EURODIS (PA-08).** `receive-pan` non ha un canale per
   rifiutare una spedizione. Ipotesi da verificare: l'esito passa da
   `send-tracking` (evento di eccezione).
5. **Tracking (PA-07).** Visto dal nostro lato, "Send Tracking data to
   EURODIS" sembra essere l'API con cui SDA restituisce gli eventi. Lo stesso
   vale per `send-pod` con le prove di consegna. Anche questa è un'ipotesi.
6. **Mapping (PA-03, PA-04).** I campi che plausibilmente servono a ce-rules
   per ricavare prodotto e servizi accessori sono `shipmentTypeIndicator`,
   `deliveryService`, `deliveryType`, `cashOnDeliveryService`,
   `customsService`, ADR e `pudoID`.

## Registro punti aperti

I **dubbi funzionali** sul mapping (DF-nn) sono raccolti a parte in
[punti-aperti-analisi-2026-10-23.md](punti-aperti-analisi-2026-10-23.md).

Owner RTI = chi lo porta avanti lato fornitore; Rif. Poste = referente lato cliente.

| ID | Data | Tema | Owner RTI | Rif. Poste | Azione / decisione | Stato | Note |
|---|---|---|---|---|---|---|---|
| PA-01 | 22-Oct | ms collection — gestione repliche | — | Tagliente | Fissare una call per farsi consigliare | aperto | Proposta Mary: una sola istanza attiva (evidenza 2) |
| PA-02 | 22-Oct | ms collection — con stato o senza stato | — | — | Deciso: si salva lo storico | chiuso | |
| PA-03 | 22-Oct | Mapping prodotto / servizi accessori | — | — | Deciso il 22-Oct: ce-rules da `id_ldv`. **Rivisto il 29-Oct (proposta)**: i servizi si traducono nel nostro mapping in `codici_servizi` e nei campi delle sottochiavi, formato PDB; il prodotto ha fallback `APT000901` nel ms sync | da validare | Vedi accessori-eurodis-pdb-proposta.md, DF-05, DF-07, DF-21 |
| PA-04 | 22-Oct | Mapping dati EURODIS → DTO del dichiarato | Azzurra / Diego | — | Mapping fatto con LLM confrontando lo swagger EURODIS con l'ICD | in corso | Prima stesura il 22-Oct nel file ICD, foglio "Mapping EURODIS". Restano 15 campi DA DEFINIRE |
| PA-05 | 22-Oct | ms collection — come EURODIS gestisce lo stato delle spedizioni inviate | — | Chiapponi | | aperto | Evidenza 1. Chiesto a Chiapponi con mail del 26-Oct (dom. 1) |
| PA-06 | 22-Oct | ms collection — come EURODIS gestisce la prima chiamata | — | Chiapponi | | aperto | Evidenza 3. Chiesto a Chiapponi con mail del 26-Oct (dom. 2) |
| PA-07 | 22-Oct | ms tracking — quale API chiamare e con quali dati | — | Chiapponi | | aperto | Evidenza 5. Riguarda il task a parte `ce-eurodis-send-tracking`. Chiesto a Chiapponi con mail del 26-Oct (dom. 8) |
| PA-08 | — | Come si restituisce a EURODIS un errore (validazione o altro) | — | Chiapponi | | aperto | Evidenza 4. Chiesto a Chiapponi con mail del 26-Oct (dom. 7) |
| PA-09 | — | Errore tra la chiamata a receive-shipments e la persistenza | — | Chiapponi | | aperto | Evidenza 1. Chiesto a Chiapponi con mail del 26-Oct (dom. 1) |
| PA-10 | — | Reperire contratto / codice cliente / AUC | — | — | Deciso: si reperiscono da F1 | chiuso | |
| PA-11 | 22-Oct | Quale campo EURODIS diventa la LDV SDA? Una LDV per spedizione o per collo? | da assegnare | — | Deciso: `consignorsColloBarcode` → `collo.id_ldv`; `europlateBarcode` → `internazionale.id_ldv_itz`; `edReference` → `rif_spedizione` | aperto | Restano: (a) `id_ldv_itz` è un campo di spedizione e `europlateBarcode` uno per collo, con più colli quale si usa? (b) da dove arriva `collo.id_collo`; (c) madre/figlio nel multicollo |
| PA-12 | 22-Oct | Ambiente di produzione EURODIS e chiave API di produzione | da assegnare | Chiapponi | | aperto | Proposto da Mary; oggi c'è solo TEST. Chiesto a Chiapponi con mail del 26-Oct (dom. 9) |
| PA-13 | 22-Oct | Spedizioni con dogana e ADR: rientrano nel perimetro? | da assegnare | Chiapponi | | aperto | Proposto da Mary. Chiesto a Chiapponi con mail del 26-Oct (dom. 12) |
| PA-14 | 22-Oct | Frequenza del batch e volumi attesi | da assegnare | Chiapponi | | aperto | Proposto da Mary. Chiesto a Chiapponi con mail del 26-Oct (dom. 11) |
| PA-15 | 22-Oct | Identificativi di canale: `id_preadvising` (obbligatorio), `id_canale`, `id_file`, `id_partner` | da assegnare | — | Deciso per `id_preadvising`: `UUID.randomUUID().toString()` | aperto | Restano `id_canale`, `id_file`, `id_partner`. UUID 36 caratteri contro i 15 dell'ICD: vedi Note per lo sviluppo |
| PA-16 | 22-Oct | Lunghezze incompatibili (email 80→50, SMS 35→30, civico 40→5, nome contatto, note, TARIC) | — | — | Deciso: si passa il valore intero, non si tronca. Se serve si cambia la validazione | chiuso | |
| PA-17 | 22-Oct | Resi e rettifiche (`shipmentTypeIndicator` R, `referencedEurodis…`, `returnAddress`), `verso`, `consegna.modalita`, `mancata_consegna` | da assegnare | — | | aperto | Dal mapping |
| PA-18 | 22-Oct | Preavviso: semantica di `notifiche_sms` / `notifiche_email`; il preavviso telefonico EURODIS non ha un campo ICD | da assegnare | — | | aperto | Dal mapping. È il cuore del topic preadvising |
| PA-19 | 22-Oct | Contrassegno: codifica del tipo pagamento (3 contanti / 5 assegno); conto di accredito e valuta non hanno un campo ICD | da assegnare | — | | aperto | Dal mapping |
| PA-20 | 22-Oct | Consegna a punto di ritiro (`pudoID`): nessun campo ICD generico | da assegnare | — | | aperto | Dal mapping |
| PA-23 | 22-Oct | `rif_prodotto_cliente` (`APT000902`) e `centro_costo` (`CDC-00000014`) nell'esempio EUD_INVIOFILE: sono costanti di contratto (F1) o si derivano? | da assegnare | — | | aperto | Emerso dall'esempio; `rif_prodotto_cliente` potrebbe pesare su ce-rules |
| PA-22 | 22-Oct | Campi con semantica diversa, non di lunghezza: `region` EURODIS → `provincia` ICD; valore merce in valuta non EUR | da assegnare | — | | aperto | Separati da PA-16 |
| PA-24 | 22-Oct | Payload di esempio di produzione con dati reali (dati sensibili oscurati) | da assegnare | Chiapponi | | aperto | Serve a verificare DF-01, DF-02, DF-18. Chiesto a Chiapponi con mail del 26-Oct (dom. 10) |
| PA-25 | 22-Oct | Decidere il nome del canale che guida tutta l'elaborazione | da assegnare | — | | aperto | Vedi DF-04 (`EURODIS` o `EUD_INVIOSYSTEM`) e PA-15 |
| PA-26 | 26-Oct | ms ingestione: servono due livelli di ms? Uno consuma dall'API, salva in Mongo e produce su coda; l'altro consuma dalla coda e fa il mapping DTO | da assegnare | — | | aperto | Conseguenza di PA-02 (si salva lo storico); tocca PA-01 |
| PA-27 | 26-Oct | Comportamento API receive-pan: aggiornamenti e annullamenti, limiti di chiamata (paginazione, rate limit, timeout), durata della rilettura puntuale, fuso orario dei timestamp, rotazione della chiave API | da assegnare | Chiapponi | | aperto | Chiesto a Chiapponi con mail del 26-Oct (dom. 3, 4, 5, 6). Dalla mail è stata tolta la domanda sulle restrizioni di rete (whitelist IP) |
| PA-28 | 26-Oct | Roll out incrementale, no big bang: il controllo sul dato è lato API EURODIS, quindi si può partire con un sottoinsieme (per mittente/cliente, per ufficio o per volume) e allargare per gradi? Chi decide il perimetro di ogni fase: EURODIS (chiave API, filtro lato loro) o noi (filtro lato ms)? | da assegnare | Chiapponi | Chiesto a Chiapponi con mail di follow up del 26-Oct (dom. 13) | aperto | Lo swagger `receive-pan` non ha parametri di filtro: `GET /shipments/v1` restituisce tutte le nuove spedizioni del partner (chiave API) e le segna come consegnate, senza ack. Un filtro lato nostro scarterebbe spedizioni già "consegnate" da EURODIS: serve il filtro lato EURODIS, oppure si salvano tutte (PA-02) e si elabora solo il perimetro attivo. Tocca PA-05, PA-12, PA-13 |
| PA-29 | 29-Oct | Test integrati con EURODIS su `receive-pan` (ambiente TEST): scenari, dati di prova, referente, finestre | da assegnare | Chiapponi | Chiedere a EURODIS di proporre i propri scenari, con almeno un esempio ciascuno e le combinazioni; solo ingestione | in corso | Mail a Gianluca Chiapponi inviata il 29-Oct (scenari, LDV valide e univoche, dati reali, modalità operative). Referente e accessi: coordina Chiapponi, i dati di accesso li abbiamo già. Riferimento interno: test list INVIOFILE (52 scenari) e matrice di compatibilità nella cartella TEST LIST su SharePoint |
| PA-30 | 29-Oct | Osservazioni sul ms `ce-dichiarato-ldv-pdb-sync` (in test): canale `POU`/`WEBSERVICE`, ISO4 non risolto, default peso e dimensioni, troncamento, nome Punto Poste, contrassegno a 0 | da assegnare | — | Segnalare al responsabile del ms | aperto | Elenco S1…S7 nel file di proposta; DF-26, DF-27 |
