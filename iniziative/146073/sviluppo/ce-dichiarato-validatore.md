# `ce-dichiarato-validatore` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.5 · **Data**: 2026-11-25
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del validatore (Amelia)
**Intervento HLD**: 01 della fase 1, stima TOW 1.2 di 0,80
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-validatore` (in locale `gitposte/SDA/preadvising/ce-dichiarato-validatore`)
**Branch**: `develop` [DECISO, Diego 2026-11-24]. Stato: commit `6cd722a` del 25-11 su `develop`. Non si sviluppa su `master` né sui branch di altre iniziative: se la copia locale è su un altro branch si usa un `git worktree`.
**Stack**: Spring Boot 3, Java 17, Kafka, Drools (KIE), MongoDB
**Generato da**: [prompt-ce-dichiarato-validatore.md](prompt-ce-dichiarato-validatore.md)
**Fonti**: [analisi.md](../analisi.md), sezione "Contratto della fase 1" (AS-01…AS-07, **vincolante**); `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (intervento 01); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md` (§4, §5, §6); codice di `origin/develop` (`68083fb` letto il 16-11, `6cd722a` del 25-11)
**Documento collegato**: [ce-dichiarato-ldv.md](ce-dichiarato-ldv.md), dove sta la verifica Compliance USA

Etichette usate nel documento:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default. Va confermata (sezione 10).

> **Versione 0.5 (Diego, 2026-11-25): il validatore porta solo i campi.** La verifica Compliance USA
> (riconoscimento delle spedizioni soggette ed errori `1320`…`1323`) è stata **spostata in
> `ce-dichiarato-ldv`**, nel processo normale, dove `codice_prodotto` è sicuramente valorizzato
> (calcolato da ce-rules sulla LDV). In ingresso al validatore i flussi SDA reali non portano i codici
> prodotto in modo affidabile. Il validatore ora **non ha regola, errori né configurazione** di
> compliance: aggiunge i tre campi ai DTO e li propaga senza controlli su tutti i canali, SDA e PDB.
>
> **Nota storica.**
> - 0.1-0.3 (16-24 novembre): regola in un componente Java del validatore (`ComplianceUsaValidator`),
>   chiamato da `SdaFlussoHandler` e `PdbPreadvisingHandler`. Commit `090d037` (campi, regola, errori,
>   flag) e `43f5cbe` (chiavi `zonos_*` su Mongo con `@Field`).
> - 0.4 (25-11 mattina): verifica tolta dal `PdbPreadvisingHandler`, solo flussi SDA. Commit `c7f82eb`.
> - 0.5 (25-11): verifica tolta anche da `SdaFlussoHandler` e spostata in `ce-dichiarato-ldv`
>   (commit `1bd3517` del ldv). Nel validatore il commit `6cd722a` rimuove il package `compliance/`,
>   la metrica, la configurazione `config.compliance-usa` e le variabili `COMPLIANCE_USA_*` da helm,
>   svil e collaudo. I commit precedenti restano nella storia; `6cd722a` li supera.

---

## 1. Contesto e obiettivo

Le spedizioni verso gli USA che contengono merce devono rispettare la normativa USA **Entry Type 13**.
Nella fase 1 il preavviso porta due campi nuovi [FATTO, descrizione §2]: **Account Key** (uno per
spedizione, 52 caratteri) e **Product ID** (uno per articolo, 1-255 caratteri). C'è anche
`zonos_declaration_id`, solo **predisposto** (AS-01).

Il validatore legge il tracciato unico da `preadvising.pre-enrichment`, lo valida con le regole di
oggi e, se valido, lo pubblica su `preadvising.enrichment`; manda gli stati all'event store su
`preadvising.evensource` e salva il preavviso su Mongo `dichiarato_events`.

Obiettivo nella 146073 [DECISO, Diego 2026-11-25]: **i tre campi attraversano il validatore senza
perdersi e senza essere controllati**, su tutti i canali. Senza la modifica dei DTO i campi si
perderebbero (3.1).

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Riconoscimento delle spedizioni soggette, controllo di presenza e lunghezza, errori `1320`…`1323` | `ce-dichiarato-ldv`, processo normale ([ce-dichiarato-ldv.md](ce-dichiarato-ldv.md)) |
| Verifica sui flussi PDB (PDB, PDW, ILP, EUD) | nessuno, finché non arrivano le specifiche (PA-14) |
| Lookup in anagrafica, chiamate a Zonos, valorizzazione del Declaration ID | fase 2 (AS-06) |
| Normalizzazione, `trim`, conversione dei campi | nessuno (R-04) |
| Acquisizione dei campi dai canali | builder, adapter (AS-05) |

## 2. Requisiti e interventi HLD coperti

| Fonte | Cosa chiede | Come si copre |
|---|---|---|
| HLD fase 1, int. 01: "Modifica dto del applicativo" | campi nuovi nei DTO, propagazione | 3.1, 5 |
| HLD fase 1, int. 01: "logica per riconoscere queste spedizioni" e "nuove logiche di validazione" | riconoscimento e validazione | **spostati in `ce-dichiarato-ldv`** [DECISO, Diego 25-11]: l'intervento 01 resta stimato sul validatore, ma la logica è nel ldv |
| Descrizione §4: Account Key in testata, Product ID negli articoli | cardinalità | 5 |
| Descrizione §5: nessuna incompatibilità con eventi storici e scenari non USA | campi opzionali | 5 |

## 3. Dove si interviene nel codice

### 3.1 DTO e serializzazione [FATTO, codice]

- L'`ObjectMapper` del servizio ha `FAIL_ON_UNKNOWN_PROPERTIES = false` (`config/AppConfig.java`):
  un campo che non è nel DTO viene ignorato in lettura senza errori, quindi **si perde**.
- In uscita `FlussoHandler.processaMessaggioValido` pubblica su `preadvising.enrichment` il JSON del
  DTO tipizzato; partono dal DTO anche l'evento per l'event store (`EventStorePayloadUtil`), il
  salvataggio su Mongo `dichiarato_events` (`PreadvisingEvents`) e i cloni del multicollo
  (`LdvUtil.clonaConLdvFiglia`, `SdaFlussoHandler.clonaConSingoloCollo`).
- Aggiunti i campi ai DTO, tutti questi punti li riportano senza altre modifiche.

| Classe (`kafka/dto/`) | Campo (stato al commit `6cd722a`) |
|---|---|
| `SpedizioneDTO` | `zonosAccountKey` e `zonosDeclarationId`, ciascuno con `@JsonProperty("zonos_…")`, `@Field("zonos_…")` e `@ToString.Exclude` |
| `ArticoloDTO` | `zonosProductId` con `@JsonProperty("zonos_product_id")`, `@Field("zonos_product_id")` e `@ToString.Exclude` |
| `ColloDTO`, `DichiaratoDTO` | nessuna modifica |

Regole per i campi:
- tipo `String`, nessun default, nessuna trasformazione (AS-01, R-04);
- **nessuna annotazione Bean Validation** (`@Size`, `@NotBlank`): la regola semantica "Validazione
  annotazioni DTO" valida il DTO in cascata e scarterebbe con codici `_OBBL_…` anche spedizioni non
  soggette (VAL-AS-10);
- `@Field` serve perché il `MongoConverter` di Spring Data usa il nome del campo Java e ignora
  `@JsonProperty`: senza, su Mongo le chiavi sarebbero camelCase (RV-05, VAL-AS-20);
- `@ToString.Exclude` su tutti e tre: il DTO finisce nei log in più punti (per esempio a WARN in
  `salvaErroreRegole`) e l'Account Key non deve comparire (VAL-AS-11);
- il `null` si serializza come oggi: l'`ObjectMapper` del validatore non ha `NON_NULL`, quindi i campi
  assenti escono come `null` espliciti (VAL-AS-18, AS-07).

### 3.2 Handler [FATTO, `6cd722a`]

`CanaleFlussoResolver.resolve` sceglie l'handler. **Nessun handler fa controlli di compliance**:

| Handler | Canali | Campi `zonos_*` |
|---|---|---|
| `SdaFlussoHandler` | `IF`, `IS`, `IE` e i canali sconosciuti | propagati; la chiamata alla verifica è stata tolta (`6cd722a`) |
| `PdbPreadvisingHandler` | `PDB_INVIOSYSTEM`, `PDB_INVIOFILE`, `PDB_INVIOEASY`, `PDB_STAMPAMASSIVA`, `EUD_INVIOFILE`, `EUD_INVIOSYSTEM` | propagati; nessuna verifica (`c7f82eb`) |
| `PdbPdwFlussoHandler` | `PDB`, `PDW`, `ILP` (dall'adapter) | propagati |
| `TfiFlussoHandler` | `MYSDA`, `SDA_WS`, `INVIO_WEB`, `TFI/TWS/BNC` | propagati |
| `TupFlussoHandler` | `TUP`, `OMP` | propagati |

Le regole Drools (semantic, logic, PDB) e la configmap **non cambiano**.

### 3.3 Cosa è stato rimosso con `6cd722a`

- package `compliance/` (`ComplianceUsaProperties`, `ComplianceUsaValidator`, `EsitoComplianceUsa`) e
  relativi test;
- in `FlussoHandler` il metodo `aggiungiErroriComplianceUsa` e la metrica
  `business_compliance_usa_verifiche_total`;
- in `application.yaml` il blocco `config.compliance-usa`; in `.helm/values.yaml`, `deploy-svil` e
  `deploy-coll` le variabili `COMPLIANCE_USA_*`.

I test rimasti: propagazione JSON e Mongo, `SdaFlussoHandlerZonosCampiTest` (nuovo) e
`PdbPreadvisingHandlerTest` adeguato: una spedizione USA senza campi passa senza errori `1320`…`1323`
e i campi presenti arrivano invariati.

## 4. Dati

| Dato | Percorso JSON | Uso |
|---|---|---|
| Account Key | `spedizione[].zonos_account_key` | solo propagazione |
| Declaration ID | `spedizione[].zonos_declaration_id` | solo propagazione |
| Product ID | `spedizione[].collo[].articolo[].zonos_product_id` | solo propagazione, sul suo articolo |

## 5. Regole funzionali

| ID | Regola |
|---|---|
| RV-01 | `zonos_account_key` e `zonos_declaration_id` in `SpedizioneDTO`, `zonos_product_id` in `ArticoloDTO`; nomi JSON esattamente questi [DECISO, AS-01] |
| RV-02 | I tre campi sono opzionali: un messaggio senza campi si comporta esattamente come oggi (R-05) |
| RV-03 | I valori escono su `preadvising.enrichment`, nell'evento dell'event store e su Mongo **identici a come sono entrati**: niente `trim`, maiuscole o troncamenti (R-04). Ogni `zonos_product_id` resta sul suo articolo, anche nei cloni del multicollo |
| RV-04 | `zonos_declaration_id` non ha regole in fase 1 |
| RV-05 | [DECISO, Diego 24-11] Su MongoDB (`dichiarato_events`, anche `dichiarato_ldv_history` se contiene la spedizione) le chiavi sono `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id` |
| RV-06 | [DECISO, Diego 25-11] Il validatore **non verifica** i campi su nessun canale: niente errori `1320`…`1323`, niente scarti per compliance, niente metrica di compliance. La verifica è in `ce-dichiarato-ldv` |
| RV-07 | Nessun valore dei campi `zonos_*` nei log (`@ToString.Exclude`) |

## 6. Esempi [dati inventati]

Ingresso su `preadvising.pre-enrichment` (ridotto):

```json
{
  "canale": "IF",
  "id_preadvising": "b1000000-0000-4000-8000-000000000001",
  "spedizione": [{
    "codice_prodotto": "456",
    "tipo_merce": "M",
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "destinatario": { "codice_nazione": "USA", "codice_nazione_iso_2": "US" },
    "collo": [{ "articolo": [
      { "posizione": "1", "zonos_product_id": "PRD-TEST-0001" },
      { "posizione": "2" }
    ]}]
  }]
}
```

Uscita su `preadvising.enrichment` (`tipo_lavorazione: "validato"`): i campi identici, nelle stesse
posizioni; `zonos_declaration_id` e il `zonos_product_id` mancante escono `null`. **Nessun errore**,
anche se il secondo articolo non ha Product ID: se la spedizione è soggetta, lo scarto `1322` lo dà
`ce-dichiarato-ldv` più avanti nella catena.

```json
{
  "canale": "IF",
  "tipo_lavorazione": "validato",
  "spedizione": [{
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "zonos_declaration_id": null,
    "collo": [{ "articolo": [
      { "posizione": "1", "zonos_product_id": "PRD-TEST-0001" },
      { "posizione": "2", "zonos_product_id": null }
    ]}]
  }]
}
```

Lo stesso vale su `PDB_INVIOFILE`, `EUD_INVIOSYSTEM`, `PDW`, `MYSDA`, `TUP`.

## 7. Configurazione

Nessuna. Il blocco `config.compliance-usa` e le variabili `COMPLIANCE_USA_*` sono stati rimossi
(3.3); la configurazione della verifica sta in `ce-dichiarato-ldv` con prefisso `compliance-usa`.
Nessun secret nuovo.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato il messaggio della sezione 6, su `preadvising.enrichment` esce un messaggio con `zonos_account_key`, `zonos_declaration_id` e ogni `zonos_product_id` identici e nelle stesse posizioni dell'ingresso |
| AC-02 | Dato un messaggio senza campi nuovi, l'uscita è uguale a quella di oggi tranne i campi a `null`, e nessuna regola esistente cambia esito |
| AC-03 | L'evento `PREAD_EMESSO` su `preadvising.evensource` e il documento in `dichiarato_events` contengono i tre campi; su Mongo le chiavi sono `zonos_*`, nessuna chiave camelCase |
| AC-04 | Una spedizione USA, con merce e prodotto `456`, senza Account Key e senza Product ID, su `IF`, `IS`, `IE`, `PDB_INVIOFILE`, `EUD_INVIOSYSTEM`, `PDW`, `MYSDA`, `TUP`: nessun errore `1320`…`1323`, il messaggio prosegue |
| AC-05 | Nel multicollo a riga singola (`002`) ogni clone ha `zonos_account_key` della spedizione e, sul suo collo, gli articoli con il loro `zonos_product_id` |
| AC-06 | Una spedizione con `zonos_product_id` di 300 caratteri passa senza errori (nessuna Bean Validation) |
| AC-07 | Nei log (anche a DEBUG e nel WARN di `salvaErroreRegole`) non compaiono i valori dei campi `zonos_*` |
| AC-08 | Non esistono più la proprietà `config.compliance-usa`, le variabili `COMPLIANCE_USA_*` e la metrica `business_compliance_usa_verifiche_total` nel validatore |
| AC-09 | I test esistenti restano verdi. Eccezione nota: i 153 test `regoledrools/Invio*Test` falliscono già su `develop` prima della 146073 (verificato il 24-11) e si sistemano a parte |

## 9. Casi di test

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit (Jackson) | JSON → DTO → JSON con e senza campi | campi uguali e nella stessa posizione; senza campi → `null` | AC-01, AC-02 |
| TC-02 | unit (`MongoConverter`) | `PreadvisingEvents` con i tre campi | chiavi `zonos_*`, nessuna camelCase | AC-03 |
| TC-03 | handler SDA (`SdaFlussoHandlerZonosCampiTest`) | spedizione USA soggetta senza campi su `IF` | nessun errore `1320`…`1323`, invio su enrichment con i campi | AC-04 |
| TC-04 | handler PDB (`PdbPreadvisingHandlerTest`) | stessa spedizione su `PDB_INVIOFILE`, `EUD_INVIOSYSTEM` | nessun errore `1320`…`1323`, campi propagati | AC-04 |
| TC-05 | handler di passaggio | stessa spedizione su `PDW`, `MYSDA`, `TUP` | campi propagati | AC-04 |
| TC-06 | handler SDA multicollo `002` | 2 colli con Product ID diversi | cloni con i campi giusti | AC-05 |
| TC-07 | log capture | TC-03 a DEBUG | nessun valore `zonos_*` | AC-07 |
| TC-08 | regressione | suite esistente | verde (salvo i 153 preesistenti) | AC-09 |
| TC-09 | integrato svil | messaggi a mano su `preadvising.pre-enrichment` | campi su `preadvising.enrichment` e su `dichiarato_events`; l'eventuale scarto di compliance arriva dal ldv | AC-01, AC-03 |

## 10. Assunzioni e domande aperte

| ID | Contenuto | Stato |
|---|---|---|
| VAL-AS-10 | Nessuna annotazione Bean Validation sui campi nuovi | in vigore |
| VAL-AS-11 | L'Account Key non va nei log: `@ToString.Exclude` (dal `6cd722a` anche su `zonos_declaration_id`; c'era già su `zonos_product_id`) | in vigore; riservatezza da confermare con Poste |
| VAL-AS-12, -13, -14, -16, -17, -19, -21 | Perimetro della regola negli handler, regola in Java, unione con gli errori semantici, confronti, codici, flag, esclusione del PDB | **superate** il 25-11: la regola non è più nel validatore. Le decisioni ancora valide (codici, confronti, flag, PDB escluso) sono nel funzionale del ldv |
| VAL-AS-15 | `tipi-merce-documenti` = `D` su `tipo_merce` | decisa (23-11), ora applicata nel ldv |
| VAL-AS-18 | Campi assenti in uscita come `null` espliciti | in vigore (AS-07) |
| VAL-AS-20 | Chiavi Mongo `zonos_*` | decisa (24-11) |
| VAL-DA-03 | Copie disallineate dei DRL fra classpath e configmap | resta da segnalare, fuori perimetro |
| VAL-DA-04 | Le spedizioni USA dai canali di passaggio (portali, web service, adapter, TUP) vanno controllate? | ora riguarda il ldv: i portali passano dal processo semplificato, che non verifica (vedi [ce-dichiarato-ldv.md](ce-dichiarato-ldv.md)) |

## 11. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1, R-01…R-07, PA-01…PA-14.
- [ce-dichiarato-ldv.md](ce-dichiarato-ldv.md): la verifica Compliance USA.
- `cliente/HLD_146073_dati_preadvising_fase_1.xlsx`: intervento 01.
- Codice: `origin/develop` del validatore, commit `090d037`, `43f5cbe`, `c7f82eb`, `6cd722a`.
