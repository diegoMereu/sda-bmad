# Importi in centesimi e dimensioni in cm: impatti

> **Aggiornamento 26/11/2026.** Il perimetro è stato allargato: anche i pesi vanno uniformati, in grammi interi,
> e tutte le conversioni interne alla catena vanno tolte. Restano solo quelle verso i sistemi esterni che non si
> adeguano (BEP, SAP-EM, SEW, ce-contratti, ce-vendite). La versione aggiornata, con l'elenco delle conversioni, è
> nella nota per il cliente [comunicazioni/2026-11-26-pesi-importi-dimensioni.md](comunicazioni/2026-11-26-pesi-importi-dimensioni.md).
> Da analizzare anche il file impianti, generato dal completed, il cui generatore non è nei repo in locale.

Analisi d'impatto, novembre 2026. Nessuno sviluppo avviato. Si basa sullo stato attuale descritto in
[pesi-importi.md](pesi-importi.md).

## 1. Obiettivo e perimetro

- **Importi**: tutti in **centesimi interi** dal validatore in poi, cioè su `preadvising.enrichment`,
  `preadvising.completed`, `.completed.poste` e `.completed.sda`.
- **Dimensioni** (collo e contenuto del ritiro): **cm interi**.
- **Pesi**: fuori perimetro, restano come oggi (grammi prima della LDV, kg dopo).
- **Builder e eurodis-mapper non si toccano**: su `preadvising.pre-enrichment` gli importi restano in
  euro, come oggi.
- **Trascodifica nel validatore**, che è il punto da cui passano tutti i canali.

## 2. Contratto risultante

| Campo | Su `pre-enrichment` (ingresso, invariato) | Dal validatore in poi |
|---|---|---|
| `contrassegno/importo_contrassegno` | euro | **centesimi interi** |
| `assicurata/importo_assicurata` | euro | **centesimi interi** |
| `internazionale/valore_spedizione` | euro | **centesimi interi** |
| `spedizione/valore` | euro (vedi decisione D1) | **centesimi interi** |
| `internazionale/importo_oneri`, `importi/*`, `articolo/valore` | centesimi | centesimi (nessuna conversione) |
| `collo/lunghezza`, `altezza`, `profondita`, `ritiro/contenuto/*` | cm, anche con decimali | **cm interi**, arrotondati HALF_UP |
| `versione_tracciato` | `1` (lo valorizzano builder, adapter, eurodis-mapper e TUP) | **`2`** = importi in centesimi |

`versione_tracciato = 2` è il **marcatore dell'unità**.
- Chi legge il tracciato decide come interpretare gli importi in base a questo valore.
- Il validatore non riconverte un messaggio che arriva già a 2.

Il marcatore serve per tre motivi:
- il periodo di transizione;
- i retry che rileggono Mongo;
- lo storico.

## 2bis. Campi da cambiare e impatti per campo

Legenda:
- **M** = modifica necessaria;
- **V** = da verificare;
- **—** = punto che tocca il campo ma resta invariato.

I percorsi sono relativi ai repo in `gitposte/SDA/preadvising`.

### A. Importi da euro a centesimi

#### A1. `spedizione/contrassegno/importo_contrassegno`

Oggi è in euro con 2 decimali. Nuova unità: centesimi interi.

