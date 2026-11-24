# Prompt — documento funzionale `consumer-sew_sped` (146073, int. 07)

> Prompt per Mary (analyst), con Winston per le DDL: genera il documento funzionale del consumer
> `consumer-sew_sped` per la fase 1 dell'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/consumer-sew-sped.md`, da passare allo sviluppatore.
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11.

---

# Contesto

Sei l'Analyst del progetto. Iniziativa 146073 "Compliance USA Entry Type 13" (Poste Italiane / SDA,
filone PCL-127), **solo la fase 1**. Le spedizioni verso gli USA con merce portano due campi
nuovi: `zonos_account_key` sulla testata della spedizione (52 caratteri) e `zonos_product_id` su ogni articolo di
`collo[].articolo[]` (da 1 a 255 caratteri). Il terzo campo, `zonos_declaration_id`, è solo predisposto: è
sempre `null` in fase 1. Sono i "3 nuovi campi" dell'HLD.

HLD, int. 07 "Adeguamento consumer sew_spedizioni": "I 3 nuovi campi … devono essere storicizzati dentro
la tabella `sew_spedizioni_work`: modifica del consumer kafka per ricevere e storicizzare i 3 nuovi campi".

Il "Contratto della fase 1" di `iniziative/146073/analisi.md` (AS-01…AS-06) è **vincolante**: il
documento lo dettaglia e non lo cambia. Le incoerenze vanno fra le domande aperte.

**Branch (regola di Diego)**: questo repo (`sda-ldv-preadv-consumer`) è l'unico della 146073 che resta
sul branch dedicato `146073_compliance_usa_fase1`, da `origin/dev202508_preadvising` (il repo non ha
`develop`). Decisione del 2026-11-24: gli altri repo si sviluppano su `develop`. Mai sviluppo su
`dev202508_preadvising` o `master`, né su branch di altre iniziative.

**Colonne SEW (decisione di Diego del 2026-11-23)**: `zonos_account_key char(52) default ''`,
`zonos_declaration_id char(13) default ''` sulla tabella della spedizione, `zonos_product_id char(255) default ''`
sulla tabella articoli. Le colonne entrano nella INSERT (e nell'eventuale UPDATE) **solo se il campo
arriva valorizzato**: senza i campi lo statement resta identico a quello di oggi, così il consumer
funziona anche prima delle DDL.

# Fonti

- `iniziative/146073/analisi.md` (contratto della fase 1); `cliente/HLD_146073_dati_preadvising_fase_1.xlsx`
  (leggilo con `python -I` e openpyxl).
- `contesto/microservizi-preadvising.md`, `contesto/ambienti.md`, `contesto/linee-guida-sviluppo.md`,
  `contesto/modo-di-lavorare.md`.
- Codice in sola lettura (non modificare, non fare checkout, non committare):
  `gitposte/SDA/ESITI/sda-ldv-preadv-consumer/consumer-sew_sped`, che è la copia più aggiornata (l'altra
  copia, in `gitposte/SDA/preadvising/`, ha modifiche di altri). Leggi in particolare `App.processRecord`,
  `constants/AppConstants` (`queryInsertSewSpedizioniWork`, `…Work2`, `queryInsertSewSpedizioni`),
  `dao/QueriesManagerDao.insertSewSpedizioni` e `setParam`, `dto/SpedizioneDTO`, `dto/ArticoloColloDTO`,
  `dao/CliDatiStampaTfDao`, `.classpath` (driver).
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (con branch e base verificata), contesto e obiettivo, interventi HLD coperti,
come lavora oggi il consumer, dove si interviene nel codice, mapping campo JSON → tabella.colonna,
esempi, configurazione e prerequisiti (ordine DDL → rilascio), criteri di accettazione numerati, casi
di test, assunzioni e domande aperte (prefisso SEW-).

Approfondisci:

1. quali tabelle scrive davvero l'insert (`kafka.tabella`, work, `_2`, `sew_spedizioni`, clienti BS,
   `cli_dati_stampa_tf_2` per i non autoproduttori) e quali si toccano;
2. dove va il `zonos_product_id`, visto che il consumer non scrive nessuna tabella articoli;
3. `null` contro `" "` (`setParam` con `campoVuoto`): i campi nuovi non si trasformano (R-04, R-05);
4. la posizione dei parametri nuovi in un insert posizionale con 102 parametri;
5. i rami di update (messaggi senza `id_file`): si toccano o no;
6. l'assenza di test automatici: come si prova in svil.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Assunzioni nuove con prefisso `SEW-`, numerate.
- Niente dati di produzione né secret: LDV, ordini e chiavi d'esempio inventati. Nel codice ci sono
  stringhe di test con nomi di persona: non riportarle.
- Lingua italiana, conciso. Nomi file e ID ASCII.
