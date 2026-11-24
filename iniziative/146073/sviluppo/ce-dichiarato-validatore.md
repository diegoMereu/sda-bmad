# `ce-dichiarato-validatore` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del validatore (Amelia)
**Intervento HLD**: 01 della fase 1, stima TOW 1.2 di 0,80
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-validatore` (in locale `gitposte/SDA/preadvising/ce-dichiarato-validatore`)
**Branch**: `develop` [DECISO, Diego 2026-11-24: sostituisce il branch dedicato `146073_compliance_usa_fase1` deciso il 16-11]. Ultimo commit letto `68083fb` del 13-11. Non si sviluppa su `master` né sui branch di altre iniziative (es. `feature/eurodis-canale-eud-inviosystem`, che oggi è in checkout nella copia locale): in quel caso si usa un `git worktree` separato.
**Stack**: Spring Boot 3, Java 17, Kafka, Drools (KIE), MongoDB
**Generato da**: [prompt-ce-dichiarato-validatore.md](prompt-ce-dichiarato-validatore.md)
**Fonti**: [analisi.md](../analisi.md), sezione "Contratto della fase 1" (AS-01…AS-06, **vincolante**); `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (intervento 01); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md` (§4 `ce-dichiarato-validatore`, §5, §6); codice di `origin/develop` (`68083fb`), letto il 16-11 senza checkout

Etichette usate nel documento:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default. Va confermata (sezione 12).

> **Il contratto della fase 1 (AS-01…AS-07 di `analisi.md`) non si cambia.** Questo documento lo
> dettaglia per il validatore. La versione 0.2 recepisce le decisioni di Diego del 2026-11-23: nomi
> `zonos_*` dei campi, regola senza la condizione "cliente business", prodotti su `codice_prodotto` o
> `id_servizio`, descrizioni degli errori. I buchi e le incoerenze trovati nel codice sono fra le assunzioni
> (VAL-AS-10 e seguenti) e le domande aperte.

---

## 1. Contesto e obiettivo

Le spedizioni verso gli USA che contengono merce devono rispettare la normativa USA
**Entry Type 13**. Nella fase 1 il preavviso porta due campi nuovi [FATTO, descrizione §2]:

- **Account Key**: uno per spedizione, di 52 caratteri;
- **Product ID**: uno per articolo, da 1 a 255 caratteri.

Il validatore legge il tracciato unico da `preadvising.pre-enrichment`. Se il tracciato è valido,
lo pubblica su `preadvising.enrichment`. All'event store manda gli stati su `preadvising.evensource`.
L'intervento 01 chiede al validatore tre cose [FATTO, HLD fase 1]:

1. **estendere i DTO** con i campi nuovi. Senza questa modifica i campi **si perdono**: vedi 3.1;
2. **riconoscere le spedizioni soggette**, cioè dirette negli USA, con merce e con un prodotto
   interessato (AS-02);
3. **validare presenza e lunghezza** dei due campi sulle spedizioni soggette, con un errore che
   indica il campo e, per il Product ID, l'articolo (R-02, R-03, AS-03).

C'è anche `zonos_declaration_id`: in fase 1 è solo **predisposto**. Si aggiunge al DTO e si propaga così
come arriva (sempre assente o `null`), senza regole (AS-01).

**Non fa**:

| Fuori perimetro | Riferimento |
|---|---|
| Lookup in anagrafica e chiamate a Zonos per validare i valori | R-02 |
| Normalizzazione, `trim`, conversione o ricalcolo dei campi | R-04 |
| Valorizzazione del Declaration ID, dazi e fee | AS-06 (fase 2) |
| Acquisizione dei campi dai canali (builder, adapter) | AS-05 |
| Propagazione a valle (orchestratore, smistatore, event store, SEW) | funzionali degli altri microservizi |

## 2. Requisiti e interventi HLD coperti

| Fonte | Cosa chiede | Dove nel documento |
|---|---|---|
| HLD fase 1, int. 01: "Modifica dto del applicativo" | campi nuovi nei DTO, propagazione | 3.1, 5.1 |
| HLD fase 1, int. 01: "logica per riconoscere queste spedizioni" | riconoscimento delle spedizioni soggette | 5.2 |
| HLD fase 1, int. 01: "implementare nuove logiche di validazione" | regole su Account Key e Product ID | 5.3, 5.4 |
| Descrizione §4: Account Key in testata, Product ID negli articoli | cardinalità | 5.1 |
| Descrizione §4: errore puntuale per campo e articolo | descrizione dell'errore | 5.4 |
| Descrizione §4: nessun lookup, nessuna chiamata a Zonos | solo controlli formali | 5.3 |
| Descrizione §5: nessuna incompatibilità con eventi storici e scenari non USA | campi opzionali | 5.1, 5.2 |
| Descrizione §6: casi di test minimi della fase 1 che riguardano il validatore | casi di test | 11 |

## 3. Dove si interviene nel codice

Indicazioni sul codice di `origin/develop` (`68083fb`) [FATTO, letto il 16-11]. I nomi delle classi
nuove sono proposte.

### 3.1 DTO e serializzazione: oggi i campi non dichiarati si perdono

- L'`ObjectMapper` del servizio ha `FAIL_ON_UNKNOWN_PROPERTIES = false` (`config/AppConfig.java`).
  Un campo che non è nel DTO viene **ignorato in lettura** senza errori.
- `KafkaConsumer.execute` deserializza il messaggio in `DichiaratoDTO`. In uscita
  `FlussoHandler.processaMessaggioValido` pubblica su `preadvising.enrichment` il JSON del DTO
  tipizzato (`objectMapper.writeValueAsString(dichiaratoDTO)`).
- Anche gli altri punti partono dal DTO: l'evento per l'event store (`EventStorePayloadUtil.buildEventData`,
  `valueToTree(dto)`), il salvataggio su Mongo `dichiarato_events` (`PreadvisingEvents`, che contiene
  `List<SpedizioneDTO>`) e i cloni del multicollo (`LdvUtil.clonaConLdvFiglia`,
  `SdaFlussoHandler.clonaConSingoloCollo`, con un giro JSON → DTO).

**Quindi oggi `zonos_account_key`, `zonos_declaration_id` e `zonos_product_id` arrivano dal builder ma non escono dal
validatore**: non vanno su `preadvising.enrichment`, sull'event store e su Mongo. Una volta
aggiunti ai DTO, tutti questi punti li riportano senza altre modifiche.

| Classe (`kafka/dto/`) | Cosa c'è oggi | Cosa si fa |
|---|---|---|
| `SpedizioneDTO` | testata della spedizione: campi snake_case con getter Lombok (es. `id_servizio`, `codice_prodotto`, `tipo_merce`), `importiDto` (`@JsonProperty("importi")`), `destinatario`, `List<ColloDTO> collo` | `private String zonos_account_key;` e `private String zonos_declaration_id;`, oppure campi camelCase con `@JsonProperty("zonos_account_key")` e `@JsonProperty("zonos_declaration_id")` |
| `ColloDTO` | `@Valid List<ArticoloDTO> articolo` | nessuna modifica |
| `ArticoloDTO` | `posizione` (`@Size(max = 1)`), `codice_taric`, `valore`, `quantita`, `peso_totale`, `paese_origine`, `english_descr`, `ita_descr`, `valuta` | `private String zonos_product_id;` (oppure `@JsonProperty("zonos_product_id")`) |
| `DichiaratoDTO` | `errors` (`Map<String,String>`, chiave = codice), `warnings`, `canale`, `spedizione` | nessuna modifica |

Regole per i campi nuovi:
- tipo `String`, nessun default, nessuna trasformazione (AS-01, R-04);
- **nessuna annotazione Bean Validation** (`@Size`, `@NotBlank`). La regola semantica "Validazione
  annotazioni DTO" (`rules/semantic/validation-rules.drl`) valida tutto il DTO in cascata (`@Valid`).
  Un `@Size(max = 255)` farebbe quindi scattare un errore `_OBBL_…zonos_product_id` su **tutte** le spedizioni
  del flusso SDA, anche su quelle non soggette (VAL-AS-10);
- il `null` si serializza come oggi (l'`ObjectMapper` non ha `NON_NULL`): `zonos_declaration_id` esce come
  `"zonos_declaration_id": null`, in linea con l'esempio di AS-01;
- Lombok `@Data` mette i campi nel `toString()`. Il DTO finisce nei log in più punti, per esempio
  `salvaErroreRegole` lo logga **a WARN** (`payload: {}`). L'Account Key è una chiave del cliente e
  non deve finire nei log: si annota `@ToString.Exclude` su `zonos_account_key` (VAL-AS-11).

### 3.2 Come sono organizzate le regole oggi

| Insieme di regole | Dove | Come si carica | Chi lo usa |
|---|---|---|---|
| **semantic** (`semanticKSession`) | `src/main/resources/rules/semantic/validation-rules.drl` (Bean Validation del DTO, codici `_OBBL_<path>`) e `validation-rules-all.drl` (lunghezze, codici `_ART_…`, `_COL_…`, `E_OBBL_…`) | `DroolsConfig`: dal classpath, oppure da `${DROOLS_RULES_DIR}/semantic` se la variabile è valorizzata | `SdaFlussoHandler` |
| **logic** (`rulesKSession`) | `rules/logic/dominio-rules.drl`, `validation-procedure.drl` (codici numerici 3 cifre: 003, 143, 208, 300…432) | come sopra, da `${DROOLS_RULES_DIR}/logic`; filtro `@elaborazione` (`AnnotationFilter`) per tipo elaborazione del cliente | `SdaFlussoHandler`, dopo il controllo 143 della postazione |
| **PDB** (`pdbKSession`) | `rules/pdb/generated/ce-pdb-rules.drl` (109 regole `pdb_1xxxx`, codici numerici 4 cifre 1009…2037, es. `1181` "Articolo Numero: Campo obbligatorio mancante") | `PdbRulesCacheService`: **solo dal classpath**, KieContainer separato | `PdbPreadvisingHandler` (canali `PDB_*` ed `EUD_*`, con `PdbChannel.canaleRegole`) |
| **configmap Helm** | `.helm/config/files/rules/semantic/*.drl`, `.helm/config/files/rules/logic/*.drl` | montati in `/config/semantic` e `/config/logic` (`configMap.enabled: true`) | letti solo se `DROOLS_RULES_DIR` è valorizzata |

Fatti da tenere presenti [FATTO]:
- **`DROOLS_RULES_DIR`** vale `/config` in `.helm/values.yaml`, ma **non** è impostata in
  `deploy-svil/values.yaml` e in `deploy-coll/values.yaml`, che sono copie complete del file. Quindi
  in svil e collaudo le regole semantic e logic si leggono dal **classpath**. Dove vale
  `.helm/values.yaml` si leggono invece dalla **configmap**. Le due copie sono già disallineate: in
  `logic/dominio-rules.drl` la regola 324 è in un'altra posizione, e
  `semantic/validation-rules-all.drl` ha un `*/` in più. Una regola DRL nuova andrebbe quindi
  scritta in due posti (VAL-DA-03).
- **Le regole PDB sono generate fuori dal repo.** Il commento di `PdbChannel.canaleRegole` dice "Il
  DRL … è generato esternamente". Il pacchetto `pdb/dsl/` (`CeDslParser`, `FieldPathMapper`,
  `PdbRuleHelpers`) traduce il DSL di ce-rules in Drools, ma nessun codice di `main` chiama
  `CeDslParser` e `FieldPathMapper`: il generatore e la sorgente tabellare non sono nel repo, e il
  DRL si aggiorna a mano ("Update ce-pdb-rules.drl", ottobre 2026). Una regola aggiunta a mano
  rischia di sparire alla prossima rigenerazione (VAL-DA-02).
- **Errori come mappa codice → descrizione** (`DichiaratoDTO.errors`). Se lo stesso codice scatta su
  due articoli, la seconda `put` sovrascrive la prima. Lo fanno già le regole PDB, per esempio 1181
  su più articoli. Per R-03 le descrizioni dello stesso codice si **concatenano** (5.4).

### 3.3 Handler per famiglia di canale e dove vale R-01

`CanaleFlussoResolver.resolve` sceglie l'handler [FATTO]:

| Handler | Canali | Validazione oggi | R-01 si applica? |
|---|---|---|---|
| `PdbPreadvisingHandler` | `PdbChannel.SUPPORTED`: `PDB_INVIOSYSTEM`, `PDB_INVIOFILE`, `PDB_INVIOEASY`, `PDB_STAMPAMASSIVA`, `EUD_INVIOFILE`, `EUD_INVIOSYSTEM` | regole PDB | **sì** |
| `PdbPdwFlussoHandler` | `config.canali-pdb` (`CANALI_PDB`, default `PDB,PDW,ILP`), cioè gli ingressi dell'adapter | nessuna: LDV, duplicato e passaggio | no (VAL-AS-12) |
| `TfiFlussoHandler` | `id_canale` in `config.id-canali` (`TFI,TWS,BNC`), canale `MYSDA`, `SDA_WS`, `INVIO_WEB` | nessuna (commento nel codice: "NIENTE VALIDAZIONE") | no (VAL-AS-12) |
| `TupFlussoHandler` | `TUP`, `OMP` | nessuna | no (VAL-AS-12) |
| `SdaFlussoHandler` | tutti gli altri: `IF`, `IS`, `IE` (canali a file del builder); un canale sconosciuto finisce qui, e la regola logic "Canale non valido" lo scarta con 400 | semantic, controllo 143, logic | **sì** |

**R-01 si applica nei due handler che validano**, `SdaFlussoHandler` e `PdbPreadvisingHandler`.
Gli handler di solo passaggio non cambiano: i loro canali arrivano già validati dai sistemi di
origine (adapter, portali, web service), e aggiungere uno scarto lì cambierebbe il loro
comportamento (VAL-AS-12, VAL-DA-04).

### 3.4 Dove si mette la regola: componente Java comune (proposta)

La regola si scrive **in Java**, in un componente nuovo (es. `compliance/ComplianceUsaValidator`)
chiamato dai due handler. Non si scrive in un DRL (VAL-AS-13), per tre motivi:

1. serve una **configurazione** (flag, valori, elenco prodotti: 8). Le sessioni Drools di oggi non
   leggono proprietà Spring;
2. un DRL andrebbe scritto in tre posti: semantic sul classpath, semantic nella configmap e DRL PDB
   generato. Il DRL generato si può sovrascrivere a ogni rigenerazione (3.2);
3. la descrizione per articolo e la concatenazione per codice (5.4) sono più semplici e testabili
   in Java.

| Punto | Cosa si fa |
|---|---|
| nuovo `ComplianceUsaProperties` (`@ConfigurationProperties(prefix = "config.compliance-usa")`) | proprietà della sezione 8 |
| nuovo `ComplianceUsaValidator` (`@Component`) | `Map<String,String> valida(DichiaratoDTO dto)`: riconoscimento (5.2) e controlli (5.3); restituisce gli errori senza modificare il DTO |
| `SdaFlussoHandler.gestisci` | subito dopo `validaEventoConRegoleSemantiche`, si uniscono gli errori di compliance a quelli semantici (`errori.putAll(...)`, con le regole di unione di 5.4) **prima** del controllo `if (!errori.isEmpty())`. L'operatore vede così tutti gli errori formali in un solo scarto (VAL-AS-14) |
| `PdbPreadvisingHandler.validaConRegolePdb` | dopo `fireAllRules`, e dopo il ripristino del canale, si uniscono gli errori di compliance a `dto.getErrors()` |
| `FlussoHandler` | eventuale metodo protetto comune `aggiungiErroriComplianceUsa(dto, errori)`, per non duplicare il codice nei due handler (Sonar) |

Il multicollo a riga singola (configurazione `002` in `SdaFlussoHandler`) clona il DTO dopo la
validazione: i cloni ereditano `zonos_account_key` e, collo per collo, gli articoli con il loro
`zonos_product_id`. Non serve altro.

## 4. Dati usati

| Dato | Percorso JSON | Accessor Java | Uso |
|---|---|---|---|
| Account Key | `spedizione[].zonos_account_key` | `SpedizioneDTO.getZonos_account_key()` | controllo 5.3 |
| Declaration ID | `spedizione[].zonos_declaration_id` | `SpedizioneDTO.getZonos_declaration_id()` | solo propagazione |
| Product ID | `spedizione[].collo[].articolo[].zonos_product_id` | `ArticoloDTO.getZonos_product_id()` | controllo 5.3 |
| Nazione ISO2 del destinatario | `spedizione[].destinatario.codice_nazione_iso_2` | `getDestinatario().getCodiceNazioneIso2()` | riconoscimento |
| Nazione del destinatario | `spedizione[].destinatario.codice_nazione` | `getDestinatario().getCodice_nazione()` | riconoscimento |
| Tipo merce | `spedizione[].tipo_merce` (1 carattere, nessun dominio nello schema del builder) | `getTipo_merce()` | riconoscimento |
| Codice prodotto | `spedizione[].codice_prodotto` | `getCodice_prodotto()` | riconoscimento |
| Servizio | `spedizione[].id_servizio` | `getId_servizio()` | riconoscimento |
| Posizione articolo | `…articolo[].posizione` (`@Size(max = 1)`) | `ArticoloDTO.getPosizione()` | descrizione dell'errore |

## 5. Regole funzionali

### 5.1 Campi nuovi nel DTO [DECISO, AS-01]

| ID | Regola |
|---|---|
| RV-01 | `zonos_account_key` e `zonos_declaration_id` si aggiungono a `SpedizioneDTO`, `zonos_product_id` ad `ArticoloDTO`; nomi JSON esattamente questi |
| RV-02 | I tre campi sono opzionali: un messaggio senza campi (eventi storici, canali non adeguati) si comporta esattamente come oggi (R-05) |
| RV-03 | I valori escono su `preadvising.enrichment`, nell'evento dell'event store e su Mongo **identici a come sono entrati**: niente `trim`, maiuscole o troncamenti (R-04). Ogni `zonos_product_id` resta sul suo articolo |
| RV-04 | `zonos_declaration_id` non ha regole in fase 1: qualunque valore (tipicamente assente o `null`) passa così com'è |

### 5.2 Riconoscimento delle spedizioni soggette [DECISO, AS-02, Diego 2026-11-23]

Si valuta **per ogni elemento** di `spedizione[]`. Una spedizione è soggetta se il flag è acceso
(`config.compliance-usa.abilitata = true`) e valgono **tutte** queste condizioni. La condizione C1
("cliente business", `importi.cliente_business`) della versione 0.1 **non c'è più**: gli ID C2…C4
restano invariati per non confondere i riferimenti.

| # | Condizione | Proprietà (8) | Default |
|---|---|---|---|
| C2 | `destinatario.codice_nazione_iso_2` = `US` **oppure** `destinatario.codice_nazione` è fra le nazioni USA | `nazioni-usa` | `US,USA` |
| C3 | `tipo_merce` **diverso** da "documenti". Se `tipo_merce` manca, la spedizione conta come merce | `tipi-merce-documenti` | `D` |
| C4 | `codice_prodotto` **oppure** `id_servizio` è nell'elenco dei prodotti interessati; con l'elenco vuoto valgono tutti i prodotti | `prodotti` | `456,457,458,459,515,516` |

I prodotti interessati, con i codici di `ce_prodotto` di ce-rules:

| Codici | Prodotto |
|---|---|
| `456`, `457` | EXPORT BOX |
| `458`, `459` | EXPORT BOX PCIM |
| `515`, `516` | CRONO INTERNAZIONALE (`516` = assicurato) |

Diego ha elencato CRONO INTERNAZIONALE quattro volte, ma in `ce_prodotto` risultano solo `515` e
`516`: l'elenco è da confermare (PA-12). Si cambia in configurazione, senza toccare il codice.

- I confronti delle condizioni ignorano maiuscole e spazi iniziali e finali. Si tratta dei campi di
  riconoscimento: i campi nuovi non si toccano (VAL-AS-16).
- Se `destinatario` manca, C2 è falsa e la spedizione non è soggetta. Se mancano sia
  `codice_prodotto` sia `id_servizio`, C4 è falsa (con l'elenco valorizzato).
- **Con il flag spento** il validatore non riconosce nessuna spedizione e non produce errori. I
  campi nuovi si propagano comunque (RV-03). È il default finché il builder non manda i campi [DECISO, AS-02].
- Su una spedizione non soggetta i campi nuovi non si controllano. Se ci sono si propagano, anche
  con lunghezze fuori regola (R-02, VAL-AS-10).

### 5.3 Controlli sulle spedizioni soggette [DECISO, R-02]

Solo presenza e lunghezza, sul valore così com'è.

| ID | Controllo | Errore (5.4) |
|---|---|---|
| RV-10 | `zonos_account_key` assente: `null`, stringa vuota o di soli spazi | `1320` |
| RV-11 | `zonos_account_key` presente ma di lunghezza diversa da **52** caratteri (lunghezza Java `String.length()` del valore non modificato, spazi compresi) | `1321` |
| RV-12 | Per **ogni** articolo di **ogni** collo: `zonos_product_id` assente (`null`, vuoto o di soli spazi) | `1322` |
| RV-13 | Per ogni articolo: `zonos_product_id` più lungo di **255** caratteri | `1323` |

- RV-10 e RV-11 si escludono a vicenda. Lo stesso vale per RV-12 e RV-13 sullo stesso articolo.
- **Spedizione soggetta senza articoli** (`collo` assente, o colli senza `articolo`): non si produce
  nessun errore di Product ID, perché non c'è un articolo da indicare. Si logga un WARN con
  `id_preadvising` (VAL-DA-05).
- Le lunghezze 52 e 255 sono costanti nel codice e vengono dalla descrizione (§2). Non sono
  configurabili.

### 5.4 Errori: codici, descrizioni, unione [ASSUNTO VAL-AS-17 sui codici; formato da AS-03]

Codici e descrizioni decisi da Diego il 23-11 (PA-04 chiuso). Li ho verificati come **liberi** nel codice, nei DRL (classpath, configmap, PDB
generato) del validatore e nel codice Java e DRL degli altri repo della catena (16-11). L'unica
occorrenza di `1320`…`1323` è dentro un CSV di dati dell'orchestratore, senza legami con gli
errori. Stanno subito dopo l'ultimo codice PDB in uso (`1311`) e seguono il formato a 4 cifre
delle regole PDB (AS-03).

| Codice | Quando | Descrizione |
|---|---|---|
| `1320` | RV-10 | `zonos_account_key: Campo obbligatorio mancante` |
| `1321` | RV-11 | `zonos_account_key: lunghezza non valida (attesi 52 caratteri)` |
| `1322` | RV-12 | `zonos_product_id: Campo obbligatorio mancante (collo <n> articolo <posizione>)` |
| `1323` | RV-13 | `zonos_product_id: lunghezza non valida, attesi 1-255 caratteri (collo <n> articolo <posizione>)` |

Come si indicano collo e articolo (R-03):
- `<n>` è il numero d'ordine del collo nella lista `collo[]` della spedizione, a partire da 1. Il
  collo non ha un campo di posizione;
- `<posizione>` è `articolo.posizione` così com'è. Se manca, si usa `#<k>`, cioè l'indice
  dell'articolo nel collo a partire da 1 (es. `Articolo #2 collo 1`);
