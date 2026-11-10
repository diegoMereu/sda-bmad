# 136596 — Esiti BEP del canale `EUD_INVIOSYSTEM` (adapter e orchestratore)

**Data**: 2026-11-10 · **Autore**: Amelia (dev), analisi con Winston · **Stato**: implementato su `develop`

## Richiesta

Diego, 10-11: l'adapter deve gestire gli esiti del canale `EUD_INVIOSYSTEM` come i PDB di
fase 2 (se il preadvising è a DB, l'esito va verso l'enrichment), "o meglio ancora come fa per
il canale che oggi l'orchestratore manda verso il dichiarato BEP sync". Indicazione successiva:
`EUD_INVIOSYSTEM` si comporta allo stesso modo di `EUD_INVIOFILE`, stesso percorso degli esiti.

## Come funziona oggi (codice su `develop`, verificato il 10-11)

**Orchestratore** (`application.yaml`, `routing.azioni.mappings`):

| Step | Topic | Servizio |
|---|---|---|
| `normalizzazione` | `Preadvising.enrichment.normalizzatore` | normalizzatore |
| `ldv-pdb` | `preadvising.enrichment.pdb` | `ce-dichiarato-ldv-pdb` (asincrono) |
| `ldv-bep-sync` | `preadvising.enrichment.bepsync` | `ce-dichiarato-ldv-pdb-sync` ("dichiarato BEP sync") |
| `enrichment_bep` | nessun topic: è l'attesa dell'esito BEP | rientra dall'adapter |

Percorsi prima della modifica:
- `EUD_INVIOFILE`: normalizzazione → enrichment_bep → **ldv-bep-sync**;
- `EUD_INVIOSYSTEM` (aggiunto da azzurrazezza il 10-11, `23bf1dd`): normalizzazione →
  enrichment_bep → **ldv-pdb**;
- `PDB_*`: normalizzazione → ldv-pdb → enrichment_bep.

**Adapter** (`KafkaConsumerPDB`, `PDBFase2Service`, `PdbMapper.toOutputPDBFase2`). Legge gli
esiti PDB/BEP da `kafka.consumer.topic.pdb`. Per un esito di fase 2:

1. **Callback con `code_externalId`** e `booking_channel` tra `INVIOFILE`, `INVIOSYSTEM`,
   `INVIOEASY`:
   - cerca il preadvising su Mongo per `rif_spedizione` e suffisso del canale (regex
     `INVIOSYSTEM$`, quindi trova sia `PDB_INVIOSYSTEM` sia `EUD_INVIOSYSTEM`);
   - se lo trova, chiama la fase 2 con il canale letto da Mongo.
2. **Callback BEP POU**, cioè il percorso del dichiarato BEP sync:
   - arriva con `booking_channel=WEB` e senza `code_externalId`;
   - l'adapter cerca il preadvising per `walletRequestId`, che coincide con il `rif_spedizione`
     inviato da `ldv-pdb-sync` a BEP;
   - se il canale a DB inizia con `EUD_`, rimappa `booking_channel` sul suffisso del canale.
     La regola è generica (`mario.reda`, 03-11), quindi vale già per `EUD_INVIOSYSTEM` → `INVIOSYSTEM`;
   - poi chiama la fase 2.
3. **Fase 2**: costruisce l'enrichment con `canale` = canale di Mongo, `id_canale` = booking
   channel, `tipo_lavorazione` = `enrichment_bep`, `result` = `OK`, e lo pubblica su
   `kafka.producer.topic.preadvising-enrichment`.
4. **Nessun preadvising a DB**: flusso normale (`AdapterPDBService`).

Nell'adapter non c'era più nessuna regola specifica per `EUD_INVIOFILE`: l'esclusione di
`spedizione_a_valore` è stata ritirata con `5b08e74`.

## Scelta

**`EUD_INVIOSYSTEM` segue lo stesso percorso di `EUD_INVIOFILE`**, come chiesto da Diego e come
preferito nella richiesta ("come il canale che l'orchestratore manda verso il dichiarato BEP sync").

- **Orchestratore**: `EUD_INVIOSYSTEM` passa da `ldv-pdb` a `ldv-bep-sync`. La spedizione va a
  `ce-dichiarato-ldv-pdb-sync`, che è anche quanto chiesto da Diego per l'evento verso ldv-pdb-sync.
- **Adapter**: nessuna modifica di logica. Il rimappaggio `EUD_*` del callback POU e la ricerca
  per suffisso coprono già `EUD_INVIOSYSTEM`. Ho aggiunto i test che lo provano e chiarito il commento.

Nessuna incompatibilità tecnica emersa nell'adapter. Da verificare a valle, fuori da questo lavoro:
- che `ce-dichiarato-ldv-pdb-sync` accetti il tracciato del mapper con canale `EUD_INVIOSYSTEM`.
  È l'analisi in corso in `integrazione-ldv-pdb-sync.md`;
- che il callback BEP POU per questo canale porti `walletRequestId` = `rif_spedizione`
  (`edReference`), come per `EUD_INVIOFILE`.

## Modifiche

| Repo | Commit su `develop` | Contenuto |
|---|---|---|
| `ce-dichiarato-orchestratore` | `2d65031` | `EUD_INVIOSYSTEM`: normalizzazione → enrichment_bep → ldv-bep-sync, in `application.yaml` e `application-test.yaml`; test `AzioneRoutingEudTest` sul binding del routing |
| `ce-dichiarato-adapter` | `95c8f2b` | test per `EUD_INVIOSYSTEM`: callback con `code_externalId` (canale da Mongo); callback POU per `walletRequestId`, con rimappaggio a `INVIOSYSTEM`, con il controllo di parità su `EUD_INVIOFILE` e il caso non trovato a DB; mapper di fase 2 (`canale`, `id_canale`, `enrichment_bep`). Commento aggiornato in `KafkaConsumerPDB` |

## Test

- Orchestratore: 58 test, tutti verdi.
- Adapter: 56 test, 55 verdi. Fallisce
  `PDBFase2ServiceTest.erroreMapper_contatoreKoIncrementatoEccezioneRilanciata`, che fallisce
  anche su `origin/develop` senza le mie modifiche: è un problema già esistente, da segnalare a
  chi mantiene l'adapter. I test nuovi (`KafkaConsumerPDBTest`: 21; `PdbMapperFase2Test`: 13)
  sono tutti verdi.

## Da sapere

- Il `develop` locale dell'adapter in `gitposte` ha due commit di Diego del 30-10 mai pushati
  (`c4a26d1`, `1a6202d`) e un Excel modificato. Non li ho toccati: ho lavorato in un worktree
  separato su `origin/develop`.
- Rilascio: **orchestratore** (cambia il percorso) e **adapter** (solo test e commento: il
  rilascio non cambia il comportamento).
