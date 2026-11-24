# Prompt — documento funzionale `ce-dichiarato-bff` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del BFF per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-bff.md`.
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11.

---

# Contesto

Sei l'Analyst del progetto sda-iniziative. Iniziativa 146073 "Compliance USA Entry Type 13", **solo
fase 1**: il preavviso porta `zonos_account_key` (testata di `spedizione[]`), `zonos_product_id` (ogni
`spedizione[].collo[].articolo[]`) e `zonos_declaration_id` solo predisposto. L'HLD, intervento 04, chiede
di adeguare monitoring, event store e bff per "ricevere e propagare i nuovi campi".

Il "Contratto della fase 1" di `iniziative/146073/analisi.md` (AS-01…AS-06) è **vincolante**: il
documento lo dettaglia, non lo cambia. Le incoerenze vanno fra le domande aperte.

# Fonti

- `CLAUDE.md`, `contesto/modo-di-lavorare.md`, `contesto/microservizi-preadvising.md`,
  `contesto/linee-guida-sviluppo.md`, `contesto/test-integrati.md`.
- `iniziative/146073/analisi.md`; `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (con `python -I`
  e openpyxl); `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`.
- Codice in sola lettura in `C:\Users\diego.mereu\gitposte\SDA\preadvising`:
  `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-bff` e `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-bff-master`
  (capisci quale è il repo vivo e dichiara il ref letto con `git show`); `ce-monitoraggio-fe-develop`
  se il BFF serve un front-end. Non modificare, non fare checkout, non committare.

# Cosa ti chiedo

Struttura come `iniziative/144216/sviluppo/shipment-info.md`: contesto e obiettivo, interventi HLD
coperti, dove si interviene nel codice, regole, esempi, configurazione, RNF e osservabilità, criteri
di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. ogni API esposta: collection letta e modello di lettura (DTO tipizzato o `Document`/`Map`), e se
   i campi nuovi arrivano nella risposta;
2. la risottomissione dei preavvisi (reinvii senza perdita dei campi, R-04);
3. la forma dei campi assenti nella risposta (`null` o omessi) per i documenti storici;
4. se un front-end consuma le API e deve mostrare i campi: in fase 1 nessuna modifica a front-end
   salvo indicazione contraria (domanda aperta).

Se per qualche API i dati sono JSON generico, dillo con [FATTO] e riducila a test di non regressione.
Se per tutto il servizio non serve nessuna modifica, scrivi comunque un funzionale breve e dillo in
testa al documento: è un'informazione importante per la stima.

# Regole

- Intestazione con **Branch** `develop` (decisione di Diego del 2026-11-24, sostituisce il branch dedicato
  `146073_compliance_usa_fase1` del 16-11; il branch dedicato resta solo per `sda-ldv-preadv-consumer`).
  Mai sviluppo su `master` né su branch di altre iniziative.
  Dove basta un test di non regressione non serve nessuna modifica.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Assunzioni nuove con prefisso `BFF-`, numerate.
- Esempi JSON inventati (chiavi con prefisso `99`), niente dati di produzione né valori di secret.
- Italiano, conciso; nomi file e ID ASCII.
