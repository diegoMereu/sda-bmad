# `consumer-sew_sped_poste` — Documento funzionale per lo sviluppo (int. 08, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 · **Fase**: 1 · **Versione**: 0.1 · **Data**: 2026-11-16
**Autrice**: Mary (analyst), DDL con Winston · **Destinatario**: sviluppatore del consumer
**Repository**: `gitlab.alm.poste.it/esiti/poste-ldv-preadv-consumer` (locale `gitposte/SDA/ESITI/poste-ldv-preadv-consumer`), modulo `consumer-sew_sped_poste`
**Branch**: `146073_compliance_usa_fase1` da **`origin/develop`** (`03f66b9` del 10-11, verificato con git
il 16-11). Lo sviluppo non si fa mai su `develop` o `master`, né su branch di altre iniziative
(`dev202511_preadvising_extend`, `dev20261013_handling_storico_oneri`, `dev202610_prodotto_a_valore`…).
**Stack**: Java 8, client Kafka, Jackson, JDBC Informix (`ifxjdbc` 3.70.JC7X1), SQL dinamico (`MERGE …
FROM SYSMASTER:'informix'.SYSDUAL`). Progetto Eclipse senza `pom.xml`. Nessun test automatico nel repo.
**Generato da**: [prompt-consumer-sew-sped-poste.md](prompt-consumer-sew-sped-poste.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" AS-01…AS-06 (**vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx`, int. 08; codice di `origin/develop` letto il 16-11;
`campi_tabelle_PDB.md` nella radice del repo (non versionato: mappatura colonna → campo Kafka di
`QueriesManagerDao`). **DDL**: [ddl-sew-146073.md](ddl-sew-146073.md)

Etichette: **[FATTO]** (HLD o codice, con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]**
(ID e default, da confermare nella sezione 10).

> Il contratto della fase 1 non si cambia. Le differenze fra il codice e il contratto sono fra le
> assunzioni SWP-xx.

---

## 1. Contesto e obiettivo

`consumer-sew_sped_poste` legge i preavvisi completati con destinazione Poste. Il topic atteso è
`preadvising.completed.poste`, uscita Poste dello smistatore; `kafka.topic` sta nelle properties
esterne. Il consumer li scrive nelle tabelle SEW Poste su Informix. I nomi delle tabelle arrivano dalle
properties `kafka.tabella.*` (file esterno al repo) e sostituiscono `${TABLE}` (`sqlWithTable`) [FATTO, `App`]:

| Property | Tabella logica | Scritta per |
|---|---|---|
| `kafka.tabella.main` | `SEW_SPEDIZIONI_POSTE` | ogni messaggio (MERGE su `ID_LDV`) |
| `kafka.tabella.extender` | `SEW_SPEDIZIONI_POSTE_EXTENDER` | ogni messaggio (MERGE su `FK_ID_RECORD`) |
| `kafka.tabella.inter` | `SEW_SPEDIZIONI_POSTE_INTER` | **una riga per articolo**, solo nei rami internazionali PRTN |
| `kafka.tabella.articolo` | `PRTN_ARTICOLO` | una riga per articolo, solo nei rami PRTN |
| `kafka.tabella.collo`, `.spedizione` | `PRTN_COLLO`, `PRTN_SPEDIZIONE` | rami PRTN |
| `kafka.tabella.scarto`, `.interscarto` | scarto extender, scarto inter | messaggi in errore |
| `.ldvinter`, `.time`, `.dhlscarti` | associazioni LDV internazionali, `TIMEDEF_ARCH`, scarti DHL | casi particolari |

Con l'int. 08 il consumer deve **storicizzare in `sew_spedizioni_poste` i 3 nuovi campi** [FATTO, HLD].
È l'unico intervento della fase 1 con impatto Database (foglio Impatti: 241 Database, M50).

| Campo (AS-01) | Livello | Fase 1 |
|---|---|---|
| `account_key` | `spedizione[]` | valorizzato per le spedizioni soggette, 52 caratteri |
| `declaration_id` | `spedizione[]` | solo predisposto: sempre assente o `null` |
| `product_id` | `spedizione[].collo[].articolo[]` | ogni articolo delle spedizioni soggette, da 1 a 255 caratteri |

**Non fa**: validazione, Zonos, PRTN verso i vettori (SWP-02), palmari, stampe (AS-06).

## 2. Interventi HLD coperti

| Int. | Titolo HLD | Cosa chiede | Dove |
|---|---|---|---|
| 08 | Adeguamento consumer `sew_spedizioni_poste` | "I 3 nuovi campi … devono essere storicizzati dentro la tabella `sew_spedizioni_poste`: modifica del consumer kafka per ricevere e storicizzare i 3 nuovi campi" (0,32 + Database medio) | sezioni 4, 5, 7 |

## 3. Come lavora oggi il consumer [FATTO, codice]

- `App` sceglie il DAO dal canale: `PDW` → `QueriesManagerDao2`, `PDB` e tutti gli altri → `QueriesManagerDao`.
  Prima `normalizzaCanale` porta `PDB_xxx` ed `EUD_xxx` a `KFK`.
- **Tabella main**: `prepareInsertIntoSewSpedizioniPoste(topicDTO, canale)`, uno per DAO, costruisce
  il MERGE con quattro `StringBuilder` (`fields` `SSP.X`, `fakeFields` `FAKE.X`, `fieldsEquality`
  `SSP.X = FAKE.X`, `valuesAndFields` `"valore" AS X`). Una colonna entra nello statement **solo se il
  valore non è null o blank** (`isNullOrBlank`). Esempio di `NUM_ORDINE` in `QueriesManagerDao`:

  ```java
  if (!isNullOrBlank(numOrdine)) {
      fields.append("SSP.NUM_ORDINE, ");
      fakeFields.append("FAKE.NUM_ORDINE, ");
      fieldsEquality.append("SSP.NUM_ORDINE = FAKE.NUM_ORDINE, ");
      values.append("\"").append(numOrdine).append("\", ");
      valuesAndFields.append("\"").append(numOrdine).append("\" AS NUM_ORDINE, ");
  }
  ```

- I valori sono letterali fra doppi apici concatenati nello statement, non parametri JDBC. Tutto lo
  statement passa poi da `cleanString`, che sostituisce `’` con `'` ed `€` con `E` e **toglie ogni
  carattere fuori da `[\x20-\x7e]`**. Molti campi passano anche da `cleanDoubleQuotesForInsert`
  (`"` → `'`, via `\`).
- **Articoli**: solo in `QueriesManagerDao`, solo nei rami PRTN (MADRE, FIGLIO, ALTRO internazionale:
  prefisso LDV `5U`/`6U`/`7U`/`8U`, esclusi DHL, EURODIS e `id_ldv_itz(2)`; vedi `campi_tabelle_PDB.md`,
  "Condizione generale per il blocco PRTN"). Per ogni `collo[0].articolo[]`:
  - `prepareInsertIntoSewInter(cd, idExt, false)` scrive su `SEW_SPEDIZIONI_POSTE_INTER`
    (`FK_SEW_SPE_EXT`, `ITEMNUMBER` = `posizione`, `TARIC`, `QUANTITY`, `TOTALVALUE`, …);
  - `prepareInsertIntoPrtnArticolo(cd, idCollo)` scrive su `PRTN_ARTICOLO` (`ARTICOLO` è sempre `1`,
    senza posizione).
- **Scarto**: nel `catch`, `prepareInsertIntoSewInter(cd, id, true)` scrive gli articoli nella tabella
  `kafka.tabella.interscarto`, con lo **stesso metodo**.
- `QueriesManagerDao2` (PDW) non scrive articoli.
- Il mapper Jackson ignora i campi sconosciuti (`FAIL_ON_UNKNOWN_PROPERTIES = false`) e non distingue
  maiuscole e minuscole nei nomi.

## 4. Dove si interviene nel codice

| Punto | Cosa si fa |
|---|---|
| `dto/SpedizioneDTO.java` | `String account_key`, `String declaration_id`, con getter e setter nello stile del file |
| `dto/ArticoloColloDTO.java` | `String product_id`, con getter e setter |
| `dao/QueriesManagerDao.prepareInsertIntoSewSpedizioniPoste` | due blocchi come `NUM_ORDINE`, per `ACCOUNT_KEY` e `DECLARATION_ID`, da `spedizione[0]`, aggiunti in coda ai campi opzionali. Valore con l'escape della sezione 5 |
| `dao/QueriesManagerDao2.prepareInsertIntoSewSpedizioniPoste` (PDW) | gli stessi due blocchi |
| `dao/QueriesManagerDao.prepareInsertIntoSewInter` | blocco `if (!isNullOrBlank(cd.getProduct_id()))` → `fields.append("PRODUCT_ID, ")`, `values.append("\"" + escape(product_id) + "\", ")`. Il metodo serve sia `INTER` che `INTERSCARTO`: le due tabelle hanno bisogno della colonna (DDL, script 4) |
| `prepareInsertIntoPrtnArticolo`, extender, `prepareInsertIntoSewScarto`, `…PosteOLD` | **nessuna modifica** (SWP-02, SWP-04) |
| log | se serve, solo `account_key=presente/assente` e il numero di articoli con `product_id`, mai i valori |

Prima di committare: niente letterali ripetuti (Sonar S1192) e niente riferimenti a PA o documenti nei commenti.

## 5. Mapping campo JSON → colonna

| Campo JSON (AS-01) | DTO | Tabella.colonna | Tipo (DDL) | Regola |
|---|---|---|---|---|
| `spedizione[0].account_key` | `SpedizioneDTO.account_key` | `SEW_SPEDIZIONI_POSTE.ACCOUNT_KEY` | `VARCHAR(52)` | inserita solo se non blank, come le altre colonne; nessun trim né troncamento |
| `spedizione[0].declaration_id` | `SpedizioneDTO.declaration_id` | `SEW_SPEDIZIONI_POSTE.DECLARATION_ID` | `VARCHAR(64)` (SEW-03) | idem; in fase 1 assente, quindi la colonna resta `NULL` |
| `spedizione[0].collo[0].articolo[i].product_id` | `ArticoloColloDTO.product_id` | `SEW_SPEDIZIONI_POSTE_INTER.PRODUCT_ID` (e `…INTER` scarto) | `VARCHAR(255)` | una riga per articolo, accanto a `ITEMNUMBER` = `posizione` |

**Escape** (SWP-07): per i tre campi nuovi il doppio apice si raddoppia (`"` → `""`, letterale Informix
fra doppi apici), così il valore arriva intatto. Non si usa `cleanDoubleQuotesForInsert`, che
trasformerebbe `"` in `'`. Resta l'effetto di `cleanString` su tutto lo statement: i caratteri non
ASCII stampabili vengono tolti (SWP-08).

**MERGE e ripetizioni**: se un messaggio successivo della stessa LDV arriva senza `account_key`, la
colonna non entra nello statement e il valore salvato resta. È il comportamento di tutte le colonne (SWP-06).

## 6. Esempi [dati inventati]

Messaggio (estratto), canale `PDB`, LDV internazionale nel ramo MADRE:

```json
{
  "canale": "PDB",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-146073-02",
    "account_key": "AK00000000000000000000000000000000000000000000000002",
    "internazionale": { "vettore": "UPS" },
    "collo": [{
      "id_ldv": "6UTST1460730002",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": 2, "product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": 1, "product_id": "PRD \"TEST\" 0002" }
      ]
    }]
  }]
}
```

Frammento atteso nel MERGE su main:
`… "AK0…02" AS ACCOUNT_KEY …`, poi `WHEN NOT MATCHED THEN INSERT (…, SSP.ACCOUNT_KEY) …`. Non c'è
`DECLARATION_ID` perché è assente.

Righe attese:
- `SEW_SPEDIZIONI_POSTE`: `ACCOUNT_KEY = 'AK0…02'`, `DECLARATION_ID = NULL`.
- `SEW_SPEDIZIONI_POSTE_INTER`:
  - `ITEMNUMBER = '1'`, `PRODUCT_ID = 'PRD-TEST-0001'`;
  - `ITEMNUMBER = '2'`, `PRODUCT_ID = 'PRD "TEST" 0002'` (doppio apice conservato).
- `PRTN_ARTICOLO`: invariato.

## 7. Configurazione e prerequisiti

- **DDL prima del rilascio**: [ddl-sew-146073.md](ddl-sew-146073.md), script 3 e 4. Le colonne entrano
  nello statement solo se valorizzate, ma il primo messaggio USA fallirebbe senza DDL e finirebbe nello
  scarto.
- I **nomi reali** delle tabelle stanno nelle properties dell'ambiente (`kafka.tabella.main`,
  `.inter`, `.interscarto`): la DDL va fatta su quelli (SWP-09).