| Componente | Punto | Impatto |
|---|---|---|
| builder | `.ini` per cliente, formato `IIIIII.DD`; template `json_output_template.ftl:161` | — |
| eurodis-mapper | `EurodisToIcdMapper.java:496` `setScale(2)` | — |
| adapter, flusso normale | `PdbMapper.java:485-500` (APT000918), `PdwMapper.java:95` (÷100) | — (resta in euro) |
| adapter, fase 2 | stesso mapping, pubblicato su `enrichment` | **M** ×100 |
| validatore | `ContrassegnoDTO:13` `@Digits(9,2)`; `validation-procedure.drl:49` (99999.999, errore 004); `ce-pdb-rules.drl:608-635` (punto decimale) | — (girano in euro); **M** conversione in uscita |
| orchestratore | `ContrassegnoDTO` BigDecimal; `OrchestratoreMongoService:344-357` | — |
| ce-dichiarato-ldv | `ProcessLdvService.java:710-725` contro `limiti-pagamento-incasso.properties` (`CON.importo=4999.990`, `CEC=258.530`) | **M** ÷100 prima del confronto |
| ldv-pdb asincrono | `BepRequestMapper.java:336-341, 527-529` APT000918 `money()` | **M** ÷100 a scala 2 |
| ldv-pdb-sync | `PdbRequestMapper.java:289, 467` | **M** ÷100 a scala 2 |
| smistatore, topic | `ContrassegnoDTO:11`, invariato verso `.completed.poste` e `.sda` | **contratto esterno** |
| smistatore, palmari | `PalmariMapperService.java:487` ×100 | **M** niente ×100 se v2 |
| consumer SEW | `QueriesManagerDao.java:408-412` `importo_contrass`; `temp_ritiri_clienti` (`:1044-1128`); `CliDatiStampaTfDao.java:252-369` | **M** ÷100 se v2 |
| consumer SEW on-out-tot | `QueriesManagerDao` del modulo (`sew_sped_pre_adv_online_out_tot`) | **M** ÷100 se v2 |
| ttrepo | `@Digits(9,2)` | — |
| bff, preavviso, monitoraggio FE | `ContrassegnoDTO:19`; `PreadvisingDettaglioResponseDTO` (Double) | **M** visualizzazione ÷100 |
| palmari-comparatore | esclude `IMPORTO_CONTRASS` | **M** includerlo |

#### A2. `spedizione/assicurata/importo_assicurata`

Oggi è in euro. Nuova unità: centesimi interi.

| Componente | Punto | Impatto |
|---|---|---|
| builder | formato `IIIIIII.DD`; template `:156` | — |
| adapter, flusso normale | `PdbMapper.java:503-512` (APT000919, 955, 956), `PdwMapper.java:117` | — |
| adapter, fase 2 | idem | **M** ×100 |
| validatore | `AssicurataDTO:14` `@Digits(10,2)`; `dominio-rules.drl:227` (99999.999, errore 415), `:181-185` (CIN sopra 1500, in double), `:211` (copia da `valore`); `VenditeClient.java:132,163` verso `ce-vendite` | — (girano in euro); **M** conversione in uscita |
| ce-dichiarato-ldv | `VenditeClient.java:185` `importoAssicurata` verso `ce-vendite` | **M** ÷100 prima della chiamata |
| ldv-pdb asincrono | `BepRequestMapper.java:419-425` | **M** ÷100 a scala 2 |
| ldv-pdb-sync | `PdbRequestMapper.java:371` | **M** ÷100 a scala 2 |
| smistatore, palmari | `PalmariMapperService.java:505-508` ×100 | **M** niente ×100 se v2 |
| consumer SEW (+ on-out-tot) | `QueriesManagerDao.java:402-406` `importo_ass`; `temp_ritiri_clienti.importoassicurata`; `cli_dati_stampa_tf_2` | **M** ÷100 se v2 |
| tipi | `@Digits(10,2)`: fino a 10^12 centesimi, non entra in `Integer` | **M** `Long` o `BigDecimal` a scala 0 dove si tipizza in centesimi |
| bff, preavviso, monitoraggio FE | come A1 | **M** visualizzazione |

#### A3. `spedizione/internazionale/valore_spedizione`

Oggi è in euro. Nuova unità: centesimi interi.

