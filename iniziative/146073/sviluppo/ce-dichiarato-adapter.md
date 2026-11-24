# `ce-dichiarato-adapter` — Documento funzionale per lo sviluppo (fase 1)

> **Rimandato al punto 2 della fase 1** (decisione di Diego del 2026-11-24): l'intervento non si
> sviluppa nel primo passo perché mancano ancora i dettagli (nomi dei campi nei messaggi
> sorgente PDB, PDW e ILP). Il documento resta allineato ai nomi `zonos_*` e va completato quando i dettagli arrivano.

**Iniziativa**: 146073 — Compliance USA Entry Type 13, **solo fase 1** · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del `ce-dichiarato-adapter`
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-adapter` (locale `gitposte/SDA/preadvising/ce-dichiarato-adapter`)
**Branch**: `develop` [DECISO, Diego 2026-11-24: sostituisce il branch dedicato `146073_compliance_usa_fase1` deciso il 16-11]. Mai sviluppo su `master` né su branch di altre iniziative
**Stack**: Spring Boot, Java 17, Spring Kafka, Jackson, Lombok
**Generato da**: [prompt-ce-dichiarato-adapter.md](prompt-ce-dichiarato-adapter.md)
**Fonti**: [analisi.md](../analisi.md), sezione "Contratto della fase 1" (AS-01…AS-06, **vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (int. 05) e `_fase_2.xlsx` (int. 05);
`cliente/20261116_descrizione_compliance_usa_entry_type_13.md`; codice di `origin/develop` al commit
`e615495` (12-11-2026), letto con `git show` il 16-11 (il `git fetch` del 16-11 non è riuscito: rete).

Etichette:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default; da confermare (sezione 11).

> **Aggiornamento 0.2 (2026-11-24).** Nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` (Diego, 23-11); colonne SEW con gli stessi nomi (Diego, 24-11); branch
> `develop` (Diego, 24-11).
>
> Il contratto della fase 1 (nomi e posizione dei campi nel tracciato unico, AS-01) viene da
> `analisi.md` e non si cambia. Questo documento lo applica all'adapter. Buchi e incoerenze sono fra
> le assunzioni ADA-xx.

---

## 1. Contesto e obiettivo

Le spedizioni verso gli USA con merce devono rispettare la normativa USA **Entry Type 13**.
In fase 1 il preavviso porta due campi nuovi, validati dal validatore e propagati fino alle SEW:

- **Account Key**: uno per spedizione, 52 caratteri;
- **Product ID**: uno per articolo, 1–255 caratteri.

Un terzo campo, **Declaration ID**, si predispone in fase 1 e si valorizza in fase 2 (Zonos).

L'adapter è uno degli **ingressi** della catena [FATTO, codice]: consuma tre sorgenti, converte ogni
messaggio nel tracciato unico (`DichiaratoOutputDTO`) e lo pubblica.

| Sorgente | Topic (values Helm) | Consumer | Mapper | Pubblica su |
|---|---|---|---|---|
| PDB/BEP | `PACCHI.BEP.ALL.ANAG_LDV` (`KAFKA_TOPIC_PDB`) | `KafkaConsumerPDB` | `PdbMapper` | flusso normale: `preadvising.pre-enrichment`; esiti BEP (fase 2 della catena, `enrichment_bep`): `preadvising.enrichment` |
| PDW | `PACCHI.PDW.TT.PREWEB` (`KAFKA_TOPIC_PDW`) | `KafkaConsumerPDW` | `PdwMapper` | `preadvising.pre-enrichment` |
| ILP | `PACCHI.ILP.ANAGLDV` (`KAFKA_TOPIC_ANAGLDV`, attivo con `KAFKA_ILP_ENABLED`, solo `messageInOutShipment` in `KAFKA_ILP_ALLOWED_SHIPMENTS`, default `inbound`) | `KafkaConsumerILP` | `IlpMapper` | `preadvising.pre-enrichment` |