- se il messaggio ha **più di un elemento** in `spedizione[]`, ogni descrizione ha il prefisso
  `Spedizione <k>: ` (k da 1). Con una sola spedizione, che è il caso normale, non c'è prefisso;
- **più occorrenze dello stesso codice** (più articoli senza Product ID, o più spedizioni) diventano
  **una sola voce** della mappa: le descrizioni si concatenano con `"; "`, nell'ordine di spedizione,
  collo e articolo. Esempio: `"1322": "zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 1; collo 2 articolo 3)"` (nome del campo sempre prima dei due punti, letto così dal monitoring; occorrenze elencate fra parentesi separate da `"; "`);
- se il codice c'è già nella mappa, perché lo ha prodotto un'altra regola, si concatena allo stesso
  modo e non si sovrascrive;
- le descrizioni **non contengono i valori** dei campi, solo le posizioni.

### 5.5 Effetto dello scarto [FATTO, codice degli handler]

Con almeno un errore di compliance, il preavviso si **scarta** come per gli altri campi obbligatori
mancanti (AS-03). Si usa il percorso che già esiste, senza nulla di nuovo:

| Handler | Cosa succede |
|---|---|
| `SdaFlussoHandler` | `gestisciEsito`: span marcato con l'errore di validazione, evento `PREADVISING_PARZIALE_E_BLOCCATO` (`ST_R0006`) su `preadvising.evensource` con `eventData.errori` = la mappa degli errori, Mongo `dichiarato_events` a `stato` 2 con `errori`, `dichiarato_ldv_history` a `stato` 2, contatore `kafka_message_consumed_total_ko{canale=SDA}` |
| `PdbPreadvisingHandler` | stesso evento `ST_R0006` con errori, `salvaErroreRegole`, contatore `kafka_message_consumed_total_ko{canale=<canale>}` e `business_stato_pread_stato_total{stato=PREADVISING_PARZIALE_E_BLOCCATO}` |