| Componente | Punto | Impatto |
|---|---|---|
| builder | `Valore_Spedizione`, template `:150` (lo stesso valore va anche in `spedizione/valore`) | — |
| eurodis-mapper | valorizzato a 0 (`InternazionaleDTO.java:20`) | — |
| adapter, flusso normale | `PdbMapper.java:527` (euristica in `PdbMapperUtils.java:119-138`), `PdwMapper.java:200`, `IlpMapper.java:208` | — |
| adapter, fase 2 | idem | **M** ×100 |
| validatore | `dominio-rules.drl:541` (lunghezza > 10), `validation-procedure.drl:314` (> 0 per EUD, INT, CIN, EXB) | — (girano in euro); **M** conversione in uscita |
| ldv-pdb asincrono | `BepRequestMapper.java:196` `waybillTotalValue` | **M** ÷100 a scala 2 |
| ldv-pdb-sync | `PdbRequestMapper.java:173` | **M** ÷100 a scala 2 |
| smistatore, palmari | `PalmariMapperService.java:173-176` `VALORE_DICH` ×100 | **M** niente ×100 se v2 |
| SEW | non scritto | — |
| bff, ttrepo | `@Digits(10,2)` | **M** visualizzazione (bff) |

#### A4. `spedizione/valore`

Oggi è misto: euro dai canali SDA, centesimi dall'adapter PDB. Nuova unità: centesimi interi.

| Componente | Punto | Impatto |
|---|---|---|
| builder | template `:89` (euro) | — |
| adapter, flusso normale | `PdbMapper.java:516-520` `customsDeclaration_totalValue` (centesimi) | **M** ÷100 (decisione D1) |
| adapter, fase 2 | idem | — (è già in centesimi) |
| eurodis-mapper, TUP | 0, oppure null (`TUPMapper.java:110`) | — |
| OMP | produttore sconosciuto, interi da 1030 a 3279 | **V** (Q2) |
| validatore | `SpedizioneDTO` BigDecimal; `dominio-rules.drl:211` lo copia in `importo_assicurata` | **M** conversione in uscita |
| orchestratore, smistatore | String, invariato | — |
| consumer SEW (+ on-out-tot) | `QueriesManagerDao.java:497` `valore_dich`; `temp_ritiri_clienti.valore_spedizione` | **M** ÷100 se v2. Si corregge così l'errore attuale per PDB |
| ICD | v12 lo dichiara già in centesimi | — |

### B. Importi già in centesimi, toccati dai percorsi di ritorno

#### B1. `spedizione/collo/articolo/valore`

Resta in centesimi.

| Componente | Punto | Impatto |
|---|---|---|
| ldv-pdb asincrono, esito | `BepResponseMapper.java:102` ÷100 | **M** togliere |
| adapter, fase 2 | `PdbMapper.java:247-266` `convertiPesiEValoriArticoli` ÷100 | **M** togliere la ÷100 (la ÷1000 del peso resta) |
| adapter ILP | `IlpMapper.java:241-242`, in euro | **V** ×100 (Q4) |
| BEP | `BepRequestMapper.java:272`, `PdbRequestMapper.java:241` `toString()` | **V** arrotondare a scala 0 (oggi può partire `"1500.0"`) |
| Effetto a valle | sui flussi PDB in fase 2 o con esito asincrono, `articolo/valore` su `completed` passa da euro a centesimi | **contratto esterno** |

#### B2. `internazionale/importo_oneri` e `importi/*`

`importi/*` comprende i diritti postali e doganali (5 campi), `tassa_ritorno` e gli incassi (2 campi).

Nessuna modifica: sono già centesimi interi. Resta il rischio che un decimale in ingresso venga
troncato senza errore (Jackson `ACCEPT_FLOAT_AS_INT` è attivo), oppure dia `NumberFormatException` in
`PdbMapper.java:293-295` dell'adapter.

### C. Dimensioni in cm interi

#### C1. `spedizione/collo/lunghezza`, `altezza`, `profondita`

