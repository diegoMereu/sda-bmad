# Prompt — documento funzionale `ce-dichiarato-ldv` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del ldv per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-ldv.md`, da passare allo sviluppatore (Amelia).
> Regola di progetto: un documento funzionale per microservizio.
>
> Creato il 2026-11-25, dopo la decisione di Diego di spostare la verifica Compliance USA dal
> validatore al ldv.

---

# Contesto

Sei l'Analyst del progetto. Scrivi il **documento funzionale per lo sviluppo** di
`ce-dichiarato-ldv` per l'iniziativa 146073 "Compliance USA Entry Type 13" (AP-00988 Corriere
Espresso / PK-03089 ce-dichiarato), **solo fase 1**.

**Decisione di Diego del 2026-11-25**: la verifica Compliance USA (errori `1320`…`1323` su
`zonos_account_key` e `zonos_product_id`) passa dal `ce-dichiarato-validatore` al `ce-dichiarato-ldv`,
perché solo nel ldv `codice_prodotto` è sicuramente valorizzato (calcolato da ce-rules sulla LDV). In
ingresso al validatore i flussi SDA reali non portano i codici prodotto in modo affidabile. Il
validatore ora porta solo i campi (commit `6cd722a`).

Stato del codice: commit `1bd3517` su `develop` del ldv. Il documento descrive quello che c'è:

- campi `zonos_account_key`, `zonos_declaration_id` (spedizione) e `zonos_product_id` (articolo) nei
  DTO con `@JsonProperty`, `@Field` e `@ToString.Exclude`, propagati senza trasformazioni;
  `ObjectMapper` `NON_NULL`;
- package `compliance/` (`ComplianceUsaProperties` con prefisso `compliance-usa`,
  `ComplianceUsaValidator`, `EsitoComplianceUsa`), variabili `COMPLIANCE_USA_*` in `application.yaml`,
  `.helm/values.yaml` e `deploy-coll` (flag `false`); `deploy-svil` vuoto; `values_TEMPLATE` non
  toccato;
- regola identica a quella del validatore (tipo merce non documenti, destinatario USA, prodotto
  456-459/515/516 su `codice_prodotto` o `id_servizio`; trim e maiuscole; elenco vuoto = tutti);
  errori `1320`…`1323` con le descrizioni di AS-03 e le occorrenze fra parentesi;
- aggancio **solo nel processo normale**, in `ProcessLdvService.doProcessEvento` subito dopo
  `assegnaLdv`, per AutoProduttore (IS) e GenerazioneLdv (IF/IE); non nel processo semplificato dei
  portali;
- **un solo errore per messaggio**: il primo nell'ordine `1320`, `1321`, `1322`, `1323`, con
  `Utils.addError` (`codice-descrizione`); gli altri su span e log;
- span `verificaComplianceUsa`, metrica `business_compliance_usa_verifiche_total{canale,esito}`, log
  INFO senza valori;
- in IF/IE il KO arriva dopo `generaLdv`: LDV già consumata, come per gli altri errori successivi.

Il **contratto della fase 1** (`analisi.md`, AS-01…AS-07) è **vincolante**.

# Fonti

- `iniziative/146073/analisi.md`; `iniziative/146073/sviluppo/ce-dichiarato-validatore.md` (nota
  storica); `ce-dichiarato-orchestratore.md` (come l'orchestratore tratta il KO di una lavorazione).
- `iniziative/146073/cliente/20261116_descrizione_compliance_usa_entry_type_13.md`, §4 `ce-dichiarato-ldv`.
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`.
- Codice in **sola lettura**: `gitposte/SDA/preadvising/ce-dichiarato-ldv`, con `git show 1bd3517:<path>`
  (non fare checkout). Leggi anche `Utils.gestisciErroreLavorazione` dell'orchestratore.

# Cosa ti chiedo

Struttura come gli altri funzionali della cartella: intestazione (con **branch** `develop` e commit),
contesto e obiettivo, requisiti coperti, dove si interviene nel codice (DTO, processi, aggancio,
componenti), dati, regole (campi, spedizioni soggette, controlli, errori, effetto dello scarto),
esempi JSON inventati, configurazione per ambiente, RNF e osservabilità, criteri di accettazione,
casi di test, assunzioni (`LDV-AS-`) e riferimenti.

Metti in evidenza fra le assunzioni: un solo errore per messaggio; LDV consumata in IF/IE;
`values_TEMPLATE` cert/prod da valorizzare quando si accende; il ldv non è nell'HLD (PA-10).

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Niente dati di produzione e niente valori di secret: esempi inventati.
- Nei repo dei servizi solo lettura. Il commit in `sda-iniziative` lo fa chi ti ha chiamato.
- Lingua italiana, prosa chiara e concisa; nomi file e ID ASCII.