`preadvising.pre-enrichment` è il valore di `KAFKA_TOPIC_DICHIARATO` (proprietà
`kafka.producer.topic.dichiarato-eventi`), `preadvising.enrichment` di `KAFKA_TOPIC_PREADVISING_ENRICHMENT`
[FATTO, `.helm/values.yaml`, `deploy-coll/values.yaml`].

All'adapter si chiede di **leggere i nuovi campi dai messaggi delle tre sorgenti e metterli nel
tracciato unico**: Account Key sulla testata della spedizione, ogni Product ID sul suo articolo,
`zonos_declaration_id` predisposto e sempre `null`.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Controllo di presenza e lunghezza, riconoscimento delle spedizioni soggette (R-01, R-02, R-03) | `ce-dichiarato-validatore` (int. 01) |
| Aggiunta dei campi nei messaggi di PDB, PDW e ILP | sistemi sorgente (ADA-01) |
| Ingresso da file e da API | `ce-dichiarato-builder` (team applicativo, AS-05) |
| Merge nell'orchestratore dei dati arrivati con gli esiti BEP | `ce-dichiarato-orchestratore` (int. 02, ADA-06) |
| Declaration ID valorizzato, dazi, fee, Zonos, invio a BEP | fase 2 (AS-06) |
| "Mapping verso PDB, IPER" della descrizione | nessuno in fase 1: vale l'HLD (ADA-09) |

## 2. Interventi HLD coperti

| Int. | Fase | Testo HLD [FATTO] | Copertura |
|---|---|---|---|
| 05 | 1 | "Deve essere adeguato il ms ce-dichiarato-adapter per la ricezione dei nuovi campi nei consumer in lettura pdb e pdw, ilp — modifica dei 3 consumer per acquisizione e propagazione dei nuovi campi" (stima 0,40) | tutto il documento |
| 05 | 2 | "ricezione del nuovo campo, non anticipabile in quanto essendo una ricezione integrata non conosciamo il nome del campo" (0,50) | **non in fase 1**: si predispone solo `zonos_declaration_id` nel DTO di uscita, senza leggerlo dalle sorgenti (5.4) |

Indicazioni della descrizione per l'adapter in fase 1 [FATTO]: Account Key a livello spedizione,
ogni Product ID sull'articolo corrispondente, campi assenti senza effetti sugli scenari non
applicabili. La voce "aggiornare i contratti e i mapping verso PDB, IPER" non corrisponde né all'HLD
né al codice (ADA-09).

## 3. Dove si interviene nel codice

Codice di `origin/develop` `e615495` [FATTO]. Le classi sono quelle esistenti; non servono classi nuove.

