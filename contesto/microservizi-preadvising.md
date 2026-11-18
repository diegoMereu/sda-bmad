# Microservizi della catena preadvising (Corriere Espresso)

Repository clonati in `C:\Users\diego.mereu\gitposte\SDA\preadvising`, namespace
OpenShift `corriere-espresso-preadvising`. Nomi dei topic presi dai values Helm
(novembre 2026): prima di usarli in un documento ricontrolla i values del servizio.

## Catena (flussi a file e via API)

```
file cliente -> ce-dichiarato-builder -> preadvising.pre-enrichment
API EURODIS  -> ce-dichiarato-eurodis-in -> preadvising.eud.pre.build -> ce-dichiarato-eurodis-mapper -> preadvising.pre-enrichment
preadvising.pre-enrichment -> ce-dichiarato-validatore -> preadvising.enrichment
-> ce-dichiarato-orchestratore (passi per canale: normalizzazione, check-ldv, ldv-pdb, enrichment_bep, ldv-bep-sync)
   ldv-pdb      -> preadvising.enrichment.pdb     -> ce-dichiarato-ldv-pdb      -> preadvising.enrichment
   ldv-bep-sync -> preadvising.enrichment.bepsync -> ce-dichiarato-ldv-pdb-sync
-> preadvising.completed -> ce-dichiarato-smistatore -> preadvising.completed.poste / .completed.sda / palmari
```

