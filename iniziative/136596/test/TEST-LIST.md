# 136596 — TEST-LIST `e2e-eurodis-svil`

Priorità: **C** = critico (blocca l'obiettivo `preadvising.completed`), **A** = alto, **M** = medio.
Esito: vedi [STORICO.md](STORICO.md). Dati: inventati; `edReference` di test `99000000000nn`.

## Fondazione (assessment di `-in`, AS-22)

| ID | P | Caso | Verifica | Rif. |
|---|---|---|---|---|
| TC-136596-001 | C | `-in` deployato e avviato con PostgreSQL e Kafka veri | messaggi su `preadvising.eud.pre.build` ogni 2 minuti con header `idFile`, `idEsecuzione`, `fonte`, `schemaVersion`; il job di elaborazione gira (legge gli scarichi da PostgreSQL) | AS-22, RF-01..RF-10 |
| TC-136596-002 | C | Eventi del file fittizio | per ogni scarico con spedizioni: `ST_F0002` poi `ST_F0005` su `preadvising.evensource`, stesso `idFile` dell'header delle spedizioni, `nomeFile` `eurodis.<ts>.json`, canale configurato, `source` `ce-dichiarato-eurodis-in` | RF-19..RF-21, AC-17 |
| TC-136596-003 | A | Righe su PostgreSQL | `eurodis_scarichi` con stato finale, `id_file`; `eurodis_spedizioni` `INVIATA` con `inviata_il` | RF-06..RF-10 (bloccato: DB non raggiungibile) |
| TC-136596-004 | M | 2 repliche: un solo scarico per ciclo | un solo `idEsecuzione` per ciclo di 2 minuti | AC-13 (richiede scaling in svil) |

## Mapper (`preadvising.pre-enrichment`)

| ID | P | Caso (variante di `esempio-eurodis-spedizione.json`) | Verifica |
|---|---|---|---|
| TC-136596-010 | C | Spedizione completa: destinatario IT, `deliveryPartnerBarcode`, europlate, contrassegno | `canale` configurato, `flag_autoproduttore` `S`, `id_file` = header `idFile`, `upload_time` = `ricevutoIl`, `link_file_fisico_inviato` = `rifGrezzo`, `collo.id_ldv` = `deliveryPartnerBarcode`, `id_ldv_itz` = europlate, peso in grammi, `codici_servizi` `APT000918`, contrassegno `S`/`CON`, chiave = `rif_spedizione` |
| TC-136596-011 | C | Codici nazione | destinatario IT → `codice_nazione` ISO3, `codice_nazione_poste` ISO4, `codice_nazione_iso_2` IT; mittente estero idem (da `ce-anagrafica`) |
| TC-136596-012 | A | Destinatario assente (come i dati TEST EURODIS) | nessuna pubblicazione (RF-14) |
| TC-136596-013 | A | `deliveryPartnerBarcode` assente | pubblicato, `collo.id_ldv` `""` |
| TC-136596-014 | M | europlate `0` / vuoto | `id_ldv_itz` `""` |
| TC-136596-015 | M | `collis: null` | pubblicato, `collo: []` |
| TC-136596-016 | M | `edReference` `…01.0` / `…01.5` | `"…01"` / non pubblicato |
| TC-136596-017 | M | Multicollo (3 colli) | 3 `collo`, `numero_colli_parz` 1..3 |
| TC-136596-018 | M | Servizio di consegna `6` + contrassegno | `codici_servizi` `APT000910\|APT000918` |

## Catena a valle fino a `preadvising.completed`

| ID | P | Caso | Verifica |
|---|---|---|---|
| TC-136596-020 | C | Validatore: instradamento | il tracciato EURODIS entra nel flusso PDB (`PdbPreadvisingHandler`), non in quello SDA; evento `ST_R0002` |
| TC-136596-021 | C | Validatore: regole | nessun errore bloccante sul tracciato di TC-136596-010; tracciato su `preadvising.enrichment` |
| TC-136596-022 | C | Orchestratore | azioni del canale eseguite, tracciato su **`preadvising.completed`** |
| TC-136596-023 | C | Arricchimento su `completed` | su `preadvising.completed` restano i campi del mapper (`id_file`, LDV del collo, `id_ldv_itz`, canale, destinatario, contrassegno) e ci sono quelli aggiunti a valle (normalizzazione, enrichment BEP) |
| TC-136596-025 | A | Copertura dei campi su `completed` (e ai salti intermedi) rispetto ai canali `PDB`/`PDB_INVIOSYSTEM` ed `EUD_INVIOFILE` | per canale, insieme dei campi valorizzati (non vuoti, non 0); tabella campo × canale con i campi pieni negli altri canali e vuoti in `EUD_INVIOSYSTEM` e la causa (dato assente in EURODIS, regola di mapping mancante, arricchimento a valle che non scatta per il canale). Nel repo solo nomi di campo e percentuali |
| TC-136596-024 | A | Spedizione scartata dal validatore | evento di record con errore (`ST_R0006`), nessun messaggio su `completed` |

## Send-tracking (`ce-eurodis-send-tracking`, da `PACCHI.TRACKING`)

Si parte quando il servizio è rilasciato in svil (develop `ec2f65b`). `PACCHI.TRACKING` in svil è
**condiviso** con altri consumer: pochi eventi, chiaramente di test (LDV `99…`, `idFrazionarioEvento`
`99999`), elencati nello STORICO; mai su collaudo o produzione. Nessun topic di uscita: si verifica da
log JSON (MDC `ldv` mascherata, `status_sda`, `codice_eurodis`, `esito`) e metriche `eurodis_tracking_*`
(`lette`, `tracce_total{esito}`, `scartati_total{filtro}`, `retry`, `cache_ldv`, `mongo`), più l'esito
della chiamata a EURODIS TEST.

LDV del giro precedente (canale `EUD_INVIOSYSTEM`, arrivate al validatore e quindi in `dichiarato_events`;
Mongo non è raggiungibile da qui, la presenza si deduce dai topic): `9900000000001001`, `9900000000003001`,
`9900000000005001`, `9900000000006001`.

Evento da produrre (struttura reale di `PACCHI.TRACKING`, sezione 3.2 della specifica; nessuna chiave Kafka):
`{"header":{"applicativo":"CE","timestamp":"<ora> "},"payload":{"canale":"PDT","status":"<status>","ldv":"<LDV>","dataTrack":"<yyyy-MM-dd HH:mm:ss>","idFrazionarioEvento":"99999","numTentativiDiConsegna":"1"}}`

| ID | P | Caso (esempio della specifica) | Evento | Verifica |
|---|---|---|---|---|
| TC-136596-030 | C | `GGG` → `1767` (E2) | status `GGG`, LDV `9900000000003001` | `tracce_total{esito=inviata}` +1, log `codice_eurodis=1767`, EURODIS TEST risponde 201 senza errori sull'elemento |
| TC-136596-031 | A | `GIA` → `1785` (E3) | status `GIA`, LDV `9900000000003001` | come 030 con `1785` |
| TC-136596-032 | A | `ARR` → `1766` (E4) | status `ARR`, canale `HUB`, LDV `9900000000001001` | come 030 con `1766` |
| TC-136596-033 | A | `000` → `1100` senza nome di chi ritira (E1) | status `000`, LDV `9900000000005001` | scartata, `scartati_total{filtro=acceptor_name}` +1, nessuna chiamata (con `EURODIS_TRACKING_ACCEPTOR_NAME_DEFAULT` vuoto) |
| TC-136596-034 | M | `000` → `1100` con nome di default | come 033 con `EURODIS_TRACKING_ACCEPTOR_NAME_DEFAULT` impostato in svil | inviata `1100`, il valore non compare nei log |
| TC-136596-035 | A | status non abilitato (E5) | status `THE`, LDV `9900000000006001` | scartata al filtro status, Mongo non interrogato |
| TC-136596-036 | A | LDV non EURODIS (E7) | status `GGG`, LDV nuova `9900000000099001` (mai vista, fuori dalla cache) | scartata al filtro LDV, `mongo` +1; secondo evento sulla stessa LDV entro 10 min: nessuna nuova query (cache) |
| TC-136596-037 | M | doppione (E8) | stesso evento di 030 prodotto due volte | comportamento atteso da 14.4 (niente storico: verificare se parte un secondo invio e che EURODIS non dia errore) |
| TC-136596-038 | M | override da ConfigMap (E9) | `EURODIS_TRACKING_STATI_OVERRIDE=THE=1767` in svil, poi evento di 035 | inviato `1767` |
| TC-136596-039 | M | applicativo diverso (E6) | `applicativo` `TT`, status `000` | con filtro applicativo spento (default) passa ai filtri successivi; con `EURODIS_TRACKING_APPLICATIVI=CE` scartato al filtro 1 |

## Dati usati

| edReference | Variante | Note |
|---|---|---|
| `9900000000001` | completa (TC-010, 011, 020..023) | destinatario inventato `Destinatario Prova`, `Via di Prova 1`, `40121 BOLOGNA` IT; mittente `Mittente Prova` DE; `deliveryPartnerBarcode` `9900000000001001` |
| `99000000000nn` | varianti TC-012..018 | stesse basi, una variazione per caso |
