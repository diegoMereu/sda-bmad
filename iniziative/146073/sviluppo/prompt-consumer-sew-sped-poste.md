# Prompt — documento funzionale `consumer-sew_sped_poste` (146073, int. 08)

> Prompt per Mary (analyst), con Winston per le DDL: genera il documento funzionale del consumer
> `consumer-sew_sped_poste` per la fase 1 dell'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/consumer-sew-sped-poste.md`, da passare allo sviluppatore.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Iniziativa 146073 "Compliance USA Entry Type 13" (Poste Italiane / SDA,
filone PCL-127), **solo la fase 1**. I campi nuovi sono:
- `account_key`: testata della spedizione, 52 caratteri;
- `product_id`: ogni articolo di `collo[].articolo[]`, da 1 a 255 caratteri;
- `declaration_id`: testata, solo predisposto (sempre `null` in fase 1).

Sono i "3 nuovi campi" dell'HLD.

HLD, int. 08 "Adeguamento consumer sew_spedizioni_poste": "I 3 nuovi campi … devono essere storicizzati
dentro la tabella `sew_spedizioni_poste`: modifica del consumer kafka". È l'unico intervento della
fase 1 con impatto Database (M50).

Il "Contratto della fase 1" di `iniziative/146073/analisi.md` (AS-01…AS-06) è **vincolante**: le
incoerenze vanno fra le domande aperte, senza cambiarlo.

**Branch (regola di Diego)**: lo sviluppo si fa sul branch dedicato `146073_compliance_usa_fase1`, da
`origin/develop`. Se il repo non ha `develop`, si parte dal branch di integrazione, dopo averlo
verificato con git, e lo si scrive nell'intestazione. Mai sviluppo su `develop` o `master`, né su
branch di altre iniziative.

# Fonti

- `iniziative/146073/analisi.md`; `cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (con `python -I` e openpyxl).
- `contesto/microservizi-preadvising.md`, `contesto/ambienti.md`, `contesto/linee-guida-sviluppo.md`.
- Codice in sola lettura (non modificare, non fare checkout, non committare):
  `gitposte/SDA/ESITI/poste-ldv-preadv-consumer/consumer-sew_sped_poste`:
  - `App` (scelta del DAO per canale, properties `kafka.tabella.*`);
  - `constants/AppConstants` (MERGE e insert con `${TABLE}`);
  - `dao/QueriesManagerDao` e `dao/QueriesManagerDao2`: `prepareInsertIntoSewSpedizioniPoste`,
    `prepareInsertIntoSewInter`, `prepareInsertIntoPrtnArticolo`, `cleanString`,
    `cleanDoubleQuotesForInsert`, ramo scarto;
  - `dto/SpedizioneDTO`, `dto/ArticoloColloDTO`;
  - `campi_tabelle_PDB.md` nella radice del repo.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (con branch e base verificata), contesto (tabelle e properties), interventi HLD
coperti, come lavora oggi il consumer, dove si interviene nel codice, mapping campo JSON →
tabella.colonna, esempi, configurazione e prerequisiti, criteri di accettazione numerati, casi di test,
assunzioni e domande aperte (prefisso SWP-).

Approfondisci:

1. quale tabella articoli: `SEW_SPEDIZIONI_POSTE_INTER` o `PRTN_ARTICOLO` (`kafka.tabella.articolo`),
   e con quale legame all'articolo (posizione);
2. in quali rami si scrivono gli articoli (PRTN, prefissi LDV, DHL, EURODIS, PDW) e cosa resta scoperto;
3. il SQL dinamico con letterali concatenati: escape, `cleanString` sui caratteri non ASCII, R-04;
4. MERGE e ripetizioni: un valore già salvato non si cancella;
5. i metodi condivisi con lo scarto, che rendono necessaria la colonna anche lì;
6. nomi reali delle tabelle nelle properties esterne.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]**, **[ASSUNTO]** (ID e default).
- Assunzioni nuove con prefisso `SWP-`, numerate.
- Niente dati di produzione né secret: esempi inventati. `App.java` contiene una stringa di test con
  nomi di persona e indirizzi: non riportarla.
- Lingua italiana, conciso. Nomi file e ID ASCII.
