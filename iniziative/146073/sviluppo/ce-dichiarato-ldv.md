# `ce-dichiarato-ldv` — Documento funzionale per lo sviluppo (Compliance USA, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato) · **Versione**: 0.1 · **Data**: 2026-11-25
**Autrice**: Mary (analyst) · **Destinatario**: sviluppatore del ldv (Amelia)
**Intervento HLD**: nessuno. Il ldv non è nell'HLD della fase 1 (PA-10); la verifica Compliance USA è la logica dell'intervento 01 (validatore), spostata qui da Diego il 2026-11-25
**Repository**: `gitlab.alm.poste.it/CORRIERE-ESPRESSO/PREADVISING/ce-dichiarato-ldv` (in locale `gitposte/SDA/preadvising/ce-dichiarato-ldv`)
**Branch**: `develop` [DECISO, Diego 2026-11-24, come gli altri servizi preadvising]. Stato: commit `1bd3517` del 25-11 su `develop`, 78 test verdi
**Stack**: Spring Boot 3, Java 17, Kafka, MongoDB, client REST verso ce-rules, ce-vendite, ce-ldv, ce-anagrafica
**Generato da**: [prompt-ce-dichiarato-ldv.md](prompt-ce-dichiarato-ldv.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" (AS-01…AS-07, **vincolante**); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md` (§4 `ce-dichiarato-ldv`); decisione di Diego del 25-11; codice di `origin/develop` al commit `1bd3517`
**Documento collegato**: [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md) 0.5 (il validatore ora porta solo i campi)

Etichette usate nel documento:
- **[FATTO]**: scritto nell'HLD, nella descrizione o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default. Va confermata (sezione 11).

> **Perché la verifica è qui [DECISO, Diego 2026-11-25].** La regola R-01 riconosce le spedizioni
> soggette anche dal prodotto (`codice_prodotto` oppure `id_servizio`). In ingresso al validatore i
> flussi SDA reali non portano i codici prodotto in modo affidabile; nel ldv, nel processo normale,
> `codice_prodotto` è sicuramente valorizzato, perché lo calcola ce-rules sulla LDV. Per questo la
> verifica (prima nel validatore, commit `090d037`, `43f5cbe`, `c7f82eb`) è stata spostata qui
> (`1bd3517`) e tolta dal validatore (`6cd722a`). La regola è **identica** a quella che c'era nel
> validatore; cambia solo il modo di riportare gli errori (un solo errore per messaggio, 5.4).

---

## 1. Contesto e obiettivo

Il ldv consuma `preadvising.enrichment.ldv` (lavorazione `ldv` dell'orchestratore), assegna o genera
la LDV della spedizione, calcola il prodotto con ce-rules, fa i controlli di business e ripubblica il
tracciato su `preadvising.enrichment` con `result` `OK` o `KO` [FATTO, `application.yaml`,
`KafkaConsumer`].

Nella 146073 il ldv deve:

1. **portare i campi** `zonos_account_key`, `zonos_declaration_id` (spedizione) e `zonos_product_id`
   (articolo): senza dichiararli nei DTO si perderebbero in uscita (descrizione §4: "mantenere i campi
   nell'associazione della LDV");
2. **verificare** presenza e lunghezza di Account Key e Product ID sulle spedizioni soggette (R-01,
   R-02, R-03), con gli errori `1320`…`1323` (AS-03), **solo nel processo normale**.

**Non fa**:

| Fuori perimetro | Riferimento |
|---|---|
| Verifica nel processo semplificato (`processEventoSemplificato`, preadvising dei portali: `TFI`, `TWS`, `BNC`, `MYSDA`, `SDA_WS`, `INVIO_WEB`) | 3.2, LDV-AS-02 |
| Verifica sui flussi PDB (PDB, PDW, ILP, EUD): passano da `ce-dichiarato-ldv-pdb`, non da qui | PA-14, fino alle specifiche |
| Lookup in anagrafica, chiamate a Zonos, valorizzazione del Declaration ID | R-02, AS-06 |
| Trasformazione dei campi (`trim`, maiuscole, troncamenti) | R-04 |

## 2. Requisiti coperti

| Fonte | Cosa chiede | Dove nel documento |
|---|---|---|
| Descrizione §4, `ce-dichiarato-ldv`: mantenere i campi nell'associazione della LDV | campi nei DTO, propagazione | 3.1, 5.1 |
| HLD fase 1, int. 01: riconoscere le spedizioni soggette e validarle (spostato qui il 25-11) | regola R-01, controlli R-02, errori R-03 | 5.2, 5.3, 5.4 |
| Descrizione §5: nessun impatto su scenari non USA ed eventi storici | campi opzionali, flag spento | 5.1, 7 |

## 3. Dove si interviene nel codice [FATTO, commit `1bd3517`]

### 3.1 DTO

| Classe (`kafka/dto/`) | Campo |
|---|---|
| `SpedizioneDTO` | `zonosAccountKey`, `zonosDeclarationId` |
| `ArticoloDTO` | `zonosProductId` |

Ogni campo ha `@JsonProperty("zonos_…")`, `@Field("zonos_…")` con il nome del tracciato e
`@ToString.Exclude`. Tipo `String`, nessun default, nessuna Bean Validation. L'`ObjectMapper` del ldv
ha `NON_NULL` (`config/AppConfig.java`): i campi assenti **non** vengono serializzati in uscita
(AS-07: assente e `null` sono equivalenti nella catena).

### 3.2 Processi e dove si aggancia la verifica

`KafkaConsumer` sceglie il processo [FATTO]:

| Processo | Quando | Verifica Compliance USA |
|---|---|---|
| `processAutoProduttoreService.processEventoSemplificato` | preadvising dei portali: `id_canale` `TFI`, `TWS`, `BNC` oppure `canale` `MYSDA`, `SDA_WS`, `INVIO_WEB` | **no** |
| `processAutoProduttoreService.processEvento` (AutoProduttore) | `flag_autoproduttore` `S`/`Y`: LDV fornita dal cliente (`IS`, e `IE` con LDV fornita) | **sì** |
| `processGenerazioneLdvService.processEvento` (GenerazioneLdv) | gli altri: LDV da generare (`IF`, `IE`) | **sì** |

L'aggancio è **uno solo**, in `ProcessLdvService.doProcessEvento`, comune alle due varianti del
processo normale, **subito dopo `assegnaLdv`**:

```
... normalizzaCodiciNazione → prepareServizi → validateServizio → getIdVendita
→ assegnaLdv                       (IS: prodotto già calcolato; IF/IE: LDV generata e prodotto calcolato qui)
→ verificaComplianceUsa            ← 146073
→ validateTipoAzzeramento → validateContrassegno → consegna → filiale → antifrode ...
```

In quel punto `codice_prodotto` è definitivo in entrambe le varianti (IS lo calcola prima del
mapping, IF/IE dentro `assegnaLdv` dopo la generazione) e i codici nazione sono già normalizzati.

### 3.3 Componenti nuovi (package `compliance/`)

| Classe | Ruolo |
|---|---|
| `ComplianceUsaProperties` | `@ConfigurationProperties(prefix = "compliance-usa")`: flag ed elenchi (sezione 7) |
| `ComplianceUsaValidator` | `verifica(TracciatoUnicoDTO)`: riconoscimento e controlli su tutte le spedizioni del messaggio; non modifica il DTO; descrizioni senza i valori dei campi. Log INFO della configurazione all'avvio (`@PostConstruct`) |
| `EsitoComplianceUsa` | record con flag, numero di spedizioni soggette, errori ordinati per codice; `esito()` (`disabilitata`, `non_soggetta`, `ok`, `ko`) e `primoErrore()` |
| `ProcessLdvService.verificaComplianceUsa` | span, log, metrica; con errori chiama `Utils.addError` con il primo errore e interrompe il processo |
| `ProcessLdvCollaboratori` | aggiunto `ComplianceUsaValidator` fra i collaboratori |

## 4. Dati usati

| Dato | Percorso JSON | Uso |
|---|---|---|
| Account Key | `spedizione[].zonos_account_key` | controllo 5.3, propagazione |
| Declaration ID | `spedizione[].zonos_declaration_id` | solo propagazione |
| Product ID | `spedizione[].collo[].articolo[].zonos_product_id` | controllo 5.3, propagazione |
| Nazione del destinatario | `destinatario.codice_nazione_iso_2` / `destinatario.codice_nazione` (già normalizzati) | riconoscimento |
| Tipo merce | `spedizione[].tipo_merce` | riconoscimento |
| Prodotto | `spedizione[].codice_prodotto` (calcolato da ce-rules sulla LDV) oppure `id_servizio` | riconoscimento |
| Posizione articolo | `…articolo[].posizione` | descrizione dell'errore |

## 5. Regole funzionali

### 5.1 Campi [DECISO, AS-01]

| ID | Regola |
|---|---|
| RL-01 | I tre campi sono opzionali: un messaggio senza campi si comporta esattamente come oggi (R-05) |
| RL-02 | I valori escono su `preadvising.enrichment` **identici a come sono entrati**, ognuno nella sua posizione (R-04); i campi assenti non vengono serializzati (`NON_NULL`) |
| RL-03 | `zonos_declaration_id` non ha regole in fase 1 |

### 5.2 Spedizioni soggette [DECISO, AS-02, Diego 2026-11-23]

Si valuta per ogni elemento di `spedizione[]`. Con il flag acceso (`compliance-usa.abilitata`) una
spedizione è soggetta se valgono **tutte**:

| # | Condizione | Proprietà |
|---|---|---|
| C1 | `tipo_merce` **non** è fra i valori "documenti"; `tipo_merce` assente = merce | `tipi-merce-documenti` (`D`) |
| C2 | `codice_nazione_iso_2` **oppure** `codice_nazione` del destinatario è fra le nazioni USA; senza destinatario la spedizione non è soggetta | `nazioni-usa` (`US,USA`) |
| C3 | `codice_prodotto` **oppure** `id_servizio` è fra i prodotti interessati; con l'elenco vuoto valgono tutti i prodotti | `prodotti` (`456,457,458,459,515,516`) |

- Confronti con trim e maiuscole, sui campi di riconoscimento; i campi `zonos_*` non si toccano.
- Prodotti: `456`, `457` EXPORT BOX; `458`, `459` EXPORT BOX PCIM; `515`, `516` CRONO INTERNAZIONALE
  (elenco da confermare, PA-12). Si cambia in configurazione.
- Con il flag spento non c'è nessuna spedizione soggetta e nessun effetto.

### 5.3 Controlli [DECISO, R-02]

Solo presenza e lunghezza, sul valore così com'è. Un campo blank (vuoto o di soli spazi) conta come
mancante.

| ID | Controllo | Codice |
|---|---|---|
| RL-10 | `zonos_account_key` mancante | `1320` |
| RL-11 | `zonos_account_key` di lunghezza diversa da 52 | `1321` |
| RL-12 | per ogni articolo di ogni collo, `zonos_product_id` mancante | `1322` |
| RL-13 | per ogni articolo, `zonos_product_id` di lunghezza fuori 1-255 (in pratica oltre 255: il vuoto è già `1322`) | `1323` |

Una spedizione soggetta senza articoli non produce errori di Product ID: si logga un WARN con
`id_preadvising` (LDV-AS-04).

### 5.4 Errori: descrizioni e un solo errore per messaggio [DECISO, AS-03; FATTO, `1bd3517`]

| Codice | Descrizione |
|---|---|
| `1320` | `zonos_account_key: Campo obbligatorio mancante` |
| `1321` | `zonos_account_key: lunghezza non valida (attesi 52 caratteri)` |
| `1322` | `zonos_product_id: Campo obbligatorio mancante` |
| `1323` | `zonos_product_id: lunghezza non valida, attesi 1-255 caratteri` |

- Le occorrenze vanno fra parentesi, separate da `"; "`: `(collo 1 articolo 2; collo 2 articolo #1)`.
  `<n>` del collo parte da 1; l'articolo è `posizione`, oppure `#<k>` (indice da 1) se manca.
- Con più elementi in `spedizione[]` ogni occorrenza ha il prefisso `spedizione <k>`, dentro le
  parentesi: `(spedizione 2 collo 1 articolo 1)`; per l'Account Key `(spedizione 2)`. Con una sola
  spedizione `1320` e `1321` non hanno parentesi.
- Le descrizioni non contengono mai i valori dei campi.
- **Un solo errore per messaggio**, come per le altre verifiche del ldv: vale il **primo nell'ordine
  `1320`, `1321`, `1322`, `1323`**, con le sue occorrenze. `Utils.addError` imposta `result` = `KO` e
  `description` = `<codice>-<descrizione>` (es. `1322-zonos_product_id: Campo obbligatorio mancante
  (collo 1 articolo 2)`). Gli altri codici trovati vanno solo sull'attributo dello span e nella riga di
  log. Conseguenza: **il cliente vede `1322` solo dopo aver corretto `1320`** (LDV-AS-01).

### 5.5 Effetto dello scarto [FATTO, codice di ldv e orchestratore]

- Il ldv interrompe il processo (i controlli successivi non si fanno) e pubblica il tracciato con
  `result` `KO` su `preadvising.enrichment`.
- L'orchestratore (`Utils.gestisciErroreLavorazione`) divide `description` al primo `-`: chiave =
  codice, valore = descrizione. Salva l'errore su `dichiarato_events` e manda l'evento
  `PREADVISING_PARZIALE_E_BLOCCATO` con la mappa `{"1322": "zonos_product_id: …"}`. Il monitoring
  legge il campo prima dei due punti, come per gli altri errori (nessuna modifica).
- **IF/IE: LDV già consumata.** Nel processo GenerazioneLdv il KO di compliance arriva dopo la
  generazione della LDV: la LDV risulta consumata. Succede già oggi per tutti gli errori successivi
  (tipo azzeramento, contrassegno, consegna…); anticipare la verifica non si può, perché il prodotto è
  noto solo dopo la generazione (LDV-AS-03).

### 5.6 Regole riassuntive

| ID | Regola |
|---|---|
| RL-01…RL-03 | campi e propagazione (5.1) |
| RL-05 | riconoscimento C1…C3 con flag (5.2) |
| RL-10…RL-13 | controlli (5.3) |
| RL-20 | errori `1320`…`1323`, un solo errore per messaggio, il primo in ordine di codice (5.4) |
| RL-21 | verifica solo nel processo normale (`doProcessEvento`), dopo `assegnaLdv`; non nel semplificato (3.2) |
| RL-22 | nessun valore `zonos_*` né descrizione degli errori nei log; nessun valore nelle metriche e negli span |

## 6. Esempi [dati inventati]

### 6.1 Spedizione soggetta valida (IF)

Ingresso su `preadvising.enrichment.ldv` (ridotto). Dopo `assegnaLdv` `codice_prodotto` vale `456`:

```json
{
  "canale": "IF",
  "id_preadvising": "b1000000-0000-4000-8000-000000000001",
  "spedizione": [{
    "tipo_merce": "M",
    "zonos_account_key": "TESTAK0000000000000000000000000000000000000000000001",
    "destinatario": { "codice_nazione": "USA", "codice_nazione_iso_2": "US" },
    "collo": [{ "articolo": [
      { "posizione": "1", "zonos_product_id": "PRD-TEST-0001" },
      { "posizione": "2", "zonos_product_id": "PRD-TEST-0002" }
    ]}]
  }]
}
```

Esito: nessun errore di compliance, il processo continua; in uscita i campi sono identici.

### 6.2 Account Key mancante e articolo senza Product ID (IS)

Come 6.1 ma `"canale": "IS"`, senza `zonos_account_key` e con il secondo articolo senza
`zonos_product_id`. Errori trovati: `1320` e `1322`. In uscita (ridotto):

```json
{ "result": "KO", "description": "1320-zonos_account_key: Campo obbligatorio mancante" }
```

Span: `errore.codice` = `1320,1322`. Log: `COMPLIANCE_USA | id_preadvising=… soggette=1 esito=ko
codici=1320,1322`. Il cliente corregge l'Account Key, reinvia e riceve `1322-zonos_product_id: Campo
obbligatorio mancante (collo 1 articolo 2)`.

### 6.3 Non soggetta

Destinatario `DE`/`DEU`, oppure `tipo_merce` `D`, oppure prodotto fuori elenco: nessun controllo, i
campi presenti si propagano.

### 6.4 Portale

Lo stesso 6.2 con `canale` `MYSDA`: processo semplificato, nessuna verifica, campi propagati.

## 7. Configurazione

```yaml
compliance-usa:
  abilitata: ${COMPLIANCE_USA_ABILITATA:false}
  tipi-merce-documenti: ${COMPLIANCE_USA_TIPI_MERCE_DOCUMENTI:D}
  nazioni-usa: ${COMPLIANCE_USA_NAZIONI_USA:US,USA}
  prodotti: ${COMPLIANCE_USA_PRODOTTI:456,457,458,459,515,516}
```

| File | Stato al `1bd3517` |
|---|---|
| `src/main/resources/application.yaml` | blocco sopra |
| `.helm/values.yaml` (`envFrom`) | le quattro variabili, `COMPLIANCE_USA_ABILITATA: 'false'` |
| `deploy-coll/values.yaml` (`envFrom`) | le quattro variabili, `COMPLIANCE_USA_ABILITATA: 'false'` |
| `deploy-svil/values.yaml` | vuoto nel repo del ldv: valgono i default (`false`) |
| `deploy-config/values_TEMPLATE.yaml` (cert, prod) | **non toccato**: vale il default `false`. Va valorizzato quando si accende la verifica (LDV-AS-05) |

Liste separate da virgola; elenco prodotti vuoto = tutti i prodotti. Nessun secret nuovo.

## 8. Requisiti non funzionali e osservabilità

- **Prestazioni**: controllo in memoria, lineare sugli articoli, senza chiamate esterne.
- **Tracing**: sotto-span `verificaComplianceUsa` con `compliance_usa.abilitata`,
  `compliance_usa.spedizioni_soggette`, `verifica.esito` e, se ci sono errori, `errore.codice` (tutti
  i codici trovati, separati da virgola).
- **Metrica**: `business_compliance_usa_verifiche_total{canale,esito}` con `esito` `non_soggetta`,
  `ok`, `ko`; una volta per messaggio, solo con il flag acceso; mai bloccante (`try/catch`). In più il
  contatore degli errori di business di `Utils.addError`.
- **Log**: INFO all'avvio con la configurazione; INFO per i messaggi con spedizioni soggette
  (`COMPLIANCE_USA | id_preadvising=… soggette=… esito=… codici=…`); WARN per la spedizione soggetta
  senza articoli. Mai i valori `zonos_*` né le descrizioni.

## 9. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato 6.1 con flag acceso, su `preadvising.enrichment` esce `result` `OK` con i tre campi identici e nelle stesse posizioni |
| AC-02 | Con flag spento nessuna verifica, nessuna metrica di compliance, campi propagati |
| AC-03 | Dato 6.2, `result` `KO` e `description` `1320-zonos_account_key: Campo obbligatorio mancante`; span con `1320,1322` |
| AC-04 | Account Key di 51 e 53 caratteri → `1321`; 52 (spazi compresi) → nessun errore |
| AC-05 | Product ID mancante o blank → `1322` con collo e articolo; 256 caratteri → `1323`; 1 e 255 → nessun errore |
| AC-06 | Più articoli senza Product ID → una sola descrizione con le occorrenze fra parentesi, separate da `"; "` |
| AC-07 | Spedizione non USA, solo documenti o prodotto fuori elenco → nessun errore; prodotto su `id_servizio` in elenco con `codice_prodotto` fuori elenco → soggetta |
| AC-08 | Stesso messaggio di 6.2 su canale portale (`MYSDA`, `SDA_WS`, `INVIO_WEB`, `TFI`, `TWS`, `BNC`) → processo semplificato, nessun errore di compliance |
| AC-09 | Verifica attiva sia in AutoProduttore sia in GenerazioneLdv; con errore di compliance i controlli successivi (tipo azzeramento, contrassegno…) non vengono eseguiti |
| AC-10 | Nei log non compaiono valori `zonos_*` né descrizioni degli errori di compliance |
| AC-11 | Test esistenti verdi (78 al commit `1bd3517`, compreso il test di caratterizzazione corretto) |

## 10. Casi di test

| TC | Tipo | Cosa | AC |
|---|---|---|---|
| TC-01 | unit `ComplianceUsaValidatorTest` | condizioni C1…C3 (una alla volta false, maiuscole e spazi, elenco vuoto), lunghezze 51/52/53 e 1/255/256, blank, più colli, articolo senza posizione, più spedizioni, nessun articolo | AC-04…AC-07 |
| TC-02 | `ProcessLdvServiceComplianceUsaTest` | aggancio in `doProcessEvento` nelle due varianti, primo errore in ordine di codice, interruzione dei controlli successivi, flag spento, metrica | AC-01…AC-03, AC-09 |
| TC-03 | unit | processo semplificato con spedizione soggetta senza campi | AC-08 |
| TC-04 | regressione | suite esistente | AC-11 |
| TC-05 | integrato svil | messaggi a mano su `preadvising.pre-enrichment` con il flag acceso solo per il test (anche nel ldv di svil, che oggi non ha le variabili): soggetta valida, `1320`, `1322` dopo la correzione, non soggetta | AC-01, AC-03 |

## 11. Assunzioni e domande aperte

Da `analisi.md`, vincolanti: AS-01 (nomi e posizione), AS-02 (regola), AS-03 (errori), AS-06 (fuori
fase 1), AS-07 (assente = `null`).

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| LDV-AS-01 | **Un solo errore per messaggio**, come per le altre verifiche del ldv: il cliente vede `1322` solo dopo aver corretto `1320` | primo errore in ordine di codice, gli altri su span e log | Diego / Poste |
| LDV-AS-02 | Il processo semplificato dei portali non verifica (i campi arrivano dai portali solo se scritti nelle SEW, PRD-05) | nessuna verifica | Poste (VAL-DA-04) |
| LDV-AS-03 | In IF/IE il KO di compliance arriva dopo `generaLdv`: la LDV risulta consumata, come oggi per gli altri errori successivi | accettato, non anticipabile | Diego / Poste |
| LDV-AS-04 | Spedizione soggetta senza articoli: nessun errore di Product ID, WARN | come il validatore (VAL-DA-05) | Poste |
| LDV-AS-05 | `values_TEMPLATE` cert/prod non toccato: vale `false` | da valorizzare quando si accende | Diego |
| LDV-AS-06 | Il ldv non è nell'HLD della fase 1: la verifica è a carico della stima dell'intervento 01 | da allineare con Poste (PA-10) | Diego |

## 12. Riferimenti

- [analisi.md](../analisi.md): contratto della fase 1, R-01…R-05, PA-10, PA-12, PA-14.
- [ce-dichiarato-validatore.md](ce-dichiarato-validatore.md): campi nei DTO del validatore, nota storica.
- [ce-dichiarato-orchestratore.md](ce-dichiarato-orchestratore.md): gestione del KO delle lavorazioni.
- Codice (`origin/develop`, `1bd3517`): `kafka/consumer/KafkaConsumer.java`,
  `service/ProcessLdvService.java`, `service/ProcessLdvCollaboratori.java`, `compliance/*.java`,
  `kafka/dto/{SpedizioneDTO,ArticoloDTO}.java`, `util/Utils.java`, `application.yaml`,
  `.helm/values.yaml`, `deploy-coll/values.yaml`.
