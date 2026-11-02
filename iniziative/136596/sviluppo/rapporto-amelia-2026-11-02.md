# 136596 — Rapporto di ricognizione dei repository (Amelia → Mary)

**Data**: 2026-11-02 · **Autrice**: Amelia (dev) · **Destinataria**: Mary (analyst)
**Mandato** (John, 02-11): clonare i 3 repository, fare la ricognizione, impostare un
`CLAUDE.md` in ciascuno e riportare cosa c'è e le incongruenze con la specifica. Nessuno
sviluppo applicativo.

## Dove e cosa

- Cloni in `C:\Users\diego.mereu\gitposte\SDA\preadvising\CORRIERE-ESPRESSO_PREADVISING_<ms>`.
- Branch di riferimento (indicazione di Diego): `feature/eurodis-base-implementation`.
  `master` e `develop` contengono solo il template ALM del 30-10.

| Repository | Ultimo commit sul branch | Stato |
|---|---|---|
| `ce-dichiarato-eurodis-in` | `0bb3993` 02-11 azzurrazezza "Update Dockerfile" | **Solo scheletro**: template + pipeline/Dockerfile sistemati. Nessuna logica |
| `ce-dichiarato-eurodis-mapper` | `0300284` 02-11 EXTA17G "impostazione progetto" | **Impostato, con il primo pezzo di mapping**: consumer, servizio, mapper, producer, 11 test verdi |
| `ce-eurodis-send-tracking` | `cc3f4f3` 02-11 azzurrazezza "fix build" | **Solo scheletro**: template, build sistemata. Nessuna logica |

`CLAUDE.md` creato nei 3 cloni (non committato, non pushato): rimanda alla specifica in
`sda-iniziative`, al blueprint `contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md`, e fissa le
regole non negoziabili di ciascun servizio.

---

## 1. `ce-dichiarato-eurodis-in`

Contenuto: `Application.java`, `application.yml`, Helm, pipeline Jenkins (namespace
`corriere-espresso-preadvising`, cluster svil, `DEPLOY: false`), Dockerfile.

| # | Rilievo | Gravità | Rispetto a |
|---|---|---|---|
| IN-1 | **`application.yml` contiene una configurazione ServiceNow (`snowcore`) con `client-id` e `client-secret` in chiaro**. È un residuo del template, estraneo a EURODIS. Lo stesso blocco c'è in `ce-eurodis-send-tracking` | **alta (sicurezza)** | Regola "credenziali solo da secret". Va rimosso; se la credenziale è reale va ruotata da chi la possiede |
| IN-2 | Nello stesso blocco c'è `retry.max-attempts: 3`. Oggi non è usato, ma se una configurazione di retry generica venisse riusata per il client EURODIS violerebbe RF-04 | media | RF-04, RNF-02 |
| IN-3 | Spring Boot **3.2.2**, groupId `it.poste.temp`, package `it.posteitaliane` | media | Blueprint: Spring Boot 3.5.14, `it.poste.ce`, `it.poste.dichiarato.eurodis.in`. Il mapper è già allineato |
| IN-4 | Mancano le dipendenze che la specifica richiede: `spring-kafka`, `spring-data-mongodb` (D1), un lock distribuito (D3, per esempio ShedLock), `micrometer-registry-prometheus`, `logstash-logback-encoder`, `spring-boot-starter-validation` | — | Specifica sezioni 3, 4, 9 (lavoro da fare, non un errore) |
| IN-5 | Helm `application.properties` è ancora il placeholder del template (`myvar`) | bassa | Sezione 8 della specifica |
| IN-6 | `server.servlet.context-path: /ce-dichiarato-eurodis-in` su porta 8080: utile per gli endpoint amministrativi di recupero (D6), se ammessi | — | D6 |

## 2. `ce-dichiarato-eurodis-mapper`

Allineato al blueprint: Spring Boot 3.5.14, Java 17, groupId `it.poste.ce`, package
`it.poste.dichiarato.eurodis.mapper`, constructor injection, DTO in snake_case, log JSON con
MDC, metriche con i nomi standard. **Test eseguiti** (`mvn -s settings.xml test`): **11/11
verdi** (consumer 3, mapper 5, servizio 3).

**Cosa fa oggi**

- Consuma da `preadvising.eud.pre.build` e pubblica su `preadvising.pre-enrichment`: coerente
  con la decisione del 30-10.
- Assume come corpo **un elemento di `GetShipmentResponse2` così com'è**: coerente con la
  sezione 3.2 della specifica di `-in` (corpo puro, metadati negli header). Gli header non li
  legge ancora.
- At-least-once reale: `ack-mode: record`, elaborazione sincrona, producer sincrono `acks=all`.
  È meglio dell'orchestratore, dove il blueprint segnala il commit anticipato come anomalia.
- Campi mappati:

| Campo ICD | Regola nel codice | Rispetto al mapping di Mary |
|---|---|---|
| `canale` | da config, default `EURODIS` | DF-04 aperto. Ma il mapper BEP passa `collo.id_ldv` **solo per il canale INVIOSYSTEM**: con `EURODIS` la LDV potrebbe non arrivare a PDB |
| `id_preadvising` | `UUID.randomUUID()` | Coerente con la decisione del 22-10 |
| `spedizione[0].rif_spedizione` | `edReference` senza decimali | ✓ |
| `spedizione[0].numero_colli` | `numberOfHandlingUnits`, `0` se assente | ✓ (in EURODIS il campo è obbligatorio) |
| `collo[].id_ldv` | `consignorsColloBarcode`, `""` se assente | ✓ |
| `internazionale.id_ldv_itz` | primo `europlateBarcode` non vuoto | Default provvisorio di DF-03. Non filtra il valore `0` del neighbourhood business (DF-18) |

**Incongruenze e domande per Mary**

| # | Rilievo | Gravità | Rif. |
|---|---|---|---|
| MAP-1 | **`flag_autoproduttore` non è valorizzato.** Nel mapping è COSTANTE `"S"` ed è il tratto che distingue l'iniziativa. Mancano anche `versione_tracciato` (1) e `progressivo` (obbligatorio per BEP) | ✅ **risolto 02-11** (`beb8fd6`): `flag_autoproduttore="S"`, `versione_tracciato=1`, `progressivo=1` (un messaggio = una spedizione). **Mary**: nel foglio la regola di `progressivo` dice "progressivo nell'esecuzione batch", va allineata | foglio "Mapping EURODIS" |
| MAP-2 | `id_preadvising` casuale + consegna at-least-once: se un messaggio viene rielaborato (riavvio, retry dell'error handler), a valle arrivano **due preadvising diversi per la stessa spedizione**. Serve una regola: id deterministico (da `edReference` + versione) oppure deduplica a valle. Va coordinato con RF-09 di `-in` (ripubblica solo se il contenuto cambia) | alta | Nuovo punto aperto |
| MAP-3 | Errore tecnico: l'eccezione è rilanciata ma non c'è un `DefaultErrorHandler` configurato. Vale il default di Spring (9 nuovi tentativi senza backoff, poi log e **salto del messaggio**). Payload non deserializzabile o non valido: scartato con log e metrica, nessuna DLT | alta | PA-32 |
| MAP-4 | Mancano quasi tutte le regole del foglio: cliente (F1), mittente, destinatario, peso in grammi, dimensioni, `data_spedizione`/`ora_spedizione` da `entranceTimestamp`, `no_firma`, contrassegno, `codici_servizi` e accessori, `consegna.note`, `id_ldv_associata`, `link_file_fisico_inviato`, `upload_time` | — | Lavoro da fare: la specifica del mapper deve partire dal foglio |
| MAP-5 | `edReference.toBigInteger()` tronca in silenzio un'eventuale parte decimale (`...401.5` → `...401`). La specifica di `-in` (RF-07) la considera invalida. Il mapper potrebbe usare la chiave del messaggio, già normalizzata da `-in` | bassa | RF-07 |
| MAP-6 | `dispatchPartnersDomesticShipmentNumber` è validato (`@NotBlank`, max 35) ma non mappato. Nel foglio va in `id_ldv_partner_master` | bassa | foglio "Mapping EURODIS" |
| MAP-7 | Il codice contiene riferimenti a punti aperti e documenti di analisi nei commenti (`PA-32`, `DF-04`, `PA-11a`, nome del file Excel). Sono utili oggi, ma le regole di sviluppo li escludono dal codice: vanno spostati in specifica o tracker quando i punti si chiudono | bassa | Regole di sviluppo |
| MAP-8 | `link_file_fisico_inviato`: la specifica di `-in` offre l'header `rifGrezzo`, che il mapper non legge ancora | media | Specifica di `-in`, sezione 3.2 |

## 3. `ce-eurodis-send-tracking`

Solo template, con la build sistemata. Stessi rilievi di `-in`: blocco ServiceNow con
credenziali in chiaro (IN-1), Spring Boot 3.2.2, groupId `it.poste.temp`. Senza specifica e
senza lo swagger EURODIS di tracking non c'è niente da confrontare.

## 4. Cosa propongo

1. **Subito**: rimuovere il blocco `snowcore` da `-in` e `send-tracking` e verificare con chi
   ha creato il template se la credenziale è reale (IN-1).
2. Allineare `-in` e `send-tracking` al blueprint (IN-3) prima di scrivere codice: è un
   commit di impostazione, come quello già fatto sul mapper.
3. Mary: integrare MAP-1…MAP-8 nella specifica del mapper e aprire il punto su MAP-2 (id
   deterministico o deduplica).
4. Estendere `mock-eurodis` per i criteri di accettazione di `-in` (`500`, timeout,
   `edReference` con `.0` o assente, campi di `GetShipmentResponse`, `401` in testo semplice).