Il messaggio **non** va su `preadvising.enrichment`. Gli scarti si leggono dall'event store come
quelli di oggi (`ce-event-handler-dichiarato-scarti` e il file esiti, senza modifiche). Prima dello
scarto c'è sempre l'evento `PREAD_EMESSO` (`ST_R0002`): con i DTO estesi porta anche i campi nuovi.

### 5.6 Regole riassuntive

| ID | Regola |
|---|---|
| RV-01…RV-04 | DTO e propagazione (5.1) |
| RV-05 | Riconoscimento per spedizione con C2…C4 e flag (5.2) |
| RV-10…RV-13 | Controlli di presenza e lunghezza (5.3) |
| RV-20 | Errori 1320…1323, descrizioni con collo e articolo, concatenazione per codice (5.4) |
| RV-21 | Esito = scarto con il percorso esistente dell'handler (5.5) |
| RV-22 | La regola vale in `SdaFlussoHandler` e `PdbPreadvisingHandler`, non negli handler di passaggio (3.3) |
| RV-23 | Nessun valore di `zonos_account_key` o `zonos_product_id` nei log, nelle metriche e negli attributi degli span (9) |

## 6. Esempi di messaggi [dati inventati]

Gli esempi sono ridotti ai campi che servono: il resto del tracciato unico resta com'è oggi. Gli
identificativi sono inventati. L'Account Key di esempio è lunga 52 caratteri:
`TESTAK0000000000000000000000000000000000000000000001`.

