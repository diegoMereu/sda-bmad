# 146073 — Dazi USA: nuovi campi e controlli sul preadvising — analisi

Versione 0.1 del 2026-11-16. Fonte: i due HLD v.1 del 09/11/2026 in `cliente/`
(`HLD_146073_dati_preadvising_fase_1.xlsx`, `HLD_146073_dati_preadvising_fase_2.xlsx`,
titolo interno "HLD_146073 - Dazi dati preadvising"). Sistema impattato in entrambi:
**AP-00988 Corriere Espresso / PK-03089 ce-dichiarato**.

## Obiettivo

Il preavviso delle spedizioni soggette ai dazi USA deve avere due campi in più, **Account Key**
e **Product ID**. Va controllato in validazione e i dati vanno propagati lungo tutta la
catena preadvising fino alle tabelle SEW e a BEP. L'HLD parla di **3 nuovi campi**
(interventi 07, 08 e 09 della fase 1), ma ne nomina solo due (vedi PA-01).

L'iniziativa è divisa in due fasi:

- **Fase 1**: riconoscere le spedizioni, validare e propagare i nuovi campi. Ci sono già
  i campi predisposti per la fase 2.
- **Fase 2**: nuova lavorazione dell'orchestratore, ricezione di un campo da un "nuovo
  sistema integrato" e invio dei due campi a BEP per la verifica su **SOROS**.

## Fase 1 — interventi

| Int. | Microservizio | Cosa fa (HLD) | Stima TOW 1.2 | Repo (da verificare) |
|---|---|---|---|---|
| 01 | `ce-dichiarato-validatore` | Riconosce i casi in cui il preavviso deve avere Account Key e Product ID, aggiunge una validazione dedicata e prepara la propagazione dei campi. Va modificato il DTO e vanno scritte le nuove regole | 0,80 | `ce-dichiarato-validatore` (regole Drools in `rules/`, handler `PdbPreadvisingHandler`, `SdaFlussoHandler`, `PdbPdwFlussoHandler`…) |
| 02 | `ce-dichiarato-orchestratore` | Propaga i nuovi campi sul topic: modifica del DTO, salvataggio a DB e metodo di merge | 0,40 | `ce-dichiarato-orchestratore` (`OrchestratoreService`, merge) |
| 03 | `ce-dichiarato-smistatore` | Riceve i nuovi campi e li propaga sul topic | 0,40 | `ce-dichiarato-smistatore` |
| 04 | `ce-dichiarato-monitoring`, event store, bff | Riceve i nuovi campi e li propaga | 0,40 | `ce-event-handler-monitoring`, `ce-event-handler-event-store`, `ce-dichiarato-bff` |
| 05 | `ce-dichiarato-adapter` | Riceve i nuovi campi nei 3 consumer (PDB, PDW, ILP) e li propaga | 0,40 | `ce-dichiarato-adapter` (`KafkaConsumerPDB`, `KafkaConsumerPDW`, consumer ILP) |
| 07 | Consumer `sew_spedizioni` | Salva i 3 nuovi campi nella tabella `sew_spedizioni_work` | 0,32 | `sda-ldv-preadv-consumer/consumer-sew_sped` (`AppConstants.queryInsertSewSpedizioniWork*`) |
| 08 | Consumer `sew_spedizioni_poste` | Salva i 3 nuovi campi nella tabella `sew_spedizioni_poste` (unico intervento con impatto Database, M50) | 0,32 | `gitposte/SDA/ESITI/poste-ldv-preadv-consumer/consumer-sew_sped_poste` |
| 09 | Producer dei dati da portali e web service | Modifica del batch che legge i preavvisi dei portali e dei web service, perché invii anche i 3 nuovi campi | 0,45 | da individuare (forse `sda-ldv-preadv-consumer/producer-sew-sped`, che legge le SEW e pubblica su Kafka) |

Non esiste un intervento 06 in fase 1: la numerazione salta dal 05 al 07.

## Fase 2 — interventi

