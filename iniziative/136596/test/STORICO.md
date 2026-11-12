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

## Stato al 10-11 sera, dopo il triage

- DEF-136596-001: corretto nel validatore, `develop` `2c8ba33`, **da rilasciare in svil**. Orchestratore gia' pronto su `develop`; smistatore in correzione (Amelia).
- DEF-136596-002 (bloccante): `ce-anagrafica` svil 500 sui codici nazione; la regola 1039 del validatore richiede `mittente.codice_nazione`.
- BLOCCO-136596-001: dati cliente EURODIS mancanti nella configurazione del mapper (regole 1010, 1011, 1012).
- Prossimo run: dopo il rilascio del validatore, iniezione di `9900000000001` (TEST-LIST) su `preadvising.eud.pre.build` e verifica fino a `preadvising.completed`.

## RUN-136596-20261112T113500Z — ripresa dopo il ripristino del DB e i rilasci del 12-11

**Tipo**: osservazione + iniezione (`9900000000001` mittente IT, `9900000000002` mittente DE, dati
inventati, `idFile` di test `721909f5-…`) · **Esito**: KO, la catena si ferma a `ldv-pdb`.

Kafka svil non raggiungibile dalla postazione fino alle 12:15 (rete), poi ok.

| TC | Esito | Evidenza |
|---|---|---|
| TC-136596-001 | ✅ | `-in` ha ripreso: scarichi ogni 2 minuti; alle 12:22 uno scarico di EURODIS TEST con 2 spedizioni nuove (`5319999944765`, `…773`) |
| TC-136596-002 | ✅ | `ST_F0002`/`ST_F0005` per lo scarico delle 12:22 |
| TC-136596-010 | ✅ | mapper in svil con `5e58c23`/`723eb11`: cliente di default valorizzato (codice login, AUC, contratto, centro di costo), destinatario IT con ITA/ITA1 |
| TC-136596-011 | ❌ | mittente estero (NL, DE) senza `codice_nazione`: `ce-anagrafica` svil risponde ancora 500 anche col DB ripristinato → [DEF-136596-002](triage/DEF-136596-002.yaml); il mapper non aveva ripiego per i paesi esteri → [DEF-136596-003](triage/DEF-136596-003.yaml), corretto su `develop` `a7544a1` |
| TC-136596-020 | ✅ | validatore `d1d05bd`: i tracciati `EUD_INVIOSYSTEM` entrano nel flusso PDB (prima finivano nel flusso SDA) |
| TC-136596-021 | ⚠️ | `9900000000001` (mittente IT) passa le regole ed è su `preadvising.enrichment`; `9900000000002` (mittente DE) e le 2 spedizioni EURODIS TEST (mittente NL) bloccate da 1039 "Mittente Codice Nazione" |
| TC-136596-022 | ❌ | orchestratore: per `9900000000001` invio a `Preadvising.enrichment.normalizzatore` (ritorno ricevuto alle 12:39, indirizzo inventato `SCARTATO` dalla normalizzazione) e a `preadvising.enrichment.pdb`; nessun ritorno da `ldv-pdb`. In svil `ldv-pdb` (`develop`) fa `BepChannel.valueOf("EUD_INVIOSYSTEM")` → eccezione. Correzione su branch `feature/eurodis-canale-eud-inviosystem` `07c13d0` (fast-forward su `develop`), non rilasciata |
| TC-136596-023 | ⛔ | nessun tracciato EURODIS su `preadvising.completed` |
| TC-136596-025 | ⛔ | confronto della copertura dei campi: in svil `preadvising.completed` ha solo `PDB` e `TUP`, nessun `EUD_INVIOFILE`; si rifà appena un tracciato EURODIS arriva su `completed` |

Nota per i prossimi casi: usare un indirizzo reale di un luogo pubblico, perché la normalizzazione scarta le vie inventate.

## RUN-136596-20261112T122000Z — dopo il rilascio di ldv-pdb (develop c8b94db)

**Tipo**: iniezione su `preadvising.eud.pre.build` (`9900000000003` mittente IT, `…004` mittente DE,
indirizzi reali di luoghi pubblici, resto inventato, `idFile` `acadddc6-…`) e reiniezioni mirate su
`preadvising.pre-enrichment` del tracciato del mapper (`…005`, `…006`, `…007`) per isolare le cause.
**Esito**: KO, BEP rifiuta; nessun tracciato EURODIS su `completed`.

| Caso | Esito | Evidenza |
|---|---|---|
| `…004` (DE) | ❌ 1039 | il mapper `a7544a1` non risulta ancora in svil (codice nazione del mittente vuoto) |
| `…003` (IT), dal mapper | ❌ BEP:100 `product` | normalizzazione ok; `ldv-pdb` → BEP: prodotto mancante. `ldv-pdb` usa solo `rif_prodotto_cliente`, che il mapper lasciava vuoto → [DEF-136596-004](triage/DEF-136596-004.yaml) |
| `…005` = `…003` + `rif_prodotto_cliente` APT000901 | ❌ BEP:101 `country` | `codice_nazione` del mapper è ISO3 (`ITA`); nei tracciati PDB che arrivano a BEP è ISO4 Poste (`ITA1`, `USA1`, `SPA1`) → [DEF-136596-005](triage/DEF-136596-005.yaml) |
| `…006` = `…005` + `codice_nazione` ISO4 | ❌ BEP:112 `Errore di sistema` (2 volte) | il paese passa; LDV del collo inventata (`9900000000006001`) |
| `…007` = `…006` senza LDV del collo | ❌ BEP:100 `Collo id_ldv: code` | per Invio System la LDV è obbligatoria → serve una LDV PDB Express valida per BEP svil → [BLOCCO-136596-002](triage/BLOCCO-136596-002.yaml) |

Mapper corretto su `develop` `05720e6` (DEF-004, DEF-005; supera il ripiego ISO3 di `a7544a1`).
Smistatore e TC-025: non verificabili finché un tracciato EURODIS non arriva su `completed`.