| Punto | Cosa c'è oggi | Cosa si fa |
|---|---|---|
| `kafka/dto/SpedizioneDTO.java` | DTO della spedizione del tracciato unico, `@JsonProperty` snake_case, nessun `@JsonInclude` (i `null` si serializzano) | due campi `String`: `accountKey` → `zonos_account_key`, `declarationId` → `zonos_declaration_id` |
| `kafka/dto/ArticoloDTO.java` | `@Builder @Data`: `valore`, `posizione`, `codice_taric`, `quantita`, `peso_totale`, `paese_origine`, `english_descr`, `ita_descr`, `valuta` | campo `String productId` → `zonos_product_id` |
| `kafka/dto/pdb/PdbMessageDTO.java` | messaggio BEP piatto (`code_externalId`, `booking_channel`, `contract_*`…), articoli in `customsDeclaration_items` | campo Account Key (nome sorgente provvisorio, 5.1) |
| `kafka/dto/pdb/DeclarationItem.java` | articolo BEP: `itemNumber`, `taric`, `totalValue`… (camelCase); `hasValidProperties()` scarta gli articoli tutti `null` | campo Product ID; **aggiungerlo a `hasValidProperties()`**, altrimenti un articolo con il solo Product ID viene scartato |
| `mapper/PdbMapper.java` | `toOutputPDB` (un messaggio = una spedizione con un collo); `convertToOutputItem` (articolo); `toOutputPDBFase2` unisce i messaggi dello stesso `code_externalId` (un messaggio per collo) e fa il merge della testata con `mergeSpedizioneScalarFields` (`mergeIfNull`) | Account Key in `toOutputPDB`; Product ID in `convertToOutputItem`; `accountKey` in `mergeSpedizioneScalarFields` (5.1) |
| `kafka/dto/pdw/PreWebDTO.java` | oggetto `PRE_WEB` (in `TRACES[].TRACE.PRE_WEB`), campi MAIUSCOLI (`ID_PRODOTTO`, `CONTENUTO`, `VALORE_DICH`…); nessuna lista di articoli | campi Account Key e Product ID (5.2) |
| `mapper/PdwMapper.java` | `toOutputPDW`: una traccia = una spedizione, un collo, **un solo articolo** costruito da `VALORE_DICH` (senza `posizione`) | Account Key sulla spedizione, Product ID sull'unico articolo |
| `kafka/dto/ilp/IlpContentDTO.java`, `IlpDeclarationItemDTO.java` | `content` camelCase, `services` è una mappa `{nome: {code}}` letta con `getServiceCode(nome)`; articoli in `customsDeclarationItems` (`itemNumber` intero) | campo Account Key in `content`, Product ID nell'articolo (5.3) |
| `mapper/IlpMapper.java` | `toOutputILP` (una `content` = una spedizione, un collo); `toArticolo` | Account Key sulla spedizione, Product ID in `toArticolo` |
| `service/Adapter*Service`, `PDBFase2Service`, `consumer/KafkaConsumer*` | serializzano `DichiaratoOutputDTO` e pubblicano | **nessuna modifica** |
| `mongo/model/*`, `PreadvisingEventsRepository` | lookup del preavviso per gli esiti BEP | **nessuna modifica** |
| test esistenti: `PdbMapperFase2Test`, `PdwMapperTest`, `IlpMapperTest`, `KafkaConsumerPDBTest`, `AdapterILPServiceTest`, `PDBFase2ServiceTest` | | casi nuovi della sezione 10 |

La deserializzazione usa l'`ObjectMapper` di Spring Boot, che ignora le proprietà sconosciute
[FATTO, nessuna configurazione contraria nel repo]: finché le sorgenti non mandano i campi, o se li
mandano con un nome diverso, il messaggio si elabora come oggi e i campi escono `null`.

> Nota: la copia locale di `develop` ha 2 commit di Diego del 30-10 non presenti su `origin/develop`
> (`c4a26d1` fix PDW ritiro e codici nazione, `1a6202d` mapping PDB e PRE_WEB). Toccano `PdwMapper`,
> `PdbMapper`, `SpedizioneDTO`. Il branch parte da `origin/develop`; i due commit non si includono
> (ADA-10).

## 4. Il contratto in uscita (tracciato unico) [DECISO, AS-01]

```json
{
  "spedizione": [{
    "zonos_account_key": "<52 caratteri>",
    "zonos_declaration_id": null,
    "collo": [{
      "articolo": [
        { "posizione": "1", "codice_taric": "...", "zonos_product_id": "<1-255 caratteri>" }
      ]
    }]
  }]
}
```

- `zonos_account_key` e `zonos_declaration_id` su ogni elemento di `spedizione[]`; `zonos_product_id` su ogni elemento di
  `spedizione[].collo[].articolo[]`.
