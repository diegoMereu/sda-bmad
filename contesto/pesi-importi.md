# Pesi e importi lungo la catena preadvising

Unità di misura di pesi, dimensioni e importi, servizio per servizio.

Fonti:
- ICD `ICD_PREADVISING_LDV_v12 (2).xlsx`;
- codice dei repo in `gitposte/SDA/preadvising` (novembre 2026);
- campione di 1998 messaggi di `preadvising.completed` in collaudo, 24-26/11/2026. Il 97% è PDB, poi OMP, EUD, PDW, IS e IE.

## Regola di fatto

| Grandezza | Prima della LDV (pre-enrichment, BEP) | Su `completed` e a valle (SEW) | Palmari (`AnaLdv`) |
|---|---|---|---|
| `collo.peso` | **grammi** | **kg** (fino a 3 decimali) | grammi (`PESO_COLLI`) |
| dimensioni collo | cm interi | cm | cm, troncati |
| `contrassegno.importo_contrassegno` | euro, 2 decimali | euro | centesimi (`IMPORTO_CONTRASS`, non arrotondato) |
| `assicurata.importo_assicurata` | euro | euro | centesimi (`IMPORTO_ASS`) |
| `internazionale.valore_spedizione` | euro | euro | centesimi (`VALORE_DICH`) |
| `articolo.valore` | centesimi | centesimi; in euro solo dopo la fase 2 dell'adapter | — |
| `articolo.peso_totale` | grammi | grammi; in kg solo dopo la fase 2 dell'adapter | — |
| `internazionale.importo_oneri` | centesimi interi | centesimi interi | `IMPORTO_ONERI` intero |
| `importi.*` (diritti, `tassa_ritorno`, incassi) | centesimi interi (ICD) | idem; nel campione non sono mai valorizzati | — |

## Campo per campo

Quattro gruppi di campi del tracciato unico: pesi, dimensioni, importi e quantità. Le colonne:
- **ICD v12**: tipo e unità come scritti nell'ICD;
- **Ingresso → BEP**: unità e conversioni fino alla creazione della LDV;
- **Su `completed` (collaudo)**: unità osservata nel campione;
- **A valle**: SEW (`sda-ldv-preadv-consumer`) e palmari (`AnaLdv` dello smistatore).

### Pesi

| Campo | ICD v12 | Ingresso → BEP | Su `completed` (collaudo) | A valle |
|---|---|---|---|---|
| `spedizione/collo/peso` | number 8, **unità non indicata** | grammi (builder per cliente, EURODIS ×1000). Il validatore SDA divide per 1000 (2 decimali). Verso BEP `weight` è un intero in grammi, troncato | **kg** su tutti i canali (PDB 0.001-80, EUD fino a 3 decimali, OMP, PDW, IS). Il sync lo lascerebbe in grammi | SEW `peso_colli` varchar(10) in kg. Palmari `PESO_COLLI` in grammi |
| `spedizione/internazionale/peso` | number, **grammi** | EURODIS in grammi; adapter PDB ÷1000; ILP in kg | **misto**: PDB in kg (0.07-30), EUD_INVIOSYSTEM in grammi (4150, 15000) | non usato |
| `spedizione/collo/articolo/peso_totale` | number 7, **grammi** | BEP `totalWeight` in grammi, invariato | **grammi** (la somma degli articoli è 1000 volte `collo.peso`). Diventa kg solo con la fase 2 dell'adapter o l'esito di ldv-pdb | non usato |
| `ritiro/contenuto/peso` e `spedizione/ritiro/contenuto/peso` | number 7, **unità non indicata** | grammi (builder `Ritiro_Peso` = `PESO_COLLO`); nessuna conversione | **grammi** (IE: 100000, con il collo a 100.0 kg) | `temp_ritiri_clienti.peso_colli` viene da `collo.peso` (kg), non da questo campo |

### Dimensioni