### 6.1 Ingresso su `preadvising.pre-enrichment`: spedizione soggetta e valida (canale IF)

```json
{
  "canale": "IF",
  "id_preadvising": "b1000000-0000-4000-8000-000000000001",
  "id_file": "f1000000-0000-4000-8000-000000000001",
  "spedizione": [{
    "codice_prodotto": "456",
    "tipo_merce": "M",
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "zonos_declaration_id": null,
    "destinatario": { "codice_nazione": "USA", "codice_nazione_iso_2": "US" },
    "collo": [{
      "id_ldv": "TSTLDV000000001",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": 2, "valore": 40, "zonos_product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203420000", "quantita": 1, "valore": 60, "zonos_product_id": "PRD-TEST-0002" }
      ]
    }]
  }]
}
```

Esito: nessun errore di compliance. Su `preadvising.enrichment` esce il tracciato con
`tipo_lavorazione: "validato"` e i tre campi identici, ognuno nella sua posizione:

```json
{
  "canale": "IF",
  "id_preadvising": "b1000000-0000-4000-8000-000000000001",
  "tipo_lavorazione": "validato",
  "spedizione": [{
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "zonos_declaration_id": null,
    "collo": [{ "articolo": [
      { "posizione": "1", "zonos_product_id": "PRD-TEST-0001" },
      { "posizione": "2", "zonos_product_id": "PRD-TEST-0002" }
    ]}]
  }]
}
```

