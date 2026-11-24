# Prompt — documento funzionale `ce-dichiarato-adapter` (146073, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del `ce-dichiarato-adapter` per
> l'iniziativa 146073, solo fase 1.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-adapter.md`, da passare allo sviluppatore.
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per lo sviluppatore** del
`ce-dichiarato-adapter`, nell'iniziativa 146073 "Compliance USA Entry Type 13" (Poste Italiane / SDA,
filone PCL-127), **solo fase 1** (decisione di Diego del 16-11).

In fase 1 il preavviso porta due campi nuovi: **Account Key** (uno per spedizione, 52 caratteri) e
**Product ID** (uno per articolo, 1–255). Il **Declaration ID** si predispone soltanto: in fase 1 è
sempre `null`. L'adapter è un ingresso della catena: consuma PDB/BEP (`PACCHI.BEP.ALL.ANAG_LDV`), PDW
(`PACCHI.PDW.TT.PREWEB`) e ILP (`PACCHI.ILP.ANAGLDV`), converte nel tracciato unico e pubblica su
`preadvising.pre-enrichment` (gli esiti BEP su `preadvising.enrichment`). L'HLD int. 05 chiede la
"modifica dei 3 consumer per acquisizione e propagazione dei nuovi campi".

Il **contratto della fase 1** di `analisi.md` (AS-01…AS-06: `zonos_account_key` e `zonos_declaration_id` sulla
testata di `spedizione[]`, `zonos_product_id` su `collo[].articolo[]`, tutti `String` opzionali, nessuna
trasformazione) è **vincolante**: il documento lo applica, non lo cambia. Incoerenze e buchi vanno fra
le domande aperte.

La descrizione generale chiede all'adapter "mapping verso PDB, IPER"; l'HLD int. 05 parla di ricezione
nei consumer PDB, PDW e ILP. Vale l'HLD; la discrepanza va fra le domande aperte.

# Fonti

- `iniziative/146073/analisi.md`, soprattutto "Contratto della fase 1", "Differenze fra la descrizione e
  l'HLD", punti aperti.
- `iniziative/146073/cliente/HLD_146073_dati_preadvising_fase_1.xlsx` e `_fase_2.xlsx` (leggili con
  `python -I` e openpyxl): intervento 05.
- `iniziative/146073/cliente/20261116_descrizione_compliance_usa_entry_type_13.md`, sezione dell'adapter.
- `CLAUDE.md`, `contesto/modo-di-lavorare.md`, `contesto/microservizi-preadvising.md`,
  `contesto/linee-guida-sviluppo.md`.
- Codice in sola lettura (non modificare, non fare checkout, non committare):
  `gitposte/SDA/preadvising/ce-dichiarato-adapter`. Verifica i branch con git e leggi `origin/develop`
  con `git show`, dichiarando ref e commit. Classi: `consumer/KafkaConsumer{PDB,PDW,ILP}`,
  `mapper/{Pdb,Pdw,Ilp}Mapper`, `service/*`, DTO in `kafka/dto` (`SpedizioneDTO`, `ArticoloDTO`,
  `pdb/PdbMessageDTO`, `pdb/DeclarationItem`, `pdw/PreWebDTO`, `ilp/IlpContentDTO`,
  `ilp/IlpDeclarationItemDTO`); values Helm per i topic; `documenti/Mapping_*_tracciato_unico.md`;
  esempi in `esempi/`.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (repository, **branch**, stack, fonti, ref del codice letto), contesto e
obiettivo, interventi HLD coperti, dove si interviene nel codice, contratto in uscita, regole e mapping
per sorgente, esempi, configurazione, RNF e osservabilità, criteri di accettazione numerati, casi di
test, assunzioni e domande aperte.

Approfondisci:

1. i 3 consumer: DTO sorgente, mapper verso il tracciato unico, publish (topic e servizio);
2. per ogni sorgente, se esiste già un campo per Account Key, Product ID, articoli (DTO, mapping,
   esempi JSON). Se non c'è, proponi un nome provvisorio e mettilo fra le domande: i sistemi sorgente
   devono aggiungere il dato. Attenzione agli omonimi (`ID_PRODOTTO` di PDW, `services.product` di ILP
   sono codici prodotto SDA);
3. come si mappano oggi gli articoli (`collo[].articolo[]`, `posizione`) per ciascuna sorgente: il
   Product ID deve finire sull'articolo corrispondente, anche quando gli esiti BEP uniscono più colli
   (`toOutputPDBFase2`, merge della testata) e quando un filtro scarta gli articoli
   (`DeclarationItem.hasValidProperties`);
4. esiti BEP e fase 2 PDB/PDW/ILP gestiti dall'adapter: cosa si tocca in fase 1 (Declaration ID solo
   predisposto).

# Regole

- **Branch** `develop` (decisione di Diego del 2026-11-24, sostituisce il branch dedicato
  `146073_compliance_usa_fase1` del 16-11; il branch dedicato resta solo per `sda-ldv-preadv-consumer`).
  Mai sviluppo su `master` né su branch di altre iniziative.
- L'intervento è **rimandato al punto 2 della fase 1** (decisione di Diego del 2026-11-24): mancano i
  nomi dei campi nei messaggi sorgente PDB, PDW e ILP. Il funzionale va tenuto allineato ai nomi `zonos_*`.
- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Riprendi le AS di `analisi.md` che toccano l'adapter e aggiungi le tue con prefisso **ADA-**, numerate.
- Niente dati di produzione né valori di secret: messaggi d'esempio inventati (Account Key d'esempio di
  52 caratteri).
- Non cambiare il contratto della fase 1.
- Lingua italiana, conciso; nomi file e ID ASCII. Non committare: lo fa chi ti ha chiamato.