| Campo | ICD v12 | Ingresso → BEP | Su `completed` (collaudo) | A valle |
|---|---|---|---|---|
| `spedizione/collo/lunghezza`, `altezza`, `profondita` | number 5, **unità non indicata** | cm (EURODIS: `width` va in `profondita`). BEP `length`/`height`/`width` stringhe in cm | cm interi (PDB 1-170) | SEW `dim_l/h/w` decimal. Palmari `DIM_*` interi troncati. `temp_ritiri.volume` = l×a×p, oppure 9999.99 se il ritiro è voluminoso |
| `ritiro/contenuto/altezza`, `larghezza`, `profondita` (e `spedizione/ritiro/...`) | number 5, **unità non indicata** | cm presunti | non presenti nel campione | — |

### Importi

| Campo | ICD v12 | Ingresso → BEP | Su `completed` (collaudo) | A valle |
|---|---|---|---|---|
| `spedizione/valore` | string 12, **centesimi** | builder in euro (`Valore_Spedizione`). Adapter PDB copia `customsDeclaration_totalValue` invariato. Validatore SDA lo copia in `importo_assicurata`. Non va a BEP | **misto**: IS in euro (200.0); PDB in centesimi (250-31545, uguale alla somma degli articoli); OMP interi 1030-3279, unità non determinabile | SEW `valore_dich` decimal(8,3) invariato: **PDB ×100**. `temp_ritiri.valore_spedizione` |
| `spedizione/internazionale/valore_spedizione` | number 10, **euro** | euro. BEP `waybillTotalValue` con 2 decimali. Ritorno con euristica: senza punto lo tratta come centesimi e divide per 100. EURODIS non lo valorizza | euro, interi (PDB 4-799, IS 200) | Palmari `VALORE_DICH` in centesimi (×100). Non su SEW |
| `spedizione/internazionale/importo_oneri` | number 8, **centesimi** | intero in centesimi (Integer nel validatore, String nell'orchestratore). ILP euro ×100. Non va a BEP | non valorizzato | Palmari `IMPORTO_ONERI` con `parseInt`: un decimale diventa null. Non su SEW |
| `spedizione/assicurata/importo_assicurata` | number 10, **euro** | euro `IIIIIII.DD`, validatore `@Digits(10,2)`. BEP APT000919/955/956 con 2 decimali. PDW ÷100 | euro (258.23, 49000.23, 36) | SEW `importo_ass` decimal(8,3) in euro. Palmari `IMPORTO_ASS` in centesimi interi |
| `spedizione/contrassegno/importo_contrassegno` | number 9, **unità non indicata** | euro `IIIIII.DD`, validatore `@Digits(9,2)`, massimale 4999.99. BEP APT000918 con 2 decimali. PDW ÷100. EURODIS arrotonda a 2 decimali | euro (123.45, 159.75, 54.9) | SEW `importo_contrass` decimal(8,3) in euro. Palmari `IMPORTO_CONTRASS` ×100 non arrotondato |
| `spedizione/collo/articolo/valore` | number 10, **centesimi** | BEP `totalValue` invariato, in centesimi | **centesimi** (PDB 250-19200). Diventa euro solo con la fase 2 dell'adapter o l'esito di ldv-pdb | non usato |
| `spedizione/importi/importo_diritti_postale`, `importo_diritti_doganali`, `importo_diritti_postali_pddp`, `_smart`, `_up`, `tassa_ritorno`, `incasso_diritti_doganali`, `incasso_diritti_postali` | int 15, **centesimi** (ICD v12: le descrizioni di `importo_diritti_postale` e `importo_diritti_doganali` erano invertite) | Integer ovunque. Arrivano solo da TUP, invariati. Un decimale viene troncato senza errore | mai valorizzati | non arrivano né a SEW né ai palmari |

### Quantità (pezzi, senza unità di misura)

| Campo | ICD v12 | Note |
|---|---|---|
| `spedizione/numero_colli` | integer 5 | `@Max(99999)`. EURODIS segnala `colli_incoerenti` se non coincide con l'elenco dei colli |
| `spedizione/collo/numero_colli_parz` | string 5 | — |
| `spedizione/collo/articolo/quantita` | integer 3 | — |
| `ritiro/contenuto/quantita` (e `spedizione/ritiro/...`) | integer 3 | — |

## Dove cambia l'unità

1. **Ingresso.**
   - Il builder porta a grammi il peso del file con una funzione JS diversa per ogni cliente, nel suo `.ini`. I fattori usati sono ×1000, ×100 o ×10; in 19 output su 141 il valore passa invariato.
   - `ce-dichiarato-eurodis-mapper` converte kg → g con ×1000 e HALF_UP.
   - Gli importi restano in euro.
2. **Validatore, solo flusso SDA** (`SdaFlussoHandler`, regola E018 in `validation-procedure.drl`): g → kg con ÷1000, 2 decimali. I flussi PDB, EUD, TUP e TFI non convertono.
3. **ldv-pdb e ldv-pdb-sync verso BEP.**
   - `weight` in grammi con `intValue()`, cioè **troncato**; un collo senza peso parte con 0.
   - Contrassegno e assicurata in euro con `setScale(2)`.
   - Articoli inviati così come sono.
4. **Ritorno.**
   - `ldv-pdb` (asincrono) e adapter PDB riportano il peso a kg con ÷1000, 3 decimali.
   - Gli articoli passano a kg ed euro solo in fase 2.
   - `ldv-pdb-sync` **non riconverte**: il peso resta in grammi.
5. **Smistatore verso i palmari:** kg → g ed euro → centesimi.
6. **`sda-ldv-preadv-consumer` verso SEW:** nessuna conversione.
   - `peso_colli` è varchar(10) in kg.
   - Importi e `valore_dich` sono decimal(8,3) in euro.

## Incoerenze (codice + collaudo)

- **`spedizione.valore` ha due unità.**
  - L'ICD v12 lo indica in centesimi.
  - Lo schema del builder lo indica in euro.
  - Nel campione: IS 200.0 = `valore_spedizione` 200, quindi euro; PDB 250-31545 interi, uguale alla somma di `articolo.valore`, quindi centesimi.
  - Il consumer SEW lo scrive in `valore_dich` così com'è: per PDB il valore finisce su SEW **×100**.
- **`internazionale.peso` ha due unità.**
  - L'ICD v12 lo indica in grammi.
  - Su `completed` PDB è in kg (0.07-30), mentre EUD_INVIOSYSTEM è in grammi (4150, 15000).
- **Nello stesso messaggio collo e articoli sono in unità diverse.** Su `completed` PDB la somma di `articolo.peso_totale` è 1000 volte `collo.peso`: articoli in grammi, collo in kg.
- **`ritiro.contenuto.peso` non viene convertito.** Nel campione IE: ritiro 100000 (grammi) e collo 100.0 (kg).
- **`collo.peso` nell'ICD non ha unità.** Il codice la deduce: grammi prima della LDV, kg dopo.
- **Interi che troncano in silenzio.**
  - Jackson `ACCEPT_FLOAT_AS_INT` è attivo su validatore, orchestratore e smistatore: un decimale che arriva in `importi.*` o `importo_oneri` (Integer) viene troncato senza errore.
  - Nell'adapter PDB `importo_oneri` decimale va in `parseInt` e lancia eccezione.
  - Nello smistatore palmari `importo_oneri` decimale diventa `null`.
- **Soglie SDA in kg dipendenti dall'ordine Drools.** Le regole di soglia (5 kg, 30 kg) hanno la stessa salience della conversione E018: non è garantito che leggano il peso già convertito.
- **Contrassegno 0.** Il sync invia `"0.00"` a BEP, l'asincrono lo omette.