### 6.2 Spedizione soggetta con Account Key corta e un articolo senza Product ID (canale PDB_INVIOFILE)

Ingresso: come 6.1 ma `"canale": "PDB_INVIOFILE"`, `"zonos_account_key": "TESTAK-CORTA"` e il secondo articolo
senza `zonos_product_id`. Evento su `preadvising.evensource` (ridotto):

```json
{
  "aggregateId": "b1000000-0000-4000-8000-000000000002",
  "aggregateType": "ldv",
  "eventType": "ST_R0006",
  "eventData": {
    "canale": "PDB_INVIOFILE",
    "errori": {
      "1321": "zonos_account_key: lunghezza non valida (attesi 52 caratteri)",
      "1322": "zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2)"
    },
    "spedizione": [{ "zonos_account_key": "TESTAK-CORTA", "zonos_declaration_id": null, "collo": [{ "articolo": [
      { "posizione": "1", "zonos_product_id": "PRD-TEST-0001" }, { "posizione": "2" } ] }] }]
  },
  "metadata": { "source": "ce-dichiarato-validatore", "replay": false }
}
```

Il messaggio non va su `preadvising.enrichment`.

### 6.3 Due colli, articoli senza Product ID in entrambi

Collo 1: articoli `1` (con `zonos_product_id`) e `2` (senza). Collo 2: un articolo senza `posizione` e
senza `zonos_product_id`. Errori:

```json
{ "1320": "zonos_account_key: Campo obbligatorio mancante",
  "1322": "zonos_product_id: Campo obbligatorio mancante (collo 1 articolo 2; collo 2 articolo #1)" }
```

(con `zonos_account_key` assente)

### 6.4 Spedizione non soggetta: nessun controllo, propagazione

Come 6.1 ma `"destinatario": { "codice_nazione": "DEU", "codice_nazione_iso_2": "DE" }`, senza
`zonos_account_key` e con un articolo senza `zonos_product_id`. Esito: nessun errore di compliance. Il messaggio
prosegue e i campi presenti si propagano come sono arrivati.

### 6.5 Messaggio storico senza campi nuovi

Un tracciato di oggi, senza `zonos_account_key`, `zonos_declaration_id` e `zonos_product_id`, verso una nazione
qualsiasi e con il flag spento. Esito identico a quello di oggi. In uscita la testata ha
`"zonos_account_key": null, "zonos_declaration_id": null` e gli articoli `"zonos_product_id": null`, perché
l'`ObjectMapper` serializza i `null` (VAL-AS-18).

## 7. Casi d'uso

| UC | Situazione | Esito |
|---|---|---|
| UC-01 | soggetta, 1 articolo, Account Key di 52 e Product ID validi | valida, campi propagati |
| UC-02 | soggetta, più articoli con Product ID distinti (anche su più colli) | valida, ogni Product ID sul suo articolo |
| UC-03 | soggetta, Account Key assente | scarto `1320` |
| UC-04 | soggetta, Account Key di 51 o 53 caratteri | scarto `1321` |
| UC-05 | soggetta, un solo articolo senza Product ID fra più articoli | scarto `1322` con collo e posizione di quell'articolo |
| UC-06 | soggetta, Product ID di 256 caratteri | scarto `1323` |
| UC-07 | soggetta, più errori insieme (6.2, 6.3) | un solo scarto con tutti i codici |
| UC-08 | soggetta per il solo `id_servizio` (`codice_prodotto` fuori elenco, `id_servizio` = `515`) | controlli attivi, come UC-01…UC-07 |
| UC-09 | non USA (es. `DE`/`DEU`) | nessun controllo |
| UC-10 | USA con soli documenti (`tipo_merce` = `D`) | nessun controllo |
| UC-11 | prodotto fuori dall'elenco configurato | nessun controllo |
| UC-12 | flag spento (default) | nessun controllo, campi propagati |
| UC-13 | soggetta, con anche un errore semantico esistente (flusso SDA) | un solo scarto con entrambi gli errori |
| UC-14 | messaggio storico senza campi nuovi | come oggi |
| UC-15 | soggetta su canale di passaggio (`PDW`, `MYSDA`, `TUP`) | nessun controllo (VAL-AS-12), campi propagati |
| UC-16 | multicollo a riga singola (`002`) | i cloni portano `zonos_account_key` e gli articoli del proprio collo con `zonos_product_id` |

