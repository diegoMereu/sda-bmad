# Prompt — documento funzionale `ce-event-handler-event-store` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale dell'event store per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-event-handler-event-store.md`.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto sda-iniziative. Iniziativa 146073 "Compliance USA Entry Type 13", **solo
fase 1**: il preavviso porta `account_key` (testata di `spedizione[]`), `product_id` (ogni
`spedizione[].collo[].articolo[]`) e `declaration_id` solo predisposto (sempre assente o `null`).
L'HLD, intervento 04, chiede di adeguare monitoring, event store e bff per "ricevere e propagare i
nuovi campi". La descrizione generale aggiunge per l'event store: cardinalità per articolo in
serializzazione e deserializzazione, replay e ricostruzione dello stato, compatibilità con gli
eventi storici senza i campi.

Il "Contratto della fase 1" di `iniziative/146073/analisi.md` (AS-01…AS-06) è **vincolante**: il
documento lo dettaglia, non lo cambia. Le incoerenze vanno fra le domande aperte.

# Fonti

- `CLAUDE.md`, `contesto/modo-di-lavorare.md`, `contesto/microservizi-preadvising.md`,
  `contesto/linee-guida-sviluppo.md`, `contesto/test-integrati.md`.
- `iniziative/146073/analisi.md`; `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (leggilo con
  `python -I` e openpyxl); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`.
- `iniziative/146073/sviluppo/ce-dichiarato-validatore.md` per codici e forma degli errori.
- Codice in sola lettura in `C:\Users\diego.mereu\gitposte\SDA\preadvising\ce-event-handler-event-store`:
  la working copy ha modifiche non committate di altri, quindi leggi `origin/develop` con `git show`
  e dichiara il ref. Non modificare, non fare checkout, non committare.
- ICD dell'evento: `ce-event-handler-monitoring/icd/ICD_preadvising_eventsource.md`.

# Cosa ti chiedo

Struttura come `iniziative/144216/sviluppo/shipment-info.md`: contesto e obiettivo, interventi HLD
coperti, dove si interviene nel codice, regole, esempi, configurazione, RNF e osservabilità, criteri
di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. il percorso di un evento da `preadvising.evensource` alla collection Mongo: tipo di `eventData`
   (DTO tipizzato o `Object`/`Map`), configurazione dell'`ObjectMapper`, nome della collection;
2. quali DTO ed entity del repo sono davvero usati nel flusso;
3. replay, consultazione e ricostruzione dello stato: chi rilegge l'event store;
4. eventi storici senza i campi;
5. log del payload e dati riservati.

Se scopri che `eventData` è trattato come JSON generico e non serve nessuna modifica, scrivi comunque
un funzionale breve che lo dimostri con [FATTO] e riduca l'intervento a verifica e test di non
regressione, e dillo in testa al documento: è un'informazione importante per la stima.

# Regole

- Intestazione con **Branch** `146073_compliance_usa_fase1` da `origin/develop` (se il repo non ha
  `develop`, dal branch di integrazione del repo, verificato con git). Dove basta un test di non
  regressione il branch serve solo se emerge una modifica. Mai sviluppo su `develop`/`master` né su
  branch di altre iniziative.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Assunzioni nuove con prefisso `EVS-`, numerate.
- Esempi JSON inventati (chiavi con prefisso `99`), niente dati di produzione né valori di secret.
- Italiano, conciso; nomi file e ID ASCII.
