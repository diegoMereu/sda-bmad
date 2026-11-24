# `ce-dichiarato-smistatore` — Documento funzionale per lo sviluppo (fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13, nuovi campi sul preadvising · **Fase**: 1 · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst) · **Destinataria**: sviluppatrice back-end della catena preadvising
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-smistatore` (locale `gitposte/SDA/preadvising/ce-dichiarato-smistatore`)
**Branch**: `develop` [DECISO, Diego 2026-11-24: sostituisce il branch dedicato `146073_compliance_usa_fase1` deciso il 16-11]. Mai sviluppo su `master` né su branch di altre iniziative
**Codice letto**: `origin/develop` @ `e03c333` (2026-11-12), con `git show`. La working copy locale è su `develop` con modifiche non committate di altri (`.helm/values.yaml`, `PalmariMapperService.java`, `application*.yaml`): **non** partire da lì, lavorare in un `git worktree` dopo il `fetch`
**Stack**: Spring Boot 3.5.14, Java 17, Kafka
**Generato da**: [prompt-ce-dichiarato-smistatore.md](prompt-ce-dichiarato-smistatore.md)
**Fonti**: [analisi.md](../analisi.md), sezione "Contratto della fase 1" (AS-01…AS-06, **vincolante**); HLD `cliente/HLD_146073_dati_preadvising_fase_1.xlsx`, intervento 03; `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`
**Documento gemello**: [ce-dichiarato-orchestratore.md](ce-dichiarato-orchestratore.md)

Etichette usate nel documento:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default; da confermare (sezione 10).

> **Il contratto della fase 1 (AS-01…AS-07 di `analisi.md`) non si cambia.** Buchi e incoerenze
> trovati sono fra le assunzioni SMI-xx.

---

## 1. Contesto e obiettivo

Lo smistatore consuma `preadvising.completed` (pubblicato dall'orchestratore a lavorazioni
completate) e, per ogni preavviso:

1. completa filiale di destinazione e data prevista di consegna (chiamate a `ce-anagrafica`);
2. lo inoltra **o** su `preadvising.completed.poste` (canali in `CANALI_POSTE`) **o** su
   `preadvising.completed.sda` (canali in `smistatore.canali.sda`);
3. costruisce il tracciato per i **palmari** (`PalmariMapperService`, formato `ANALDV`) e lo invia,
   salvo i canali in `CANALI_ESCLUSI_PALMARI`.

Con l'iniziativa 146073 il preavviso porta `zonos_account_key` e `zonos_declaration_id` sulla testata di ogni
`spedizione[]` e `zonos_product_id` su ogni `spedizione[].collo[].articolo[]` (AS-01). `zonos_declaration_id` in
fase 1 è sempre assente o `null`.

Obiettivo: i tre campi **arrivano identici su `.completed.poste` e `.completed.sda`**, con
`zonos_product_id` sul suo articolo, e **non** vanno ai palmari (AS-06). Lo smistatore non li valida e non
li trasforma (R-02, R-04).

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Scrittura dei campi nelle SEW | consumer `sew_spedizioni` (int. 07) e `sew_spedizioni_poste` (int. 08) |
| Palmari (`sew_sped_pre_adv_online_out_tot`), T&T-Repo, OneTracking | nessuno in fase 1 (AS-06, PA-11) |
| Propagazione nell'orchestratore | [ce-dichiarato-orchestratore.md](ce-dichiarato-orchestratore.md) (int. 02) |

## 2. Interventi HLD coperti

| Int. | Cosa chiede l'HLD [FATTO] | Indicazioni dalla descrizione [FATTO] | Dove nel documento |
|---|---|---|---|
| 03 (fase 1) | Riceve e propaga i nuovi campi. Stima TOW 1.2: 0,40 gg | Inoltro solo ai destinatari previsti dai contratti; compatibilità con i destinatari non adeguati | sezioni 3, 5 |

## 3. Dove si interviene nel codice

### 3.1 Ingresso e uscite per ramo [FATTO, `origin/develop`]

| Ramo | DTO | Come si costruisce il messaggio | I campi nuovi oggi |
|---|---|---|---|
| Ingresso `preadvising.completed` | `KafkaConsumer.processaMessaggio` → `objectMapper.readValue(..., SmistatoreDTO.class)`; tutti i DTO con `ignoreUnknown`, `FAIL_ON_UNKNOWN_PROPERTIES=false` (`AppConfig`) | — | **scartati** in deserializzazione (anche la canary property dell'orchestratore) |
| Poste, `preadvising.completed.poste` | `SmistatoreDTO` | `SmistatoreConsumerService.inviaErmes(dto, "poste")` → `serialize(dto)`: **lo stesso DTO d'ingresso**, arricchito di `consegna.id_fil_dest`, `filiale`, `data_prevista_consegna` | assenti |
| SDA, `preadvising.completed.sda` | `SmistatoreDTO` | `inviaErmes(dto, "sda")`, stessa serializzazione | assenti |
| Palmari, topic `palmari` o `palmari-bs` | `Traces` / `AnaLdv` (`kafka/dto/palmari`) | `PalmariMapperService.mapFrom(dto)`: mapping **campo per campo** su un formato proprio. Legge spedizione e colli (`mapCollo`), **non legge gli articoli** | non mappati |
| Evento di stato `PREAD_INVIATO_PALMARI` (solo con `smistatore.palmari.evento-stato.enabled=true`, default `false`) | `MacchinaStatiService.inviaEvento` → `objectMapper.valueToTree(dto)` come `eventData` | `SmistatoreDTO` intero | assenti |

Non esistono mapping specifici per Poste e per SDA: i due rami pubblicano **lo stesso JSON**, solo su
topic diversi, e un preavviso va su **uno solo** dei due (prima si prova `CANALI_POSTE`, poi
`smistatore.canali.sda`; se nessuno dei due, "Ldv non inviabile ad ermes" e solo palmari).

`SmistatoreDTO` è un **sottoinsieme** del tracciato: per esempio non ha `cliente` né `codici_servizi`.
Ciò che non è dichiarato non arriva a valle. Per i campi nuovi basta dichiararli nei DTO di spedizione
e articolo, che sono già in `SmistatoreDTO.spedizione`.

### 3.2 Cosa si fa

| Punto | Modifica |
|---|---|
| `kafka/dto/SpedizioneDTO.java` | due campi `String` nuovi, `zonos_account_key` e `zonos_declaration_id` (in questa classe i nomi Java sono snake_case, come `rif_spedizione`), con `@JsonInclude(JsonInclude.Include.NON_NULL)` sul campo (SMI-02) |
| `kafka/dto/ArticoloDTO.java` | campo `String` nuovo: `@JsonProperty("zonos_product_id") private String zonosProductId;` (in questa classe i nomi Java sono camelCase con `@JsonProperty`, come `codiceTaric`), con `@JsonInclude(NON_NULL)` |
| `SmistatoreDTO`, `ColloDTO` | nessuna modifica (`ColloDTO.articolo` è già `List<ArticoloDTO>`) |
| `SmistatoreConsumerService` | **nessuna modifica**: `inviaErmes` serializza il DTO, quindi i campi escono da soli sui due topic |
| `PalmariMapperService`, `kafka/dto/palmari/*` | **nessuna modifica**: i palmari restano fuori (AS-06, SMI-01). Attenzione: nella working copy locale questo file ha modifiche non committate di altri |
| `application*.yaml`, `.helm`, `deploy-*` | nessuna modifica |
| test | casi della sezione 9: per i DTO sul modello di `kafka/dto/NuoviCampiPdwTest`, per i palmari su `PalmariMapperCaratterizzazioneTest` (con `caratterizzazione/palmari-mapper.json`), per l'instradamento su `SmistatoreCanaliEurodisTest` |

Regole sui campi nuovi (AS-01, R-04, R-05): `String`, opzionali, senza default, senza vincoli e senza
trasformazioni; nessun log dei valori.

## 4. Esempi [dati inventati]

### 4.1 Ingresso da `preadvising.completed`, estratto

```json
{
  "id_preadvising": "a1460730-0000-4000-8000-000000000001",
  "canale": "PDB_INVIOSYSTEM",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-USA-0001",
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "consegna": { "filiale": "TST" },
    "collo": [{
      "id_ldv": "TST0000000146",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": "2", "zonos_product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": "1", "zonos_product_id": "PRD-TEST-0002" }
      ]
    }]
  }],
  "canary_7f3a": "x"
}
```

### 4.2 Uscita su `preadvising.completed.poste` (canale Poste), estratto

```json
{
  "id_preadvising": "a1460730-0000-4000-8000-000000000001",
  "canale": "PDB_INVIOSYSTEM",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-USA-0001",
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "consegna": { "filiale": "TST", "id_fil_dest": "TST" },
    "collo": [{
      "id_ldv": "TST0000000146",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "quantita": "2", "zonos_product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "quantita": "1", "zonos_product_id": "PRD-TEST-0002" }
      ]
    }]
  }]
}
```

Per un canale SDA (es. `MYSDA`) il messaggio è lo stesso, su `preadvising.completed.sda`.
`zonos_declaration_id` non compare (`null`, SMI-02). La canary property non passa (comportamento attuale).

### 4.3 Uscita palmari

Invariata rispetto a oggi: nessun campo nuovo nel tracciato `ANALDV`, con o senza i campi in ingresso.

### 4.4 Preavviso non USA

Nessun campo nuovo in ingresso: le uscite Poste/SDA sono **identiche a quelle di oggi** (nessuna chiave
`zonos_account_key`, `zonos_declaration_id`, `zonos_product_id`, nemmeno `null`).

## 5. Regole funzionali

### 5.1 Destinatari dei campi [ASSUNTO SMI-01]

| Destinatario | Riceve i campi | Perché |
|---|---|---|
| `preadvising.completed.poste` | **sì** | ne legge il consumer `sew_spedizioni_poste` (int. 08) |
| `preadvising.completed.sda` | **sì** | ne legge il consumer `sew_spedizioni` (int. 07) |
| Palmari (`palmari`, `palmari-bs`) | **no** | AS-06; il mapper non li legge, quindi basta non toccarlo |
| Evento di stato `PREAD_INVIATO_PALMARI` | sì, se il flag è attivo | è l'`eventData` del DTO intero; va all'event store, che li tratta nell'int. 04 |

"Inoltro solo ai destinatari previsti" della descrizione è quindi rispettato **senza logica nuova**:
nessun filtro per canale, per nazione o per tipo di spedizione nello smistatore. I campi escono sul
topic Poste o SDA del preavviso, secondo le regole di instradamento di oggi.

### 5.2 Compatibilità con i destinatari non adeguati [ASSUNTO SMI-02]

- L'`ObjectMapper` dello smistatore **non** è `NON_NULL`: oggi serializza anche i campi `null`. Senza
  accorgimenti tutti i preavvisi, anche quelli non USA, uscirebbero con `"zonos_account_key": null`,
  `"zonos_declaration_id": null` e `"zonos_product_id": null` su ogni articolo.
- Per non cambiare la forma dei messaggi di chi non è adeguato, i tre campi hanno
  `@JsonInclude(NON_NULL)` **sul singolo campo**: escono solo se valorizzati. Il resto del DTO resta
  com'è (non si cambia l'`ObjectMapper` globale: cambierebbe la forma di tutti i messaggi).
- Un consumer di `.completed.poste`/`.completed.sda` che non tollera campi sconosciuti si romperebbe
  solo sui preavvisi USA. I due consumer SEW vengono adeguati (int. 07, 08); gli altri consumer dei due
  topic non sono censiti (SMI-03).

### 5.3 Regole riassuntive

| ID | Regola |
|---|---|
| RS-01 | `zonos_account_key`, `zonos_declaration_id` in `SpedizioneDTO`; `zonos_product_id` in `ArticoloDTO`; `String`, opzionali, `NON_NULL` sul campo |
| RS-02 | I campi escono su `.completed.poste` o `.completed.sda` con valori identici e cardinalità del contratto |
| RS-03 | Il tracciato palmari non cambia |
| RS-04 | Arricchimenti di oggi (filiale, data prevista consegna) e instradamento invariati |
| RS-05 | Preavvisi senza campi: uscite identiche a oggi |
| RS-06 | Valori dei campi mai nei log, metriche, span (il DEBUG di payload esistente resta com'è: è già `debug`) |

## 6. Configurazione

Nessuna proprietà nuova. Restano invariati `CANALI_POSTE`, `smistatore.canali.sda`,
`CANALI_ESCLUSI_PALMARI`, `CANALI_BS_PALMARI`, `smistatore.palmari.invio-forzato`.

## 7. Requisiti non funzionali e osservabilità

- **Prestazioni**: nessun impatto.
- **Log, metriche, span**: nessuna aggiunta. Non loggare i valori (SMI-04).
- **Sonar**: costanti per i valori d'esempio nei test; nessun riferimento a PA/AS nei commenti.

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato 4.1 con canale `PDB_INVIOSYSTEM`, il messaggio su `preadvising.completed.poste` ha `zonos_account_key` sulla spedizione e i due `zonos_product_id` sui rispettivi articoli, identici all'ingresso |
| AC-02 | Dato 4.1 con canale `MYSDA`, lo stesso vale su `preadvising.completed.sda`, e nulla esce su `.completed.poste` |
| AC-03 | Dato 4.1, il messaggio palmari è uguale (campo per campo) a quello prodotto dallo stesso input senza i campi nuovi |
| AC-04 | Dato un ingresso senza i campi (4.4), le uscite Poste/SDA non contengono le chiavi `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id` |
| AC-05 | Dato `zonos_declaration_id: null` in ingresso, l'uscita non ha la chiave `zonos_declaration_id` |
| AC-06 | Dato un preavviso con 2 colli e 3 articoli, ogni `zonos_product_id` resta sul proprio collo e articolo in uscita |
| AC-07 | Dato `zonos_account_key` di lunghezza diversa da 52, viene propagato identico (la validazione non è dello smistatore) |
| AC-08 | Filiale di destinazione e data prevista di consegna sono calcolate come oggi anche con i campi nuovi |
| AC-09 | Con `smistatore.palmari.evento-stato.enabled=true`, l'`eventData` di `PREAD_INVIATO_PALMARI` contiene i campi |
| AC-10 | I test esistenti, fra cui `PalmariMapperCaratterizzazioneTest`, restano verdi |

## 9. Casi di test

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit (service, `KafkaTemplate` simulato) | 4.1 con canale Poste | payload su topic `poste` come 4.2 | AC-01 |
| TC-02 | unit | 4.1 con canale SDA | payload su topic `sda`, nessun invio su `poste` | AC-02 |
| TC-03 | unit (caratterizzazione palmari) | 4.1 e 4.1 senza i campi | `Traces` identici | AC-03 |
| TC-04 | unit | preavviso senza campi, con `zonos_declaration_id: null` | chiavi assenti | AC-04, AC-05 |
| TC-05 | unit | 2 colli × più articoli | `zonos_product_id` al loro posto | AC-06 |
| TC-06 | unit | `zonos_account_key` di 10 caratteri, `zonos_product_id` di 300 | propagati identici | AC-07 |
| TC-07 | regressione | suite esistente | verde | AC-08, AC-10 |
| TC-08 | unit | flag evento stato attivo | `eventData` con i campi | AC-09 |
| TC-09 | integrato svil | preavviso USA costruito a mano su `preadvising.pre-enrichment` (AS-05), un canale Poste e uno SDA | campi su `.completed.poste` / `.completed.sda`, palmari invariati | AC-01…AC-03 |

## 10. Assunzioni e domande aperte

Dal contratto della fase 1 (`analisi.md`, vincolanti): AS-01 nomi e posizione, AS-04 SEW, AS-05
ingresso, AS-06 palmari, T&T-Repo e OneTracking fuori dalla fase 1.

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| SMI-01 | **Destinatari**: i campi vanno su `.completed.poste` e `.completed.sda` (lette dai consumer SEW, int. 07 e 08) e non ai palmari. Non serve un filtro: il mapper palmari non li legge | nessuna logica nuova, `PalmariMapperService` invariato | Diego (si lega a PA-11) |
| SMI-02 | **Forma dei messaggi**: l'`ObjectMapper` dello smistatore serializza i `null`. Per non cambiare i messaggi non USA i campi nuovi hanno `@JsonInclude(NON_NULL)` sul campo | chiavi assenti se non valorizzate | Diego |
| SMI-03 | **Altri consumer** di `.completed.poste` e `.completed.sda` oltre ai consumer SEW (es. strumenti di retry, servizi di altri team): non censiti. Vanno verificati per la tolleranza ai campi sconosciuti | nessuna verifica nello smistatore | Diego / Poste |
| SMI-04 | Valori dei campi mai nei log, metriche, span | come detto | — |
| SMI-05 | **Working copy locale** con modifiche non committate di altri su `PalmariMapperService` e configurazione: il branch dell'iniziativa parte da `origin/develop` aggiornato, non dalla working copy | worktree dopo `fetch` | sviluppatrice |
| SMI-06 | `SmistatoreDTO` è un sottoinsieme del tracciato (non ha `cliente`, `codici_servizi`): è il comportamento di oggi, fuori dal perimetro. Lo si segnala perché "inoltro senza perdita" vale solo per i campi dichiarati | nessuna modifica | — |

## 11. Riferimenti

- [analisi.md](../analisi.md), "Contratto della fase 1".
- [ce-dichiarato-orchestratore.md](ce-dichiarato-orchestratore.md): come i campi arrivano su `preadvising.completed`.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md): instradamento dello smistatore.
- [contesto/linee-guida-sviluppo.md](../../../contesto/linee-guida-sviluppo.md).
