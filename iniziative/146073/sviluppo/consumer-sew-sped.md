# `consumer-sew_sped` — Documento funzionale per lo sviluppo (int. 07, fase 1)

**Iniziativa**: 146073 — Compliance USA Entry Type 13 · **Fase**: 1 · **Versione**: 0.2 · **Data**: 2026-11-24
**Autrice**: Mary (analyst), DDL con Winston · **Destinatario**: sviluppatore del consumer
**Repository**: `gitlab.alm.poste.it/esiti/sda-ldv-preadv-consumer`, modulo `consumer-sew_sped`
**Branch**: `146073_compliance_usa_fase1` da **`origin/dev202508_preadvising`** [DECISO, Diego 2026-11-24: è l'unico
repo della 146073 che resta sul branch dedicato; gli altri vanno su `develop`]. Il repo non ha `develop`, e
`origin/master` contiene solo il `README` (verificato con git il 16-11). Lo sviluppo non si fa mai su
`dev202508_preadvising` o `master`, né su branch di altre iniziative.
**Copie locali**: `gitposte/SDA/ESITI/sda-ldv-preadv-consumer` è la più aggiornata (`7881cee` del 10-11).
`gitposte/SDA/preadvising/sda-ldv-preadv-consumer` è ferma a `d0d571b` e ha modifiche non committate di
altri: lì si lavora solo in un `git worktree` separato, dopo `git fetch`.
**Stack**: Java 8, client Kafka 2.2, Jackson 2.9, JDBC Informix (`ifxjdbc` 3.70.JC7X1), libreria
`sdaKafkaLibrary` (`SdaConsumer`). Progetto Eclipse senza `pom.xml`, jar su `L:`. Nessun test automatico nel repo.
**Generato da**: [prompt-consumer-sew-sped.md](prompt-consumer-sew-sped.md)
**Fonti**: [analisi.md](../analisi.md), "Contratto della fase 1" AS-01…AS-06 (**vincolante**);
`cliente/HLD_146073_dati_preadvising_fase_1.xlsx`, int. 07; codice di `origin/dev202508_preadvising`
letto il 16-11. **DDL**: [ddl-sew-146073.md](ddl-sew-146073.md)

Etichette:
- **[FATTO]**: scritto nell'HLD o nel codice, con la fonte.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default, da confermare (sezione 10).

> **Aggiornamento 0.2 (2026-11-24).** Nomi dei campi `zonos_account_key`, `zonos_product_id`,
> `zonos_declaration_id` (Diego, 23-11); colonne SEW con gli stessi nomi (Diego, 24-11); branch
> `develop` (Diego, 24-11).
>
> Il contratto della fase 1 (AS-01…AS-07 di `analisi.md`) non si cambia. Dove il codice non torna con
> il contratto, la differenza è segnata fra le assunzioni SEW-xx.

---

## 1. Contesto e obiettivo

`consumer-sew_sped` legge dal topic Kafka della catena preadvising i preavvisi completati di SDA e li
scrive nelle tabelle SEW su Informix. Il nome del topic e quello della tabella arrivano dal file di
properties esterno (`kafka.topic`, `kafka.tabella`), che non sta nel repo [FATTO, `App.runConsumer`].
Il topic atteso è `preadvising.completed.sda`, uscita SDA dello smistatore: va confermato sulle
properties dell'ambiente.

Con l'int. 07 il consumer deve **storicizzare in `sew_spedizioni_work` i 3 nuovi campi** [FATTO, HLD]:

| Campo (AS-01) | Livello nel tracciato | Fase 1 |
|---|---|---|
| `zonos_account_key` | `spedizione[]` (testata) | valorizzato per le spedizioni soggette, 52 caratteri |
| `zonos_declaration_id` | `spedizione[]` (testata) | solo predisposto: sempre assente o `null` |
| `zonos_product_id` | `spedizione[].collo[].articolo[]` | valorizzato per ogni articolo delle spedizioni soggette, da 1 a 255 caratteri |

**Non fa**: validazione dei campi (è del validatore), Zonos, palmari (`consumer-sew-sped-pre-adv-on-out-tot`,
AS-06), stampe.

## 2. Interventi HLD coperti

| Int. | Titolo HLD | Cosa chiede | Dove nel documento |
|---|---|---|---|
| 07 | Adeguamento consumer `sew_spedizioni` | "I 3 nuovi campi … devono essere storicizzati dentro la tabella `sew_spedizioni_work`: modifica del consumer kafka per ricevere e storicizzare i 3 nuovi campi" (stima 0,32) | sezioni 3, 4, 5 |

Nel foglio Impatti l'int. 07 non ha la voce Database. La DDL è comunque necessaria (sezione 7).

## 3. Come lavora oggi il consumer [FATTO, codice]

`App.processRecord` decide la tabella così:

| Messaggio | Ramo | Scrittura |
|---|---|---|
| `id_file` valorizzato, `flag_autoproduttore` `S`/`Y` | insert | `QueriesManagerDao.insertSewSpedizioni(conn, dto, tabella)`: tabella da `kafka.tabella`, cioè `sew_spedizioni_work` (`queryInsertSewSpedizioniWork`), `sew_spedizioni_work_2` (`queryInsertSewSpedizioniWork2`) oppure `sew_spedizioni` (`queryInsertSewSpedizioni`). I clienti BS (`BsClientCache`) vanno sempre su `sew_spedizioni_work` |
| `id_file` valorizzato, non autoproduttore | insert | `CliDatiStampaTfDao.insert` su `cli_dati_stampa_tf_2` |
| `id_file` assente (preavviso nato in SDA e rientrato dalla catena, vedi [producer-sew-sped.md](producer-sew-sped.md)) | update | `updateSewSpedizioniWork`, `updateSewSpedizioni` o update di `cli_dati_stampa_tf`: **solo indirizzi, telefoni e normalizzazione** |

- Una riga per messaggio: si leggono solo `spedizione.get(0)` e `collo.get(0)`.
- L'insert è un `PreparedStatement` con parametri posizionali (`setParam(pstm, n, valore, tipo, campoVuoto)`).
  Nelle tabelle work i parametri sono 102. Il blocco `if (!query.equals("sew_spedizioni"))` valorizza
  le colonne da 92 a 102, che esistono solo nelle work.
- `setParam` con `campoVuoto = true` scrive `" "` (o `0`) al posto di `null`.
- Un duplicato di chiave viene saltato (idempotenza). Gli altri errori fanno partire il retry sul
  savepoint del record; dopo `record.retry.max-attempts` tentativi il record viene saltato.
- **Nessuna tabella articoli**: `ColloDTO.articolo` (lista di `ArticoloColloDTO`: `posizione`,
  `codice_taric`, `valore`, `quantita`, `peso_totale`, `paese_origine`) viene deserializzata ma non
  scritta da nessuna parte.
- Il mapper Jackson ha `FAIL_ON_UNKNOWN_PROPERTIES = false` e `ACCEPT_CASE_INSENSITIVE_PROPERTIES = true`.
  Oggi un campo nuovo nel JSON viene ignorato senza errori.

## 4. Dove si interviene nel codice

| Punto | Cosa si fa |
|---|---|
| `dto/SpedizioneDTO.java` | nuovi campi `String zonos_account_key`, `String zonos_declaration_id`, con getter e setter nello stile del file (snake_case, nessuna annotazione) |
| `dto/ArticoloColloDTO.java` | nuovo campo `String zonos_product_id`, con getter e setter. Serve per la variante B (SEW-02) e per non perdere il campo nel DTO |
| `constants/AppConstants.java` | `queryInsertSewSpedizioniWork` e `queryInsertSewSpedizioniWork2` **restano come sono**. `queryInsertSewSpedizioni` **non cambia** (SEW-01) |
| `dao/QueriesManagerDao.insertSewSpedizioni` | [DECISO, Diego 23-11] solo per le tabelle work (blocco `if (!query.equals("sew_spedizioni"))`): se `zonos_account_key` è **valorizzato** si aggiungono in coda la colonna `zonos_account_key` e un `?` (parametro 103); se è valorizzato `zonos_declaration_id`, la colonna `zonos_declaration_id` e un `?` (parametro successivo). "Valorizzato" = non `null` e non `""`. Senza i campi lo statement è **identico a quello di oggi** e le colonne prendono il default `''`: il consumer funziona anche prima della DDL. I valori si passano così come sono (`Types.CHAR` o `VARCHAR`), senza trim |
| `dao/QueriesManagerDao` (update), `CliDatiStampaTfDao` | **nessuna modifica** (SEW-01, SEW-04) |
| log | nel log DEBUG di `insertSewSpedizioni` si può aggiungere `zonos_account_key=presente/assente`, mai il valore |

Nota a margine, fuori perimetro: `gestisciAutoproduttore` chiama `insertSewSpedizioni(conn, dto, idLdv)`,
quindi passa l'LDV dove il metodo si aspetta il nome della tabella. Il ramo finisce sempre su
`sew_spedizioni_work`. È il comportamento di oggi e non si corregge qui.

## 5. Mapping campo JSON → colonna

