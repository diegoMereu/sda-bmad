# Prompt — documento funzionale `ce-event-handler-monitoring` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del monitoring per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-event-handler-monitoring.md`.
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11.

---

# Contesto

Sei l'Analyst del progetto sda-iniziative. Iniziativa 146073 "Compliance USA Entry Type 13", **solo
fase 1**: il preavviso porta `zonos_account_key` (testata di `spedizione[]`), `zonos_product_id` (ogni
`spedizione[].collo[].articolo[]`) e `zonos_declaration_id` solo predisposto. `ce-dichiarato-ldv` (processo normale; fino al 25-11 era il validatore) aggiunge quattro
errori nuovi (codici `1320`…`1323`). L'HLD, intervento 04, chiede di adeguare monitoring,
event store e bff per "ricevere e propagare i nuovi campi sul topic"; il foglio Impatti cita
"Adeguamento ce-dichiarato-monitoring" con impatto M50.

Il "Contratto della fase 1" di `iniziative/146073/analisi.md` (AS-01…AS-06) è **vincolante**: il
documento lo dettaglia, non lo cambia. Le incoerenze vanno fra le domande aperte.

# Fonti

- `CLAUDE.md`, `contesto/modo-di-lavorare.md`, `contesto/microservizi-preadvising.md`,
  `contesto/linee-guida-sviluppo.md`, `contesto/test-integrati.md`.
- `iniziative/146073/analisi.md`; `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (con `python -I`
  e openpyxl, anche il foglio Impatti); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`.
- `iniziative/146073/sviluppo/ce-dichiarato-ldv.md`: codici e descrizioni degli errori.
- Codice in sola lettura in `C:\Users\diego.mereu\gitposte\SDA\preadvising\ce-event-handler-monitoring`:
  la working copy ha modifiche non committate, quindi leggi `origin/develop` con `git show` e dichiara
  il ref. Non modificare, non fare checkout, non committare. ICD non versionate in `icd/`.

# Cosa ti chiedo

Struttura come `iniziative/144216/sviluppo/shipment-info.md`: contesto e obiettivo, interventi HLD
coperti, dove si interviene nel codice, regole, esempi, configurazione, RNF e osservabilità, criteri
di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. che cosa il monitoring estrae dagli eventi (DTO tipizzati o `Map`, `FAIL_ON_UNKNOWN_PROPERTIES`)
   e che cosa pubblica sul topic di cambio stato;
2. come arrivano alla console gli errori nuovi (mapping chiave/valore → codice, campo, descrizione),
   anche con descrizioni concatenate e spedizioni multicollo;
3. se "propagare i campi sul topic" richiede di cambiare il contratto del topic di cambio stato:
   proponi un default e, a parte, la variante con i campi, abbastanza dettagliata per stimarla;
4. log del payload e dati riservati.

Se scopri che i dati sono trattati in modo che non serve nessuna modifica, scrivi comunque un
funzionale breve che lo dimostri con [FATTO] e riduca l'intervento a verifica e test di non
regressione, e dillo in testa al documento.

# Regole

- Intestazione con **Branch** `develop` (decisione di Diego del 2026-11-24, sostituisce il branch dedicato
  `146073_compliance_usa_fase1` del 16-11; il branch dedicato resta solo per `sda-ldv-preadv-consumer`).
  Mai sviluppo su `master` né su branch di altre iniziative.
  Dove basta un test di non regressione non serve nessuna modifica.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Assunzioni nuove con prefisso `MON-`, numerate.
- Esempi JSON inventati (chiavi con prefisso `99`), niente dati di produzione né valori di secret.
- Italiano, conciso; nomi file e ID ASCII.
