# `portal-pages` — Documento funzionale per lo sviluppo (sezione "Informazioni preavviso")

**Iniziativa**: 144216 — Assistenza Clienti, Customer Journey preavviso (PRJ0049429) · **Versione**: 0.1 · **Data**: 2026-11-13
**Autrice**: Mary (analyst) · **Destinataria**: sviluppatrice front-end di OneTracking
**Repository**: `gitlab.alm.poste.it/ONETRACKING/PRESENTATION/portal-pages` (locale `gitposte/SDA/ONETRACKING/PRESENTATION/portal-pages`), branch `144216_preavviso_onetracking` da `origin/develop`
**Stack**: Nuxt 3.14, Vue 3.5, store Vuex 4 (`stores/views`), tabelle `vue-good-table-next`, chiamate con `utils/safe-fetch.js`
**Generato da**: [prompt-portal-pages.md](prompt-portal-pages.md)
**Fonti**: [analisi.md](../analisi.md) (regole, mapping, contratto: **vincolanti**); mock up
`cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx` (slide 2-5); [contesto/onetracking.md](../../../contesto/onetracking.md); codice di `origin/develop` letto il 13-11
**Documento gemello (back-end)**: [shipment-info.md](shipment-info.md)

Etichette usate nel documento:
- **[FATTO]**: scritto nel mock up o nel codice; la fonte è indicata.
- **[DECISO]**: decisione presa, con data e riferimento.
- **[ASSUNTO]**: scelta adottata per non bloccare lo sviluppo, con ID e default; da confermare (sezione 11).

> **Il contratto dell'API (sezione 5) viene da `analisi.md` e non si cambia**: front-end e back-end lo
> stanno sviluppando in parallelo. Le decodifiche (stato del preavviso, stato del file) e la scelta del
> preavviso le fa il back-end: il front-end mostra, formatta le date e decide la visibilità delle sezioni.

---

## 1. Contesto e obiettivo

OneTracking è il portale degli operatori SDA/Poste per lo stato delle spedizioni. Nel dettaglio di una
LdV, l'operatore dell'assistenza clienti deve vedere il **preavviso** della spedizione: i dati del
preavviso, il file da cui viene (se viene da file) e gli errori riscontrati, senza aprire altri sistemi.

A `portal-pages` si chiede **una sottosezione nuova, "Informazioni preavviso"**, nel tab
"Mittente/Destinatario" del dettaglio LV, **fra "Informazioni LV" e "Cliente/Mittente/Destinatario"**
(mock up, slide 2), alimentata dalla nuova API `GET /api/preavviso/{ldv}` di `shipment-info`.

**Non fa**:

| Fuori perimetro | Chi lo fa |
|---|---|
| Scelta del preavviso fra più preavvisi, decodifiche, lettura del T&T-Repo | `shipment-info` ([shipment-info.md](shipment-info.md)) |
| Nuove funzionalità di profilazione `OTR_*` | nessuno (AS-06) |
| Modifiche a "Dati Cliente", "Informazioni LV", "Cliente/Mittente/Destinatario" | nessuno |
| Export PDF/Excel della sezione | fuori da questa versione (AS-18) |

## 2. Requisiti coperti

Requisiti del mock up v0.8 (slide 1 e 2) [FATTO]:

| Requisito | Cosa chiede (dal mock up) | Dove a video |
|---|---|---|
| DREQ0062862 | Dati di preavviso della singola LdV consultabili nel dettaglio LV, nuova sottosezione fra "Informazioni LV" e "Cliente/Mittente/Destinatario" | sezione 3 |
| DREQ0062864 | Dati preavviso LdV: numero ordine, identificativo collo, numero colli, stato preavviso | blocco 4.1 "Informazioni preavviso" |
| DREQ0062865 | Dati file preavviso, solo se il preavviso proviene da file | blocco 4.2 "Dati file preavviso" |
| DREQ0062866 | Dettaglio errori, solo in presenza di anomalie, con campo in errore, codice e descrizione | blocco 4.3 "Dettaglio errori" |

L'attribuzione requisito → blocco è nostra, sull'ordine della slide 2: il mock up elenca i quattro
DREQ insieme (AS-23).

## 3. Dove si interviene nel codice

