# Prompt — documento funzionale `ce-dichiarato-orchestratore` (fase 1)

> Prompt per Mary (analyst): genera il documento funzionale dell'orchestratore per l'iniziativa
> 146073, fase 1.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-orchestratore.md`, da passare alla sviluppatrice.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per la sviluppatrice** di
`ce-dichiarato-orchestratore`, nell'iniziativa 146073 "Compliance USA Entry Type 13" (Poste Italiane /
SDA, filone PCL-127), **solo fase 1** [DECISO 16-11, Diego].

In fase 1 il preavviso porta `account_key` (testata di `spedizione[]`), `product_id` (ogni
`spedizione[].collo[].articolo[]`) e `declaration_id` (testata, solo predisposto, sempre assente o
`null`). L'orchestratore deve propagarli senza perdita né appiattimento: intervento 02 dell'HLD
(modifica del DTO, del salvataggio a DB e del metodo di merge; nessuna perdita nei rami, nei retry e
nelle ripartenze).

Il "Contratto della fase 1" di `analisi.md` (AS-01…AS-06) è **vincolante**: il documento lo dettaglia,
non lo cambia. Incoerenze e buchi vanno fra le assunzioni, con prefisso **ORC-** numerato.

# Fonti

- `iniziative/146073/analisi.md` (contratto della fase 1, regole R-01…R-07, interventi, punti aperti).
- `iniziative/146073/cliente/`: HLD fase 1 (xlsx, leggilo con `python -I` e openpyxl), descrizione
  generale (.md).
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`,
  `contesto/MICROSERVICE_TECHNICAL_BLUEPRINT.md` (blueprint dell'orchestratore).
- Codice in sola lettura (non modificare, non fare checkout, non committare): repo in
  `gitposte/SDA/preadvising`. Verifica il branch corrente con git e leggi `origin/develop` con
  `git show`; dichiara il ref letto.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (con il **branch**, vedi Regole), contesto e obiettivo, interventi HLD coperti,
dove si interviene nel codice, esempi JSON, regole funzionali, regole riassuntive, configurazione,
RNF e osservabilità, criteri di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. DTO tipizzati o `JsonNode`; tutti i punti in cui i campi non dichiarati si perdono
   (deserializzazione, salvataggio su Mongo, fan-out alle lavorazioni, merge, retry per conflitto di
   versione, pubblicazione su `preadvising.completed`, `dichiarato_events`, eventi di stato).
2. Il merge (`MergeProperties`, `manageMerge`, `OrchestratoreMongoService.merge`): come si fondono i
   ritorni di normalizzazione, `check-ldv`, `ldv-pdb`, `ldv-bep-sync`; se un ritorno senza i campi li
   cancella; come si fondono `collo[]` e `articolo[]` (per indice o per `posizione`).
3. Nei repo `ce-dichiarato-ldv`, `ce-dichiarato-ldv-pdb`, `ce-dichiarato-ldv-pdb-sync` e del
   normalizzatore: se ricevono e restituiscono il preavviso intero, compresi i campi sconosciuti, o
   solo i propri. Riportalo come rischio o domanda, senza scrivere documenti per quei servizi.
4. Retry e ripartenze (`ce-preadvising-retry-*`): solo se rileggono da Mongo il documento salvato
   dall'orchestratore e se quindi beneficiano della modifica.

# Regole

- Intestazione: **Branch `146073_compliance_usa_fase1` da `origin/develop`** (se il repo non ha
  `develop`, dal branch di integrazione del repo, verificato con git e indicato). Mai sviluppo su
  `develop`/`master` né su branch di altre iniziative.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Niente dati di produzione né valori di secret: esempi JSON inventati.
- Lingua italiana, conciso; nomi file e ID ASCII.