| Campo JSON (AS-01) | DTO | Tabella.colonna | Tipo (DDL) | Regola |
|---|---|---|---|---|
| `spedizione[0].zonos_account_key` | `SpedizioneDTO.zonos_account_key` | `sew_spedizioni_work.zonos_account_key`, `sew_spedizioni_work_2.zonos_account_key` | `char(52) default ''` | così com'è: niente trim, maiuscole o troncamenti (R-04). Assente, `null` o vuoto → colonna fuori dallo statement, resta `''` |
| `spedizione[0].zonos_declaration_id` | `SpedizioneDTO.zonos_declaration_id` | `….zonos_declaration_id` | `char(13) default ''` | come sopra. In fase 1 di norma è assente, quindi resta `''` |
| `spedizione[0].collo[].articolo[].zonos_product_id` | `ArticoloColloDTO.zonos_product_id` | **nessuna** nella variante A di default (SEW-02). Variante B: `sew_spedizioni_work_art.zonos_product_id` | `char(255) default ''` | una riga per articolo, con `posizione` |

"Vuoto" vale per la stringa `""`. Una stringa di soli spazi si scrive com'è: il validatore la scarta
prima (AS-03). Le colonne sono `char`: Informix completa con spazi a destra fino alla lunghezza, quindi
chi le legge (es. il producer) toglie gli spazi finali prima di confrontarle.

## 6. Esempi [dati inventati]

Messaggio (estratto), con `id_file` valorizzato, autoproduttore, `kafka.tabella=sew_spedizioni_work`:

```json
{
  "canale": "IS", "id_file": "f1460730-0000-4000-8000-000000000001", "flag_autoproduttore": "S",
  "spedizione": [{
    "rif_spedizione": "ORD-TEST-146073-01",
    "zonos_account_key": "AK00000000000000000000000000000000000000000000000001",
    "zonos_declaration_id": null,
    "destinatario": { "codice_nazione": "USA", "codice_nazione_iso_2": "US" },
    "collo": [{
      "id_ldv": "TST146073001",
      "articolo": [
        { "posizione": "1", "codice_taric": "6109100010", "zonos_product_id": "PRD-TEST-0001" },
        { "posizione": "2", "codice_taric": "6203423100", "zonos_product_id": "PRD-TEST-0002" }
      ]
    }]
  }]
}
```

Riga attesa in `sew_spedizioni_work` (solo le colonne nuove): `id_ldv = 'TST146073001'`,
`zonos_account_key = 'AK0…01'` (52 caratteri), `zonos_declaration_id = ''` (non è nello statement:
default). Le altre colonne restano identiche a oggi.

Lo stesso messaggio senza `zonos_account_key` (spedizione non USA): lo statement è quello di oggi,
`zonos_account_key = ''`, `zonos_declaration_id = ''`, il resto invariato.

## 7. Configurazione e prerequisiti

- **DDL** (vedi [ddl-sew-146073.md](ddl-sew-146073.md), script 1 e 2). Le colonne entrano nell'insert
  solo se i campi arrivano valorizzati, quindi il codice si può rilasciare anche prima della DDL. La
  DDL deve però essere eseguita **prima** che il builder mandi i campi e che il validatore accenda la
  regola: un insert con le colonne nuove su una tabella senza colonne va in errore e, dopo i retry, il
  record viene saltato.
- Nessuna property nuova. `kafka.tabella` resta com'è.
- Il pacchetto si consegna come oggi (HLD, Delivery: pacchetti su SVN).

## 8. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato il messaggio della sezione 6 con `kafka.tabella=sew_spedizioni_work`, la riga inserita ha `zonos_account_key` uguale al valore ricevuto, carattere per carattere (52), e `zonos_declaration_id` `''` (default) |
| AC-02 | Come AC-01 con `kafka.tabella=sew_spedizioni_work_2`: stesso risultato su `sew_spedizioni_work_2` |
| AC-03 | Dato un messaggio senza `zonos_account_key` né `zonos_declaration_id`, oppure con valori `null` o `""`, lo statement è identico a quello di oggi e le due colonne valgono `''` (default) |
| AC-04 | Dato un messaggio con `zonos_declaration_id: "DECL-TEST-0001"` (caso di prova per la predisposizione), la colonna vale `DECL-TEST-0001` |
| AC-05 | Dato un messaggio di un cliente BS, la riga va su `sew_spedizioni_work` con i nuovi campi, qualunque sia `kafka.tabella` |
| AC-06 | Con `kafka.tabella=sew_spedizioni` l'insert funziona come prima, senza colonne nuove e senza errori |
| AC-07 | Per i messaggi non autoproduttore (`cli_dati_stampa_tf_2`) e senza `id_file` (update), il comportamento è identico a prima |
| AC-08 | Un messaggio storico, senza i campi nuovi nel JSON, viene scritto come prima (R-05), anche su una tabella su cui la DDL non è ancora stata eseguita |
| AC-09 | Nessun log riporta i valori di `zonos_account_key` o `zonos_product_id` |
| AC-10 | Un messaggio duplicato (stessa chiave) viene ancora saltato come duplicato: idempotenza invariata |

## 9. Casi di test

