# 136596 — Eurodis autoproduttore · Punti aperti da vedere con Diego (lunedì 2026-11-23)

Emersi dai test integrati del 20-11 (esiti in `uat/mock-test/esiti-completed-2026-11-19.md`).
Distinguo ciò che è **verificato** (letto nei messaggi o nei log) da ciò che è **dedotto**.

| ID | Tema | Cosa è successo | Da decidere |
|---|---|---|---|
| OP-01 | BEP non accetta indirizzi esteri | S60: `BEP:101` "Dati non conformi: zipCode" | come trattare i mittenti fuori Italia |
| OP-02 | LDV madre e figlia nel multicollo | S02: scartato dal mapper, `ldv_non_pdb` | formato valido dei figli e regola RF-17 |

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

## Altri punti dai test del 20-11 (da fare o da chiarire)

| Punto | Stato |
|---|---|
| `ora_spedizione` è `00:00:00`, atteso `06:53:55` da `entranceTimestamp` (AC-01) | da correggere; causa non ancora verificata |
| `no_firma` non visibile nei messaggi, quindi non verificabile (S18-D, S12, S13, S30) | servono S18-S / S18-N |
| `consegna.contactless "S"` e `consegna.modifica_modalita "S"` valorizzati, nessuna regola in specifica | da chiarire con Diego |
| Accessori `T12`/`T10` e servizi `TD3`/`TD0` per M/F: corrispondenza non trovata in specifica | da verificare |
