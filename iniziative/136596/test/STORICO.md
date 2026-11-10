# 136596 — STORICO run `e2e-eurodis-svil`

## RUN-136596-20261110T170000Z — osservazione della catena in svil

**Tipo**: osservazione (sola lettura dei topic, nessuna iniezione) · **Esito**: KO, la catena si
ferma al validatore.

| TC | Esito | Evidenza |
|---|---|---|
| TC-136596-001 | ✅ | `preadvising.eud.pre.build`: un messaggio ogni 2 minuti, chiave `edReference`, header `idFile`, `idEsecuzione`, `fonte` `receive-pan/shipments/v1`, `schemaVersion` `1`. Il job di elaborazione gira, quindi `-in` legge e scrive su PostgreSQL. EURODIS TEST rimanda sempre la stessa spedizione (`7319003746401`): è il comportamento atteso dell'ambiente TEST (Diego, 10-11), non una difformità di `-in` |
| TC-136596-002 | ✅ | `preadvising.evensource`: `ST_F0002` e `ST_F0005` per ogni scarico, `source` `ce-dichiarato-eurodis-in`, `nomeFile` `eurodis.<ts>.json`, canale `EUD_INVIOSYSTEM`, `idFile` uguale a quello delle spedizioni (scarico delle 17:16: `78533218-…`) |
| TC-136596-003 | ⛔ bloccato | PostgreSQL svil non raggiungibile dalla postazione |
| TC-136596-012 | ✅ | la spedizione TEST `7319003746401` (destinatario `null`) non compare su `preadvising.pre-enrichment`: scartata dal mapper (RF-14) |
| TC-136596-010 | ⚠️ parziale | scarico delle 17:16 (9 spedizioni TEST con destinatario): su `pre-enrichment` canale, `flag_autoproduttore`, `id_file`, `upload_time`, `link_file_fisico_inviato`, data, peso in grammi, `id_ldv_partner_master`, `id_ldv_itz` corretti. `collo.id_ldv` vuoto: `deliveryPartnerBarcode` assente nei dati TEST (atteso, domanda aperta a EURODIS). Cliente vuoto: valori di configurazione non ancora forniti |
| TC-136596-011 | ❌ | `codice_nazione` e `codice_nazione_poste` vuoti (IT, NL). `ce-anagrafica` svil risponde **500** su `/anagrafica/indirizzi/nazione/{IT,ITA,ITA1}` (la route `matrice/filiale` risponde 200). Il mapper si comporta come da RF-15 (pubblica senza ISO3/ISO4) → [DEF-136596-002](triage/DEF-136596-002.yaml) |
| TC-136596-020 | ❌ | il validatore manda i 9 tracciati `EUD_INVIOSYSTEM` nel flusso **SDA** (handler di default): `ST_R0002` e poi `ST_R0006` `PREADVISING_PARZIALE_E_BLOCCATO`, errore `143 Cliente non configurato o non attivo` → [DEF-136596-001](triage/DEF-136596-001.yaml) |
| TC-136596-021..023 | ⛔ bloccati | nessun tracciato EURODIS su `preadvising.enrichment` né su `preadvising.completed` (ultimi messaggi del 04-11, canale `TUP`) |

Note:
- `preadvising.eventsource` non esiste in svil: il topic è `preadvising.evensource` (confermato il default di `-in`).
- Code di scarto `preadvising.pre-enrichment-dlq` e `preadvising.completed-dlq` vuote.