## 8. Configurazione

Le proprietà seguono il modello di `config.*` in `application.yaml`: valore da variabile d'ambiente
con default.

```yaml
config:
  compliance-usa:
    abilitata: ${COMPLIANCE_USA_ABILITATA:false}
    tipi-merce-documenti: ${COMPLIANCE_USA_TIPI_MERCE_DOCUMENTI:D}
    nazioni-usa: ${COMPLIANCE_USA_NAZIONI_USA:US,USA}
    prodotti: ${COMPLIANCE_USA_PRODOTTI:456,457,458,459,515,516}
```

- Le liste sono separate da virgola. Gli elementi vuoti si scartano, quindi `COMPLIANCE_USA_PRODOTTI`
  vuota dà un elenco vuoto, cioè **tutti i prodotti**.
- `nazioni-usa` vale per `codice_nazione`; per `codice_nazione_iso_2` basta `US`, che è nella stessa lista.
- I nomi delle variabili d'ambiente sono una proposta: valgono quelli scelti in sviluppo, purché il
  default del flag resti `false`.
- All'avvio si logga una riga INFO con flag ed elenchi, che non sono dati sensibili.
- Dove si scrivono:

| File | Valori |
|---|---|
| `src/main/resources/application.yaml` | blocco sopra |
| `.helm/values.yaml` (`envFrom`) | `COMPLIANCE_USA_ABILITATA: 'false'`; le altre solo se diverse dal default |
| `deploy-svil/values.yaml` (`envFrom`) | `COMPLIANCE_USA_ABILITATA: 'false'`; si accende solo per i test integrati (VAL-AS-19) |
| `deploy-coll/values.yaml` (`envFrom`) | `COMPLIANCE_USA_ABILITATA: 'false'` finché il builder non manda i campi |
| `deploy-config/values_TEMPLATE.yaml` | `COMPLIANCE_USA_ABILITATA: '_#COMPLIANCE_USA_ABILITATA' #certificazione:'false', produzione:'false'` e `COMPLIANCE_USA_PRODOTTI: '_#COMPLIANCE_USA_PRODOTTI' #certificazione:'456,457,458,459,515,516', produzione:'456,457,458,459,515,516'` |

Nessun secret nuovo. Le regole DRL e la configmap **non cambiano** (3.4).

## 9. Requisiti non funzionali e osservabilità

- **Prestazioni**: il controllo è in memoria e lineare sul numero di articoli, senza chiamate esterne.
  Non deve cambiare in modo misurabile il tempo di lavorazione.
- **Robustezza**: un'eccezione inattesa nel componente non deve bloccare la lavorazione in modo
  silenzioso. La gestione è quella di oggi in `KafkaConsumer.processaMessaggio`: log ERROR e
  contatore `kafka_message_consumed_total_ErroreTecnico`. Il componente però non deve mai lanciare
  eccezioni su dati mancanti: ogni accesso a un valore nullable va controllato (Sonar).
- **Tracing**: un sotto-span `verificaComplianceUsa` (`TraceUtil.callInChildSpan`), con attributi
  `compliance_usa.abilitata`, `compliance_usa.spedizioni_soggette` (numero), `verifica.esito`
  (`ok`/`ko`/`non_soggetta`) e `errore.codice` (codici separati da virgola). Niente valori dei campi.
- **Metriche**: contatore `business_compliance_usa_verifiche_total` con tag `canale` ed `esito`
  (`non_soggetta`, `ok`, `ko`), incrementato una volta per messaggio quando il flag è acceso. La
  metrica non deve mai far fallire la lavorazione: `try/catch` come in `incrementaContatoreStato`.
  Serve per un alert Datadog sugli scarti `ko` per canale.
- **Log**: una riga INFO per messaggio soggetto: `COMPLIANCE_USA | id_preadvising=<id> soggette=<n> esito=<ok|ko> codici=<1320,1322>`.
  Nei log non vanno mai `zonos_account_key` e `zonos_product_id` (RV-23; `@ToString.Exclude` su `zonos_account_key`,
  VAL-AS-11). MDC come oggi (`partition`, `offset`, `id_preadvising`, `id_file`).
- **Sonar**: metodi brevi (riconoscimento, controllo testata, controllo articoli, composizione della
  descrizione), complessità cognitiva ≤ 15, letterali dei codici e dei messaggi in costanti, nessun
  riferimento a PA o documenti di analisi nei commenti.

## 10. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato il messaggio 6.1 con flag acceso, quando il validatore lo lavora, allora su `preadvising.enrichment` esce un messaggio con `zonos_account_key`, `zonos_declaration_id` e ogni `zonos_product_id` identici e nelle stesse posizioni dell'ingresso |
| AC-02 | Dato 6.1 con flag **spento**, l'uscita è la stessa di AC-01 (la propagazione non dipende dal flag) |
| AC-03 | Dato un messaggio senza campi nuovi (6.5), l'uscita è uguale a quella di oggi tranne i campi nuovi a `null`, e nessuna regola esistente cambia esito |
| AC-04 | L'evento `PREAD_EMESSO` su `preadvising.evensource` e il documento in `dichiarato_events` contengono i tre campi |
| AC-05 | Dato UC-03, il preavviso è scartato con `errori` = `{"1320": "zonos_account_key: Campo obbligatorio mancante"}` ed evento `ST_R0006`; nulla esce su `preadvising.enrichment` |
| AC-06 | Dato UC-04 con 51 e con 53 caratteri, l'errore è `1321`; con 52 caratteri, spazi compresi, nessun errore |
| AC-07 | Dato UC-05, l'errore è `1322` con la descrizione `zonos_product_id: Campo obbligatorio mancante (collo <n> articolo <posizione>)` dell'articolo mancante |
| AC-08 | Dato UC-06, l'errore è `1323`; con un Product ID di 1 e di 255 caratteri nessun errore |
| AC-09 | Dato 6.3, la mappa ha una voce `1322` con le due occorrenze elencate fra parentesi, separate da `"; "`, nell'ordine collo e articolo, e la voce `1320` |
| AC-10 | Dato un messaggio con due elementi in `spedizione[]`, le descrizioni hanno il prefisso `Spedizione <k>: ` |
| AC-11 | Dati UC-09, UC-10, UC-11, UC-12 con Account Key assente e Product ID assenti, nessun errore di compliance; dato UC-08 con Account Key assente, errore `1320` |
| AC-12 | Con `nazioni-usa` = `US,USA`, una spedizione con solo `codice_nazione` = `usa ` (minuscolo, spazio finale) è soggetta |
| AC-13 | Con `prodotti` di default è soggetta una spedizione con `codice_prodotto` `456`, e una con `codice_prodotto` `ALTRO` e `id_servizio` `516`; non lo è una con `codice_prodotto` `ALTRO` e `id_servizio` `ALTRO2`; con `prodotti` vuoto ogni prodotto è interessato |
| AC-14 | Dato UC-13 nel flusso SDA, lo scarto contiene sia l'errore semantico sia quello di compliance |
| AC-15 | Dato UC-15 (canali `PDW`, `MYSDA`, `TUP`) con campi mancanti, il preavviso prosegue senza errori di compliance |
| AC-16 | Dato 6.2 su `PDB_INVIOFILE` ed `EUD_INVIOSYSTEM`, lo scarto ha gli errori di compliance oltre a quelli PDB, e il canale in uscita è quello originale |
| AC-17 | Dato UC-16, ogni clone ha `zonos_account_key` della spedizione e, sul suo collo, gli articoli con il loro `zonos_product_id` |
| AC-18 | Una spedizione non soggetta con `zonos_product_id` di 300 caratteri passa senza errori: nessuna annotazione Bean Validation sui campi nuovi |
| AC-19 | Nei log (anche a DEBUG e nel WARN di `salvaErroreRegole`) non compare il valore di `zonos_account_key`; nei log a INFO e WARN non compare `zonos_product_id` |
| AC-20 | La metrica `business_compliance_usa_verifiche_total` si incrementa con `esito` `ok`, `ko` e `non_soggetta` nei casi attesi e non si incrementa con il flag spento |
| AC-21 | Tutti i test esistenti (`regoledrools/*`, `handler/*`) restano verdi |