| Int. | Microservizio | Cosa fa (HLD) | Stima TOW 1.2 |
|---|---|---|---|
| 02 | `ce-dichiarato-orchestratore` | Instrada i casi riconosciuti in fase 1 verso una **nuova tipologia di lavorazione** e predispone la ricezione del suo esito. Va implementata la **lista dei campi che questa lavorazione può sovrascrivere** nel preavviso (DTO, salvataggio a DB, merge) | 1,00 |
| 05 | `ce-dichiarato-adapter` | Riceve il nuovo campo nei 3 consumer. Non si può anticipare in fase 1 perché il nome del campo del sistema integrato non è ancora noto | 0,50 |
| 06 | Invio e ricezione verso BEP | Aggiunge alla richiesta verso BEP i **due nuovi campi** che servono per la verifica su SOROS (modifica dell'evento Kafka prodotto verso BEP) | 0,54 |
| 03, 04, 07, 08, 09 | smistatore, monitoring/event store/bff, consumer SEW, producer portali | Nessuna stima. L'HLD presume che in fase 1 la predisposizione copra **anche il campo propagato dal nuovo sistema integrato** | — |

Il verso BEP passa da `ce-dichiarato-ldv-pdb` e `ce-dichiarato-ldv-pdb-sync`
(`BepClient`, `waybill-service-ou`). L'HLD però parla di "evento Kafka prodotto verso BEP",
quindi va confermato quale dei due flussi è coinvolto (PA-06).

## Stime HLD (Accenture)

| | TOW 1.1 Analisi | TOW 1.2 Sviluppo | TOW 1.3 Collaudo | TOW 1.4 Delivery | Importo |
|---|---|---|---|---|---|
| Fase 1 | 1,89 | 3,49 | 1,25 | 1,10 | 22.388,73 € |
| Fase 2 | 1,08 | 2,04 | 0,71 | 0,61 | 12.969,62 € |

Catalogo dimensionale:
- Fase 1: 11 Servizio/API/Microservizio medio 0,5 e 1 Database medio 0,5.
- Fase 2: 6 Servizio/API/Microservizio medio 0,5.

Entrambe le fasi contano anche 1 Integration SFTP e 1 Sterling Integrator (basso 0,3).
Nel foglio Impatti queste due voci non sono legate a nessun intervento: sembrano un residuo
del template.

## Cosa c'è già nel tracciato unico

Nell'ICD del tracciato unico preadvising (`ICD_PREADVISING_LDV_EVENT_SOURCE_v11`, in
`iniziative/136596/`) e nel codice dei repo preadvising **non esiste** nessun campo
Account Key o Product ID, né riferimenti a SOROS. Ci sono già i campi doganali, che possono
servire a riconoscere le spedizioni:

- In `spedizione.importi`: `importo_diritti_doganali`, `incasso_diritti_doganali`,
  `status_doganale`, `flag_pddp`, `addebito_oneri`, `importo_oneri`.
- In `spedizione.internazionale`: `nazionalita`, `valore_spedizione`, `valuta`,
  `descrizione`.
- In `spedizione.collo.articolo`: `codice_taric`, `valore`, `valuta`, `english_descr`.

Nel T&T-Repo (`pacchi_anagrafica`, ICD 138975) esistono `customsDeclaration_*` e
`price_customsCharges`.

## Punti aperti

| # | Punto | Perché serve |
|---|---|---|
| PA-01 | Qual è il **terzo campo**? L'HLD dice "3 nuovi campi" ma nomina solo Account Key e Product ID. Forse è il campo del sistema integrato della fase 2 | DTO, DDL SEW, ICD |
| PA-02 | Nome, tipo, lunghezza e obbligatorietà di Account Key e Product ID, e la loro posizione nel tracciato unico (sezione `spedizione.importi`, `spedizione.internazionale` o una nuova sezione) | ICD, validatore, DDL |
| PA-03 | Regola che individua le spedizioni soggette: solo destinazione USA (`nazione` del destinatario `US`/`USA`)? Per quali clienti, canali e prodotti? Ci sono soglie di valore? | Validatore (int. 01) |
| PA-04 | Esito della validazione se mancano i campi: scarto (codice e descrizione errore) o warning? | Validatore, scarti |
| PA-05 | Da dove arrivano i campi in ingresso: tracciati a file (builder), PDB, PDW, ILP, portali e web service. Con quali nomi in ciascun canale? | Builder, adapter (int. 05), producer (int. 09) |
| PA-06 | Verso BEP: quale flusso (`ldv-pdb` asincrono, `ldv-pdb-sync` `waybillCreate`, `enrichment_bep`) e quale contratto per i due campi. Cos'è SOROS e chi fa la verifica | Int. 06 fase 2 |
| PA-07 | Fase 2: qual è la "nuova tipologia di lavorazione", su che topic gira, chi la esegue e quali campi può sovrascrivere | Orchestratore fase 2 |
| PA-08 | Fase 2: nome e formato del campo del "nuovo sistema integrato". Senza questo dato non si può fare la predisposizione in fase 1 che l'HLD presume per smistatore, monitoring, SEW e producer | Coerenza fase 1 / fase 2 |
| PA-09 | DDL di `sew_spedizioni_work` (e `_2`?) e `sew_spedizioni_poste`: l'HLD stima un impatto Database solo per `sew_spedizioni_poste`. Dove sta `sew_spedizioni_poste` e chi esegue le DDL | Int. 07, 08 |
| PA-10 | Il batch producer dei preavvisi da portali e web service: quale repo? Il consumer di `sew_spedizioni_poste` è `ESITI/poste-ldv-preadv-consumer/consumer-sew_sped_poste` | Int. 09 |
| PA-11 | Palmari (`sew_sped_pre_adv_online_out_tot`), T&T-Repo e OneTracking sono fuori perimetro? | Perimetro |

## Incongruenze negli HLD

- Il file della fase 2 ha come titolo interno "…dati preadvising_fase1".
- Nel foglio Impatti la numerazione non corrisponde a quella del foglio HLD:
  - in fase 1 l'intervento 04 compare solo come "monitoring";
  - in fase 2 gli interventi sono numerati 01, 02 e 03, mentre nel foglio HLD sono 02, 05 e 06.
- Il "nuovo campo" dell'adapter in fase 2 non si può anticipare perché il suo nome è
  ignoto. Gli altri servizi però dovrebbero predisporlo già in fase 1.
