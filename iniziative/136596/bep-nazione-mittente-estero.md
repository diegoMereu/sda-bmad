# 136596 — Nazione del mittente estero verso BEP

Contesto raccolto il 18-11-2026 dopo lo scarto BEP `101 Dati non conformi: country` sulle
preadvising `EUD_INVIOSYSTEM` in svil. Vale anche per `EUD_INVIOFILE`.

## Regola del cliente

**Per l'inbound EURODIS il prodotto è nazionale e `sender.country` = `receiver.country` =
`ITA1` costante, anche quando il mittente è estero.** La transcodifica ISO2 → ISO4 non si
applica al flusso nazionale.

Fonte: `127558_EURODIS_Analisi_Mapping_ImportPAN_BEP_v1_7.docx` (cartella
`EURODIS/PRJ0039590-127558-EURODIS Inbound (SD-1)-ImportPanBEP/`), decisione della minuta
di riunione del **29/07/2026**:

- **OP-NAZ, risolto:** "sender.country e receiver.country = ITA1 costante (anche per
  mittenti esteri)". Resta da verificare l'impatto di `ITA1` sulla validazione degli
  indirizzi esteri del mittente (OP-WSADDR).
- **Regole di mapping verso `createWaybill`:** `data.sender.country/countryName` = `ITA1`
  costante ("prodotto nazionale"); `data.receiver.country` = `ITA1`.
- **Esempio JSON del documento:** mittente austriaco con `"country": "ITA1"`,
  `"countryName": "Italia"`, `"province": "EE"`. La convenzione "EE" per la provincia
  estera è "DA CONFERMARE con BEP".
- **Prodotto:** `APT000901` (PDB Express, nazionale). Il blocco internazionale della
  request BEP non si valorizza.
- **Destinatario:** sempre italiano.

## Cosa conferma l'evidenza in svil (18-11)

- ldv-pdb mappa come da tabella "Mapping CM": `country` ← `CODICE_NAZIONE`, `countryName`
  ← `NAZIONE`, senza trasformazioni (`BepRequestMapper.java:477-498`; uguale in
  ldv-pdb-sync, `PdbRequestMapper.java:416-437`).
- Su `PACCHI.MEDIATION.BEP.INVIOSYSTEMREQUEST` le richieste EURODIS hanno sender
  `GER1`/`GERMANIA` e receiver `ITA1`/`ITALIA`. BEP risponde `101 country`.
- `POST /international/nations` con contratto `SFA-00633620` restituisce `countries: []`:
  il contratto EURODIS non ha nazioni estere abilitate. Qualunque `country` estero viene
  rifiutato, anche se nel formato ISO4 corretto.
- ICD BEP REST v2.1 (`ICD_BEP_ALL_CanaleWEBSERVICE_RESTJSON v2.1.docx`): `country` è
  "Codice nazione ISO 4", "unica codifica riconosciuta dai sistemi Poste".

## Impatto sulla nostra catena

| Canale | Oggi | Atteso dalla regola |
|---|---|---|
| `EUD_INVIOSYSTEM` | il mapper mette in `codice_nazione` l'ISO4 di `ce-anagrafica` (`GER1`) e in `nazione` il nome (`GERMANIA`) | verso BEP: mittente `ITA1` / `Italia` |
| `EUD_INVIOFILE` | il builder (`cli_c49353.ini`, righe 488-493 e 597-602) copia il codice nazione di 3 caratteri del file sia in `codice_nazione` sia in `nazione`, senza `ce-anagrafica` | verso BEP: mittente `ITA1` / `Italia` |

Entrambi i canali usano il contratto `SFA-00633620` e il centro di costo `CDC-00000014`
(mapper: `MAPPER_CLIENTE_CONTRATTO` / `MAPPER_CENTRO_COSTO`; builder: costanti nel `.ini`).

## Da decidere

1. **Dove si applica la costante `ITA1`.** Due strade:
   - in ldv-pdb e ldv-pdb-sync, solo per i canali `EUD_*`: il tracciato unico conserva la
     nazione vera del mittente per il resto della catena (SEW, tracking);
   - nel mapper e nel builder: più semplice, ma la nazione vera del mittente si perde a valle.
2. **`countryName` e `province` del mittente estero:** `Italia` e `EE`, come nell'esempio
   del documento? La provincia "EE" è da confermare con BEP (OP-WSADDR).
3. **Canale verso BEP.** La minuta del 29/07 indica il web service REST sincrono
   `waybill/create` (`channel = WEBSERVICES`). La catena attuale passa da ldv-pdb su Kafka
   (`INVIOSYSTEM`). Da riallineare con la decisione o da confermare.

## Altri riferimenti utili dallo stesso documento

- **Tabella di transcodifica ISO2 → codice BEP**, "resta come riferimento" per un futuro
  flusso internazionale: ES→`ESP1`, FR→`FRA1`, DE→`DEU1`, NL→`NLD1`, BE→`BEL1`,
  AT→`AUT1`, PT→`PRT1`, IT→`ITA1`. Per la Germania `ce-anagrafica` restituisce `GER1`,
  non `DEU1`: va verificato se mai si passa a un prodotto internazionale.
- **Mono centro di costo** al primo rilascio. Un centro di costo per nazione del mittente
  è rinviato.
- **Europlate non inviato a BEP:** resta lato SDA per la correlazione con la LDV PDB
  (OP-BEP-02).
- **Etichetta:** `paperless = false`, `printFormat = ZPL`, stampa in filiale tramite NAF.
- **Peso:** default 1 grammo se assente (OP-PESO). Dimensioni del collo obbligatorie per
  BEP, interi > 0 (OP-DIM).
- **Note della riunione BEP** (`Riunione bep.docx`): BEP genera una LDV PDB nazionale,
  perché gli impianti non riconoscono l'Europlate.
