# `producer-sew-sped` — Documento funzionale per lo sviluppo (int. 09, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 · **Fase**: 1 · **Versione**: 0.1 · **Data**: 2026-11-16
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del batch
**Repository**: `gitlab.alm.poste.it/esiti/sda-ldv-preadv-consumer`, modulo `producer-sew-sped` (lo stesso repo di `consumer-sew_sped`)
**Branch**: `146073_compliance_usa_fase1` da **`origin/dev202508_preadvising`**. Il repo non ha
`develop`, `origin/master` contiene solo il `README` e `dev202508_preadvising2` non ha il modulo
producer (verificato con git il 16-11). È lo stesso branch dell'int. 07: i due moduli si sviluppano
insieme. Lo sviluppo non si fa mai su `dev202508_preadvising` o `master`, né su branch di altre iniziative.
**Copie locali**: `gitposte/SDA/ESITI/sda-ldv-preadv-consumer` è la più aggiornata. Per l'altra copia
vale la nota di [consumer-sew-sped.md](consumer-sew-sped.md).
**Stack**: Java 8, `KafkaProducer<String, JsonNode>`, Jackson (`Include.NON_NULL`), JDBC Informix,
`sdaKafkaLibrary` (`SdaProducer`). Batch a esecuzione singola (`main` → `System.exit(0)`), schedulato
fuori dal repo.
**Generato da**: [prompt-producer-sew-sped.md](prompt-producer-sew-sped.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" (**vincolante**); HLD fase 1, int. 09;
codice di `origin/dev202508_preadvising` letto il 16-11. **DDL**: [ddl-sew-146073.md](ddl-sew-146073.md)

Etichette: **[FATTO]**, **[DECISO]**, **[ASSUNTO]** (ID e default, sezione 10).

---

## 1. Individuazione del producer (PA-06)

HLD, int. 09 "Adeguamento producer dati da portali e webservice": "deve essere modificato il batch che
prende i dati di preavviso dei portali e dei webservice per inviare anche i 3 nuovi campi: modifica
producer kafka".

**Candidato: `producer-sew-sped`. Grado di certezza: alto** (PRD-01). È un batch, legge i preavvisi
dalle tabelle SEW scritte dai canali SDA e li pubblica su Kafka nella catena:

| Indizio [FATTO, codice] | Dove |
|---|---|
| È un batch: una passata e poi `System.exit(0)`; legge con watermark in `properties_pt_online` (`${data_ins}`, `${progressivo}`, `${controllo}`) | `App.main`, `App.runProducer` |
| Le query di lettura stanno nelle properties `select.query.*` (con `.table`). Le tabelle sorgente gestite nel codice sono `sew_spedizioni_work`, `sew_spedizioni_work_2`, `cli_dati_stampa_tf(_2)` e `sew_sped_pre_adv_online_out_tot`; dopo l'invio, se `update.enabled`, si imposta `flag_trasmesso_sew='S'` | `QueriesManagerDao.getRecordsToSend`, update candidati |
| Il canale del messaggio dipende dal canale di origine: `WS` → `SDA_WS` (**web service**), `MYS` → `MYSDA` e `IWN` → `INVIO_WEB` (**portali**), `CLI_DATI_STAMPA_TF` → `IF`, altrimenti `IS` | `QueriesManagerDao.mapRowToTopic` |
| `SDA_WS` e `INVIO_WEB` sono canali configurati nella catena | `ce-dichiarato-orchestratore` `application.yaml`, values dello smistatore |
| `id_file` è sempre `null` e `id_preadvising` è un UUID nuovo. Il consumer, quando riceve un messaggio senza `id_file`, lo tratta come "dato che per SDA nasce su Ermes" e aggiorna la riga di origine | `mapRowToTopic`; `consumer-sew_sped` `App.processRecord` |

Non è uno strumento di replay o di migrazione: il watermark e il flag `flag_trasmesso_sew` ne fanno un
flusso continuo. Il **topic** sta nelle properties (`kafka.topic`). Ci si aspetta
`preadvising.pre-enrichment` o il topic d'ingresso del builder: va verificato (PRD-07).

**Esclusi** (ricerca del 16-11 in `gitposte/SDA`: `KafkaProducer`/`KafkaTemplate` e riferimenti a
`sew_spedizioni_work`, `cli_dati_stampa_tf`, `PRE_WEB`):

| Candidato | Perché no |
|---|---|
| Servizi `ce-*` di `preadvising/` e `CORRIERE-ESPRESSO/` (builder, adapter, orchestratore, `ce-ermes-event`, retry…) | producono dentro la catena e non leggono SEW né tabelle dei portali. Il builder è fuori perimetro; l'adapter (PDB, PDW `PRE_WEB`, ILP) è l'int. 05 |
| `consumer-sew-sped-pre-adv-on-out-tot` | consumer dei palmari (AS-06) |
| `Internazionale/partner-ear` (PARTNER-DAS) | legge `cli_dati_stampa_tf` con MyBatis, ma non produce su Kafka |
| `gitposte/SDA/ESITI/sda-ldv-preadv-consumer` | stesso repo remoto di `preadvising/sda-ldv-preadv-consumer`, copia più aggiornata |
| `Altro/` | solo driver e strumenti |

## 2. Interventi HLD coperti

| Int. | Cosa chiede | Dove |
|---|---|---|
| 09 | il batch invia anche i 3 nuovi campi (0,45) | sezioni 3, 4, 5 |

## 3. Come lavora oggi il batch [FATTO, codice]

- Per ogni `select.query.*`: legge il watermark, sostituisce il segnaposto, esegue la SELECT (fino a
  `batch.size`) e trasforma ogni riga in un `TopicDTO` (`mapRowToTopic`).
- Il mapping è **per nome di colonna, se presente**: `setTextIfColumnPresent(setter, rs, "colonna", …)`
  usa `rs.findColumn`. Una colonna assente dal ResultSet non valorizza il campo. Una colonna presente
  ma `NULL`, o con il testo `NULL`, diventa `""`.
- Una riga produce una spedizione con un collo. `mapCollo` mette in `articolo` un **solo articolo
  segnaposto** (`posizione ""`, `codice_taric ""`, `valore 0`…): le tabelle sorgente non hanno articoli.
- Serializzazione con `Include.NON_NULL`: i campi `null` non compaiono nel JSON.
- Header: `traceId` = `id_preadvising`, `fileId` vuoto.

## 4. Dove si interviene nel codice

| Punto | Cosa si fa |
|---|---|
| `dto/SpedizioneDTO.java` | `String account_key`, `String declaration_id`, con getter e setter |
| `dto/ArticoloDTO.java` | `String product_id`, con getter e setter, per simmetria del contratto. In fase 1 resta `null` (PRD-04) |
| `dao/QueriesManagerDao.mapSpedizione` | lettura delle colonne `account_key` e `declaration_id` se presenti nel ResultSet, con una variante di `setTextIfColumnPresent` che lascia **`null`** il valore vuoto o `NULL` (non `""`), così il campo resta fuori dal JSON (R-05). Nessun trim oltre a quello del valore letto (PRD-02) |
| `spedCols` di `mapSpedizione` | aggiungere `account_key` e `declaration_id` all'elenco delle colonne che "attivano" la spedizione (solo per completezza) |
| properties `select.query.*` (fuori repo) | se la SELECT elenca le colonne, aggiungere `account_key, declaration_id`; con `SELECT *` non serve (PRD-06) |
| `mapCollo` / `mapArticolo` | **nessuna modifica** in fase 1 (PRD-04) |

## 5. Mapping colonna → campo JSON

| Tabella sorgente.colonna | Campo JSON (AS-01) | Regola |
|---|---|---|
| `sew_spedizioni_work.account_key`, `sew_spedizioni_work_2.account_key` (DDL int. 07) | `spedizione[0].account_key` | se la colonna c'è ed è valorizzata; altrimenti il campo non si invia |
| `….declaration_id` | `spedizione[0].declaration_id` | idem; in fase 1 è sempre vuoto, quindi il campo non c'è |
| `cli_dati_stampa_tf(_2)`, `sew_sped_pre_adv_online_out_tot` | — | non hanno le colonne: nessun campo (PRD-03) |
| (nessuna sorgente) | `spedizione[0].collo[0].articolo[].product_id` | non inviato (PRD-04) |

## 6. Esempio [dati inventati]

Riga di `sew_spedizioni_work` con `id_canale = 'MYS'`, `id_ldv = 'TST146073003'` e
`account_key = 'AK0…03'` (52 caratteri). La SELECT è `SELECT * …`.

Messaggio (estratto):

```json
{
  "canale": "MYSDA", "flag_autoproduttore": "S", "id_preadvising": "<uuid>",
  "spedizione": [{
    "account_key": "AK00000000000000000000000000000000000000000000000003",
    "collo": [{ "id_ldv": "TST146073003", "articolo": [ { "posizione": "", "codice_taric": "", "valore": 0 } ] }]
  }]
}
```

La stessa riga con `account_key` `NULL`: il JSON è identico a quello di oggi, senza `account_key` né
`declaration_id`.

## 7. Configurazione e prerequisiti

- **DDL dell'int. 07 prima del rilascio** ([ddl-sew-146073.md](ddl-sew-146073.md), script 1 e 2): sono
  le stesse colonne che legge il producer. Con `SELECT *` il codice nuovo funziona anche senza DDL,
  perché la colonna è assente e il campo non si invia. Con una SELECT che elenca le colonne, invece, la
  query va aggiornata solo dopo la DDL.
- Le properties del batch sono fuori repo: chi le gestisce aggiorna `select.query.*` se serve.
- Chi valorizza `account_key` nelle tabelle sorgente sono i portali e il web service (MySDA, Invio Web,
  SDA WS), che sono fuori dal perimetro di Accenture (PRD-05). Finché non lo fanno, il batch invia il
  campo solo per righe di test valorizzate a mano.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Data la riga dell'esempio, il messaggio ha `spedizione[0].account_key` uguale alla colonna, 52 caratteri |
| AC-02 | Data una riga con `account_key` `NULL` o `''`, il messaggio non contiene `account_key` (né `""` né `null`) |
| AC-03 | Data una SELECT senza le colonne nuove, il messaggio è identico a quello di oggi |
| AC-04 | Data una riga con `declaration_id = 'DECL-TEST-0003'`, il messaggio contiene `declaration_id` |
| AC-05 | Le righe di `cli_dati_stampa_tf` (canale `IF`) e di `sew_sped_pre_adv_online_out_tot` producono messaggi identici a oggi |
| AC-06 | Canali, watermark, `flag_trasmesso_sew` e header sono invariati |
| AC-07 | Il messaggio con `account_key` attraversa la catena in svil e arriva in `sew_spedizioni_work` con lo stesso valore (insieme a int. 07) |
| AC-08 | Nessun log riporta il valore di `account_key` |

## 9. Casi di test

Nessun test automatico nel repo. Le prove si fanno in svil, su Informix di sviluppo, con
`producer.send.enabled=false` (DRY-RUN, il payload finisce nel log) per i controlli sul JSON, e poi con
invio reale.

| TC | Input | Atteso | AC |
|---|---|---|---|
| TC-01 | riga di test con `account_key`, DRY-RUN | JSON con `account_key` | AC-01 |
| TC-02 | `account_key` `NULL`; `''` | campo assente | AC-02 |
| TC-03 | properties con una SELECT a colonne esplicite, senza le nuove | JSON uguale a prima | AC-03 |
| TC-04 | `declaration_id` valorizzato a mano | campo presente | AC-04 |
| TC-05 | sorgente `CLI_DATI_STAMPA_TF` | regressione | AC-05 |
| TC-06 | due esecuzioni consecutive | watermark e flag avanzano come oggi | AC-06 |
| TC-07 | invio reale e catena svil fino alla SEW | valore conservato | AC-07 |

Nota: il DRY-RUN scrive nel log il JSON intero, che contiene dati della spedizione. Va usato solo con
righe di test e non contraddice AC-08, che vale per i log applicativi.

## 10. Assunzioni e domande aperte

Dal contratto: AS-01, AS-04, AS-05, AS-06.

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| PRD-01 | **Il batch dell'int. 09 è `producer-sew-sped`**, con certezza alta (sezione 1) | si sviluppa qui | Poste / Diego |
| PRD-02 | I campi si leggono dalle colonne omonime della riga sorgente (`account_key`, `declaration_id`) e si inviano solo se valorizzati | come detto | — |
| PRD-03 | Tabelle sorgente coperte: solo `sew_spedizioni_work` e `_2`, che hanno le colonne grazie alla DDL dell'int. 07. `cli_dati_stampa_tf(_2)` (canale `IF`) e `sew_sped_pre_adv_online_out_tot` no | nessuna DDL su quelle tabelle | Poste |
| PRD-04 | **Product ID senza sorgente**: le tabelle lette hanno una riga per LDV e l'articolo inviato è un segnaposto. Il producer non può inviare un `product_id` per articolo finché i portali non scrivono gli articoli da qualche parte (vedi SEW-02, variante B) | non inviato | Poste |
| PRD-05 | **Chi scrive `account_key` nelle tabelle sorgente**: i portali e il web service, fuori perimetro. Senza di loro l'int. 09 trasporta un campo sempre vuoto | da chiedere a Poste chi adegua i portali | Poste |
| PRD-06 | **SELECT nelle properties**: non sono nel repo. Se elencano le colonne vanno aggiornate | aggiornamento a cura di chi gestisce le properties, dopo la DDL | Diego |
| PRD-07 | **Topic di destinazione** (`kafka.topic`) e schedulazione del batch | da leggere sulle properties dell'ambiente | Diego |

## 11. Riferimenti

- [consumer-sew-sped.md](consumer-sew-sped.md) (int. 07, stesso repo e stesso branch).
- [ddl-sew-146073.md](ddl-sew-146073.md).
- [analisi.md](../analisi.md), PA-06.
