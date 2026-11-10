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
| `ce-db-sync` | Sincronizzazioni su PostgreSQL `ce_cen`. Modello per l'accesso a PostgreSQL (JDBC, secret `ce-postgres`) |
| `ce-dichiarato-eurodis-in`, `-mapper`, `ce-eurodis-send-tracking` | Flusso EURODIS autoproduttore: vedi `iniziative/136596/sviluppo/` |

## Aggiungere un canale nuovo

Va toccato in tutti questi punti, altrimenti il messaggio si ferma a metà catena:

1. **validatore**: enum dei canali (`PdbChannel` o equivalente), handler, regole Drools che citano i canali;
2. **orchestratore**: passi del canale in `application.yaml`, `CANALI_PDB`;
3. **ldv-pdb / ldv-pdb-sync**: conversione nel canale BEP (`BepChannel`);
4. **smistatore**: `CANALI_POSTE` (values svil, coll, `.helm`, `application*.yaml`, default nel codice), `CANALI_ESCLUSI_PALMARI`, elenchi in `MacchinaStatiService` e `TraceUtil`;
5. **adapter**: gestione degli esiti per canale (spesso già generica sui prefissi);
6. il servizio che produce il tracciato (`canale` nel messaggio).

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