## 11. Casi di test

Test unitari del componente con DTO costruiti in memoria, test degli handler come quelli esistenti
(`PdbPreadvisingHandlerTest`, `regoledrools/*`), poi test integrato in svil con messaggi costruiti a
mano su `preadvising.pre-enrichment` (AS-05). Tutti i dati sono inventati.

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit (Jackson) | JSON 6.1 → DTO → JSON | i tre campi sono uguali e nella stessa posizione; JSON senza campi → campi `null` | AC-01, AC-03 |
| TC-02 | unit | componente su 6.1 (UC-01, UC-02) | nessun errore | AC-01 |
| TC-03 | unit (parametrico) | Account Key `null`, `""`, `"   "`, 51, 52 (anche con spazi), 53 caratteri | `1320`, `1320`, `1320`, `1321`, nessuno, `1321` | AC-05, AC-06 |
| TC-04 | unit (parametrico) | Product ID `null`, `""`, 1, 255, 256 caratteri | `1322`, `1322`, nessuno, nessuno, `1323` | AC-07, AC-08 |
| TC-05 | unit | 6.3; più spedizioni; codice già presente nella mappa | concatenazione e prefissi di 5.4 | AC-09, AC-10 |
| TC-06 | unit (parametrico) | C2…C4 una alla volta false: `DE`/`DEU`, `destinatario` assente; `tipo_merce` `D`; `codice_prodotto` e `id_servizio` fuori elenco o assenti. In più un caso con `importi.cliente_business` = `N`, che resta soggetta | non soggetta (tranne l'ultimo caso) | AC-11 |
| TC-07 | unit | maiuscole e spazi nelle condizioni; solo `codice_nazione_iso_2`, solo `codice_nazione`; `tipo_merce` assente | soggetta | AC-12 |
| TC-08 | unit | elenco di default (match su `codice_prodotto`, su `id_servizio`, su nessuno dei due), elenco vuoto | AC-13 | AC-13 |
| TC-09 | unit | flag spento con 6.2 | nessun errore | AC-02, AC-11 |
| TC-10 | unit | soggetta senza colli o senza articoli | nessun errore `1322`, WARN | 5.3 |
| TC-11 | handler SDA | 6.2 su canale `IF` con anche un campo semantico errato | scarto unico, evento `ST_R0006`, Mongo `stato` 2, niente invio su enrichment | AC-05, AC-14 |
| TC-12 | handler PDB | 6.2 su `PDB_INVIOFILE` ed `EUD_INVIOSYSTEM` | errori PDB e di compliance insieme; canale ripristinato | AC-16 |
| TC-13 | handler di passaggio | 6.2 su `PDW`, `MYSDA`, `TUP` | nessun errore di compliance, invio su enrichment con i campi | AC-15 |
| TC-14 | handler SDA multicollo `002` | 2 colli, articoli con Product ID diversi | i cloni hanno i campi giusti | AC-17 |
| TC-15 | unit | spedizione non soggetta con Product ID di 300 caratteri nel flusso SDA (regola "Validazione annotazioni DTO") | nessun errore | AC-18 |
| TC-16 | log capture | TC-11 con log a DEBUG | nessun valore di `zonos_account_key` | AC-19 |
| TC-17 | unit (MeterRegistry semplice) | ok, ko, non soggetta, flag spento | contatori attesi | AC-20 |
| TC-18 | regressione | suite esistente | verde | AC-21 |
| TC-19 | integrato svil | 4 messaggi a mano su `preadvising.pre-enrichment`: 6.1 su `IF`, 6.2 su `PDB_INVIOFILE`, 6.4, 6.5 | uscite su `preadvising.enrichment` ed eventi su `preadvising.evensource` come in AC-01, AC-05, AC-11, AC-03 | AC-01…AC-05 |

Per il canale `IF` il messaggio deve avere un cliente e una postazione di test configurati in
`ce-vendite`, altrimenti si ferma all'errore 143 prima delle regole logic. Lo scarto di compliance
però arriva prima del controllo 143 (VAL-AS-14).

Nel test integrato i campi nuovi passano anche dall'orchestratore e dai servizi a valle. Il loro
arrivo fino alle SEW si verifica con i funzionali di quei servizi. Il retry e il replay riguardano
event store e orchestratore: per il validatore basta TC-01, cioè che il giro JSON → DTO → JSON
non perde nulla.

## 12. Assunzioni e domande aperte

Da `analisi.md`, vincolanti:

| ID | Contenuto | Uso qui |
|---|---|---|
| AS-01 | Nomi `zonos_account_key`, `zonos_declaration_id` (testata), `zonos_product_id` (articolo); opzionali, `String`, senza trasformazioni | 3.1, 5.1 |
| AS-02 | Riconoscimento (Diego, 23-11): `tipo_merce` non documenti, destinatario US/USA, `codice_prodotto` o `id_servizio` in `456,457,458,459,515,516`; niente condizione business; valori e flag in configurazione, flag spento di default | 5.2, 8 |
| AS-03 | Errori `errors.put(codice, descrizione)`, codici `1320`…`1323` con le descrizioni decise il 23-11, esito scarto | 5.4, 5.5 |
| AS-04 | SEW | non riguarda il validatore |
| AS-05 | Il builder e l'adapter pubblicano i campi; test con messaggi a mano | 11 |
| AS-06 | Fuori dalla fase 1: Zonos, stampe, palmari, T&T-Repo | 1 |

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| VAL-AS-10 | Nessuna annotazione Bean Validation sui campi nuovi. La regola semantica generica le applicherebbe a tutte le spedizioni del flusso SDA, con codici `_OBBL_…` e anche fuori da R-01 | lunghezze controllate solo nel componente, solo sulle spedizioni soggette | Diego |
| VAL-AS-11 | L'Account Key è una chiave del cliente: non va nei log | `@ToString.Exclude` su `zonos_account_key`; `zonos_product_id` resta nel `toString` (non è un dato personale), ma non va nei log del componente | Diego / Poste (sicurezza) |
| VAL-AS-12 | R-01 vale solo negli handler che validano (`SdaFlussoHandler`, `PdbPreadvisingHandler`). `PdbPdwFlussoHandler` (PDB, PDW, ILP dall'adapter), `TfiFlussoHandler` (MYSDA, SDA_WS, INVIO_WEB, TFI/TWS/BNC) e `TupFlussoHandler` (TUP, OMP) oggi non validano nulla, e restano così | nessun controllo su quei canali, solo propagazione | Poste (vedi VAL-DA-04) |
| VAL-AS-13 | La regola si scrive in Java e non in DRL, per la configurazione, per le copie disallineate classpath/configmap e per il DRL PDB generato fuori dal repo | componente `ComplianceUsaValidator` | Diego |
| VAL-AS-14 | Nel flusso SDA gli errori di compliance si uniscono a quelli semantici (prima del controllo postazione 143) | un solo scarto con tutti gli errori formali | Diego |
| VAL-AS-15 | Il valore "documenti" di `tipo_merce` non è nello schema del tracciato (1 carattere, nessun dominio). Lo schema del builder ha invece `collo.codice_contenuto` con dominio `P`/`D` | **[DECISO, Diego 23-11]** `tipi-merce-documenti` = `D`, su `tipo_merce`; `tipo_merce` assente = merce | chiusa |
| VAL-AS-16 | I confronti delle condizioni di riconoscimento ignorano maiuscole e spazi; i campi nuovi non si toccano mai | come 5.2 | Diego |
| VAL-AS-17 | Codici `1320`…`1323`, liberi nella catena, dopo l'ultimo codice PDB (`1311`) | **[DECISO, Diego 23-11]** codici e descrizioni di 5.4 | chiusa |
| VAL-AS-18 | In uscita i campi assenti diventano `null` espliciti, perché l'`ObjectMapper` serializza i null come per tutti gli altri campi | nessun `@JsonInclude(NON_NULL)` | Diego (impatto a valle nullo: gli altri DTO li accettano come opzionali) |
| VAL-AS-19 | Flag spento di default in tutti gli ambienti finché il builder non manda i campi; in svil si accende solo per i test integrati | come 8 | Diego |

Domande aperte:

| ID | Domanda | Perché serve | Per chi |
|---|---|---|---|
| VAL-DA-01 | **Chiusa il 23-11 (Diego).** Niente condizione "business"; "documenti" da `tipo_merce` = `D`; prodotti `456,457,458,459,515,516` su `codice_prodotto` o `id_servizio`. Resta da confermare solo l'elenco di CRONO INTERNAZIONALE (PA-12) | configurazione | — |
| VAL-DA-02 | Le regole PDB (`ce-pdb-rules.drl`) si generano da ce-rules con un generatore che non è nel repo. Va aggiunta lì anche la regola di compliance, o basta il componente Java? | rischio di doppioni o di regole perse alla rigenerazione | Poste / team ce-rules |
| VAL-DA-03 | In produzione le regole semantic e logic si leggono dalla configmap (`DROOLS_RULES_DIR=/config` in `.helm/values.yaml`), in svil e collaudo dal classpath, e le due copie sono già disallineate. Va bene che questa iniziativa non tocchi i DRL? Chi riallinea le copie? | coerenza fra ambienti (fuori perimetro, ma va segnalato) | Diego |
| VAL-DA-04 | Le spedizioni USA soggette che arrivano dai canali di passaggio (PDB/PDW/ILP dall'adapter, portali e web service su TFI, TUP) vanno controllate anche dal validatore, o le controlla il sistema di origine? | perimetro di R-01 | Poste |
| VAL-DA-05 | Una spedizione soggetta senza articoli è valida, o va scartata perché il Product ID è "obbligatorio per ogni articolo"? | caso limite di RV-12 | Poste |
| VAL-DA-06 | L'Account Key di 52 caratteri: la lunghezza si conta sul valore così com'è (spazi compresi) o va rifiutato un valore con spazi? Ha un formato (alfanumerico)? | RV-11 | Poste |
| VAL-DA-07 | Formato delle descrizioni con collo e articolo, e concatenazione con `"; "` per più articoli con lo stesso codice: è leggibile dal file esiti e dai portali che mostrano gli scarti? | R-03, PA-04 | Poste |

## 13. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1, regole R-01…R-07, punti aperti PA-01…PA-11.
- `cliente/HLD_146073_dati_preadvising_fase_1.xlsx`: intervento 01.
- `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`: §2, §4, §5, §6.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md): catena e topic.
- [contesto/linee-guida-sviluppo.md](../../../contesto/linee-guida-sviluppo.md): stack, Sonar, osservabilità, branch.
- Codice (`origin/develop`, `68083fb`): `config/AppConfig.java`, `config/DroolsConfig.java`,
  `kafka/consumer/KafkaConsumer.java`, `handler/*.java`, `kafka/dto/{DichiaratoDTO,SpedizioneDTO,ColloDTO,ArticoloDTO,ImportiDTO,DestinatarioDTO}.java`,
  `pdb/PdbChannel.java`, `pdb/cache/PdbRulesCacheService.java`, `util/EventStorePayloadUtil.java`,
  `rules/**`, `.helm/config/files/rules/**`, `.helm/values.yaml`, `deploy-svil/values.yaml`, `deploy-coll/values.yaml`.