- Nessuna property nuova.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato l'esempio della sezione 6, `SEW_SPEDIZIONI_POSTE.ACCOUNT_KEY` è uguale al valore ricevuto (52 caratteri) e `DECLARATION_ID` è `NULL` |
| AC-02 | Dato l'esempio, `SEW_SPEDIZIONI_POSTE_INTER` ha 2 righe con `ITEMNUMBER` 1 e 2 e il `PRODUCT_ID` del rispettivo articolo; il doppio apice dell'articolo 2 è conservato |
| AC-03 | Lo stesso messaggio con canale `PDW` scrive `ACCOUNT_KEY` sulla main (`QueriesManagerDao2`) |
| AC-04 | Dato un messaggio con `declaration_id: "DECL-TEST-0002"`, `DECLARATION_ID` vale `DECL-TEST-0002` |
| AC-05 | Dato un messaggio senza i campi nuovi (non USA o storico), gli statement sono identici a prima: nessuna colonna nuova nel MERGE né nell'insert inter (R-05) |
| AC-06 | Dato un articolo senza `product_id` in una spedizione con altri articoli valorizzati, solo quella riga ha `PRODUCT_ID` `NULL` |
| AC-07 | Dato un messaggio che finisce nello scarto, gli articoli scritti nella tabella inter scarto hanno `PRODUCT_ID` |
| AC-08 | `PRTN_ARTICOLO`, `PRTN_COLLO`, `PRTN_SPEDIZIONE` ed extender sono scritti come prima |
| AC-09 | Nei log non compaiono i valori di `account_key` e `product_id` |
| AC-10 | Ricevendo due volte lo stesso messaggio, la main resta con una riga (MERGE) e `ACCOUNT_KEY` invariato |