| Componente | Punto | Impatto |
|---|---|---|
| builder | `Dimensioni_*`, template `:189-191` | — |
| eurodis-mapper | `EurodisToIcdMapper.java:547-549`, HALF_UP; la larghezza (`width`) va in `profondita` | — (da documentare) |
| adapter | `PdbMapperUtils.java:143` `setScale(0)` | — |
| validatore | `ColloDTO` `@Digits(5,2)`, soglia 999.99 | **M** `setScale(0, HALF_UP)` in uscita |
| orchestratore | String | — |
| BEP | `BepRequestMapper.java:248-250`, `PdbRequestMapper` | — (riceve `"50"` invece di `"50.0"`) |
| smistatore, palmari | `PalmariMapperService.java:630-639` troncatura | — (non ha più effetto) |
| SEW | `QueriesManagerDao.java:246-248` `dim_h`, `dim_l`, `dim_w`; `temp_ritiri_clienti.volume` = l×a×p | il volume cambia leggermente quando arrivavano decimali; **V** unità del volume (Q5) |
| bff | `@Digits(5,2)` | — |

#### C2. `ritiro/contenuto/altezza`, `larghezza`, `profondita` (e `spedizione/ritiro/contenuto/*`)

| Componente | Punto | Impatto |
|---|---|---|
| validatore | `ContenutoDTO`, `PickupContenutoDTO` | **M** `setScale(0, HALF_UP)` in uscita |
| a valle | nessun uso trovato; nel campione di collaudo non compaiono | **V** su un file reale |

### D. Campo tecnico

#### D1. `versione_tracciato`

Oggi vale 1. Diventa 2 quando gli importi sono in centesimi. Un valore assente o pari a 1 resta
**euro**.

| Componente | Punto | Impatto |
|---|---|---|
| produttori | builder (lo imposta a 1 se null), adapter (`setVersioneTracciato(1)` alle righe 51 e 318), eurodis-mapper (`:59`), pacchi-tracking (`VERSIONE_TRACCIATO = 1`) | — |
| validatore, adapter fase 2 | — | **M** impostare 2 |
| ldv-pdb, ldv-pdb-sync | il campo **non è nei DTO**: deserializzando e ripubblicando su `enrichment` si perde, e a valle il messaggio sembra v1 | **M** aggiungerlo ai DTO e propagarlo |
| retry-id-cliente | campo assente | **M/V** propagarlo da Mongo verso `completed` |
| retry-eurodis, orchestratore, smistatore, ce-dichiarato-ldv | il campo c'è | **V** che venga propagato invariato |
| consumer SEW (sew_sped e on-out-tot) | campo assente | **M** aggiungerlo, serve a decidere la ÷100 |
| producer-sew-sped (vecchio flusso, da SEW verso il tracciato) | rilegge importi in euro e non imposta la versione | — (null = euro); **V** su quale topic pubblica |
| bff, preavviso, monitoraggio FE | campo assente | **M** aggiungerlo per la visualizzazione |
| ICD | — | **M** definire il significato del valore 2 |

## 3. Come lavora il validatore

1. **Ingresso.** Se il messaggio ha `versione_tracciato >= 2`, cioè viene da un retry o da un
   reinvio, gli importi vengono riportati in euro (÷100). Le regole quindi lavorano sempre in euro.
2. **Regole Drools invariate.** Le soglie restano in euro:
   - contrassegno e assicurata fino a 99999.999 (errori 004 e 415);
   - assicurata obbligatoria per CIN sopra 1500;
   - formato con il punto per PDB (errori 1247-1250).

   Restano invariati anche la copia `valore` → `importo_assicurata` e i vincoli `@Digits`.
3. **Uscita.** Come ultimo passo, dopo le regole e prima del salvataggio su Mongo (stato 3) e della
   pubblicazione:
   - gli importi in euro moltiplicati per 100 (HALF_UP, scala 0);
   - le dimensioni arrotondate all'intero;
   - `versione_tracciato = 2`.

   Il passo si applica in tutti gli handler: SDA, PdbPreadvising, PdbPdw, Tfi e Tup.

Effetti:
- Su `dichiarato_events` lo stato 0 resta in euro, lo stato 3 è in centesimi. Lo distingue
  `versione_tracciato`.
