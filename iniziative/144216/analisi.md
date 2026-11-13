# 144216 — Analisi: sezione preavviso in OneTracking

Stato: bozza 0.1 (2026-11-13). Fonti: `cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`
(mock up, DREQ0062862, DREQ0062864, DREQ0062865, DREQ0062866), `cliente/ICD_PACCHI_ANAGRAFICA_138975_v1.0.xlsx`,
`cliente/ICD_PACCHI_FILE_v1.xlsx`, indicazioni di Diego del 13-11. Contesto del sistema:
`contesto/onetracking.md`.

## Obiettivo

Nel dettaglio di una LdV di OneTracking (ricerca per LdV) si aggiunge la sottosezione
**"Informazioni preavviso"**, tra "Informazioni LV" e "Cliente/Mittente/Destinatario", per gli
operatori dell'assistenza clienti. Dalla LdV si recupera il preavviso nel **T&T-Repo** (Solr,
collection `pacchi_anagrafica`); se il preavviso viene da file si legge il file in `pacchi_file`.

## Componenti toccati

| Repo | Branch | Cosa |
|---|---|---|
| `ONETRACKING/PRESENTATION/shipment-info` (BE) | `144216_preavviso_onetracking` da `origin/develop` | nuova API `GET /api/preavviso/{ldv}`; riusa `RestClientSolr` (`solrappgw.endpoint`, credenziali `solr.username`/`solr.password`), che già interroga `pacchi_anagrafica` per id (`pacchiAnagrafica(ldv)`, usato da `MittDestServiceImpl`) |
| `ONETRACKING/PRESENTATION/portal-pages` (FE, Nuxt 3) | `144216_preavviso_onetracking` da `origin/develop` | nuova sottosezione nel dettaglio LV |

Nessuna modifica ai servizi della catena preadvising: i dati sono già nel T&T-Repo
(iniziativa 138975 per `pacchi_anagrafica`).

## Le tre sezioni (mock up)

1. **Informazioni preavviso** — sempre presente quando si apre il dettaglio LV.
   Lettera di vettura, Numero ordine, Id collo, Numero colli, Preavviso (In tempo / In ritardo /
   Senza preavviso). **Canale** solo se il preavviso non viene da file (caso 3, es. `WEBSERVICES`).
2. **Dati file preavviso** — solo se il preavviso ha `id_file`. Nome file, Data caricamento,
   Stato file, Data stato, Canale.
3. **Dettaglio errori** — solo se il preavviso ha errori. Intestazione "N errori riscontrati",
   tabella Campo in errore, Codice errore, Descrizione errore.

Casi del mock up: 1 file con scarto ed errori, 2 file elaborato con successo, 3 preavviso non da file.

## Recupero dei dati (BE)

1. **Documento LdV**: `pacchi_anagrafica` con `id:"<ldv>"` → `stato_LdV` (`LDV ON TIME`,
   `LDV IN RITARDO`, `LDV SENZA PREAVVISO`), `id_preadvising`.
2. **Preavvisi della LdV**: `pacchi_anagrafica` con `ldv:"<ldv>"` (il campo `ldv` c'è solo sui
   documenti di preavviso), ordinati per `event_ts` decrescente.
3. **Scelta del preavviso** (regola di Diego, 13-11):
   - nessun documento → nessun preavviso;
   - un documento → quello;
   - più documenti → **quello nello stato "uno"**; se non ce n'è, **il penultimo in ordine di tempo**
     (`event_ts`).
   - Interpretazione adottata (AS-01, da confermare): lo stato "uno" è un valore di `event_type`
     configurabile (`onetracking.preavviso.stato-preferito`, default `COMPLETED`); se più documenti
     sono in quello stato si prende il più recente.
4. **File**: se il preavviso scelto ha `id_file`, `pacchi_file` con `idfile:"<id_file>"`.
5. **Errori**: dal campo `preadv_errori` del preavviso scelto (formato da confermare, AS-04).

## Mapping dei campi