Indicazioni sul codice di `origin/develop` [FATTO, letto il 13-11]. I nomi nuovi sono proposte; dove
il branch di lavoro li ha già scelti (`InfoPreavviso.vue`, `wsActionPreavviso`, `setTabPreavviso`,
`utils/preavviso.js`) il documento li riprende.

| Punto | Cosa c'è oggi | Cosa si fa |
|---|---|---|
| `components/IndexRicerche.vue`, tab `#tab-02` ("Mittente/Destinatario", voce `mittDestLine`, abilitata da `chiaviFunzioni.tabMittenteDest`) | `<DatiCliente />` (tabelle "Dati Cliente" e **"Informazioni LV"**) poi `<InfoMittenteDestinatario />` ("Cliente/Mittente/Destinatario"), nel ramo `v-else` del controllo "Dati non presenti" | nuovo `<InfoPreavviso />` **fra** `<DatiCliente />` e `<InfoMittenteDestinatario />` (AS-20 per il ramo "Dati non presenti") |
| `IndexRicerche.vue`, metodo `caseInfoSpedizioni()` | chiama `setTabMittDest(responseSelectedRow)` | chiama anche `setTabPreavviso(responseSelectedRow.idLdv)` |
| `components/DatiCliente.vue`, `InfoMittenteDestinatario.vue` | modello di stile: `<h5>` di titolo, `vue-good-table` senza ordinamento, intestazioni in grassetto nero 16 px, righe in grassetto | **non si toccano**: sono il modello da seguire |
| `components/` | — | nuovo `InfoPreavviso.vue` (sezione 4) |
| `nuxt.config.js`, `runtimeConfig.public` | `wsActionTabMittDest: process.env.wsActionTabMittDest || '/api/mittente-destinatario'` | `wsActionPreavviso: process.env.wsActionPreavviso || '/api/preavviso'` (AS-08) |
| `stores/views/` (`state.js`, `mutations.js`, `actions.js`, `getters.js`) | `tabMittDest` con `timeout`; action `setTabMittDest` con `$safeFetch` | stato `tabPreavviso`, mutation di caricamento/esito/errore/reset, action `setTabPreavviso(ldv)`, getter `getTabPreavviso` (sezione 6) |
| `utils/` | `utility.js` con `renderValue` (null/undefined/'' → `-`) | funzioni pure di trasformazione e formattazione (es. `utils/preavviso.js`) |
| `deploy-svil/`, `deploy-coll/`, `deploy-config/` | le `wsAction*` non sono nei values (vale il default) | nulla, salvo si voglia sovrascrivere `wsActionPreavviso` |

## 4. Layout ed etichette (mock up v0.8, slide 3-5)

