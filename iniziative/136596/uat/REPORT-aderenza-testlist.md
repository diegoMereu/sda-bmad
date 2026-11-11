# 136596 - Verifica di aderenza della test list UAT (EURODIS API)

**Data**: 2026-11-11 · **Oggetto**: `testlist.md` (602 casi, 85 scenari), derivata dal foglio
`SpecificaDiTest` di `TOTALE_ST_SDA_136596_Eurodis_Autoproduttore_v1.xlsx`.
**Confrontata con**: SF 0.4, DP 0.2, `ce-dichiarato-eurodis-in` 0.6.1, `ce-dichiarato-eurodis-mapper` 0.4,
`ce-eurodis-send-tracking` 0.2, `risposte-eurodis-2026-11-10.md`,
`risposte-test-autoproduttore-2026-11-10.md`, `integrazione-ldv-pdb-sync.md`,
`esiti-adapter-eud-inviosystem.md`, `contesto/microservizi-preadvising.md`.
**Limiti**: confronto tra documenti, nessun test eseguito. Le specifiche sono bozze mai provate
su PostgreSQL, Kafka e BEP veri.

## 1. Esito

- Le fasi di `-in` e del mapper (scarico, mapping, chiusura scarico) sono in buona parte allineate.
- La parte a valle (validatore, orchestratore, BEP, adapter, normalizzatore, smistatore, ERMES, monitoring)
  è ereditata dal flusso a file: l'atteso è generico e identico in tutti gli scenari.
- 15 scenari "KO VALID" non hanno un atteso determinabile; circa 20 scenari sono su perimetro dubbio.
- Mancano alcune coperture (sezione 5).

Ogni scenario aggiunge al modello comune solo la riga I3 (dati di input) e la riga O4 (verifica
specifica): tutto il resto è lo stesso testo.

## 2. Cosa è allineato

- Header e chiave di `preadvising.eud.pre.build`; eventi `ST_F0002`/`ST_F0005` su `preadvising.evensource`
  (senza "t") prima delle spedizioni.
- Mapping: `id_ldv` da `deliveryPartnerBarcode`, `id_ldv_itz` dal primo `europlateBarcode` non vuoto e
  diverso da `"0"`, peso in grammi, `flag_autoproduttore = "S"`, `canale = EUD_INVIOSYSTEM`.
- Retry Kafka di `-in` (5 minuti, poi ogni 2, fino a 10 tentativi) e backoff del mapper (3 tentativi da 2 s).
- ShedLock a 2 pod, reinvio, ripubblicazione, rilettura puntuale entro 60 giorni.
- Scarto `destinatario_assente` (C031-32, C047, C049, C066) e warning (C067-73).

## 3. Problemi aperti

### 3.1 Atteso a valle generico
- KO BEP 114/115 (C050-51): non dicono quale errore atteso né quale evento.
- Scenari KO "VALID": la fase Validazione dice ancora "in assenza di errori pubblica su enrichment".
- Codici APT attesi: nel file compaiono solo `APT000901` e `APT000918`; la tabella 6.8 del mapper dà
  906/907/908/910/911. Gli scenari C011-C015 e le combinazioni C018-C025 dovrebbero dichiarare il codice atteso.

### 3.2 Quindici scenari "KO VALID" non determinabili (superato: vedi 4ter)
C026-30, C033-36, C038-39, C042, C044-46. Usano le regole VR-xx e i record RT_xx del flusso a file.
Il mapper non applica le VR-xx; `shipmentTypeIndicator` e `lineHaulIndicator` sono ignorati per decisione
(DF-15); "Address type" non esiste nell'API. Serve la corrispondenza con le regole di `PDB_INVIOSYSTEM`
del validatore (le specifiche non la dicono).

