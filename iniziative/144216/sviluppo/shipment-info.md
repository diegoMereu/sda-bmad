# `shipment-info` — Documento funzionale per lo sviluppo (API preavviso)

**Iniziativa**: 144216 — Assistenza Clienti, Customer Journey preavviso (PRJ0049429) · **Versione**: 0.1 · **Data**: 2026-11-13
**Autrice**: Mary (analyst) · **Destinataria**: sviluppatrice back-end di OneTracking
**Repository**: `gitlab.alm.poste.it/ONETRACKING/PRESENTATION/shipment-info` (locale `gitposte/SDA/ONETRACKING/PRESENTATION/shipment-info`), branch `144216_preavviso_onetracking` da `origin/develop`
**Stack**: Spring Boot 2.7.18, Java 11, RestTemplate verso Solr T&T-Repo (AppGW)
**Generato da**: [prompt-shipment-info.md](prompt-shipment-info.md)
**Fonti**: [analisi.md](../analisi.md) (regole, mapping, contratto: **vincolanti**); mock up
`cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`; `cliente/ICD_PACCHI_ANAGRAFICA_138975_v1.0.xlsx`;
`cliente/ICD_PACCHI_FILE_v1.xlsx`; [contesto/onetracking.md](../../../contesto/onetracking.md); codice di `origin/develop` letto il 13-11
**Documento gemello (front-end)**: [portal-pages.md](portal-pages.md)

Etichette usate nel documento:
- **[FATTO]**: scritto in un ICD, nel mock up o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default; da confermare (sezione 11).

> **Il contratto della sezione 6 e le regole della sezione 5 vengono da `analisi.md` e non si cambiano**:
> front-end e back-end li stanno sviluppando in parallelo. Questo documento li dettaglia. Dove ha
> trovato buchi o incoerenze li mette fra le assunzioni (AS-08 e seguenti), senza toccare il contratto.

---

## 1. Contesto e obiettivo

OneTracking è il portale degli operatori SDA/Poste che mostra in un'unica vista lo stato di una
spedizione. `shipment-info` è il BFF: espone `/api/**` al front-end `portal-pages` e legge da molti
sistemi, fra cui il **T&T-Repo** (Solr).