- Gli importi in centesimi vanno tenuti in `Long` o `BigDecimal` a scala 0, non in `Integer`. L'assicurata
  `@Digits(10,2)` arriva a 10^12 centesimi.

## 4. Impatti per componente

L'impegno è stimato su tre livelli: basso, medio, alto.

| # | Componente | Cosa cambia | Impegno |
|---|---|---|---|
| 1 | **ce-dichiarato-validatore** | Passi di ingresso e uscita del §3 in tutti gli handler. DTO a scala 0 o `Long`. Test per canale, per i retry già a v2 e per gli arrotondamenti | **medio** |
| 2 | **ce-dichiarato-adapter**, flusso normale (verso `pre-enrichment`) | Resta in euro. Solo `spedizione/valore` PDB (`customsDeclaration_totalValue`, oggi in centesimi) va portato a euro (÷100), vedi D1 | basso |
| 3 | **ce-dichiarato-adapter**, fase 2 (verso `preadvising.enrichment`, **non passa dal validatore**) | Deve produrre direttamente la v2: APT000918, 919, 955 e 956 ×100; `valore_spedizione` ×100; `convertiPesiEValoriArticoli` non divide più `articolo/valore` per 100 (la ÷1000 del peso resta); `versione_tracciato = 2` | medio |
| 4 | **ce-dichiarato-orchestratore** | Nessuna logica. `normalizeNumericNode` va bene sugli interi. Aggiornare `docs/OrchestratoreDTO.md` | basso |
| 5 | **ce-dichiarato-ldv** | Massimali di `limiti-pagamento-incasso.properties` (es. `CON.importo=4999.990`, `CEC=258.530`): confronto dopo ÷100, oppure massimali in centesimi. `importoAssicurata` verso `ce-vendite` (fascia di assicurazione): ÷100 prima della chiamata, così `ce-vendite` non si tocca. **Da verificare** se scrive importi su DB | medio |
| 6 | **ldv-pdb asincrono** (`BepRequestMapper`) | BEP vuole euro per APT000918, 919, 955, 956 e `waybillTotalValue`: `money()` diventa ÷100 a scala 2. `items.totalValue` invariato. In `BepResponseMapper` si toglie la ÷100 su `articolo/valore`, che deve restare in centesimi | basso |
| 7 | **ldv-pdb-sync** (`PdbRequestMapper`) | Stesse modifiche della request asincrona. L'esito non cambia per gli importi | basso |
| 8 | **ce-dichiarato-smistatore**, palmari | `PalmariMapperService`: si tolgono i ×100 di `IMPORTO_CONTRASS` (riga 487), `IMPORTO_ASS` (505-508) e `VALORE_DICH` (173-176) quando `versione_tracciato >= 2`. Così si risolve anche il contrassegno non arrotondato | basso |
| 9 | **ce-dichiarato-smistatore**, `.completed.poste` e `.completed.sda` | Nessun codice: i messaggi passano così come sono. **Cambia il contratto verso i sistemi esterni** (§6) | basso nel codice, **alto come impatto** |
| 10 | **sda-ldv-preadv-consumer** (SEW, branch dedicato) | SEW resta in euro, `decimal(8,3)`. Con v2 si divide per 100 a scala 2 `importo_ass`, `importo_contrass` e `valore_dich` in `sew_spedizioni`, `_work` e `_work_2`, poi `importoassicurata`, `importo_contrassegno` e `valore_spedizione` in `temp_ritiri_clienti(_2)`, e gli importi in `cli_dati_stampa_tf_2`. Si chiude anche il problema attuale di `valore_dich` PDB 100 volte più grande | basso / medio |
| 11 | **ce-preadvising-retry-099** | Rilegge `dichiarato_events` e ripubblica su `pre-enrichment`. Nessuna modifica se si mantiene `versione_tracciato`: il validatore riconosce la v2 (§3, punto 1) | nessuno, va testato |
| 12 | **retry-eurodis** (verso `.completed.poste`) e **retry-id-cliente** (verso `completed`) | Ripubblicano da Mongo **saltando il validatore**. Va bene se mantengono `versione_tracciato`: i documenti vecchi restano v1 in euro, i nuovi v2. A valle quindi si devono leggere entrambe le versioni per tutto il tempo in cui i documenti vecchi possono essere ritentati | nessuno, va verificato e testato |
| 13 | **ce-dichiarato-bff** | Il reinvio da Mongo verso `enrichment` e `completed` ha lo stesso tema del punto 12. Nella visualizzazione ÷100 per la v2. I DTO `@Digits(9,2)` e `(10,2)` accettano anche interi | basso |
| 14 | **preavviso** (FE e BFF), **ce-monitoraggio-fe** | Visualizzazione degli importi ÷100 per la v2 (`PreadvisingDettaglioResponseDTO` usa `Double`) | basso |
| 15 | **ttrepo** | I vincoli `@Digits` accettano interi. Non manda importi a T&T-Repo | nessuno |
| 16 | **ce-palmari-comparatore** | Allineare il confronto, che oggi esclude `IMPORTO_CONTRASS` per "semantica diversa" | basso |
| 17 | builder, eurodis-mapper, eurodis-in, pacchi-tracking (TUP), state-machine, event-store, monitoring, retry-pread-completo, retry-normalizzazione | Nessuno | — |
| 18 | **ICD** (v12 → v13) | Dichiarare: centesimi per contrassegno, assicurata e `valore_spedizione`; cm interi per le dimensioni; unità del peso del collo; il significato di `versione_tracciato = 2`. Va scritto chiaramente che `pre-enrichment` resta in euro | basso, ma **va concordato con il cliente** |

