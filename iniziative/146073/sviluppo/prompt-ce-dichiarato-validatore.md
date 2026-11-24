# Prompt — documento funzionale `ce-dichiarato-validatore` (Compliance USA, fase 1)

> Prompt per Mary (analyst): genera il documento funzionale del validatore per l'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/ce-dichiarato-validatore.md`, da passare allo sviluppatore (Amelia).
> Regola di progetto: un documento funzionale per microservizio.
>
> Aggiornato il 2026-11-24: nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` e colonne SEW `zonos_*` (decisioni di Diego del 23 e 24-11), branch del 24-11,
> nomi delle chiavi su MongoDB (Diego, 24-11).

---

# Contesto

Sei l'Analyst del progetto. Scrivi il **documento funzionale per lo sviluppo** di
`ce-dichiarato-validatore` (intervento 01 dell'HLD) per l'iniziativa 146073 "Compliance USA Entry
Type 13" (AP-00988 Corriere Espresso / PK-03089 ce-dichiarato), **solo fase 1**.

Nella fase 1 il preavviso porta due campi nuovi: **Account Key** sulla testata della spedizione
(52 caratteri) e **Product ID** su ogni articolo (da 1 a 255). C'è anche `zonos_declaration_id`, solo
predisposto. Il validatore deve estendere i DTO, riconoscere le spedizioni soggette (USA, con merce,
prodotti interessati su `codice_prodotto` o `id_servizio`; la condizione "business" non c'è più) e controllare presenza e lunghezza dei due campi, con un errore che
indica il campo e, per il Product ID, l'articolo.

Il **contratto della fase 1** (`analisi.md`, AS-01…AS-06) è **vincolante**: il documento lo dettaglia,
non lo cambia. Incoerenze e buchi vanno fra le assunzioni e le domande aperte.

**Nomi su MongoDB (decisione di Diego del 2026-11-24)**: in `dichiarato_events` i campi si salvano con i
nomi del tracciato `zonos_account_key`, `zonos_declaration_id`, `zonos_product_id`, non camelCase.
Spring Data usa il nome del campo Java e ignora `@JsonProperty`: con nomi Java camelCase serve anche
`@Field("zonos_…")`. Il documento lo dice nei DTO, nelle regole, nei criteri di accettazione e nei test.

# Fonti

- `iniziative/146073/analisi.md`: soprattutto "Contratto della fase 1", regole R-01…R-05, punti aperti.
- `iniziative/146073/cliente/HLD_146073_dati_preadvising_fase_1.xlsx` (con `python -I` e openpyxl):
  intervento 01.
- `iniziative/146073/cliente/20261116_descrizione_compliance_usa_entry_type_13.md`: §2, §4 (validatore),
  §5, §6.
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`, `contesto/modo-di-lavorare.md`.
- Codice in **sola lettura** (non modificare, non fare checkout, non committare):
  `gitposte/SDA/preadvising/ce-dichiarato-validatore`. La copia locale può essere su un branch di
  un'altra iniziativa: leggi `origin/develop` con `git show origin/develop:<path>` o `git archive`
  nello scratchpad, e scrivi nell'intestazione il ref e il commit letti.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md` e `prompt-shipment-info.md`.

# Cosa ti chiedo

Intestazione come nel modello. Deve contenere anche il **branch di sviluppo**: `develop`
(decisione di Diego del 2026-11-24, sostituisce il branch dedicato `146073_compliance_usa_fase1`).
Non si sviluppa mai su `master` né su branch di altre iniziative (es. il branch EURODIS in checkout).

Sezioni: contesto e obiettivo, requisiti e interventi HLD coperti, dove si interviene nel codice,
dati usati, regole, esempi di messaggi, casi d'uso, configurazione, RNF e osservabilità, criteri di
accettazione numerati, casi di test, assunzioni e domande aperte, riferimenti.

Approfondisci:

1. **DTO** (`SpedizioneDTO`, `ColloDTO`, `ArticoloDTO`, `DichiaratoDTO` in `kafka/dto`): dove si
   aggiungono `zonos_account_key`, `zonos_declaration_id` e `zonos_product_id`; nomi JSON con Jackson; cosa succede
   oggi ai campi sconosciuti (`FAIL_ON_UNKNOWN_PROPERTIES`); se il validatore ripubblica il DTO
   tipizzato su `preadvising.enrichment`, sull'event store e su Mongo, e quindi se i campi non
   dichiarati si perdono. Effetto delle annotazioni Bean Validation (regola semantica generica) e
   dei log del DTO (`toString`).
2. **Regole**: Drools semantic (`validation-rules*.drl`), logic, PDB generate
   (`rules/pdb/generated/ce-pdb-rules.drl`, `pdb/dsl/`, `FieldPathMapper`, `PdbRuleHelpers`: da dove si
   generano, se c'è un generatore nel repo), copie in `.helm/config/files/rules` (configmap e
   `DROOLS_RULES_DIR` nei values di ogni ambiente), handler per famiglia di canale
   (`CanaleFlussoResolver`, `PdbPreadvisingHandler`, `SdaFlussoHandler`, `PdbPdwFlussoHandler`,
   `TfiFlussoHandler`, `TupFlussoHandler`). Indica a quali handler va applicata R-01 e dove metterla
   perché valga per tutti i canali che validano.
3. **Configurazione di AS-02** (flag, valori, elenco prodotti) nel modo in cui il servizio legge le
   proprietà (`application.yaml` con `${ENV:default}`, `envFrom` dei values `.helm`, svil, coll,
   template di prod con `_#VAR`).
4. **Codici di errore**: proponi codici nuovi verificando nel codice e nelle regole (anche negli altri
   repo della catena) che siano liberi. Spiega come si indicano collo e articolo nella descrizione,
   come si gestiscono più occorrenze dello stesso codice (la mappa degli errori ha come chiave il
   codice) e qual è l'effetto dello scarto (eventi, stati, Mongo, metriche, topic).
5. **Esempi JSON inventati** (niente dati reali) e casi di test che coprono i casi minimi della
   descrizione e ogni condizione di AS-02: non USA, documenti, prodotto fuori elenco (su `codice_prodotto` e su `id_servizio`),
   flag spento. Aggiungi i casi limite: lunghezze 51/52/53 e 255/256, più colli, più spedizioni,
   articolo senza posizione, multicollo, canali di passaggio.

# Regole

- Distingui **[FATTO]** (con la fonte), **[DECISO]** (data e riferimento), **[ASSUNTO]** (ID e default).
- Riprendi AS-01…AS-06 e aggiungi le tue con prefisso `VAL-` e numerazione da 10 (`VAL-AS-10`…).
  Domande aperte con `VAL-DA-01`…
- Niente dati di produzione e niente valori di secret: identificativi, Account Key e Product ID
  d'esempio inventati.
- Non cambiare il contratto della fase 1: le incoerenze vanno fra le domande aperte.
- Nei repo dei servizi solo lettura. Il commit in `sda-iniziative` lo fa chi ti ha chiamato.
- Lingua italiana, prosa chiara e concisa; nomi file e ID ASCII.