Con l'iniziativa 144216 l'operatore dell'assistenza clienti, nel dettaglio di una LdV, vede la nuova
sottosezione **"Informazioni preavviso"**: il preavviso della LdV, il file da cui viene (se viene da
file) e gli errori riscontrati. I dati ci sono già nel T&T-Repo, nelle collection `pacchi_anagrafica`
(estesa dall'iniziativa 138975) e `pacchi_file`.

A `shipment-info` si chiede **una sola API nuova**, `GET /api/preavviso/{ldv}`, che:

1. legge il documento della LdV e i documenti di preavviso in `pacchi_anagrafica`;
2. sceglie il preavviso da mostrare (regola della sezione 5.1);
3. se il preavviso viene da file, legge il file in `pacchi_file`;
4. decodifica errori, stati e date e restituisce il JSON della sezione 6.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Layout, etichette, visibilità delle sezioni a video | `portal-pages` ([portal-pages.md](portal-pages.md)) |
| Scrittura dei dati di preavviso nel T&T-Repo | catena preadvising e T&T-Repo (iniziativa 138975): nessuna modifica |
| Nuove funzionalità di profilazione `OTR_*` | nessuno (AS-06) |
| Modifiche alle API esistenti (`/mittente-destinatario`, `/tup/...`) | nessuno |

## 2. Requisiti coperti

Requisiti del mock up v0.8 (slide 1 e 2) [FATTO]:

| Requisito | Cosa chiede (dal mock up) | Dove nel documento |
|---|---|---|
| DREQ0062862 | Integrare in OneTracking i dati di preavviso della singola LdV, consultabili dagli operatori dell'assistenza nel dettaglio LV | sezioni 1, 6 |
| DREQ0062864 | Dati preavviso della LdV: numero ordine, identificativo collo, numero colli, stato preavviso | sezioni 5.2, 6 (`preavviso`) |
| DREQ0062865 | Dati del file di preavviso, solo se il preavviso viene da file | sezioni 4.3, 5.4, 6 (`file`) |
| DREQ0062866 | Dettaglio errori, solo in presenza di anomalie: campo in errore, codice, descrizione | sezioni 5.5, 6 (`errori`) |

Il mock up elenca i quattro requisiti insieme e non li attribuisce uno per uno ai blocchi della
pagina: l'attribuzione della tabella è nostra, sull'ordine della slide 2 (AS-23).

## 3. Dove si interviene nel codice

Indicazioni sul codice di `origin/develop` [FATTO, letto il 13-11]; i nomi delle classi nuove sono proposte.

| Punto | Cosa c'è oggi | Cosa si fa |
|---|---|---|
| `rest/RestClientSolr.java` | client Solr con query costruite a mano (`UriComponentsBuilder...build(true)`), credenziali `solr.username`/`solr.password`, base `solrappgw.endpoint`. `pacchiAnagrafica(ldv)` interroga `pacchi_anagrafica` con `q=id:<ldv>` e restituisce tutti i campi | due o tre metodi nuovi (sezione 4): documento LdV, preavvisi della LdV, file. **Non** inghiottono le eccezioni (gli altri metodi restituiscono `null` su errore): serve distinguere "non trovato" da "T&T-Repo non disponibile" (5.7) |
| `model/solr/SolrPacchiAnagraficaResponse.java` | `Doc` con un sottoinsieme dei campi (es. `id`, `code_international`, `send_waybill_by_email`) | aggiungere i campi della sezione 4.1 e 4.2, oppure un modello nuovo dedicato |
| `model/solr/` | nessun modello per `pacchi_file` | nuovo `SolrPacchiFileResponse` |
| `impl/MittDestServiceImpl.java` | `invokeSolr` usa `pacchiAnagrafica(ldv)` per `send_waybill_by_email` | **non si tocca**: è solo l'esempio d'uso del client |
| `controller/` | i controller espongono path senza `/api` (es. `MittDestController` → `/mittente-destinatario/{ldv}/{dbLdv}`); `TupController` mostra il modello con span `tracer.buildSpan(...)` e `@Timed` | nuovo `PreavvisoController` (o metodo in un controller esistente) con `@GetMapping("/preavviso/{ldv}")` (AS-08) |
| `service/`, `impl/` | interfaccia + implementazione per area | nuovi `PreavvisoService` / `PreavvisoServiceImpl`: regola di scelta, decodifiche, mapping |
| `controller/model/` | DTO di risposta, `ErrorResponse` (`eccezioneGestita`, `statusCode`, `errorCode`, `errorMessage`) | nuovo `PreavvisoResponse` (sezione 6) |
| `exception/GenericExceptionHandler.java` | gestisce `OneTrackingException` (500), `DataNotFoundException` (404), `GenericErrorException` (500) | nuova eccezione (es. `TtRepoNonDisponibileException`) mappata su **503** con `ErrorResponse` |
| `config/RestTemplateConfig.java` | bean `solrRestTemplate` (timeout `server.controller.solr-timeout`, 60000 ms), `genericRestTemplate` | usare `solrRestTemplate` (vedi 9) |
| `src/main/resources/application.properties`, `chart/config/files/application.properties` | proprietà Solr | proprietà nuove della sezione 8, in entrambi i file |

## 4. Sorgenti dati (T&T-Repo, Solr)

Tutte le query usano `solrappgw.endpoint` e le credenziali Solr esistenti. Si chiedono **solo i campi
che servono** (`fl`): in `pacchi_anagrafica` e `pacchi_file` ci sono indirizzi, nominativi, codici
fiscali e partite IVA che non devono transitare né finire nei log.

Il valore della LdV entra nella query fra virgolette (`%22<ldv>%22`), come in `SOLR_TUP_URL_NEW`.
Le query sono costruite con `build(true)` (niente encoding): per questo la LdV si valida prima (RF-01).

### 4.1 Documento della LdV (`pacchi_anagrafica`)

```
pacchi_anagrafica/select?q=id%3A%22<ldv>%22&fl=id,stato_LdV,id_preadvising&rows=1&wt=json
```

| Campo | Tipo (ICD) | Uso |
|---|---|---|
| `id` | string, UniqueKey | = LdV per i documenti LdV [FATTO, ICD 138975] |
| `stato_LdV` | string | `LDV SENZA PREAVVISO`, `LDV ON TIME`, `LDV IN RITARDO` (solo documenti LdV) → stato del preavviso (5.3) |
| `id_preadvising` | string | riferimento al "preavviso valido" (`id` di un documento di preavviso); assente se non c'è. Solo diagnostica (AS-11) |

Il documento può mancare (LdV non ancora nel T&T-Repo): non è un errore (5.3).

### 4.2 Preavvisi della LdV (`pacchi_anagrafica`)

```
pacchi_anagrafica/select?q=ldv%3A%22<ldv>%22
  &fl=id,ldv,id_file,event_type,event_ts,preadv_errori,code_externalId,code_parcelLabel,code_packageNumber,<campo-canale>,_lastupdate_
  &sort=event_ts+desc&rows=<max-preavvisi>&wt=json
```

Il campo `ldv` c'è **solo** sui documenti di preavviso [FATTO, ICD 138975]: la query non restituisce il
documento LdV.

| Campo | Tipo (ICD) | Origine (ICD, colonna "Mappatura con il topic") | Uso |
|---|---|---|---|
| `id` | string | `aggregate_id` = `event_data.id_preadvising` | `preavviso.idPreadvising` |
| `ldv` | string, indicizzato | `event_data.spedizione[].collo[].id_ldv` | `preavviso.ldv` |
| `id_file` | string, indicizzato | `event_data.id_file` | `preavviso.idFile`; chiave verso `pacchi_file` |
| `event_type` | string, indicizzato | `PRE_ENRICHMENT` (ST_R0002), `COMPLETED` (ST_R0004), `ERROR` (ST_R0003, ST_R0006) | regola di scelta (5.1); `preavviso.eventType` |
| `event_ts` | tdate | `metadata.timestamp` dell'ultimo evento applicato | regola di scelta; `preavviso.dataEvento` |
| `preadv_errori` | string | non descritta (AS-04, AS-22) | `errori` (5.5) |
| `code_externalId` | string | `event_data.spedizione.rif_spedizione` | `preavviso.numeroOrdine` (AS-02) |
| `code_parcelLabel` | string | `event_data.spedizione.collo.id_collo` | `preavviso.idCollo` |
| `code_packageNumber` | long | `event_data.spedizione.numero_colli` | `preavviso.numeroColli` |
| campo canale (default `channel`) | non nell'ICD | — | `preavviso.canale` (AS-03) |
| `_lastupdate_` | tdate (interno Solr) | — | solo spareggio a parità di `event_ts` (AS-15) |

L'ordinamento di Solr è una comodità: la regola di scelta si applica in Java sulla lista ricevuta
(un `event_ts` mancante conta come il più vecchio).

### 4.3 File del preavviso (`pacchi_file`)

Solo se il preavviso scelto ha `id_file`.

```
pacchi_file/select?q=idfile%3A%22<id_file>%22&fl=nomefile,upload_time_stamp,idStato,status,channel,_lastupdate_&rows=1&wt=json
```

| Campo | Tipo (ICD) | Note ICD | Uso |
|---|---|---|---|
| `idfile` | string, UniqueKey, indicizzato ma **non stored** | es. `07aeb815-…` | solo filtro: non torna nella risposta, `file.idFile` si valorizza con `id_file` del preavviso |
| `nomefile` | string | nome del file inviato dal cliente | `file.nomeFile` |
| `upload_time_stamp` | tdate | data caricamento; stesso valore per lo stesso filename | `file.dataCaricamento` |
| `idStato` | string | `ST_F0001`…`ST_F0008` | `file.idStato`, decodificato in `file.statoFile` (5.4) |
| `status` | string | stesso dominio di `idStato` | ripiego se `idStato` manca |
| `channel` | string, non indicizzato, stored | `Invio Easy`, `Invio File`, `Invio System`, `Stampa Massiva`, `Web` | `file.canale`, così com'è (AS-09) |
| `_lastupdate_` | tdate (interno Solr) | default NOW | `file.dataStato` (AS-05, AS-16) |

Non si leggono: `partitaIVA`, `ragioneSociale`, `nominativoCliente`, `codice_login_cliente`,
`linkFileFisico*`, né gli errori di file `esito`, `codiceErrore`, `descrizioneErrore` (AS-12).

## 5. Regole funzionali

### 5.1 Scelta del preavviso [DECISO 13-11, Diego; AS-01 chiusa]

Lo "stato" della regola è il campo **`event_type`** del record di preavviso in `pacchi_anagrafica`
(`PRE_ENRICHMENT` = ST_R0002, `COMPLETED` = ST_R0004, `ERROR` = ST_R0003/ST_R0006).

| N. documenti di preavviso (4.2) | Preavviso scelto |
|---|---|
| 0 | nessuno: risposta "nessun preavviso" (6.2) |
| 1 | quello, qualunque sia `event_type` |
| 2 o più, almeno uno `COMPLETED` | il `COMPLETED` più recente per `event_ts` |
| 2 o più, nessuno `COMPLETED` | il **penultimo** per `event_ts` (il secondo dal più recente) |

- Il valore `COMPLETED` sta nella proprietà `onetracking.preavviso.stato-preferito` (sezione 8);
  il confronto ignora maiuscole e spazi.
- Ordinamento: `event_ts` decrescente; a parità, `_lastupdate_` decrescente, poi `id` decrescente (AS-15).
  Un documento senza `event_ts` è il più vecchio.
- `id_preadvising` del documento LdV non entra nella scelta (AS-11).

### 5.2 Dati del preavviso

| Campo JSON | Regola |
|---|---|
| `ldv` | `ldv` del preavviso scelto; se assente, la LdV cercata. Con "nessun preavviso": la LdV cercata |
| `idPreadvising` | `id` del preavviso scelto |
| `numeroOrdine` | `code_externalId` (AS-02) |
| `idCollo` | `code_parcelLabel` |
| `numeroColli` | `code_packageNumber` come intero; `null` se assente o non numerico |
| `canale` | valorizzato **solo se il preavviso non ha `id_file`**: valore del campo configurato in `onetracking.preavviso.campo-canale` (default `channel`), altrimenti `null` (AS-03). Se il preavviso ha `id_file` è sempre `null`: il canale si legge in `file.canale` |
| `statoPreavviso`, `statoPreavvisoDescrizione` | da `stato_LdV` del documento LdV (5.3) |
| `eventType` | `event_type` del preavviso scelto, così com'è |
| `dataEvento` | `event_ts` del preavviso scelto (formato 5.6) |
| `idFile` | `id_file` del preavviso scelto, `null` se assente |

Stringhe vuote o di soli spazi valgono `null`. Il back-end non mette `"-"`: il trattino lo mette il
front-end.

### 5.3 Stato del preavviso (da `stato_LdV`)

| `stato_LdV` del documento LdV | `statoPreavviso` | `statoPreavvisoDescrizione` |
|---|---|---|
| `LDV ON TIME` | `IN_TEMPO` | `In tempo` |
| `LDV IN RITARDO` | `IN_RITARDO` | `In ritardo` |
| `LDV SENZA PREAVVISO` | `SENZA_PREAVVISO` | `Senza preavviso` |
| assente, o documento LdV assente | `SENZA_PREAVVISO` | `Senza preavviso` |
| altro valore | `SENZA_PREAVVISO` | `Senza preavviso`, con log WARN del valore (AS-10) |

- Confronto senza maiuscole/minuscole e con gli spazi normalizzati.
- I codici `IN_RITARDO` e `SENZA_PREAVVISO` sono nel contratto; `IN_TEMPO` è il terzo valore
  coerente con la descrizione "In tempo" del mapping.
- Lo stato viene dal documento LdV anche quando esiste un preavviso: è il mapping di `analisi.md`.
  Il caso "preavviso presente, `stato_LdV` assente" (es. LdV non ancora scansionata) mostra quindi
  "Senza preavviso": è un punto aperto (AS-10).

### 5.4 Dati del file e decodifica dello stato

`file` è valorizzato solo se il preavviso scelto ha `id_file` **e** la query 4.3 trova il documento;
altrimenti è `null` (se `id_file` c'è ma il file non si trova: log WARN con `id_file`).

| `idStato` (o `status`) | `statoFile` |
|---|---|
| `ST_F0001` | File inviato dal cliente |
| `ST_F0002` | File preso in carico |
| `ST_F0005` | File in elaborazione |
| `ST_F0006` | File elaborato con successo |
| `ST_F0007` | File elaborato con scarto |
| `ST_F0008` | File completamente scartato |
| altro valore | il codice stesso (es. `ST_F0099`), con log WARN |
| assente | `idStato` e `statoFile` `null` |

Le descrizioni sono quelle di `analisi.md`, con l'iniziale maiuscola come nel mock up ("File elaborato
con scarto", slide 3). Si tengono in una mappa nel codice; non serve renderle configurabili.

| Campo JSON | Regola |
|---|---|
| `idFile` | `id_file` del preavviso (l'`idfile` di Solr non è stored) |
| `nomeFile` | `nomefile` |
| `dataCaricamento` | `upload_time_stamp` (5.6) |
| `idStato`, `statoFile` | tabella sopra |
| `dataStato` | `_lastupdate_` del documento `pacchi_file` (AS-05) |
| `canale` | `channel` così com'è, senza transcodifica (AS-09) |

### 5.5 Errori del preavviso

`errori` è la lista degli errori del **preavviso scelto**, letta da `preadv_errori`. `[]` se il campo
manca o è vuoto, e con "nessun preavviso". Il formato non è nell'ICD (AS-04); il parser prova, in ordine:

1. **array JSON** di oggetti. Chiavi riconosciute, senza distinzione di maiuscole:
   - campo: `campo`, `campoErrore`, `campo_errore`, `field`;
   - codice: `codice`, `codiceErrore`, `codice_errore`, `code`;
   - descrizione: `descrizione`, `descrizioneErrore`, `descrizione_errore`, `description`, `message`.
   È ammesso anche un **oggetto JSON singolo** con le stesse chiavi (un errore);
2. **testo** con righe `campo|codice|descrizione` separate da `;` (campi mancanti → `null`);
3. **altrimenti** un solo errore con `campo` e `codice` `null` e `descrizione` = testo grezzo.

- Se `preadv_errori` è multivalore in Solr (lista di stringhe), si applica il parser a ogni elemento e
  si concatenano i risultati.
- Si scartano gli errori con tutti e tre i campi vuoti.
- L'ordine è quello della sorgente; nessuna deduplica.
- Il contenuto di `preadv_errori` non va nei log (può contenere valori del tracciato del cliente).
  In caso di formato non riconosciuto si logga solo la lunghezza.

### 5.6 Formato delle date

Le date del T&T-Repo (`tdate`) arrivano in UTC (es. `2026-11-10T07:47:00Z`). Il back-end le restituisce
in **ISO 8601 con offset, fuso `Europe/Rome`**, senza millisecondi: `2026-11-10T08:47:00+01:00`
(come l'esempio del contratto `2024-07-15T08:47:00+02:00`). Il formato a video `dd/MM/yyyy HH:mm` lo
applica il front-end. Una data non leggibile vale `null`, con log WARN.

### 5.7 Errori e disponibilità

| Situazione | Risposta |
|---|---|
| LdV non valida (RF-01) | `400`, `ErrorResponse` con `errorMessage` "LdV non valida", nessuna query (AS-13) |
| Nessun documento LdV e nessun preavviso | `200`, "nessun preavviso" (6.2) |
| Documento LdV assente, preavvisi presenti | `200`, `presente: true`, stato `SENZA_PREAVVISO` (5.3, AS-10) |
| `id_file` presente, file non trovato | `200`, `file: null` |
| Solr non raggiungibile, timeout, HTTP 5xx o 401/403 di AppGW, risposta non leggibile, su **qualsiasi** delle query | `503`, `ErrorResponse` con `statusCode` 503 ed `errorMessage` "Dati preavviso non disponibili" (AS-14) |
| Errore inatteso nel codice | `500` dal gestore esistente |

Nessun retry applicativo: la chiamata è sincrona dall'operatore, che può riaprire la sezione.

### 5.8 Regole riassuntive

| ID | Regola |
|---|---|
| RF-01 | La LdV del path si normalizza con `trim` e si valida: solo `A-Z`, `a-z`, `0-9`, lunghezza 1..35. Non si converte in maiuscolo (AS-13) |
| RF-02 | Si interroga `pacchi_anagrafica` per il documento LdV (4.1) e per i preavvisi (4.2); le due query si possono fare in parallelo |
| RF-03 | Il preavviso si sceglie con la regola 5.1 |
| RF-04 | `pacchi_file` si interroga solo se il preavviso scelto ha `id_file` (4.3) |
| RF-05 | Ogni query chiede solo i campi elencati in `fl` |
| RF-06 | Mapping 5.2, stato 5.3, file 5.4, errori 5.5, date 5.6 |
| RF-07 | `canale` del preavviso è valorizzato solo senza `id_file` |
| RF-08 | Nessun permesso nuovo: l'API è protetta come le altre di `shipment-info` (header SiteMinder) (AS-06) |
| RF-09 | Errori di accesso al T&T-Repo → `503` (5.7) |
| RF-10 | Nei log: LdV, `idPreadvising`, `id_file`, numero di preavvisi trovati, `event_type` scelto, esito ed elapsed. Mai `preadv_errori`, nomi file del cliente, credenziali Solr |

## 6. Contratto dell'API [DECISO, `analisi.md`]

`GET /api/preavviso/{ldv}`. Il browser la chiama su `portal-pages` come `/api/preavviso/{ldv}`; la
regola Nitro `'/api/**': { proxy: '${shipmentTarget}/**' }` toglie `/api`, quindi su `shipment-info`
il mapping è **`/preavviso/{ldv}`**, come `/mittente-destinatario/{ldv}/{dbLdv}` (AS-08).

- `Content-Type: application/json`.
- Nessun parametro oltre alla LdV.

### 6.1 Risposta `200`, preavviso presente

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

| Campo | Tipo | Null? | Note |
|---|---|---|---|
| `presente` | boolean | no | `true` se c'è almeno un documento di preavviso |
| `preavviso` | oggetto | **no** (anche senza preavviso) | 5.2 |
| `preavviso.ldv` | string | no | |
| `preavviso.idPreadvising` | string | sì | `null` senza preavviso |
| `preavviso.numeroOrdine`, `idCollo` | string | sì | |
| `preavviso.numeroColli` | integer | sì | |
| `preavviso.canale` | string | sì | solo senza `id_file` |
| `preavviso.statoPreavviso` | string | no | `IN_TEMPO`, `IN_RITARDO`, `SENZA_PREAVVISO` |
| `preavviso.statoPreavvisoDescrizione` | string | no | `In tempo`, `In ritardo`, `Senza preavviso` |
| `preavviso.eventType` | string | sì | `PRE_ENRICHMENT`, `COMPLETED`, `ERROR` (o altro valore così com'è) |
| `preavviso.dataEvento` | string ISO 8601 con offset | sì | |
| `preavviso.idFile` | string | sì | |
| `file` | oggetto | sì | `null` se il preavviso non ha `id_file` o il file non c'è |
| `file.*` | string | sì (tranne `idFile`) | 5.4 |
| `errori` | array | **no** | `[]` se non ci sono errori |
| `errori[].campo`, `codice`, `descrizione` | string | sì | 5.5 |

I campi `null` si serializzano (non si omettono), così il front-end trova sempre la stessa forma.

### 6.2 Risposta `200`, nessun preavviso

```json
{
  "presente": false,
  "preavviso": {
    "ldv": "TST0000000004", "idPreadvising": null, "numeroOrdine": null, "idCollo": null,
    "numeroColli": null, "canale": null, "statoPreavviso": "SENZA_PREAVVISO",
    "statoPreavvisoDescrizione": "Senza preavviso", "eventType": null, "dataEvento": null, "idFile": null
  },
  "file": null,
  "errori": []
}
```

Con `presente: false` lo stato è sempre `SENZA_PREAVVISO`, qualunque sia `stato_LdV` (contratto).

### 6.3 Risposta `503`, T&T-Repo non disponibile

```json
{ "eccezioneGestita": true, "statusCode": 503, "errorCode": "503 SERVICE_UNAVAILABLE",
  "errorMessage": "Dati preavviso non disponibili" }
```

Forma di `ErrorResponse` esistente; `errorCode` segue l'uso attuale (`HttpStatus.toString()`).

### 6.4 OpenAPI

Annotazioni `@Operation`/`@ApiResponses` come in `TupController`, con `200`, `400`, `503`, `500`.

## 7. Casi d'uso con esempi [dati inventati]

LdV, ordini, file e identificativi sono inventati. I valori a video del mock up (slide 3-5) sono
riprodotti nella struttura, non nei dati.

### UC-01 — Preavviso da file con errori, file elaborato con scarto (mock up caso 1, slide 3)

Solr:
- documento LdV: `{ "id": "TST0000000001", "stato_LdV": "LDV IN RITARDO" }`;
- preavvisi (1): `{ "id": "a1000000-0000-4000-8000-000000000001", "ldv": "TST0000000001",
  "id_file": "f1000000-0000-4000-8000-000000000001", "event_type": "ERROR",
  "event_ts": "2026-11-10T07:47:00Z", "code_externalId": "ORD-TEST-0001", "code_parcelLabel": "COLLO-001",
  "code_packageNumber": 1, "preadv_errori": "[{\"campo\":\"CAP destinatario\",\"codice\":\"ERR-4021\",\"descrizione\":\"CAP generico — normalizzazione non possibile\"},{\"campo\":\"Peso dichiarato\",\"codice\":\"ERR-4035\",\"descrizione\":\"Peso non consentito per consegna a rete terza\"},{\"campo\":\"Indirizzo mittente\",\"codice\":\"ERR-2010\",\"descrizione\":\"Indirizzo incompleto\"}]" }`;
- file: `{ "nomefile": "PREAVV_TEST_20261110_001.csv", "upload_time_stamp": "2026-11-10T07:32:00Z",
  "idStato": "ST_F0007", "channel": "Invio File", "_lastupdate_": "2026-11-10T07:47:00Z" }`.

Risposta:

```json
{
  "presente": true,
  "preavviso": { "ldv": "TST0000000001", "idPreadvising": "a1000000-0000-4000-8000-000000000001",
    "numeroOrdine": "ORD-TEST-0001", "idCollo": "COLLO-001", "numeroColli": 1, "canale": null,
    "statoPreavviso": "IN_RITARDO", "statoPreavvisoDescrizione": "In ritardo", "eventType": "ERROR",
    "dataEvento": "2026-11-10T08:47:00+01:00", "idFile": "f1000000-0000-4000-8000-000000000001" },
  "file": { "idFile": "f1000000-0000-4000-8000-000000000001", "nomeFile": "PREAVV_TEST_20261110_001.csv",
    "dataCaricamento": "2026-11-10T08:32:00+01:00", "idStato": "ST_F0007",
    "statoFile": "File elaborato con scarto", "dataStato": "2026-11-10T08:47:00+01:00", "canale": "Invio File" },
  "errori": [
    { "campo": "CAP destinatario", "codice": "ERR-4021", "descrizione": "CAP generico — normalizzazione non possibile" },
    { "campo": "Peso dichiarato", "codice": "ERR-4035", "descrizione": "Peso non consentito per consegna a rete terza" },
    { "campo": "Indirizzo mittente", "codice": "ERR-2010", "descrizione": "Indirizzo incompleto" }
  ]
}
```

### UC-02 — Preavviso da file senza errori, file elaborato con successo (mock up caso 2, slide 4)

Solr: documento LdV `stato_LdV: "LDV ON TIME"`, `id_preadvising: "a2…02"`; preavvisi (2):
`a2…01` `ERROR` `event_ts 2026-11-10T07:40:00Z`, `a2…02` `COMPLETED` `event_ts 2026-11-10T07:47:00Z`,
entrambi con `id_file "f2…01"`; file `ST_F0006`, `channel "Invio File"`.

Risposta: preavviso scelto `a2…02` (unico `COMPLETED`), `statoPreavviso: "IN_TEMPO"`, `eventType: "COMPLETED"`,
`file.statoFile: "File elaborato con successo"`, `errori: []`.

### UC-03 — Preavviso non da file (mock up caso 3, slide 5)

Solr: documento LdV `stato_LdV: "LDV ON TIME"`; un preavviso `COMPLETED` senza `id_file`, con
`channel: "WEBSERVICES"`.

Risposta: `presente: true`, `preavviso.canale: "WEBSERVICES"`, `preavviso.idFile: null`, `file: null`,
`errori: []`, `statoPreavviso: "IN_TEMPO"`.

### UC-04 — Nessun preavviso

Solr: documento LdV `{ "id": "TST0000000004", "stato_LdV": "LDV SENZA PREAVVISO" }` (o nessun
documento); nessun documento con `ldv:"TST0000000004"`.

Risposta: quella della 6.2. `pacchi_file` non si interroga.

### UC-05 — T&T-Repo non disponibile

AppGW non risponde entro il timeout (o risponde `502`/`503`) su una delle query.

Risposta: `503` della 6.3; log ERROR con LdV, query (collection) ed elapsed, senza credenziali.

### UC-06 — Più preavvisi, nessuno `COMPLETED` (regola del penultimo)

Preavvisi: `p1` `PRE_ENRICHMENT` 07:00Z, `p2` `ERROR` 07:10Z, `p3` `ERROR` 07:20Z.
Scelto: `p2` (penultimo per `event_ts`), con gli errori di `p2`.

### UC-07 — Più preavvisi `COMPLETED`

Preavvisi: `p1` `COMPLETED` 07:00Z, `p2` `ERROR` 07:10Z, `p3` `COMPLETED` 07:05Z.
Scelto: `p3` (il `COMPLETED` più recente), anche se `p2` è più recente in assoluto.

### UC-08 — File non trovato

Il preavviso scelto ha `id_file "f8…01"`, `pacchi_file` non ha documenti per quell'`idfile`.
Risposta: `200`, `file: null`, `preavviso.idFile: "f8…01"`, `preavviso.canale: null`; log WARN.

## 8. Configurazione

| Proprietà | Default | Uso |
|---|---|---|
| `solrappgw.endpoint`, `solr.username`, `solr.password` | esistenti | base e credenziali (da secret come oggi, mai nei file nuovi) |
| `onetracking.preavviso.stato-preferito` | `COMPLETED` | stato preferito della regola 5.1 [DECISO 13-11] |
| `onetracking.preavviso.campo-canale` | `channel` | campo del preavviso con il canale, solo senza file (AS-03) |
| `onetracking.preavviso.max-preavvisi` | `50` | `rows` della query 4.2; se `numFound` è maggiore, log WARN (AS-15) |

Le proprietà vanno in `src/main/resources/application.properties` e in
`chart/config/files/application.properties`. `application-test.properties` contiene credenziali Solr
versionate: non aggiungerne, non copiarle.

## 9. Requisiti non funzionali e osservabilità

- **Tempi**: 2 o 3 query Solr per richiesta, per id o campo indicizzato. Obiettivo: risposta entro
  2 s al 95° percentile in collaudo (da misurare nei test integrati).
- **Timeout**: `solrRestTemplate` ha lettura a 60 s (`server.controller.solr-timeout`), uguale al
  timeout di `$safeFetch` del front-end (60 s). Con il default il front-end va in timeout insieme al
  back-end: va bene, perché il front-end mostra comunque "Dati preavviso non disponibili". Un timeout
  dedicato più corto è un miglioramento possibile, non richiesto (AS-14).
- **Tracing**: span `SHPINFO_preavviso` figlio dello span attivo, con sotto-span per query
  (`SOLR_pacchi_anagrafica_ldv`, `SOLR_pacchi_anagrafica_preavvisi`, `SOLR_pacchi_file`), come in
  `TupController` (`tracer.buildSpan`, `tracingUtils.trace`). Errori sullo span con `Costanti.SPAN_ERRORE`.
- **Metriche**: `@Timed(value = "shp_info_get_preavviso")` sul metodo del controller.
- **Log** (RF-10): una riga INFO per richiesta `PREAVVISO | <ldv> | preavvisi=<n> scelto=<id> eventType=<x> file=<si/no> errori=<n> esito=<200/503> ms=<t>`.
  Nessun dato personale né il contenuto di `preadv_errori`.
- **Sonar**: metodi brevi (regola di scelta, parser errori e decodifiche in classi o metodi separati e
  testati), nessun duplicato con `RestClientSolr` (fattorizzare la costruzione dell'URI se serve).

## 10. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato UC-01, `GET /preavviso/TST0000000001` risponde `200` con il JSON di UC-01, campo per campo |
| AC-02 | Dato UC-02, il preavviso scelto è il `COMPLETED`, `statoPreavviso` è `IN_TEMPO`, `file.statoFile` è "File elaborato con successo", `errori` è `[]` |
| AC-03 | Dato UC-03, `preavviso.canale` è `WEBSERVICES`, `file` è `null` e `pacchi_file` non viene interrogato |
| AC-04 | Dato UC-04, la risposta è uguale alla 6.2 e `pacchi_file` non viene interrogato |
| AC-05 | Dato UC-04 ma con `stato_LdV: "LDV ON TIME"` sul documento LdV, la risposta ha comunque `presente: false` e `SENZA_PREAVVISO` |
| AC-06 | Dato un solo preavviso `PRE_ENRICHMENT`, è quello il preavviso scelto |
| AC-07 | Dato UC-06, il preavviso scelto è `p2` |
| AC-08 | Dato UC-07, il preavviso scelto è `p3` |
| AC-09 | Con `onetracking.preavviso.stato-preferito=ERROR` e i preavvisi di UC-07, il preavviso scelto è `p2` |
| AC-10 | Dati due preavvisi con lo stesso `event_ts` e nessun `COMPLETED`, la scelta segue lo spareggio `_lastupdate_` e poi `id` ed è ripetibile |
| AC-11 | Dato un preavviso con `id_file` e `channel` valorizzato sul preavviso, `preavviso.canale` è `null` |
| AC-12 | Dato UC-08, `file` è `null` e c'è un log WARN con `id_file` |
| AC-13 | Per ogni `ST_F0001`, `ST_F0002`, `ST_F0005`, `ST_F0006`, `ST_F0007`, `ST_F0008` la descrizione è quella della 5.4; con `ST_F0099` `statoFile` è `ST_F0099`; con solo `status` valorizzato si usa `status` |
| AC-14 | `stato_LdV` `LDV ON TIME`, `LDV IN RITARDO`, `LDV SENZA PREAVVISO`, assente, `ldv in ritardo`, `XYZ` danno rispettivamente `IN_TEMPO`, `IN_RITARDO`, `SENZA_PREAVVISO`, `SENZA_PREAVVISO`, `IN_RITARDO`, `SENZA_PREAVVISO` (+ WARN) |
| AC-15 | `preadv_errori` come array JSON, oggetto singolo, testo `a|b|c;d|e|f`, testo libero, stringa vuota danno rispettivamente N errori, 1 errore, 2 errori, 1 errore con solo `descrizione`, `[]` |
| AC-16 | Le date `2026-11-10T07:47:00Z` e `2026-07-15T06:47:00Z` diventano `2026-11-10T08:47:00+01:00` e `2026-07-15T08:47:00+02:00` |
| AC-17 | Dato Solr che non risponde (timeout) o risponde `503` su una qualsiasi delle tre query, la risposta è `503` con `errorMessage` "Dati preavviso non disponibili" |
| AC-18 | Data la LdV `TST 01"OR"*` (o più lunga di 35 caratteri), la risposta è `400` e non parte nessuna query Solr |
| AC-19 | Ogni query Solr ha il parametro `fl` con i soli campi della sezione 4; nessuna chiede `partitaIVA`, `ragioneSociale`, campi `receiver_*` o `sender_*` |
| AC-20 | Nei log non compaiono il contenuto di `preadv_errori`, nomi file, credenziali; compaiono LdV, numero di preavvisi ed esito |
| AC-21 | Le API esistenti (`/mittente-destinatario`, `/tup/recupera-dati-tup-new`) danno le stesse risposte di prima (nessuna regressione su `pacchiAnagrafica(ldv)`) |
| AC-22 | I campi `null` della risposta sono presenti nel JSON (non omessi) |

## 11. Casi di test

Test unitari con Solr simulato (MockRestServiceServer o WireMock) e dati inventati; poi test integrato in
svil sul T&T-Repo di test con LdV di test.

| TC | Tipo | Input | Atteso | AC |
|---|---|---|---|---|
| TC-01 | unit | UC-01 | JSON di UC-01 | AC-01, AC-15, AC-16 |
| TC-02 | unit | UC-02 | scelto il `COMPLETED` | AC-02 |
| TC-03 | unit | UC-03 | canale `WEBSERVICES`, nessuna query su `pacchi_file` | AC-03 |
| TC-04 | unit | UC-04, con e senza documento LdV, con `stato_LdV` `LDV ON TIME` | risposta 6.2 | AC-04, AC-05 |
| TC-05 | unit | regola 5.1: 1 doc di ciascun `event_type`; UC-06; UC-07; parità di `event_ts`; doc senza `event_ts` | scelte attese | AC-06…AC-10 |
| TC-06 | unit | proprietà `stato-preferito=ERROR` | scelto `p2` di UC-07 | AC-09 |
| TC-07 | unit | preavviso con `id_file` e `channel`; UC-08 | `canale` null; `file` null + WARN | AC-11, AC-12 |
| TC-08 | unit (parametrico) | stati file | decodifiche 5.4 | AC-13 |
| TC-09 | unit (parametrico) | valori `stato_LdV` | tabella 5.3 | AC-14 |
| TC-10 | unit (parametrico) | formati `preadv_errori`, anche multivalore | parser 5.5 | AC-15 |
| TC-11 | unit | date estive e invernali, data non valida | 5.6, `null` + WARN | AC-16 |
| TC-12 | unit | Solr timeout, `503`, `401`, JSON non valido, su ciascuna query | `503` | AC-17 |
| TC-13 | unit (web) | LdV con spazi, virgolette, `*`, `:`; LdV di 36 caratteri; LdV con spazi iniziali e finali | `400`, oppure `trim` e `200` | AC-18 |
| TC-14 | unit | URL generate | `fl` atteso, LdV fra `%22` | AC-19 |
| TC-15 | unit (log capture) | TC-01 e TC-12 | contenuti dei log | AC-20 |
| TC-16 | regressione | test esistenti di `MittDestServiceImpl`, `TupController` | verdi | AC-21 |
| TC-17 | integrato svil | 3 LdV di test nel T&T-Repo di test, una per caso del mock up, più una senza preavviso | come UC-01…UC-04 | AC-01…AC-04 |
| TC-18 | integrato svil | misura dei tempi su 20 chiamate | p95 ≤ 2 s | sezione 9 |

Per TC-17 servono LdV di test con preavvisi in `pacchi_anagrafica` di test (iniziativa 138975):
se non ci sono, vanno create con un preavviso di test nella catena di svil (AS-24).

## 12. Assunzioni e domande aperte

Da `analisi.md`:

| ID | Assunzione adottata | Da confermare con |
|---|---|---|
| AS-01 | **Chiusa (13-11, Diego)**: lo stato è `event_type` del record; si sceglie `COMPLETED`, fra più `COMPLETED` il più recente per `event_ts`, altrimenti il penultimo (5.1) | — |
| AS-02 | Numero ordine = `code_externalId` (riferimento spedizione del cliente) | Poste / Diego |
| AS-03 | Canale del preavviso non da file: nessun campo nell'ICD; il BE legge un campo configurabile (`onetracking.preavviso.campo-canale`, default `channel`), se manca `null` (a video "-") | Poste |
| AS-04 | Formato di `preadv_errori` non descritto nell'ICD: array JSON (`campo`/`codice`/`descrizione` e varianti), altrimenti righe `campo|codice|descrizione` separate da `;`, altrimenti un errore col testo grezzo (5.5) | Poste (team T&T-Repo) |
| AS-05 | Data stato del file = `_lastupdate_` di `pacchi_file` (non c'è un campo dedicato) | Poste |
| AS-06 | Nessuna funzionalità di profilazione nuova (`OTR_*`) | Poste |
| AS-07 | Si parte da `origin/develop` di entrambi i repo | — |

Nuove (Mary, 13-11):

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| AS-08 | **Path**: il contratto dice `GET /api/preavviso/{ldv}`. Il proxy di `portal-pages` toglie `/api` (`'/api/**' → ${shipmentTarget}/**`): se il controller mappasse `/api/preavviso` il front-end dovrebbe chiamare `/api/api/preavviso` (regola usata solo da `ProfilazioneController`/`UserController`) | mapping BE `/preavviso/{ldv}`, chiamata FE `/api/preavviso/{ldv}`. **Da allineare subito fra le due sviluppatrici** | Diego, sviluppatrici |
| AS-09 | **Canale del file**: il mock up mostra `INVIOFILE` (slide 3-4, e slide 2 "INVIOFILE, INVIOEASY, STAMPA MASSIVA"); l'ICD `pacchi_file.channel` dichiara descrizioni (`Invio File`, `Invio Easy`, …) e il contratto ha `"Invio File"` | valore di `channel` così com'è, senza transcodifica | Poste |
| AS-10 | **Stato del preavviso**: viene da `stato_LdV` del documento LdV. Se c'è un preavviso ma `stato_LdV` manca (LdV non ancora nel T&T-Repo o non ancora scansionata) si mostra "Senza preavviso", che è fuorviante. Inoltre il caso 1 del mock up ha un preavviso con errori e "In ritardo": non è chiaro se `stato_LdV` consideri anche i preavvisi `ERROR`. Valori di `stato_LdV` fuori dominio → `SENZA_PREAVVISO` + WARN | mapping di `analisi.md` senza eccezioni | Diego / Poste (T&T-Repo, 138975) |
| AS-11 | **`id_preadvising` del documento LdV** ("preavviso valido") può indicare un preavviso diverso da quello scelto con la regola 5.1 | vince la regola; `id_preadvising` non si usa | Diego |
| AS-12 | **Errori di file**: `pacchi_file` ha `esito`, `codiceErrore`, `descrizioneErrore` (es. file `ST_F0008` completamente scartato). Il contratto porta solo gli errori del preavviso | non si leggono né si mostrano | Poste |
| AS-13 | **LdV non valida**: il contratto non prevede `400`. Le query Solr sono costruite senza encoding, quindi la LdV va validata (solo alfanumerici, 1..35) | `400` senza query; il FE la tratta come qualsiasi errore | Diego |
| AS-14 | **Errore parziale**: `pacchi_anagrafica` risponde, `pacchi_file` no | `503` per tutta la risposta (anche `pacchi_file` è T&T-Repo); nessun timeout dedicato (60 s come oggi) | Diego |
| AS-15 | **Spareggio e limite**: preavvisi con lo stesso `event_ts`; numero massimo di preavvisi per LdV | spareggio `_lastupdate_` desc, poi `id` desc; `rows=50` con WARN oltre | Diego |
| AS-16 | **Data stato**: `_lastupdate_` cambia a ogni reindicizzazione del documento, non solo al cambio di stato. Il topic `preadvising.evensource` ha `eventData.dataStato`, ma l'ICD di `pacchi_file` non lo mappa | `_lastupdate_` (AS-05); chiedere al T&T-Repo di indicizzare `dataStato` | Poste (T&T-Repo) |
| AS-22 | **ICD `preadv_errori`**: la colonna "Mappatura con il topic" dice `event_type`, probabilmente un refuso. Serve la fonte vera e il formato (rafforza AS-04) | parser 5.5 | Poste (T&T-Repo) |
| AS-23 | **Attribuzione dei DREQ**: il mock up elenca DREQ0062862/64/65/66 senza dire quale copre quale blocco | tabella della sezione 2 | Poste / Diego |
| AS-24 | **Dati di test**: servono in svil/collaudo LdV di test con preavvisi nei tre casi del mock up | da costruire con la catena preadvising di svil | Diego / test manager |

AS-17…AS-21 riguardano solo il front-end: sono in [portal-pages.md](portal-pages.md).

## 13. Riferimenti

- [analisi.md](../analisi.md): regole, mapping, contratto.
- [portal-pages.md](portal-pages.md): front-end, layout ed etichette.
- [contesto/onetracking.md](../../../contesto/onetracking.md): architettura di OneTracking, T&T-Repo.
- [contesto/microservizi-preadvising.md](../../../contesto/microservizi-preadvising.md), sezione `preadvising.evensource`: eventi di stato del file.
- [contesto/glossario-ce.md](../../../contesto/glossario-ce.md): LDV, preadvising.
- ICD: `cliente/ICD_PACCHI_ANAGRAFICA_138975_v1.0.xlsx`, `cliente/ICD_PACCHI_FILE_v1.xlsx`.
- Mock up: `cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`, slide 2-5.
