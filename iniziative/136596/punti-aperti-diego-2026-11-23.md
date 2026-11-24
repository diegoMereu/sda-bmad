# 136596 — Eurodis autoproduttore · Punti aperti da vedere con Diego (lunedì 2026-11-23)

Emersi dai test integrati del 20-11 (esiti in `uat/mock-test/esiti-completed-2026-11-19.md`).
Distinguo ciò che è **verificato** (letto nei messaggi o nei log) da ciò che è **dedotto**.

| ID | Tema | Cosa è successo | Da decidere |
|---|---|---|---|
| OP-01 | BEP non accetta indirizzi esteri | S60: `BEP:101` "Dati non conformi: zipCode" | come trattare i mittenti fuori Italia |
| OP-02 | LDV madre e figlia nel multicollo | S02: scartato dal mapper, `ldv_non_pdb` | formato valido dei figli e regola RF-17 |
| OP-03 | Multicollo diviso per collo, scarto 1162 | 24-11: colli 2 e 3 scartati dal validatore, "Numero Riferimento Spedizione già utilizzato" | deciso 24-11: un record per spedizione con tutti i colli (mapper `6a6a042`); da riprovare dopo il deploy |
| OP-04 | Multicollo, BEP 101 sul barcode | 24-11: S02 `1110000000002`, `BEP:101` "Dati non conformi: barcode" su tutti e 3 i colli | figli del mock non nel formato PDB: corretti i mock; mapper allineato a PDB_INVIOSYSTEM (`506d71d`); da riprovare |

## OP-01 · BEP non accetta indirizzi esteri

- **Evidenza (S60):** il messaggio supera il mapper e BEP risponde `BEP:101`: "Dati non conformi: zipCode".
- **Mock:** mittente Zurich, CAP `8001` (4 cifre), `countryCode` `IT`. Il destinatario ha CAP `00144`.
- **Verificato:** l'errore viene da BEP, non dal mapper. Lo stesso vincolo era già emerso per S07, S12, S13 (annotato in `uat/genera_mock_test.py`: "BEP rifiuta altrimenti").
- **Dedotto:** BEP valida il CAP del mittente come CAP italiano (5 cifre). Il campo rifiutato è quello del mittente. Non ho letto il log di BEP.
- **Conseguenza:** il mittente estero (caso tipico dell'autoproduttore, S60/S61 "mittente fuori UE") non è testabile con il `countryCode` reale. Oggi nel mock si forza `IT` e un CAP di 5 cifre.
- **Rischio in produzione:** una spedizione EURODIS con mittente estero e CAP non a 5 cifre verrebbe rifiutata da BEP.
- **Da decidere con Diego:**
  1. BEP deve accettare i mittenti esteri, o il mapper deve normalizzare il CAP del mittente?
  2. Se il mittente estero è fuori perimetro, va scritto nella specifica e S07/S60/S61 vanno riclassificati.
- **Collegato:** DF-12 (codice nazione) in `punti-aperti-analisi-2026-10-23.md`; il mapper oggi passa `countryCode` solo in `codice_nazione_iso_2`.
- **Stato del mock:** per ora S07, S60 e S61 hanno un CAP di 5 cifre (`10100`, `80010`), solo per superare BEP.

## OP-02 · LDV madre e figlia non impostate bene

- **Evidenza (S02):** il mapper scarta il messaggio: `motivo=ldv_non_pdb`, colli [2, 3] di 3, nessuna pubblicazione.
- **Mock:** collo 1 con la LDV madre di 13 caratteri (`3UW2308` + 6 cifre); colli 2 e 3 con il figlio di 22 caratteri (9 caratteri casuali + la madre). Segue la regola multicollo dell'ICD BEP, secondo il commento in `uat/genera_mock_test.py:147-154` (non ho riletto l'ICD).
- **Specifica:** RF-17 e sezione 6.2.1, passo 1, di `sviluppo/ce-dichiarato-eurodis-mapper.md`: è PDB solo la LDV di 13 caratteri `[1-8]U[A-Z0-9]{5}[0-9A-Z]{6}`, controllata su **ogni** collo.
- **Verificato:** il mapper applica la specifica alla lettera.
- **Dedotto:** se i figli a 22 caratteri sono validi, ogni multicollo reale verrebbe scartato. Inoltre madre e figlio non sono distinti nel messaggio: `id_ldv_madre`, `id_ldv_figlio`, `tipo_collo`, `id_collo` restano vuoti (PA-11, DF-03).
- **Da decidere con Diego:**
  1. I figli a 22 caratteri (9 + madre) sono LDV valide nel flusso?
  2. Se sì, RF-17 va corretto: sul primo collo vale la regola dei 13 caratteri; sui successivi si accetta 9 caratteri + madre PDB valida, passando l'`id_ldv` com'è.
  3. Come si valorizzano madre e figlio nel tracciato (`id_ldv_madre`, `id_ldv_figlio`, `tipo_collo`, `id_collo`)?
