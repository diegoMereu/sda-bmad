# Prompt — documento funzionale del producer dell'int. 09 (146073)

> Prompt per Mary (analyst): individua il batch producer dell'int. 09 e scrivine il documento
> funzionale per la fase 1 dell'iniziativa 146073.
> Output: `iniziative/146073/sviluppo/producer-sew-sped.md` (nome del componente individuato).
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Iniziativa 146073 "Compliance USA Entry Type 13", **solo la fase 1**. I campi
nuovi sono:
- `account_key`: testata della spedizione, 52 caratteri;
- `product_id`: per articolo, da 1 a 255 caratteri;
- `declaration_id`: solo predisposto.

Sono i "3 nuovi campi" dell'HLD. Il contratto della fase 1 di `iniziative/146073/analisi.md`
(AS-01…AS-06) è **vincolante**.

HLD, int. 09 "Adeguamento producer dati da portali e webservice": "deve essere modificato il batch che
prende i dati di preavviso dei portali e dei webservice per inviare anche i 3 nuovi campi: modifica
producer kafka". Il repo non è indicato (PA-06).

**Branch (regola di Diego)**: lo sviluppo si fa sul branch dedicato `146073_compliance_usa_fase1`, da
`origin/develop`. Se il repo non ha `develop`, si parte dal branch di integrazione, dopo averlo
verificato con git, e lo si scrive nell'intestazione. Mai sviluppo su `develop` o `master`, né su
branch di altre iniziative.

# Prima: individua il producer

- Candidato principale: `sda-ldv-preadv-consumer/producer-sew-sped`, che legge le SEW e pubblica su
  Kafka. Verifica se è davvero il batch "portali e webservice" oppure uno strumento di replay o di
  migrazione: guarda canali, watermark, flag di trasmissione, `id_file`, schedulazione.
- Cerca altri candidati in `gitposte/SDA` (ESITI, CORRIERE-ESPRESSO, Altro, Internazionale,
  preadvising): producer Kafka che leggono preavvisi da tabelle di portali e web service (SEW_*,
  PRE_WEB, Informix) e producono su topic preadvising.
- Scrivi il funzionale sul candidato più probabile e dichiara il grado di certezza, con gli indizi e
  l'elenco di quello che hai escluso. Se non lo trovi, scrivi solo cosa hai escluso e metti la domanda.

# Fonti

- `iniziative/146073/analisi.md`; HLD fase 1 (`python -I` e openpyxl).
- `contesto/microservizi-preadvising.md`, `contesto/linee-guida-sviluppo.md`.
- Codice in sola lettura (non modificare, non fare checkout, non committare). Copia più aggiornata:
  `gitposte/SDA/ESITI/sda-ldv-preadv-consumer`. Leggi `producer-sew-sped/App`,
  `dao/QueriesManagerDao` (`getRecordsToSend`, `mapRowToTopic`, `mapSpedizione`, `mapCollo`,
  `mapArticolo`, `setTextIfColumnPresent`) e i DTO.
- [consumer-sew-sped.md](consumer-sew-sped.md) e [ddl-sew-146073.md](ddl-sew-146073.md): le colonne
  nuove di `sew_spedizioni_work`.
- Modello di forma: `iniziative/144216/sviluppo/shipment-info.md`.

# Cosa ti chiedo

Struttura: intestazione (branch e base verificata), individuazione con certezza ed esclusi, interventi
HLD coperti, come lavora oggi, dove si interviene, mapping colonna sorgente → campo JSON, esempio,
configurazione e prerequisiti, criteri di accettazione numerati, casi di test, assunzioni e domande
(prefisso PRD-).

Approfondisci:
1. da quali colonne si leggono i campi e cosa succede se mancano (`null`, `""`, `NON_NULL`);
2. il Product ID: esiste una sorgente per articolo?;
3. chi valorizza i campi nelle tabelle sorgente (portali e web service, fuori perimetro);
4. le SELECT nelle properties esterne e l'ordine rispetto alla DDL.

# Regole

- **[FATTO]**, **[DECISO]**, **[ASSUNTO]** (ID e default), prefisso `PRD-`.
- Niente dati di produzione né secret; esempi inventati; non riportare stringhe di test con nomi di persona.
- Lingua italiana, conciso.
