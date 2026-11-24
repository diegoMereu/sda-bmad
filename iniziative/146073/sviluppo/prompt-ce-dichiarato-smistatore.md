# Prompt — documento funzionale `ce-dichiarato-smistatore` (fase 1)

> Prompt per Mary (analyst): genera il documento funzionale dello smistatore per l'iniziativa
> 146073, fase 1.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-smistatore.md`, da passare alla sviluppatrice.
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per la sviluppatrice** di
`ce-dichiarato-smistatore`, nell'iniziativa 146073 "Compliance USA Entry Type 13" (Poste Italiane /
SDA, filone PCL-127), **solo fase 1** [DECISO 16-11, Diego].

In fase 1 il preavviso porta `zonos_account_key` (testata di `spedizione[]`), `zonos_product_id` (ogni
`spedizione[].collo[].articolo[]`) e `zonos_declaration_id` (testata, solo predisposto). Lo smistatore li
riceve da `preadvising.completed` e li propaga sui topic in uscita: intervento 03 dell'HLD. La
descrizione chiede di inoltrarli solo ai destinatari previsti dai contratti e di restare compatibili
con i destinatari non adeguati; AS-06 mette i palmari fuori dalla fase 1.

Il "Contratto della fase 1" di `analisi.md` (AS-01…AS-06) è **vincolante**. Incoerenze e buchi vanno
fra le assunzioni, con prefisso **SMI-** numerato.

# Fonti

- `iniziative/146073/analisi.md`; `iniziative/146073/cliente/` (HLD fase 1 xlsx con `python -I` e
  openpyxl, descrizione .md).
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`.
- Documento gemello: `iniziative/146073/sviluppo/ce-dichiarato-orchestratore.md`.
- Codice in sola lettura (non modificare, non fare checkout, non committare):
  `gitposte/SDA/preadvising/ce-dichiarato-smistatore`. Verifica il branch corrente con git (la working
  copy può avere modifiche di altri), leggi `origin/develop` con `git show`, dichiara il ref letto.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (con il **branch**), contesto e obiettivo, interventi HLD coperti, dove si
interviene nel codice, esempi JSON (Poste, SDA, palmari, preavviso non USA), regole, configurazione,
RNF e osservabilità, criteri di accettazione numerati, casi di test, assunzioni e domande aperte.

Approfondisci:

1. DTO in ingresso e in uscita per ogni ramo (`.completed.poste`, `.completed.sda`, palmari, evento di
   stato), e se esistono mapping specifici per Poste e SDA.
2. Come lo smistatore costruisce i messaggi in uscita e se i palmari vanno esclusi in modo esplicito o
   lo sono già (mapper dedicato).
3. Compatibilità: forma dei messaggi per i preavvisi senza i campi (serializzazione dei `null`).

# Regole

- Intestazione con **Branch** `develop` (decisione di Diego del 2026-11-24, sostituisce il branch dedicato
  `146073_compliance_usa_fase1` del 16-11; il branch dedicato resta solo per `sda-ldv-preadv-consumer`).
  Mai sviluppo su `master` né su branch di altre iniziative.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Niente dati di produzione né valori di secret: esempi JSON inventati.
- Lingua italiana, conciso; nomi file e ID ASCII.