## 9. Casi di test

Nessun test automatico nel repo. Le prove si fanno in svil, su Informix di sviluppo, con messaggi
costruiti a mano sul topic del consumer e LDV di test. Si possono aggiungere test unitari dei metodi
`prepareInsertInto…`, che restituiscono `fields` e `values` come stringhe e quindi si provano senza
database, se il team li vuole introdurre.

| TC | Input | Atteso | AC |
|---|---|---|---|
| TC-01 | sezione 6, canale PDB | main e inter valorizzate | AC-01, AC-02 |
| TC-02 | sezione 6, canale PDW | main valorizzata | AC-03 |
| TC-03 | `declaration_id` valorizzato | salvato | AC-04 |
| TC-04 | messaggio storico senza campi nuovi; spedizione nazionale | statement uguali a prima (confronto dello statement loggato) | AC-05 |
| TC-05 | 3 articoli, il secondo senza `product_id` | `NULL` solo sul secondo | AC-06 |
| TC-06 | messaggio che va in errore dopo il MERGE (es. lookup PRTN mancante) | inter scarto con `PRODUCT_ID` | AC-07 |
| TC-07 | regressione su un messaggio internazionale con articoli già usato nei test | PRTN ed extender invariati | AC-08 |
| TC-08 | log di TC-01 | nessun valore | AC-09 |
| TC-09 | TC-01 due volte | una riga main | AC-10 |
| TC-10 | catena completa in svil: preavviso USA verso Poste fino alla SEW | campi uguali a quelli inviati | AC-01, AC-02 |