**Dimensioni.** Bastano l'arrotondamento nel validatore e l'ICD:
- BEP riceve `"50"` invece di `"50.0"`;
- la troncatura nel mapper dei palmari non ha più effetto;
- SEW `dim_*` non cambia;
- EURODIS continua a mettere la larghezza (`width`) in `profondita`: va documentato.

## 5. Percorsi che non passano dal validatore

Sono quelli che fanno davvero il lavoro, perché qui la trascodifica centrale non arriva:

| Percorso | Topic | Gestione |
|---|---|---|
| adapter, fase 2 | `preadvising.enrichment` | produce la v2 da sé (punto 3) |
| esiti ldv-pdb e ldv-pdb-sync | `preadvising.enrichment` | ripassano il tracciato v2 ricevuto, con la correzione degli articoli (punto 6) |
| retry-eurodis, retry-id-cliente | `.completed.poste`, `completed` | lettura v1/v2 a valle (punto 12) |
| reinvio del bff | `enrichment`, `completed` | lettura v1/v2 a valle (punto 13) |
| retry-099 | `pre-enrichment` | il validatore riconosce la v2 (punto 11) |

## 6. Sistemi esterni

| Sistema | Impatto |
|---|---|
| Consumatori di `.completed.poste` e `.completed.sda` | **Da censire con il cliente**: nel codice non risultano. Devono leggere `versione_tracciato`, oppure adeguarsi insieme al rilascio. È il rischio principale |
| BEP/PDB | Nessuno, perché ldv-pdb e ldv-pdb-sync riconvertono in euro |
| SEW (Informix) | Nessuno sulle tabelle, perché il consumer riconverte in euro |
| Palmari (`AnaLdv`) | Nessuno, sono già in centesimi |
| `ce-vendite`, `ce-contratti` | Nessuno, perché `ce-dichiarato-ldv` riconverte prima della chiamata |

## 7. Rilascio e storico

**Ordine di rilascio**: prima chi legge, poi il validatore, che fa da interruttore.