| Servizio | Cosa fa |
|---|---|
| `ce-dichiarato-builder` | Riceve i file dei clienti (`preadvising.file.upload`), li converte nel tracciato unico ICD, pubblica gli eventi di stato del file. Configurazione per cliente in `docstructureconfigs/client/` (es. il cliente fisso del flusso EUD a file) |
| `ce-dichiarato-validatore` | Validazione del tracciato con regole Drools, handler per famiglia di canale (`PdbChannel`, `PdbPreadvisingHandler`, `SdaFlussoHandler`). Un canale non riconosciuto finisce nel flusso SDA di default (errore 143 "cliente non configurato") |
| `ce-dichiarato-orchestratore` | Decide i passi per canale in `application.yaml` (sezione dei canali con l'elenco dei `nome:`) e in `CANALI_PDB` di `OrchestratoreService` |
| `ce-dichiarato-ldv-pdb` | Crea la LDV su BEP/PDB (`preadvising.enrichment.pdb`). Il canale BEP si ricava in `BepChannel.fromCanale` (toglie i prefissi `PDB_` ed `EUD_`) |
| `ce-dichiarato-ldv-pdb-sync` | Variante sincrona verso PDB `waybillCreate` (`preadvising.enrichment.bepsync`). Progetto distinto da `ce-dichiarato-ldv-pdb` |
| `ce-dichiarato-adapter` | Esiti e fase 2 PDB/PDW/ILP; consulta `ce-anagrafica` e ce-rules. Modello di riferimento per metriche, span e Dockerfile |
| `ce-dichiarato-smistatore` | Instrada `preadvising.completed` verso Poste, SDA e palmari secondo `CANALI_POSTE`, `smistatore.canali.sda`, `CANALI_ESCLUSI_PALMARI` |
| `ce-dichiarato-state-machine-handler`, `ce-event-handler-*` | Stati e storico degli eventi |
| `ce-anagrafica` | REST: `GET /anagrafica/indirizzi/nazione/{codice}` (codice di 2, 3 o 4 caratteri; risponde ISO3 `codNazione`, ISO4 Poste `codNazionePoste`, ISO2 `codNazione2`), `GET /anagrafica/matrice/filiale?cap=&localita=` (in cache) |
| `ce-db-sync` | Allinea PostgreSQL `ce_cen` con l'anagrafica clienti di Informix: CRUD REST generico (Spring Data REST, `POST /api/<tabella>` = upsert, una entity per tabella, JWT), caricamento CSV manuale (`CsvProductionSync`), batch orario `PostazioneMongoSyncJob` che riporta su Mongo `dichiarato_ldv_history` i cambi di `id_postazione`. Copia delle procedure Informix in `sql/procedure/` (documentazione). Secret `ce-postgres`, Mongo dal secret del validatore. Dettagli nel suo `CLAUDE.md` |
| `ce-vendite` | REST di lettura su `ce_cen` per anagrafica e configurazione cliente (`/vendite/...`, con cache): fra gli altri `id-postazione-da-seme` e `configurazione-postazione-da-seme` (seme LDV → postazione da `cen_postazioni.id_seme_ldv`; per i clienti PDB anche da `sfa_postazioni_ou`), `id-tipo-seme`, `postazione-mysda` |
| `ce-ldv` | REST sulle LDV: `GET /ldv/seme/{ldv}` → seme e tipo seme (semantica `PPTT` per le LDV PDB, `LdvSemanticaUtil`) |
| `ce-event-handler-monitoring` | Eventi verso il monitoraggio: filtra i canali con `MONITORING_FILTRO_CANALE_ALLOWED`; degli eventi file converte solo i canali `IS`/`IF`. Un canale nuovo va aggiunto all'elenco, altrimenti non compare nel monitoraggio |
| `ce-dichiarato-eurodis-in`, `-mapper`, `ce-eurodis-send-tracking` | Flusso EURODIS autoproduttore: vedi `iniziative/136596/sviluppo/`. In sintesi: `-in` registra il file fittizio in Mongo `preadvising_file` come il builder e mette la ragione sociale `EURODIS GmbH` (`EURODIS_FILE_RAGIONE_SOCIALE`) negli eventi file (campi cliente vuoti omessi). Il mapper accetta solo LDV PDB (le altre si scartano) e prende contratto, centro di costo, id cliente, ragione sociale, P.IVA e CF dalla postazione del seme (cache → tabella `eurodis_postazioni` di `ce_eud_api_in` → `ce-vendite` → upsert), configurazione solo come fallback. Il send-tracking legge `eurodis_postazioni` (filtro: LDV PDB, seme in lista, `eurodis = true`), senza chiamare `ce-vendite`; elaborazione in parallelo a batch prevista |

Nota su `ce-vendite`: `configurazione-postazione-da-seme` cerca anche in `sfa_postazioni_ou`
(postazioni PDB) ma non espone il `booking_channel`.

## Canale dei clienti PDB lungo la catena

- `ce-dichiarato-ldv-pdb` non scrive `canale`/`id_canale` nel tracciato: ricava il canale BEP dal
  `canale` con `bep.canali.mapping` (es. `EUD_INVIOSYSTEM` → `INVIOSYSTEM`).
- BEP ripete il `channel` della request nel `booking_channel` di ANAG_LDV.
- L'adapter (`KafkaConsumerPDB`) cerca il preadvising con `rif_spedizione` + suffisso del
  `booking_channel`: se lo trova va in Fase 2 su `preadvising.enrichment` con il canale a DB;
  altrimenti flusso normale su `preadvising.pre-enrichment` con `canale = "PDB"` e
  `id_canale` = booking_channel BEP. Verificato funzionante per `EUD_INVIOSYSTEM` (novembre 2026).
- Il contratto di un autoproduttore può non avere nazioni estere abilitate verso BEP: per EURODIS
  vale la regola ITA1 costante (`iniziative/136596/bep-nazione-mittente-estero.md`).

## Aggiungere un canale nuovo

Va toccato in tutti questi punti, altrimenti il messaggio si ferma a metà catena:

1. **validatore**: enum dei canali (`PdbChannel` o equivalente), handler, regole Drools che citano i canali;
2. **orchestratore**: passi del canale in `application.yaml`, `CANALI_PDB`;
3. **ldv-pdb / ldv-pdb-sync**: conversione nel canale BEP (`BepChannel`);
4. **smistatore**: `CANALI_POSTE` (values svil, coll, `.helm`, `application*.yaml`, default nel codice), `CANALI_ESCLUSI_PALMARI`, elenchi in `MacchinaStatiService` e `TraceUtil`;
5. **adapter**: gestione degli esiti per canale (spesso già generica sui prefissi);
6. il servizio che produce il tracciato (`canale` nel messaggio);
7. **monitoraggio**: `MONITORING_FILTRO_CANALE_ALLOWED` di `ce-event-handler-monitoring`.

## Eventi di stato del file (`preadvising.evensource`)

Il topic si chiama **`preadvising.evensource`**, senza la "t" (solo uno state-machine-handler cita
`eventsource`). Formato del builder (`EventSourceMessage.newWithDefault`): `id` = `aggregateId` =
`idFile`, `aggregateType` `file`, `eventData` (idFile, nomeFile, idStato, stato, dataStato
`yyyy-MM-dd'T'HH:mm:ss.SSSXXX` ora di Roma, dati cliente, canale, numeroRecord, esito,
linkFileFisicoInviato), `metadata` (timestamp, correlationId, source, replay), `eventType` = idStato.
Nessuna chiave; header `eventTime`, `source`, `traceId`. Stati: `ST_F0002` preso in carico,
`ST_F0005` in elaborazione, `ST_F0006` elaborato con successo, `ST_F0008` scartato.

## Tracing

Contesto W3C `traceparent` negli header Kafka lungo tutta la catena: ogni servizio crea lo span
consumer come figlio del contesto ricevuto e lo inietta nei messaggi in uscita.
