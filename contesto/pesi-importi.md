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