### 3.3 Scenari su perimetro dubbio (superato: vedi 4ter)
- Dipendono da dati non presenti o non mappati: C002, C003 (shipment type), C008 (preavviso RT_65, non
  mappato per l'Open Point 29 della SF).
- ADR, non mappato dal mapper (SF Open Point 18): C017, C039, C042, C046.
- Punto Poste, fuori fase 1 nel mapper: C010, C021.
- Sono già marcati nel testo "DA DECIDERE se tenere la catena": da spostare in una sezione "fuori
  perimetro / in attesa di decisione".

### 3.4 Residui del flusso a file
- `ms-dichiarato-normalizzatore` (27 occorrenze): il nome reale del servizio non è nei documenti letti.
- "Mongo" compare 152 volte. Per `-in` la persistenza è PostgreSQL, ma l'adapter cerca ancora il
  preadvising su Mongo per `rif_spedizione`: non va tolto ovunque, va ricondotto per componente.
- Smistatore (TC009): il test prevede i Palmari; la SF 0.4 li esclude.
- ERMES (TC011, `consumer-sew-sped-poste`): non è nel DP; le risposte del 10-11 lo danno "DA DEFINIRE".
- Monitoring: topic e console "da capire"; `tipo_lavorazione: "????"` in TC005; Magic Kafka "DA DEFINIRE".

### 3.5 Incongruenza `ldv-pdb`
TC005 attribuisce a `ce-dichiarato-ldv-pdb` una chiamata sincrona a SAP-BEP.
- Il DP (flusso 14) dice che `ldv-pdb` invoca `waybillCreate` in modo sincrono.
- `integrazione-ldv-pdb-sync.md` dice che `ldv-pdb` è asincrono verso BEP e che `waybillCreate` è di
  `ldv-pdb-sync`. Il percorso `ldv-pdb` è deciso da Diego (10-11, commit `07c13d0`).
- Va chiarito prima di riscrivere TC005/TC006, perché cambia anche la forma del callback di esito
  (`code_externalId` oppure `walletRequestId`).

### 3.6 Contraddizioni tra documenti (a monte dei test)
- Punto Poste: la SF lo mappa su `APT000947`, il mapper no.
- Default di peso e dimensioni: la SF li assegna al validatore; le note su `ldv-pdb` dicono che non esistono
  (C005, C069).
- Il mock scrive la LDV in `consignorsColloBarcode`, non in `deliveryPartnerBarcode`.
- `ce-eurodis-send-tracking.md` sez. 2 dice ancora `collo.id_ldv ← consignorsColloBarcode`.
- `GetShipmentResponse2` (schema degli endpoint) non contiene `deliveryPartnerBarcode`: da verificare su payload reale.

## 4. Pulizia meccanica già applicata a `testlist.md`

Backup del testo originale non versionato; il file è sotto git come untracked. Modifiche:

| Intervento | Occorrenze |
|---|---|
| `ms-dichiarato-validatore/orchestratore/adapter` → `ce-dichiarato-*` | 121 righe |
| span `eurodis-in.get` → `eurodis.receive_pan.get` (nome della specifica `-in`, sez. 9) | 72 righe |
| Sistema/Fornitore "OP: DA CONFERMARE" → SDA-NEW / ACN (microservizi nuovi ACN) | 238 casi |
| Metriche del mapper allineate: `eurodis_mapper_spedizioni_total{esito=pubblicata}`; scarto con `esito=non_mappabile, motivo=destinatario_assente` | 53 righe |
| Warning C067-73 con la metrica specifica (`campo_mancante_total{campo=...}` oppure `avvisi_total{motivo=...}`) | 7 scenari |
| Stati finali dello scarico risolti: 404/array vuoto → `NESSUNA_SPEDIZIONE`, 401/424/451/500/timeout → `ERRORE_CHIAMATA`, grezzo non JSON → `NON_ELABORABILE`, Kafka giù → `NESSUN_INVIO` | 10 scenari |
| C053: da "KO risorsa non trovata" a "OK, nessuna spedizione nuova" (404 è esito regolare, senza alert, span senza errore: RF-05, RNF-04) | 1 scenario |
| C054, C062: nessun evento `ST_F0002/ST_F0005` (nessun file fittizio) | 2 scenari |
| `numeroRecord` = numero di spedizioni del grezzo, comprese le non identificabili (C052: 3; C065: 2) | 2 righe |
| `ce-anagrafica` in errore (C073): il mapper pubblica comunque, senza retry (RF-15) | 1 riga |
| `eurodis_richieste_manuali`: esito = stato dello scarico di rilettura (RECUPERO) o esito del reinvio (RIPUBBLICA) (C078) | 1 riga |

Dopo la pulizia restano 84 "DA VERIFICARE" sul fuso orario (EURODIS conferma lo stesso dello scambio
FTP; il valore è da verificare sui dati) e circa 30 altri, tutti su punti davvero aperti.
Il giro md → xlsx → md è ancora identico; il file Excel non è stato rigenerato.

## 4bis. Scenari aggiunti (2026-11-11)

C086-C091: dogana (`customsService`, EUR e CHF) e merci pericolose ADR (monocollo, multicollo, con dogana, con contrassegno),
catena completa come C001. Sono test di osservazione: mapper e ICD non coprono questi dati (PA-13), l'atteso
va riconfermato dopo la decisione sul mapping. I dati li genera EURODIS (`eurodis-test-scenarios-en.md`, sezione G, S60-S65).

## 4ter. Revisione del 2026-11-11 (regole VR-xx, scenari non mappati)

**VR-xx**: eliminati i 15 scenari "KO VALID" basati sulle VR-xx del flusso a file (C026-30, C033-36, C038-39, C042, C044-46)
e C017 (ADR, sostituito da C088-C091). Tolti i riferimenti "ex VR-xx" dai titoli e dai testi degli altri scenari.
Gli ID eliminati non sono riusati.

**Nuovi casi sulle regole del canale `PDB_INVIOSYSTEM`** (da `ce-dichiarato-validatore`, file `ce-pdb-rules.drl`,
109 regole; il canale `EUD_INVIOSYSTEM` oggi non è nel file: solo `EUD_INVIOFILE`, la SF prevede di riprendere le regole
di `PDB_INVIOSYSTEM`). Catena a 5 fasi come i vecchi KO; atteso: `PREAD_EMESSO` (ST_R0002), poi
`PREADVISING_PARZIALE_E_BLOCCATO` (ST_R0006) con il codice d'errore, nessun messaggio su `preadvising.enrichment`, Mongo stato 2.

| Scenario | Dato anomalo | Atteso |
|---|---|---|
| C092 | `shipperAddress` null (come i dati TEST) | 1023, 1024, 1039, 1051, 1052, 1063 |
| C093 | mittente: ragione sociale vuota | 1052 |
| C094 | mittente: CAP vuoto | 1023 |
| C095 | mittente: località vuota | 1024 |
| C096 | mittente: indirizzo vuoto | 1051 |
| C097 | mittente: codice paese vuoto | 1039, 1063 |
| C098 | destinatario: ragione sociale vuota | 1019 |
| C099 | destinatario: indirizzo vuoto | 1042 |
| C100 | destinatario: codice paese vuoto | 1064 |
| C101 | destinatario: ragione sociale > 40 caratteri | 1289 (da confermare) |
| C102 | destinatario: civico > 4 caratteri | 1292 (da confermare) |
| C103 | destinatario: località > 30 caratteri | 1294 (da confermare) |
| C104 | peso collo 10000 kg | 1083 |
| C105 | lunghezza collo 1000 cm | 1084 |
| C106 | `collis` null | 1173 |
| C107 | stessa `edReference`, LDV diversa | 1162 |
| C108 | stessa LDV, `edReference` diversa | 099, evento `PREAD_DUPLICATO` (ST_R0003) |

**Scenari esistenti aggiornati dalle regole**
- C005 (peso a zero) e C069 (peso assente): ora KO 1083 (la regola richiede peso > 0; la SF prevede invece i default di peso: da confermare).
- C077, C079 (stessa spedizione due volte): la seconda ricezione ha la stessa LDV, quindi 099 `PREAD_DUPLICATO` (chiude la parte aperta PA-27 per questo caso).
- C007: marcato "DA CONFERMARE", perché la SF prevede l'adeguamento ai limiti BEP mentre le regole rifiutano civico > 4 e località > 30.
- Corretto `ST_R000?` in `ST_R0003` e la nota su Mongo (il validatore scrive `dichiarato_events` e `preadvising_history`).

**Non mappato = osservazione** (stesso razionale di ADR): C002, C003 (`shipmentTypeIndicator` C e X), C008 (`consigneePreAdvice`),
C010, C021 (Punto Poste) diventano test di osservazione: atteso "dato non mappato, spedizione ordinaria", da riconfermare dopo la decisione sul mapping.
Nota di correzione: `shipmentTypeIndicator` è nel payload API (C = B2C, X = AUX-Pan); il testo precedente lo dava per assente.

**Ancora in attesa di decisione**: C081 (fallback `clearanceTimestamp`, DF-01) e C085 (sorgente del tracking, SF OP 35).

**Dipendenze**
- Il mock deve poter iniettare anomalie sui campi (indirizzi, pesi, dimensioni, `collis`, duplicati): oggi iniettare solo LDV vuota, duplicata o con check errato.
- Le regole di `EUD_INVIOSYSTEM` nel validatore: il branch è in verifica del Test Manager.

## 5. Coperture mancanti
- **Area di appoggio `/buffer`** (DP flusso 2, AC-23 della specifica `-in`): database giù con file pendente,
  job di recupero, metriche `eurodis_in_buffer_*`. Nessun test.
- **Limiti BEP** (città 30, nome 35, indirizzo 40, civico 4, telefono 15): C007 verifica solo che il mapper non
  tronca; l'adeguamento a valle (SF) non è testato.
- **Casi del mapper**: `deliveryService` A, D, 7, T, W; `no_firma` da `deliveryType`; note di consegna
  concatenate; mittente estero; `returnAddress` mai usato come destinatario; rilettura puntuale con 400/404.
- **`ce-eurodis-send-tracking`**: nuovo microservizio con la tabella 76 stati SDA → 24 codici EURODIS, ma un solo
  stub (C085).
- **Osservabilità**: un solo `trace_id` dal mapper al validatore (nota di integrazione); alert Datadog proposti.
- **Casi KO a 5 fasi**: la chiusura scarico non esplicita l'asimmetria "`-in` INVIATA, mapper scarta".

## 6. Prossimi passi
1. Sezione "fuori perimetro / in attesa di decisione" per gli scenari del punto 3.3 e, finché non c'è la
   corrispondenza con le regole, per quelli del punto 3.2.
2. Elenco di domande per Diego e Marzilli sui punti 3.2, 3.5 e 3.6.
3. Riscrittura delle fasi a valle per canale `EUD_INVIOSYSTEM`, dopo le risposte.
4. Test nuovi della sezione 5.
5. Rigenerare l'Excel con `md2xlsx.py` e controllare le tendine in Excel.