- Tutti `String`, opzionali, senza default. Nel JSON in uscita compaiono anche quando sono `null`,
  come gli altri campi del DTO (nessun `@JsonInclude`): va bene per R-05, i consumer a valle tollerano
  campi in più (l'adapter già inietta la proprietà "canary" `x_canary_*` per verificarlo).

## 5. Regole e mapping

### 5.0 Regole comuni

| ID | Regola |
|---|---|
| RF-01 | Valori copiati **così come arrivano**: niente `trim`, maiuscolo, troncamento, ricalcolo; stringa vuota resta stringa vuota (R-04). La validazione la fa il validatore |
| RF-02 | Campo assente o `null` nella sorgente → `null` nel tracciato, nessun errore, nessun log WARN (R-05) |
| RF-03 | Il Product ID resta sull'**articolo da cui viene**: stesso elemento, stessa `posizione`, stesso collo. L'ordine degli articoli non cambia |
| RF-04 | L'adapter non valida e non scarta: nessun controllo su lunghezza o obbligatorietà, nessun riconoscimento delle spedizioni USA |
| RF-05 | `zonos_declaration_id` sempre `null` in fase 1, per tutte le sorgenti (5.4) |
| RF-06 | Nessuna modifica ai campi esistenti: in particolare `ID_PRODOTTO` (PDW) e `services.product` (ILP) restano `codice_prodotto` (ADA-03) |

### 5.1 PDB/BEP (`PdbMessageDTO`)

Oggi nei messaggi BEP **non c'è** nessun campo per Account Key, Product ID o Declaration ID [FATTO:
`PdbMessageDTO`, `DeclarationItem`, `esempi/pdb/esempio.json`, `documenti/Mapping_anag_ldv_tracciato_unico.md`;
l'unico "account" è `contract_accountOwner` = intestatario del conto, che non c'entra]. Nomi provvisori
(ADA-01, ADA-02):

| Campo sorgente (provvisorio) | Livello sorgente | Campo tracciato unico | Punto del codice |
|---|---|---|---|
| `code_accountKey` | radice del messaggio (un messaggio = un collo) | `spedizione[0].zonos_account_key` | `toOutputPDB` |
| `customsDeclaration_items[].productId` | articolo | `collo[0].articolo[i].zonos_product_id` (stesso `i`, `posizione` = `itemNumber`) | `convertToOutputItem` |

Regole specifiche:
- `DeclarationItem.hasValidProperties()` considera anche `productId` (un articolo con il solo Product ID
  passa).
- **Esiti BEP (`toOutputPDBFase2`)**: i messaggi dello stesso `code_externalId` (uno per collo) diventano
  una spedizione. I colli si concatenano: ogni collo porta i suoi articoli con i loro Product ID (RF-03).
  `zonos_account_key` della spedizione = il primo non `null` fra i messaggi, nell'ordine di arrivo
  (`mergeIfNull` in `mergeSpedizioneScalarFields`). Se i messaggi hanno Account Key diverse, vince la
  prima e si scrive un log WARN con `code_externalId` e numero di valori distinti, **senza i valori** (ADA-05).
- Il flusso dei callback POU per `walletRequestId` passa dallo stesso `toOutputPDBFase2`: nessuna regola in più.
- Negli esiti BEP i campi valgono solo se BEP li rimanda. Se non li rimanda escono `null`, e
  l'orchestratore non deve sovrascrivere con `null` i valori arrivati dal builder (ADA-06).

### 5.2 PDW (`PRE_WEB`)

Oggi `PRE_WEB` **non ha** campi per Account Key, Product ID o Declaration ID [FATTO: `PreWebDTO`,
`esempi/pdw/*.json`, `documenti/Mapping_pre_web_tracciato_unico.md`]. `ID_PRODOTTO` è il codice
prodotto SDA (`codice_prodotto`, poi sovrascritto dal lookup ce-rules), non il Product ID di Entry
Type 13 (ADA-03). PDW non ha una lista di articoli: il mapper crea un solo articolo con il valore dichiarato.