- **Collegato:** DF-03 e PA-11 (multicollo), RF-17 (decisione del 18-11).
- **Stato del mock:** invariato; non lo cambio per non nascondere il difetto.

## OP-03 · Multicollo diviso per collo: colli 2 e N scartati con 1162

- **Evidenza (24-11, `ed_reference` `7700000000002`, 3 colli):** il mapper pubblica 3 record (log "collo 1/3 … 3/3"), con lo stesso `rif_spedizione`, tre `id_preadvising` diversi e `id_record_multicollo` comune. Su Mongo `dichiarato_events` il collo 1 (madre `3UW2308675840`) è a `stato` 3; i colli 2 e 3 (figli a 22 caratteri) sono a `stato` 2 con `errori` `1162` "Numero Riferimento Spedizione già utilizzato".
- **Verificato nel codice del validatore:**
  - la regola `pdb_1162` (`rules/pdb/generated/ce-pdb-rules.drl:1078`) chiama il gateway di `PdbPreadvisingHandler` (righe 106-123): è un duplicato se in `PreadvisingHistory` esiste lo stesso `numeroOrdine` (= `rif_spedizione`) con un `id_preadvising` **diverso** e `stato != 2`. Non considera `id_ldv`, madre/figlio né `id_record_multicollo`. Il primo collo registra il riferimento, gli altri lo trovano già usato;
  - `EUD_INVIOSYSTEM` passa da `PdbPreadvisingHandler` con le regole di `PDB_INVIOSYSTEM` (`PdbChannel.canaleRegole`, commit `0db4ca6` del 10-11), non da `SdaFlussoHandler`. Le regole logic (fra cui E225, errore 317) e il multicollo `002` per questo canale non si applicano.
- **Verificato nel codice di ldv-pdb:** `BepRequestMapper` (righe 234-245, 301-309) fa una waybill per spedizione con un `declared` per collo, e aggiunge il servizio multicollo `APT000945` solo se il record ha più di un collo. Per la famiglia PDB il multicollo è **un solo record con N colli**. Anche la regola PDB 2037 (oggi solo per i file `.csv`) controlla `numero_colli` = colli del record.
- **Dove si dividono i colli, flusso SDA e flusso PDB a confronto:**
  - flusso SDA (`IF`, `IS`, `IE`): la divisione per collo la fa il validatore (`SdaFlussoHandler`, multicollo `002`), dopo la validazione;
  - flusso PDB (`PDB_*`, `EUD_*`): nel validatore e in ldv-pdb i colli restano in un solo record (verificato). `PdbPreadvisingHandler` non divide; ldv-pdb fa una waybill con N `declared`, abbina la risposta di BEP al collo con `parcelLabel` e scrive madre e figlio sui colli dello stesso record (`BepResponseMapper.applyMulticolloIds`, righe 231-253). Il legame madre-figlio esiste dentro un record, non tra record diversi;
  - a valle: `ce-event-handler-monitoring` produce un `Record` per collo verso il monitoraggio (dalla nostra documentazione, codice non riletto), ma è una vista di monitoraggio e non tocca la creazione della spedizione. Smistatore e state machine: **non verificati**;
  - la regola 1162 funziona come previsto: nel modello PDB un `rif_spedizione` corrisponde a un solo `id_preadvising`. Il mapper invece divide in partenza come il flusso SDA, e il validatore vede tre spedizioni con lo stesso riferimento. Madre e figlio calcolati dal mapper non bastano: la regola non li legge.