La pagina è il dettaglio LV raggiunto da **Ricerca › LV** (breadcrumb del mock up "OneTracking
26.07.01 › Ricerca › LV"), con la LdV nel campo di ricerca. Nel tab "Mittente/Destinatario" l'ordine
dall'alto è:

```
Dati Cliente                       (esistente, non nel mock up)
Informazioni LV                    (esistente: Blocco | Data Blocco | Canale | Info LV | Dettaglio | Info PDS)
Informazioni preavviso             NUOVA
  Dati file preavviso              NUOVA, solo se il preavviso viene da file
  Dettaglio errori                 NUOVA, solo se ci sono errori
Cliente/Mittente/Destinatario      (esistente: Soggetto | Ragione Sociale | P.IVA | ...)
```

L'etichetta "NUOVA SEZIONE" del mock up è un'annotazione della slide, **non si mostra**.

Ogni blocco è come le tabelle esistenti: titolo `<h5>`, tabella con una riga di intestazione e righe di
valori, intestazioni in grassetto nero, valori in grassetto, nessun ordinamento, nessuna paginazione,
nessuna selezione di riga. Un valore assente si mostra **`-`** (come nel mock up, "Data Blocco -").

### 4.1 Blocco "Informazioni preavviso" (sempre presente)

Titolo: **Informazioni preavviso**. Una sola riga.

| Colonna (etichetta esatta) | Campo della risposta | Formato |
|---|---|---|
| Lettera di vettura | `preavviso.ldv` (se assente: la LdV del dettaglio) | testo |
| Numero ordine | `preavviso.numeroOrdine` | testo |
| Id collo | `preavviso.idCollo` | testo |
| Numero colli | `preavviso.numeroColli` | intero |
| Canale | `preavviso.canale` | testo così com'è (es. `WEBSERVICES`). **Colonna presente solo se il preavviso non viene da file** (4.4) |
| Preavviso | `preavviso.statoPreavvisoDescrizione` | `In tempo`, `In ritardo`, `Senza preavviso` |

Ordine delle colonne: con il canale, come nella slide 5: Lettera di vettura, Numero ordine, Id collo,
Numero colli, **Canale**, Preavviso. Senza il canale, come nelle slide 3-4: Lettera di vettura, Numero
ordine, Id collo, Numero colli, Preavviso.

### 4.2 Blocco "Dati file preavviso" (solo da file)

Titolo: **Dati file preavviso**. Una sola riga.

| Colonna (etichetta esatta) | Campo della risposta | Formato |
|---|---|---|
| Nome file | `file.nomeFile` | testo |
| Data caricamento | `file.dataCaricamento` | `dd/MM/yyyy HH:mm`, ora di Roma |
| Stato file | `file.statoFile` | testo (es. "File elaborato con scarto") |
| Data stato | `file.dataStato` | `dd/MM/yyyy HH:mm`, ora di Roma |
| Canale | `file.canale` | testo così com'è (AS-09) |

### 4.3 Blocco "Dettaglio errori" (solo con errori)

Titolo: **Dettaglio errori**. Sotto il titolo, una riga di testo con il numero di errori:
**"N errori riscontrati"** (mock up: "3 errori riscontrati"); con un solo errore **"1 errore
riscontrato"**. Poi la tabella, una riga per errore, nell'ordine della risposta.

| Colonna (etichetta esatta) | Campo della risposta |
|---|---|
| Campo in errore | `errori[].campo` |
| Codice errore | `errori[].codice` |
| Descrizione errore | `errori[].descrizione` |

### 4.4 Regole di visibilità

| ID | Regola |
|---|---|
| RV-01 | Il blocco "Informazioni preavviso" c'è sempre quando si apre il tab "Mittente/Destinatario" di una LdV, anche senza preavviso e anche se l'API fallisce (con il messaggio di RV-06) |
| RV-02 | La colonna **Canale** del blocco 4.1 c'è solo se `presente` è `true` **e** il preavviso non viene da file, cioè `preavviso.idFile` è vuoto **e** `file` è `null` (caso 3) |
| RV-03 | Il blocco "Dati file preavviso" c'è solo se `presente` è `true` e `file` non è `null` (casi 1 e 2). Non dipende dal canale: vale anche per `Invio System` o `Web` (AS-21) |
| RV-04 | Il blocco "Dettaglio errori" c'è solo se `presente` è `true` e `errori` non è vuoto (caso 1) |
| RV-05 | Con `presente: false`: solo il blocco 4.1, con Lettera di vettura = la LdV, Preavviso = "Senza preavviso", le altre colonne `-`, senza Canale |
| RV-06 | Errore dell'API (`503`, `400`, `500`, timeout, rete): sotto il titolo "Informazioni preavviso" il messaggio **"Dati preavviso non disponibili"**, nessuna tabella. Il resto del tab ("Informazioni LV", "Cliente/Mittente/Destinatario") si mostra normalmente |
| RV-07 | Durante il caricamento: sotto il titolo "Informazioni preavviso" il messaggio "Caricamento dati preavviso in corso..." (o lo spinner `LoadSpinner`), senza bloccare il resto del tab |
| RV-08 | Nessun controllo di profilazione nuovo: la sezione la vede chi vede il tab "Mittente/Destinatario" (AS-06, AS-17) |
| RV-09 | Il caso "file presente ma `file.idFile` vuoto" non esiste nel contratto: se capita, conta `file` |

### 4.5 Formati

- **Date**: l'API restituisce ISO 8601 con offset (es. `2026-11-10T08:32:00+01:00`); a video
  **`dd/MM/yyyy HH:mm`** nel fuso `Europe/Rome` (es. `10/11/2026 08:32`), con `Intl.DateTimeFormat`
  e `timeZone: 'Europe/Rome'`, `hourCycle: 'h23'`. Senza secondi. Una data `null` → `-`; una stringa
  non interpretabile si mostra com'è.
- **Valori assenti**: `null`, `undefined`, stringa vuota → `-` (`renderValue` di `utils/utility.js`).
- **Numero colli**: intero così com'è, senza separatori.
- **Testi**: così come arrivano (nessun maiuscolo/minuscolo forzato). L'API restituisce testo: niente
  `v-html`.
- **Stato del preavviso e del file**: la descrizione arriva dal back-end (`statoPreavvisoDescrizione`,
  `statoFile`). Se fosse vuota, il front-end può ripiegare sulle stesse tabelle del back-end
  ([shipment-info.md](shipment-info.md), 5.3 e 5.4), senza inventare altri valori.

## 5. Contratto dell'API [DECISO, `analisi.md`]

`GET /api/preavviso/{ldv}`. Il front-end la chiama come le altre `/api/...`:
`config.public.wsActionPreavviso + '/' + encodeURIComponent(ldv)`; il proxy Nitro
(`'/api/**' → ${shipmentTarget}/**`) la inoltra a `shipment-info` su `/preavviso/{ldv}` (AS-08).

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

- Nessun preavviso: `200`, `presente: false`, `preavviso` con `ldv` e `statoPreavviso: SENZA_PREAVVISO`,
  `file: null`, `errori: []`.
- `file` è `null` se il preavviso non viene da file (o il file non si trova); `errori` è `[]` senza errori.
- T&T-Repo non raggiungibile: `503` con messaggio; la sezione mostra "Dati preavviso non disponibili".
- `preavviso.idPreadvising`, `eventType`, `dataEvento`, `file.idFile`, `file.idStato` **non si
  mostrano**: servono per diagnosi (si possono leggere negli strumenti del browser).

## 6. Comportamento (store e chiamata)

| ID | Regola |
|---|---|
| RF-01 | La chiamata parte quando si carica il tab "Mittente/Destinatario" per una LdV (`caseInfoSpedizioni()`), accanto a `setTabMittDest`, ed è **indipendente**: non aspetta `mittente-destinatario` e non la blocca |
| RF-02 | Se la LdV è vuota non parte nessuna chiamata e la sezione non si mostra |
| RF-03 | Lo stato `tabPreavviso` tiene la LdV richiesta, la risposta, `loading`, `caricato`, `disponibile`. Una risposta che arriva per una LdV diversa da quella corrente si ignora (cambio rapido di riga in ricerca massiva) |
| RF-04 | Una nuova ricerca o il reset dei risultati azzera `tabPreavviso` (come gli altri `resetTab*`) |
| RF-05 | Qualsiasi errore di `$safeFetch` (HTTP non 2xx, timeout `isTimeout`, rete) porta a `disponibile = false` (RV-06). Il timeout è quello di default di `$safeFetch` (60 s) |
| RF-06 | Nessun retry automatico. Riaprire il tab rifà la chiamata |
| RF-07 | Il messaggio d'errore del back-end non si mostra: a video sempre "Dati preavviso non disponibili". Nella console non si stampano le risposte intere |
| RF-08 | La trasformazione risposta → righe delle tabelle sta in funzioni pure (`utils/preavviso.js`), così si prova senza store e senza runtimeConfig |
| RF-09 | In ricerca massiva la sezione si riferisce alla riga selezionata (`responseSelectedRow.idLdv`), come il resto del tab (AS-19) |

## 7. Casi d'uso con esempi [dati inventati]

I dati sono inventati; la struttura è quella delle slide 3-5. Il blocco "Cliente/Mittente/Destinatario"
sotto la sezione non cambia e non è ripetuto.

### UC-01 — Preavviso da file con errori, file elaborato con scarto (slide 3)

Risposta: quella di UC-01 in [shipment-info.md](shipment-info.md) (sezione 7). A video:

**Informazioni preavviso**

| Lettera di vettura | Numero ordine | Id collo | Numero colli | Preavviso |
|---|---|---|---|---|
| TST0000000001 | ORD-TEST-0001 | COLLO-001 | 1 | In ritardo |

**Dati file preavviso**

| Nome file | Data caricamento | Stato file | Data stato | Canale |
|---|---|---|---|---|
| PREAVV_TEST_20261110_001.csv | 10/11/2026 08:32 | File elaborato con scarto | 10/11/2026 08:47 | Invio File |

**Dettaglio errori**

3 errori riscontrati

| Campo in errore | Codice errore | Descrizione errore |
|---|---|---|
| CAP destinatario | ERR-4021 | CAP generico — normalizzazione non possibile |
| Peso dichiarato | ERR-4035 | Peso non consentito per consegna a rete terza |
| Indirizzo mittente | ERR-2010 | Indirizzo incompleto |

### UC-02 — Preavviso da file senza errori, file elaborato con successo (slide 4)

Risposta: `presente: true`, `statoPreavvisoDescrizione: "In tempo"`, `file.statoFile: "File elaborato
con successo"`, `errori: []`. A video: blocco 4.1 senza Canale con Preavviso "In tempo", blocco 4.2,
**nessun** blocco "Dettaglio errori".

### UC-03 — Preavviso non da file (slide 5)

Risposta:

```json
{ "presente": true,
  "preavviso": { "ldv": "TST0000000003", "idPreadvising": "a3000000-0000-4000-8000-000000000001",
    "numeroOrdine": "ORD-TEST-0003", "idCollo": "COLLO-001", "numeroColli": 1, "canale": "WEBSERVICES",
    "statoPreavviso": "IN_TEMPO", "statoPreavvisoDescrizione": "In tempo", "eventType": "COMPLETED",
    "dataEvento": "2026-11-10T08:47:00+01:00", "idFile": null },
  "file": null, "errori": [] }
```

A video:

**Informazioni preavviso**

| Lettera di vettura | Numero ordine | Id collo | Numero colli | Canale | Preavviso |
|---|---|---|---|---|---|
| TST0000000003 | ORD-TEST-0003 | COLLO-001 | 1 | WEBSERVICES | In tempo |

Nessun blocco "Dati file preavviso" né "Dettaglio errori".

### UC-04 — Nessun preavviso

Risposta: `presente: false` (sezione 5). A video:

**Informazioni preavviso**

| Lettera di vettura | Numero ordine | Id collo | Numero colli | Preavviso |
|---|---|---|---|---|
| TST0000000004 | - | - | - | Senza preavviso |

### UC-05 — T&T-Repo non disponibile

Risposta: `503`. A video:

**Informazioni preavviso**

Dati preavviso non disponibili

"Informazioni LV" sopra e "Cliente/Mittente/Destinatario" sotto si mostrano come sempre.

### UC-06 — Un solo errore, valori mancanti

Risposta: `presente: true`, `numeroOrdine: null`, `file` con `dataStato: null`, un errore con
`campo: null`. A video: Numero ordine `-`, Data stato `-`, "1 errore riscontrato", Campo in errore `-`.

## 8. Requisiti non funzionali

- La sezione non rallenta il tab: la chiamata è in parallelo a `mittente-destinatario` (RF-01).
- Nessun dato nuovo salvato nel browser (niente `localStorage`/cookie).
- Nessun `console.log` della risposta (contiene dati del cliente: numero ordine, nome file).
- Accessibilità come le tabelle esistenti (intestazioni `th`).
- Il plugin axios con log delle request intere e la SAS token in `nuxt.config` sono segnalati in
  `contesto/onetracking.md`: non si copiano né si estendono.

## 9. Criteri di accettazione

| # | Given / When / Then |
|---|---|
| AC-01 | Dato UC-01, nel tab "Mittente/Destinatario" compaiono, nell'ordine, "Informazioni LV", "Informazioni preavviso", "Dati file preavviso", "Dettaglio errori", "Cliente/Mittente/Destinatario" |
| AC-02 | Dato UC-01, le etichette delle colonne sono esattamente quelle della sezione 4 e i valori sono quelli di UC-01, con le date `10/11/2026 08:32` e `10/11/2026 08:47` |
| AC-03 | Dato UC-01, sotto "Dettaglio errori" c'è "3 errori riscontrati" e la tabella ha 3 righe nell'ordine della risposta; con un errore il testo è "1 errore riscontrato" |
| AC-04 | Dato UC-02, c'è "Dati file preavviso" con "File elaborato con successo" e non c'è "Dettaglio errori" |
| AC-05 | Dato UC-03, il blocco 4.1 ha la colonna Canale fra Numero colli e Preavviso con `WEBSERVICES`, e non c'è "Dati file preavviso" |
| AC-06 | Dati UC-01 e UC-02, il blocco 4.1 **non** ha la colonna Canale |
| AC-07 | Dato UC-04, c'è solo il blocco 4.1 con la LdV, `-` nelle colonne vuote e "Senza preavviso", senza Canale |
| AC-08 | Dato UC-05 (e anche con `400`, `500`, timeout), sotto "Informazioni preavviso" c'è "Dati preavviso non disponibili" e "Informazioni LV" e "Cliente/Mittente/Destinatario" si vedono |
| AC-09 | Dato UC-06, i valori `null` sono `-` |
| AC-10 | Data una data estiva `2026-07-15T08:47:00+02:00` e una invernale `2026-11-10T07:47:00Z`, a video `15/07/2026 08:47` e `10/11/2026 08:47`, con qualunque fuso del PC dell'operatore |
| AC-11 | Durante il caricamento la sezione mostra il messaggio di caricamento e il resto del tab è utilizzabile |
| AC-12 | La chiamata è `GET /api/preavviso/<ldv>` con la LdV codificata; parte una volta per apertura del tab; con LdV vuota non parte |
| AC-13 | In ricerca massiva, selezionando una riga e poi subito un'altra, la sezione mostra il preavviso dell'ultima riga selezionata |
| AC-14 | Una nuova ricerca azzera la sezione: non resta il preavviso della LdV precedente |
| AC-15 | La sezione si vede con ogni tipologia utente (ASSISTENZA, SDA, FILIALI) che ha il tab "Mittente/Destinatario", senza chiavi `OTR_*` nuove |
| AC-16 | Gli altri tab e l'export PDF/Excel del tab "Mittente/Destinatario" funzionano come prima |
| AC-17 | Nella console del browser non compare la risposta dell'API |

## 10. Casi di test

Il repo non ha un test runner configurato (`test/` vuoto, nessuno script `test` in `package.json`):
i casi si eseguono a mano in locale (con il back-end in locale o un mock dell'API) e poi in svil.
Le funzioni pure di `utils/preavviso.js` si possono provare anche da console Node.

| TC | Ambiente | Preparazione | Verifica | AC |
|---|---|---|---|---|
| TC-01 | locale, mock API | risposta di UC-01 | ordine dei blocchi, etichette, valori, date, "3 errori riscontrati" | AC-01…AC-03 |
| TC-02 | locale, mock API | UC-01 con un solo errore | "1 errore riscontrato" | AC-03 |
| TC-03 | locale, mock API | UC-02 | nessun "Dettaglio errori", niente Canale nel 4.1 | AC-04, AC-06 |
| TC-04 | locale, mock API | UC-03 | Canale fra Numero colli e Preavviso, nessun blocco file | AC-05 |
| TC-05 | locale, mock API | UC-04 | solo 4.1, `-`, "Senza preavviso" | AC-07 |
| TC-06 | locale, mock API | `503`, `400`, `500`; ritardo di 61 s (timeout) | messaggio di RV-06, resto del tab visibile | AC-08 |
| TC-07 | locale, mock API | UC-06 | `-` dove `null` | AC-09 |
| TC-08 | locale | fuso del PC su UTC e su Europe/Rome; date estive e invernali | formati di AC-10 | AC-10 |
| TC-09 | locale, mock API con ritardo di 3 s | apertura del tab | messaggio di caricamento, tab utilizzabile | AC-11 |
| TC-10 | locale, strumenti del browser | apertura del tab; LdV vuota | una sola chiamata, URL atteso | AC-12 |
| TC-11 | locale, mock API con ritardi diversi per LdV | ricerca massiva, due selezioni ravvicinate | vince l'ultima selezionata | AC-13 |
| TC-12 | locale | due ricerche consecutive | sezione azzerata | AC-14 |
| TC-13 | svil | header SiteMinder simulati (ModHeader) con `x-forwarded-server` `-SDA`, `-FILIALI`, assistenza | sezione visibile in tutti e tre | AC-15 |
| TC-14 | svil | export PDF/Excel del tab, altri tab | invariati | AC-16 |
| TC-15 | svil, back-end vero | LdV di test dei tre casi del mock up e una senza preavviso (AS-24) | come UC-01…UC-04 | AC-01…AC-07 |
| TC-16 | locale | console del browser durante TC-01 | nessuna stampa della risposta | AC-17 |

## 11. Assunzioni e domande aperte

Da `analisi.md`:

| ID | Assunzione adottata | Da confermare con |
|---|---|---|
| AS-01 | **Chiusa (13-11, Diego)**: il preavviso lo sceglie il back-end su `event_type` (`COMPLETED`, il più recente; altrimenti il penultimo per `event_ts`). Il front-end mostra quello che riceve | — |
| AS-02 | Numero ordine = `code_externalId` | Poste / Diego |
| AS-03 | Canale del preavviso non da file: campo non nell'ICD; se manca a video `-` | Poste |
| AS-04 | Formato di `preadv_errori` non descritto nell'ICD: lo interpreta il back-end | Poste (team T&T-Repo) |
| AS-05 | Data stato del file = `_lastupdate_` di `pacchi_file` | Poste |
| AS-06 | Nessuna funzionalità di profilazione nuova (`OTR_*`) | Poste |
| AS-07 | Si parte da `origin/develop` | — |

Nuove (Mary, 13-11). AS-08…AS-16 e AS-22…AS-24 sono descritte in [shipment-info.md](shipment-info.md),
sezione 12; qui quelle che toccano il front-end.

| ID | Assunzione o domanda | Default adottato | Da confermare con |
|---|---|---|---|
| AS-08 | **Path**: contratto `GET /api/preavviso/{ldv}`; il proxy toglie `/api` | FE chiama `/api/preavviso/{ldv}`, BE mappa `/preavviso/{ldv}`. **Da allineare subito con la sviluppatrice back-end** | Diego, sviluppatrici |
| AS-09 | **Canale del file**: il mock up mostra `INVIOFILE`, l'ICD e il contratto `Invio File` | si mostra il valore ricevuto, senza transcodifica | Poste |
| AS-10 | **"Senza preavviso" con preavviso presente** se il T&T-Repo non ha ancora lo stato della LdV | si mostra quello che arriva | Diego / Poste |
| AS-17 | **Tipologia utente**: nell'export del tab "Informazioni LV" è riservata agli utenti ASSISTENZA (commento in `IndexRicerche.vue`: "VEDONO LA SEZIONE SOLO GLI UTENTI ASSISTENZA E NON SDA/FILIALI"); a video `DatiCliente.vue` non ha condizioni sulla tipologia. La sezione preavviso è per l'assistenza clienti (slide 2) | visibile a chiunque veda il tab, come a video "Informazioni LV" (AS-06) | Poste |
| AS-18 | **Export PDF/Excel** del tab "Mittente/Destinatario": il mock up non ne parla | la sezione preavviso non entra nell'export in questa versione | Poste |
| AS-19 | **Tipo di ricerca**: il mock up dice "raggiungibile ricercando per LdV". Il tab "Mittente/Destinatario" si apre anche da altre ricerche e dalla ricerca massiva | la sezione c'è in ogni dettaglio LV, per la LdV selezionata | Poste |
| AS-20 | **Tab con "Dati non presenti"**: se `mittente-destinatario` non restituisce dati (o va in timeout) il tab mostra solo il messaggio e oggi non renderizza `DatiCliente`/`InfoMittenteDestinatario`. Una LdV con preavviso ma non ancora nei sistemi SDA è proprio un caso utile all'assistenza | la sezione preavviso si mostra **anche** in quel ramo, sotto il messaggio | Diego |
| AS-21 | **Quando è "da file"**: la slide 2 dice "solo se il preavviso proviene da file (INVIOFILE, INVIOEASY, STAMPA MASSIVA)"; l'ICD di `pacchi_file` ha anche `Invio System` e `Web` | il blocco file c'è quando l'API restituisce `file`, qualunque sia il canale | Poste |
| AS-23 | **Attribuzione dei DREQ** ai blocchi | tabella della sezione 2 | Poste / Diego |
| AS-24 | **Dati di test** in svil/collaudo per i tre casi | da costruire con la catena preadvising di svil | Diego / test manager |

## 12. Riferimenti

- [analisi.md](../analisi.md): regole, mapping, contratto.
- [shipment-info.md](shipment-info.md): API, regola di scelta, decodifiche, esempi di risposta.
- [contesto/onetracking.md](../../../contesto/onetracking.md): architettura, proxy, autenticazione SiteMinder.
- Mock up: `cliente/Recupero_risottomissione_preadvising_bozza_v0.8.pptx`, slide 2 (obiettivo), 3 (caso 1), 4 (caso 2), 5 (caso 3).
