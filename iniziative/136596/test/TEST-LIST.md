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
| TC-136596-024 | A | Spedizione scartata dal validatore | evento di record con errore (`ST_R0006`), nessun messaggio su `completed` |

## Dati usati

| edReference | Variante | Note |
|---|---|---|
| `9900000000001` | completa (TC-010, 011, 020..023) | destinatario inventato `Destinatario Prova`, `Via di Prova 1`, `40121 BOLOGNA` IT; mittente `Mittente Prova` DE; `deliveryPartnerBarcode` `9900000000001001` |
| `99000000000nn` | varianti TC-012..018 | stesse basi, una variazione per caso |