## 10. Assunzioni e domande aperte

Dal contratto: AS-01, AS-04, AS-05, AS-06. Comuni con [consumer-sew-sped.md](consumer-sew-sped.md):
SEW-03 (`declaration_id` `VARCHAR(64)`).

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| SWP-01 | `account_key` e `declaration_id` stanno sulla tabella main, come dice l'HLD, e non sull'extender, che pure ha i dati internazionali | main (`kafka.tabella.main`), in entrambi i DAO | Poste |
| SWP-02 | **Tabella articoli.** Ce ne sono due. `SEW_SPEDIZIONI_POSTE_INTER` è la SEW per articolo, con `ITEMNUMBER` = `posizione`. `PRTN_ARTICOLO` (`kafka.tabella.articolo`) è la tabella partner verso il vettore: `ARTICOLO` è sempre `1` e non c'è la posizione, quindi il legame con l'articolo si perderebbe (R-04) | `PRODUCT_ID` su `SEW_SPEDIZIONI_POSTE_INTER` (e inter scarto). `PRTN_ARTICOLO` non si tocca in fase 1 | Poste |
| SWP-03 | **Copertura del Product ID.** Gli articoli si scrivono solo nei rami PRTN di `QueriesManagerDao` (LDV `5U`-`8U`, esclusi DHL, EURODIS e `id_ldv_itz(2)`), mai per PDW. Una spedizione USA fuori da quei rami non salva il `product_id` | nessun ramo nuovo: si salva dove gli articoli si scrivono già | Poste / Diego |
| SWP-04 | Tabella scarto main (`kafka.tabella.scarto`, costruita da `…PosteOLD` + extender): nessuna colonna nuova. La inter scarto invece sì, perché il metodo è condiviso | come detto | Poste |
| SWP-05 | Extender non toccato | — | Poste |
| SWP-06 | Il MERGE non cancella un valore già salvato se il messaggio successivo non ha il campo | comportamento standard del consumer | Diego |
| SWP-07 | **Escape**: per i campi nuovi `"` → `""`, invece di `cleanDoubleQuotesForInsert`, per non alterare il valore (R-04) | `""` | — |
| SWP-08 | **Caratteri non ASCII**: `cleanString` li toglie da tutto lo statement, quindi anche da `product_id`. Contraddice R-04 per i Product ID con caratteri accentati o speciali | accettato per la fase 1; il validatore non vieta i non ASCII | Poste |
| SWP-09 | **Nomi reali delle tabelle** nelle properties di svil, collaudo e produzione (es. varianti `_2`) | DDL sui nomi logici, da allineare | Diego / DBA |
| SWP-10 | **Topic** `preadvising.completed.poste` | da verificare sulle properties | Diego |

## 11. Riferimenti

- [analisi.md](../analisi.md), "Contratto della fase 1".
- [ddl-sew-146073.md](ddl-sew-146073.md).
- `campi_tabelle_PDB.md` nel repo (non versionato): mappatura completa delle colonne.
- [consumer-sew-sped.md](consumer-sew-sped.md), [producer-sew-sped.md](producer-sew-sped.md).
