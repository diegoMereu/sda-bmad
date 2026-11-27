# Prompt — documento funzionale `ce-dichiarato-validatore` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del validatore per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-validatore.md`, da passare allo sviluppatore (Amelia).
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-25: la verifica Compliance USA è stata spostata in `ce-dichiarato-ldv`
> (decisione di Diego); il validatore porta solo i campi. Versioni precedenti: nomi `zonos_*` e
> colonne SEW (23 e 24-11), branch (24-11), chiavi su MongoDB (24-11), verifica solo sui flussi SDA
> (25-11 mattina, superata).

---

# Contesto

Sei l'Analyst del progetto. Scrivi il **documento funzionale per lo sviluppo** di
`ce-dichiarato-validatore` (intervento 01 dell'HLD) per l'iniziativa 146073 "Compliance USA Entry
Type 13" (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato), **solo fase 1**.

Nella fase 1 il preavviso porta **Account Key** sulla testata della spedizione (52 caratteri),
**Product ID** su ogni articolo (1-255) e `zonos_declaration_id`, solo predisposto.

**Decisione di Diego del 2026-11-25**: la verifica Compliance USA (spedizioni soggette ed errori
`1320`…`1323`) **non è più nel validatore**. È in `ce-dichiarato-ldv`, nel processo normale, perché
solo lì `codice_prodotto` è sicuramente valorizzato (calcolato da ce-rules sulla LDV); in ingresso al
validatore i flussi SDA reali non portano i codici prodotto in modo affidabile. Il validatore:

- aggiunge `zonos_account_key`, `zonos_declaration_id` (`SpedizioneDTO`) e `zonos_product_id`
  (`ArticoloDTO`), con `@JsonProperty`, `@Field` con il nome del tracciato e `@ToString.Exclude`;
- li propaga senza controlli e senza trasformazioni su tutti i canali, SDA e PDB, verso
  `preadvising.enrichment`, l'event store e Mongo `dichiarato_events`;
- non ha regola, errori, metrica né configurazione di compliance (rimossi con il commit `6cd722a`, che
  supera `090d037`, `43f5cbe` e `c7f82eb`).

Il **contratto della fase 1** (`analisi.md`, AS-01…AS-07) è **vincolante**. Il documento deve avere in
testa una nota storica breve sullo spostamento della verifica e sui commit.

# Fonti

- `iniziative/146073/analisi.md`: "Contratto della fase 1", regole R-01…R-05, punti aperti.
- `iniziative/146073/sviluppo/ce-dichiarato-ldv.md`: dove sta la verifica.
- `iniziative/146073/cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (intervento 01) e
  `cliente/20261116_descrizione_compliance_usa_entry_type_13.md`.
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`.
- Codice in **sola lettura**: `gitposte/SDA/preadvising/ce-dichiarato-validatore`, `origin/develop`
  con `git show` (non fare checkout); dichiara il ref letto.

# Cosa ti chiedo

Intestazione con **branch** `develop` (decisione del 2026-11-24) e stato del commit. Sezioni:
contesto e obiettivo, interventi HLD coperti, dove si interviene nel codice (DTO, serializzazione,
handler, cosa è stato rimosso), dati, regole, esempi JSON inventati, configurazione (nessuna),
criteri di accettazione, casi di test, assunzioni e domande aperte (indica quali VAL-AS sono
superate), riferimenti.

Approfondisci:

1. Perché senza i campi nei DTO si perdono (`FAIL_ON_UNKNOWN_PROPERTIES`, DTO tipizzato in uscita,
   event store, Mongo, cloni del multicollo).
2. Perché servono `@Field` (Spring Data ignora `@JsonProperty`) e `@ToString.Exclude` (log).
3. Perché niente Bean Validation (regola semantica generica in cascata).
4. Che nessun handler (`SdaFlussoHandler`, `PdbPreadvisingHandler`, `PdbPdwFlussoHandler`,
   `TfiFlussoHandler`, `TupFlussoHandler`) produce errori `1320`…`1323`.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Assunzioni con prefisso `VAL-AS-`, domande con `VAL-DA-`.
- Niente dati di produzione e niente valori di secret: esempi inventati.
- Nei repo dei servizi solo lettura. Il commit in `sda-iniziative` lo fa chi ti ha chiamato.
- Lingua italiana, prosa chiara e concisa; nomi file e ID ASCII.