- **Causa:** la divisione per collo (`DivisioneColli`, commit `253fd0d` del 20-11) copia il multicollo `002` del flusso SDA, ma `EUD_INVIOSYSTEM` è un canale della famiglia PDB. La nota di rilascio la motivava con "nessuno scarto 317", un errore che su questo canale non scatta.
- **Dedotto:** anche senza 1162, ldv-pdb manderebbe a BEP 3 waybill di un collo con lo stesso `shipmentRefNumber` e senza `APT000945`.
- **Proposta:** nel mapper un record per spedizione con tutti i colli, cioè togliere `DivisioneColli.perCollo` da `EurodisMapperServiceImpl.java:78`. Restano `id_collo` = LDV su ogni collo e madre/figlio calcolati dal mapper (`97242eb`), che servono a ldv-pdb (`parcelLabel`) e a send-tracking; `id_record_multicollo` non serve più. Vanno aggiornati `DivisioneColliTest`, il test del service, la nota di rilascio (riga "un record per collo nel pre-enrichment, nessuno scarto 317") e la specifica del mapper.
- **Scartata:** far ignorare a 1162 i record con lo stesso `id_record_multicollo`. Tocca un componente condiviso da tutti i canali PDB, la regola sta in un DRL generato fuori dal repo, e ldv-pdb produrrebbe comunque 3 waybill separate.
- **Rischi da verificare:**
  1. il ritorno di BEP con 3 colli su un record fino in fondo alla catena per `EUD_INVIOSYSTEM` (dal codice sì: `BepResponseMapper` lavora per collo, l'adapter unisce gli esiti per `code_externalId`; non provato);
  2. il collo 1 di questo test è passato con `numero_colli` 3 e un solo collo, senza `APT000945`: verificare cosa ha creato BEP per `3UW2308675840` (probabile LDV monocollo da annullare o ignorare).
- **[DECISO 24-11, Diego]:** correzione nel mapper, annulla la scelta del 20-11. Commit `6a6a042` del mapper: tolti `DivisioneColli` e `id_record_multicollo`, un solo invio per spedizione; restano `id_collo` = LDV e madre/figlio. Specifica (RF-01, RF-17, 6.6, AC-09/AC-09c) e nota di rilascio aggiornate. `ce-dichiarato-eurodis-in` non cambia: manda già un messaggio per spedizione con tutti i colli (`SpedizioneProducer.invia`).
- **Evidenza (24-11, 13:58, S02, `ed_reference` `9900000000002`):** ancora 3 record con `id_record_multicollo` e log "collo 1/3 … 3/3" dallo stesso offset `934`. In svil girava l'immagine precedente: `6a6a042` non era ancora pushato.
- **Da verificare dopo il deploy:** S02 di nuovo; nel pre-enrichment un solo record con 3 colli, a valle nessun 1162, in BEP una LDV con `APT000945`.
- **Collegato:** OP-02, PA-11, DF-03.

## Altri punti dai test del 20-11 (da fare o da chiarire)

| Punto | Stato |
|---|---|
| `ora_spedizione` è `00:00:00`, atteso `06:53:55` da `entranceTimestamp` (AC-01) | da correggere; causa non ancora verificata |
| `no_firma` non visibile nei messaggi, quindi non verificabile (S18-D, S12, S13, S30) | servono S18-S / S18-N |
| `consegna.contactless "S"` e `consegna.modifica_modalita "S"` valorizzati, nessuna regola in specifica | da chiarire con Diego |
| Accessori `T12`/`T10` e servizi `TD3`/`TD0` per M/F: corrispondenza non trovata in specifica | da verificare |