| Campo sorgente (provvisorio) | Livello sorgente | Campo tracciato unico |
|---|---|---|
| `ACCOUNT_KEY` | `PRE_WEB` (una traccia = una spedizione) | `spedizione[0].zonos_account_key` |
| `PRODUCT_ID` | `PRE_WEB` | `collo[0].articolo[0].zonos_product_id` (l'unico articolo) |

- L'articolo PDW oggi non ha `posizione`. Non la si inventa: resta `null` come oggi (ADA-04).
- Se PDW in futuro mandasse più articoli per spedizione, servirà una lista nel messaggio: fuori fase 1 (ADA-04).

### 5.3 ILP (`content`)

Oggi il messaggio ILP **non ha** campi per Account Key, Product ID o Declaration ID [FATTO:
`IlpContentDTO`, `IlpDeclarationItemDTO`, `esempi/ilp/*.json`]. `services.product.code` è il codice
prodotto (`codice_prodotto`), non il Product ID (ADA-03).

| Campo sorgente (provvisorio) | Livello sorgente | Campo tracciato unico |
|---|---|---|
| `content.accountKey` | `content` (una `content` = una spedizione) | `spedizione[0].zonos_account_key` |
| `content.customsDeclarationItems[].productId` | articolo | `collo[0].articolo[i].zonos_product_id` (stesso `i`; `posizione` = `itemNumber`, se presente) |

- Lo stile camelCase segue quello di `content`. Non si usa la mappa `services` (`{nome: {code}}`):
  è per i codici servizio e non è per articolo (ADA-02).
- ILP oggi elabora solo `inbound` (spedizioni in arrivo in Italia): una spedizione ILP diretta negli USA
  è improbabile. Si mappa comunque, per non dipendere dalla configurazione (ADA-07).
- `IlpMapper.toArticoli` non scarta gli articoli: un articolo con il solo Product ID passa già.

### 5.4 Declaration ID

Non si legge da nessuna sorgente: l'HLD fase 2 dice che il nome del campo non si conosce [FATTO].
In fase 1 c'è solo il campo `declarationId` in `SpedizioneDTO`, mai valorizzato dai mapper (RF-05),
che esce `"zonos_declaration_id": null`. In `mergeSpedizioneScalarFields` si aggiunge comunque il `mergeIfNull`,
così in fase 2 basta valorizzarlo nel mapper.

### 5.5 Nomi sorgente provvisori: come si scrivono nel codice

Si dichiarano con `@JsonProperty` sul nome provvisorio e `@JsonAlias` sulle varianti snake_case
(`zonos_account_key`, `zonos_product_id`), così un messaggio con i nomi del tracciato unico funziona già. Quando le
sorgenti confermano i nomi (ADA-01) si cambia solo l'annotazione e il test del mapper. Nessuna
proprietà di configurazione: un mapping a nomi configurabili costerebbe più dello 0,40 stimato e
complicherebbe i DTO (ADA-02).

## 6. Esempi [dati inventati]

### UC-01 — PDB, flusso normale, spedizione USA con 2 articoli

Ingresso (estratto, `PACCHI.BEP.ALL.ANAG_LDV`, lista con un messaggio):

```json
[{
  "code_barcode": "TST000000001", "code_externalId": "ORD-TEST-0001", "booking_channel": "WEBSERVICES",
  "code_accountKey": "AKTEST0000000000000000000000000000000000000000000001",
  "customsDeclaration_items": [
    { "itemNumber": "1", "taric": "6109100010", "totalValue": "25,00", "quantity": "2", "productId": "SKU-TEST-001" },
    { "itemNumber": "2", "taric": "4202920000", "totalValue": "40,00", "quantity": "1", "productId": "SKU-TEST-002" }
  ]
}]
```

Uscita su `preadvising.pre-enrichment` (estratto):

```json
{
  "canale": "PDB",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-0001",
    "zonos_account_key": "AKTEST0000000000000000000000000000000000000000000001",
    "zonos_declaration_id": null,
    "collo": [{
      "id_ldv": "TST000000001",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": 2, "zonos_product_id": "SKU-TEST-001" },
        { "posizione": "2", "codice_taric": "4202920000", "quantita": 1, "zonos_product_id": "SKU-TEST-002" }
      ]
    }]
  }]
}
```

(L'Account Key d'esempio è lunga 52 caratteri.)

### UC-02 — PDB, esiti BEP, spedizione di 2 colli

Due messaggi con lo stesso `code_externalId` `ORD-TEST-0002` e `booking_channel` `INVIOFILE`; il
preavviso si trova su Mongo. Collo A: `code_accountKey` = AK1, articolo 1 `productId` `SKU-A1`. Collo B:
`code_accountKey` assente, articoli 1 e 2 con `SKU-B1`, `SKU-B2`.

Uscita su `preadvising.enrichment` (`tipo_lavorazione` `enrichment_bep`): una spedizione,
`numero_colli` 2, `zonos_account_key` AK1, collo A con `[SKU-A1]`, collo B con `[SKU-B1, SKU-B2]`, nello stesso ordine.

### UC-03 — PDW

```json
{ "HEADER": { "channel": "PDW" },
  "TRACES": [ { "TRACE": { "PRE_WEB": {
    "ID_LDV": "TST000000003", "ID_PRODOTTO": "PRODTEST", "VALORE_DICH": 5000,
    "ACCOUNT_KEY": "AKTEST0000000000000000000000000000000000000000000003",
    "PRODUCT_ID": "SKU-TEST-003" } } } ] }
```

Uscita: `codice_prodotto` come oggi (dal lookup ce-rules o `PRODTEST`), `zonos_account_key` = il valore di
`ACCOUNT_KEY`, `collo[0].articolo[0]` = `{ "valore": 50, "posizione": null, "zonos_product_id": "SKU-TEST-003", ... }`.

### UC-04 — ILP

`content.accountKey` = AK4, `customsDeclarationItems` con 1 articolo senza `itemNumber` e
`productId` `SKU-TEST-004`. Uscita: `zonos_account_key` AK4, `articolo[0].posizione` `null`,
`articolo[0].zonos_product_id` `SKU-TEST-004`.

### UC-05 — Messaggio di oggi, senza i campi (tutte le sorgenti)

Uscita identica a quella di oggi più `"zonos_account_key": null`, `"zonos_declaration_id": null` sulla spedizione e
`"zonos_product_id": null` su ogni articolo. Nessun WARN, nessun errore.

### UC-06 — Valori "sporchi"

`code_accountKey` = `" AK… "` (con spazi) e `productId` = `""`: escono identici (RF-01). Lo scarto,
se la spedizione è soggetta, lo decide il validatore.

## 7. Configurazione

Nessuna proprietà nuova, nessuna modifica ai values Helm (`.helm/values.yaml`, `deploy-svil`,
`deploy-coll`, `deploy-config/values_TEMPLATE.yaml`). Topic e flag ILP restano quelli di oggi.

## 8. Requisiti non funzionali e osservabilità

- **Compatibilità**: nessun cambiamento per i messaggi senza i campi (UC-05). I test esistenti restano verdi.
- **Prestazioni**: impatto trascurabile, nessuna chiamata esterna in più.
- **Metriche**: un contatore `business_adapter_campi_usa_total` con tag `source` (`pdb`, `pdw`, `ilp`) e
  `campo` (`zonos_account_key`, `zonos_product_id`), incrementato quando il campo è valorizzato nel tracciato in uscita
  (per spedizione e per articolo). Serve a vedere quando le sorgenti cominciano a mandare i campi.
  Con `TraceUtil.incrementCounter`, che non deve mai far fallire la lavorazione.
- **Span**: nessuno span nuovo. Facoltativo l'attributo `usa.zonos_account_key.presente` (`true`/`false`) sullo
  span del mapper; **mai il valore** come attributo.
- **Log**: nessuna riga nuova con i valori. Oggi i consumer e i service loggano a INFO il payload intero
  in ingresso e il JSON in uscita, quindi Account Key e Product ID finiranno nei log come gli altri campi.
  Se l'Account Key fosse una credenziale, quei log andrebbero mascherati (ADA-08).
- **Sonar**: nessun letterale ripetuto (nomi dei tag della metrica in costanti), complessità di
  `toOutputPDB` e `toOutputPDW` invariata (estrarre un metodo se serve), niente commenti con riferimenti a
  punti aperti o documenti di analisi.

## 9. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato UC-01, il tracciato pubblicato su `preadvising.pre-enrichment` ha `zonos_account_key` uguale al valore in ingresso e `zonos_product_id` `SKU-TEST-001` sull'articolo `posizione` 1 e `SKU-TEST-002` su `posizione` 2 |
| AC-02 | Dato UC-02, il tracciato su `preadvising.enrichment` ha una spedizione con 2 colli, `zonos_account_key` AK1, e ogni Product ID sul suo collo e articolo, nell'ordine di ingresso |
| AC-03 | Dato UC-02 con AK1 sul collo A e AK2 sul collo B, `zonos_account_key` è AK1 e c'è un log WARN con `code_externalId`, senza i valori |
| AC-04 | Dato un articolo PDB con il solo `productId` valorizzato, l'articolo è nel tracciato con `zonos_product_id` (non viene scartato da `hasValidProperties`) |
| AC-05 | Dato UC-03, `zonos_account_key` e `collo[0].articolo[0].zonos_product_id` sono valorizzati; `codice_prodotto` è quello di oggi |
| AC-06 | Dato UC-04, `zonos_account_key` e `zonos_product_id` sono valorizzati e `posizione` è `null` |
| AC-07 | Dato UC-05 per ognuna delle tre sorgenti, il tracciato è uguale a quello di oggi più `zonos_account_key`, `zonos_declaration_id` e `zonos_product_id` a `null`; nessun WARN |
| AC-08 | Dato UC-06, i valori escono identici a quelli in ingresso (spazi e stringa vuota inclusi) |
| AC-09 | `zonos_declaration_id` è `null` in ogni tracciato pubblicato, anche se il messaggio sorgente contiene un campo `declarationId` o `DECLARATION_ID` |
| AC-10 | Un messaggio con i nomi del tracciato unico (`zonos_account_key`, `zonos_product_id`) nelle sorgenti viene letto come quello con i nomi provvisori (`@JsonAlias`) |
| AC-11 | Il contatore `business_adapter_campi_usa_total` cresce di 1 per UC-03 su `zonos_account_key` e di 2 per UC-01 su `zonos_product_id`; un errore della metrica non blocca la pubblicazione |
| AC-12 | Nessun valore di Account Key o Product ID compare in log nuovi, attributi di span o tag di metrica |
| AC-13 | I test esistenti del repo sono verdi senza modifiche alle asserzioni esistenti |

## 10. Casi di test

Test unitari sui mapper con messaggi inventati (gli esempi di `esempi/` e `src/test/resources/` arricchiti
con i campi, copiati in risorse di test nuove); poi test integrato in svil.

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit `PdbMapper` | UC-01 | AC-01 | AC-01 |
| TC-02 | unit `PdbMapperFase2Test` | UC-02; variante con Account Key diverse | AC-02, AC-03 | AC-02, AC-03 |
| TC-03 | unit `PdbMapper` | articolo con il solo `productId`; articolo tutto `null` | il primo c'è, il secondo no | AC-04 |
| TC-04 | unit `PdwMapperTest` | UC-03 | AC-05 | AC-05 |
| TC-05 | unit `IlpMapperTest` | UC-04; 3 articoli con Product ID distinti | AC-06, ordine e posizione | AC-06 |
| TC-06 | unit (parametrico, 3 sorgenti) | esempi di oggi senza i campi | AC-07 | AC-07 |
| TC-07 | unit | UC-06 | AC-08 | AC-08 |
| TC-08 | unit | sorgente con `declarationId`/`DECLARATION_ID` | AC-09 | AC-09 |
| TC-09 | unit (deserializzazione) | nomi provvisori e alias | AC-10 | AC-10 |
| TC-10 | unit (`SimpleMeterRegistry`) | UC-01, UC-03 | AC-11 | AC-11 |
| TC-11 | unit (log capture) | UC-01, TC-02 variante | AC-12 | AC-12 |
| TC-12 | regressione | `mvn -o test` | verde | AC-13 |
| TC-13 | integrato svil | un messaggio a mano per sorgente su `PACCHI.BEP.ALL.ANAG_LDV`, `PACCHI.PDW.TT.PREWEB`, `PACCHI.ILP.ANAGLDV` | campi su `preadvising.pre-enrichment` e, con validatore e orchestratore adeguati, fino a `preadvising.completed` | AC-01, AC-05, AC-06 |

Per TC-13 valgono le regole di [contesto/test-integrati.md](../../../contesto/test-integrati.md) sui topic
condivisi di svil. Se i sistemi sorgente non mandano ancora i campi, i messaggi si costruiscono a mano
con i nomi provvisori (AS-05).

## 11. Assunzioni e domande aperte

Da `analisi.md` (vincolanti): AS-01 (nomi e posizione nel tracciato), AS-05 (ingresso da PDB, PDW, ILP
attraverso l'adapter con i nomi di AS-01), AS-06 (fuori dalla fase 1). AS-02, AS-03, AS-04 non toccano
l'adapter.

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| ADA-01 | **Nomi dei campi nei messaggi sorgente.** PDB/BEP, PDW (`PRE_WEB`) e ILP oggi non hanno Account Key, Product ID, Declaration ID: i sistemi sorgente devono aggiungerli. Servono nome, livello (testata/articolo) e formato per ciascuno | provvisori: PDB `code_accountKey` + `customsDeclaration_items[].productId`; PDW `ACCOUNT_KEY` + `PRODUCT_ID`; ILP `content.accountKey` + `customsDeclarationItems[].productId` (5.1–5.3) | Poste (team PDB/BEP, PDW, ILP) |
| ADA-02 | **Mapping non configurabile.** I nomi provvisori stanno nelle annotazioni Jackson, con alias snake_case; quando arrivano i nomi veri si cambia l'annotazione | `@JsonProperty` + `@JsonAlias`, nessuna proprietà | Diego |
| ADA-03 | **Omonimi.** `ID_PRODOTTO` (PDW) e `services.product` (ILP) sono codici prodotto SDA, non il Product ID di Entry Type 13: non si riusano | restano su `codice_prodotto` | Poste |
| ADA-04 | **PDW ha un solo articolo**, senza `posizione`: il Product ID va su quello. R-03 chiede la posizione dell'articolo nell'errore | `posizione` resta `null`; il validatore usa l'indice nella lista. Se PDW deve gestire più articoli, serve una lista nel messaggio (fuori fase 1) | Poste (PDW), funzionale del validatore |
| ADA-05 | **Account Key diverse fra i colli** della stessa spedizione negli esiti BEP | vince la prima non `null`, WARN senza valori | Poste |
| ADA-06 | **Esiti BEP senza i campi.** Se BEP non rimanda Account Key e Product ID, l'`enrichment_bep` li porta `null`: l'orchestratore non deve cancellare i valori arrivati dal builder | l'adapter pubblica quello che riceve; il merge è nel funzionale dell'orchestratore (int. 02) | Winston / funzionale orchestratore |
| ADA-07 | **ILP e USA.** ILP elabora solo `inbound`: una spedizione ILP diretta negli USA è improbabile. Il consumer ILP rientra nell'HLD, quindi si adegua | si mappa comunque | Poste |
| ADA-08 | **Natura dell'Account Key.** Se è una credenziale (chiave Zonos del cliente) e non un identificativo, i log INFO di oggi con il payload intero la esporrebbero | trattata come dato non segreto; nessun mascheramento in fase 1 | Poste |
| ADA-09 | **"Mapping verso PDB, IPER"** della descrizione: l'HLD int. 05 e il codice dicono che l'adapter legge da PDB, PDW e ILP e pubblica sul tracciato unico. Non c'è un mapping verso IPER | vale l'HLD: solo ingresso | Poste |
| ADA-10 | **Commit locali non pubblicati.** La copia locale di `develop` ha `c4a26d1` e `1a6202d` (30-10, Diego) che non sono su `origin/develop` e toccano gli stessi mapper | branch da `origin/develop` senza quei commit | Diego |
| ADA-11 | **Declaration ID dalle sorgenti in fase 2**: l'HLD fase 2 int. 05 dice che il nome "non si conosce"; non è chiaro se arriva da PDB/PDW/ILP o solo da Zonos | in fase 1 non si legge (5.4) | Poste |

## 12. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1, interventi HLD, punti aperti PA-01…PA-11.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md): catena e topic.
- [contesto/linee-guida-sviluppo.md](../../../contesto/linee-guida-sviluppo.md): stack, Sonar, osservabilità, branch.
- Repo: `documenti/Mapping_anag_ldv_tracciato_unico.md`, `documenti/Mapping_pre_web_tracciato_unico.md`
  (da aggiornare con le righe nuove), `esempi/pdb`, `esempi/pdw`, `esempi/ilp`.
