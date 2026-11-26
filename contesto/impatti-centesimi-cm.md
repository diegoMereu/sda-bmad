# Importi in centesimi e dimensioni in cm: impatti

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