| Etichetta | Fonte |
|---|---|
| Lettera di vettura | `pacchi_anagrafica.ldv` del preavviso (se assente: la LdV cercata) |
| Numero ordine | `code_externalId` (`event_data.spedizione.rif_spedizione`) — AS-02 |
| Id collo | `code_parcelLabel` (`collo.id_collo`) |
| Numero colli | `code_packageNumber` |
| Canale (solo senza file) | campo canale del preavviso: nell'ICD non c'è — AS-03 |
| Preavviso | `stato_LdV` del documento LdV: `LDV ON TIME` → "In tempo", `LDV IN RITARDO` → "In ritardo", `LDV SENZA PREAVVISO` o assente → "Senza preavviso" |
| Nome file | `pacchi_file.nomefile` |
| Data caricamento | `pacchi_file.upload_time_stamp` |
| Stato file | `pacchi_file.idStato` (o `status`) decodificato: `ST_F0001` File inviato dal cliente, `ST_F0002` File preso in carico, `ST_F0005` File in elaborazione, `ST_F0006` File elaborato con successo, `ST_F0007` File elaborato con scarto, `ST_F0008` File completamente scartato |
| Data stato | `pacchi_file._lastupdate_` — AS-05 |
| Canale (file) | `pacchi_file.channel` (Invio Easy, Invio File, Invio System, Stampa Massiva, Web) |
| Errori | `preadv_errori` → campo, codice, descrizione — AS-04 |

Date mostrate come `dd/MM/yyyy HH:mm`, ora di Roma.

## Contratto dell'API

`GET /api/preavviso/{ldv}` (shipment-info; il FE la chiama come le altre `/api/...`).

```json
{
  "presente": true,
  "preavviso": {
    "ldv": "…", "idPreadvising": "…", "numeroOrdine": "…", "idCollo": "…",
    "numeroColli": 1, "canale": null, "statoPreavviso": "IN_RITARDO",
    "statoPreavvisoDescrizione": "In ritardo", "eventType": "COMPLETED",
    "dataEvento": "2024-07-15T08:47:00+02:00", "idFile": "…"
  },
  "file": {
    "idFile": "…", "nomeFile": "…", "dataCaricamento": "…", "idStato": "ST_F0007",
    "statoFile": "File elaborato con scarto", "dataStato": "…", "canale": "Invio File"
  },
  "errori": [ { "campo": "CAP destinatario", "codice": "ERR-4021", "descrizione": "…" } ]
}
```

- Nessun preavviso: `200`, `presente: false`, `preavviso` con `ldv` e
  `statoPreavviso: SENZA_PREAVVISO`, `file: null`, `errori: []`.
- `file` è `null` se il preavviso non ha `id_file` (o il file non si trova in `pacchi_file`);
  `errori` è `[]` se non ci sono errori. Il FE mostra le sezioni 2 e 3 solo se valorizzate.
- T&T-Repo non raggiungibile: `503` con messaggio; il FE mostra "Dati preavviso non disponibili"
  nella sezione e non blocca il resto del dettaglio.
- Nessun permesso nuovo: la sezione è visibile a chi vede il dettaglio LV (AS-06).

## Assunzioni e domande aperte

| ID | Assunzione adottata | Da confermare con |
|---|---|---|
| AS-01 | Lo stato "uno" della regola di scelta è un `event_type` configurabile, default `COMPLETED`; fra più documenti in quello stato vince il più recente | Diego |
| AS-02 | Numero ordine = `code_externalId` (riferimento spedizione del cliente) | Poste / Diego |
| AS-03 | Canale del preavviso non da file: nessun campo nell'ICD; il BE legge un campo configurabile (`onetracking.preavviso.campo-canale`, default `channel`), se manca mostra "-" | Poste |
| AS-04 | Formato di `preadv_errori` non descritto nell'ICD: il BE accetta un array JSON (`campo`/`codice`/`descrizione` e varianti), altrimenti righe `campo|codice|descrizione` separate da `;`, altrimenti un solo errore con il testo grezzo in descrizione | Poste (team T&T-Repo) |
| AS-05 | Data stato del file = `_lastupdate_` di `pacchi_file` (non c'è un campo dedicato) | Poste |
| AS-06 | Nessuna funzionalità di profilazione nuova (`OTR_*`) per la sezione | Poste |
| AS-07 | Si parte da `origin/develop` di entrambi i repo (FE già su Nuxt 3 / Vue 3) | — |