Nel repo non ci sono test automatici. I test si fanno in svil, su Informix di sviluppo, con messaggi
costruiti a mano sul topic del consumer (AS-05) e LDV di test. Prima della DDL e del rilascio si
lavora su un consumer locale puntato su svil.

| TC | Input | Atteso | AC |
|---|---|---|---|
| TC-01 | sezione 6, tabella work | colonne nuove valorizzate | AC-01 |
| TC-02 | sezione 6, tabella work_2 | idem su `_2` | AC-02 |
| TC-03 | senza campi, con `null`, con `""`; ripetuto su una tabella senza DDL | statement di oggi, colonne `''`; nessun errore senza DDL | AC-03, AC-08 |
| TC-04 | `zonos_declaration_id` valorizzato | salvato | AC-04 |
| TC-05 | cliente BS con `kafka.tabella=sew_spedizioni_work_2` | riga su work | AC-05 |
| TC-06 | `kafka.tabella=sew_spedizioni` | insert ok, nessun errore | AC-06 |
| TC-07 | non autoproduttore; messaggio senza `id_file` | regressione: come prima | AC-07 |
| TC-08 | stesso messaggio due volte | il secondo viene saltato come duplicato | AC-10 |
| TC-09 | log a livello DEBUG di TC-01 | nessun valore dei campi nuovi | AC-09 |
| TC-10 | catena completa in svil: preavviso USA dal builder (o a mano su `preadvising.pre-enrichment`) fino alla SEW | `zonos_account_key` uguale a quello inviato | AC-01 |

## 10. Assunzioni e domande aperte

Dal contratto (`analisi.md`): AS-01 (nomi e posizione), AS-04 (colonne SEW, DDL del DBA), AS-05
(ingresso), AS-06 (fuori dalla fase 1).

Nuove (Mary, 16-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| SEW-01 | **Tabelle.** L'HLD cita solo `sew_spedizioni_work`. Lo stesso insert scrive anche `sew_spedizioni_work_2` (stesse colonne) e, con `kafka.tabella=sew_spedizioni`, `sew_spedizioni`. I non autoproduttori vanno su `cli_dati_stampa_tf_2` | colonne nuove su `sew_spedizioni_work` e `_2`. `sew_spedizioni` e `cli_dati_stampa_tf(_2)` non si toccano in fase 1 | Poste (owner SEW) |
| SEW-02 | **Product ID senza tabella articoli.** AS-04 vuole `zonos_product_id` nella "tabella articoli che il consumer scrive già", ma questo consumer non ne scrive nessuna. L'HLD dice "3 campi in `sew_spedizioni_work`", che ha una riga per LDV: per R-04 il Product ID non si appiattisce sulla spedizione | **variante A**: `zonos_product_id` nel DTO, non salvato. **Variante B**, se Poste conferma: nuova tabella figlia `sew_spedizioni_work_art` (`id_ldv`, `posizione`, `zonos_product_id`, `data_ins`), DDL opzionale nello script 5 di [ddl-sew-146073.md](ddl-sew-146073.md), con una insert per articolo nella stessa transazione | Poste |
| SEW-03 | **Lunghezza di `zonos_declaration_id`** | **[DECISO, Diego 23-11]** `char(13) default ''` | chiusa |
| SEW-04 | **Update.** Per i messaggi senza `id_file` il consumer aggiorna solo indirizzi e telefoni. I campi nuovi in quella riga li ha già scritti chi ha creato il record (portali e web service, vedi PRD-05) | update invariati | Diego |
| SEW-05 | **Campi assenti.** Superata dalla decisione di Diego del 23-11: le colonne hanno default `''` ed entrano nello statement solo se il campo è valorizzato | **[DECISO]** colonna fuori dallo statement, resta `''` | chiusa |
| SEW-06 | **Lunghezze.** Il consumer non controlla le lunghezze, che sono garantite dal validatore (52, 1-255). Se un valore più lungo arrivasse lo stesso, l'esito dipende da Informix (troncamento o errore e poi skip) | nessun controllo nel consumer | — |
| SEW-07 | **Branch base**: il repo non ha `develop` | **[DECISO, Diego 24-11]** `146073_compliance_usa_fase1` da `origin/dev202508_preadvising` | chiusa |
| SEW-08 | **Topic e tabella in ambiente**: le properties sono esterne al repo | `preadvising.completed.sda`, `kafka.tabella=sew_spedizioni_work`. Da verificare sul file dell'ambiente | Diego |

## 11. Riferimenti

- [analisi.md](../analisi.md), "Contratto della fase 1".
- [ddl-sew-146073.md](ddl-sew-146073.md): DDL Informix.
- [producer-sew-sped.md](producer-sew-sped.md): il producer dello stesso repo (int. 09), che legge `sew_spedizioni_work`.
- [consumer-sew-sped-poste.md](consumer-sew-sped-poste.md): l'equivalente lato Poste (int. 08).
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md): catena e smistatore.