1. Si rilasciano consumer SEW, smistatore, ldv, ldv-pdb, ldv-pdb-sync, bff, preavviso e il
   comparatore. Leggono **sia la v1 sia la v2** in base a `versione_tracciato`. Finché nessuno
   produce la v2, il comportamento resta quello di oggi.
2. Si rilascia l'adapter (fase 2 in v2, valore PDB in euro sul flusso normale) **insieme** al validatore.
3. **Rollback**: si ripristina la versione precedente di validatore e adapter. Chi legge continua a
   funzionare con entrambe le versioni.

Altre conseguenze:
- **Storico su Mongo** (`dichiarato_events`, `enrichment_events`): convivono documenti v1 e v2. Non
  serve una migrazione se i lettori decidono in base a `versione_tracciato`.
- **Lettura doppia**: resta finché i documenti v1 possono essere ritentati o reinviati; il periodo è
  da fissare, per esempio la retention dei retry.
- **Messaggi in coda al momento del passaggio**: non sono un problema, perché ogni messaggio porta la
  sua versione.

## 8. Test

- Un caso per ogni canale e famiglia di handler:
  - IF, IS, IE;
  - PDB_INVIOFILE, INVIOSYSTEM, INVIOEASY, STAMPAMASSIVA;
  - EUD_INVIOFILE, EUD_INVIOSYSTEM;
  - PDB, PDW, ILP;
  - MYSDA, SDA_WS, INVIO_WEB;
  - TUP, OMP.

  In ognuno contrassegno, assicurata e valore spedizione valorizzati, per verificare che arrivino
  in centesimi su `completed`.
- **Arrotondamenti**: importi con 3 decimali (eredità di `decimal(10,3)`), soglie al limite
  (4999.99, 99999.999, 1500 per CIN) e importo 0, che il sync oggi invia come `"0.00"`.
- **BEP**: request con APT000918, 919, 955, 956 e `waybillTotalValue` in euro; la LDV creata deve
  avere gli importi giusti.
- **SEW**: confronto prima/dopo su `importo_ass`, `importo_contrass` e `valore_dich`, che devono
  restare identici. Fa eccezione `valore_dich` PDB, che deve risultare corretto.
- **Palmari**: confronto con il comparatore, `AnaLdv` deve restare identico.
- **Retry e reinvio**: un documento v1 ritentato dopo il rilascio (punti 11-13) e un messaggio v2
  ripassato da retry-099, che non deve essere convertito due volte.
- **Dimensioni con decimali**: verso BEP e verso i palmari.

## 9. Decisioni e domande aperte

- **D1 `spedizione/valore` su `pre-enrichment`.** Oggi i canali SDA lo mandano in euro, l'adapter PDB
  in centesimi.
  - **Proposta**: l'adapter lo porta a euro (punto 2), così l'ingresso è omogeneo e il validatore
    converte allo stesso modo per tutti.
  - Alternativa: una conversione per canale nel validatore (PDB, PDW e ILP esclusi).
- **D2 Marcatore.** Proposta: `versione_tracciato = 2`, in alternativa a un campo nuovo dedicato.
  Va concordato con il cliente perché entra nell'ICD.
- **Q1** Chi consuma `.completed.poste` e `.completed.sda`, e se può leggere `versione_tracciato`.
- **Q2** In che unità arrivano gli importi OMP: nel campione `spedizione/valore` va da 1030 a 3279,
  interi. Chi produce il canale OMP, che non risulta nei repo.
- **Q3** In che unità sono `VALORE_SPEDIZIONE`, `IMPORTO_CONTRASSEGNO` e `IMPORTO_COPERTURA_FULL` nei
  file PDB (builder `pdb_csv.ini`, che li passa invariati). Oggi verso BEP si assume l'euro.
- **Q4** ILP: l'adapter passa `articolo/valore` in euro, ma l'ICD lo vuole in centesimi. Si corregge
  insieme o resta fuori?
- **Q5** In che unità è il volume di `temp_ritiri_clienti` (oggi l×a×p, oppure 9999.99 se il ritiro è
  voluminoso).
