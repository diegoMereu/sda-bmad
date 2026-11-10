# 136596 — Integrazione con `ce-dichiarato-ldv-pdb-sync` e catena degli span

**Autore**: Winston (architect), con Amelia (dev) · **Data**: 2026-11-10
**Richiesta di Diego**: oltre la normalizzazione va mandato un evento verso
`ce-dichiarato-ldv-pdb-sync`; verificare se funziona con l'oggetto che inviamo. Il contesto di
tracing deve partire dal mapper e ricollegarsi al validatore.

## In sintesi

- **L'evento verso `ldv-pdb-sync` non lo manda il mapper: lo manda l'orchestratore**, con l'azione
  `ldv-bep-sync` sul topic `preadvising.enrichment.bepsync`, come già fa per `EUD_INVIOFILE`.
- **Oggi l'orchestratore manda `EUD_INVIOSYSTEM` a `ldv-pdb`**, cioè a `ce-dichiarato-ldv-pdb`: commit
  `23bf1dd` di azzurrazezza del 10-11. Quel servizio non riconosce i canali `EUD_*`, quindi la
  spedizione si fermerebbe lì. Correzione pronta sul branch `feature/eurodis-canale-eud-inviosystem`
  dell'orchestratore (`a1a3732`).
- **Con l'oggetto di oggi `ldv-pdb-sync` non funzionerebbe per l'autoproduttore**: non passa a PDB la LDV
  che arriva da EURODIS, così PDB ne genera una nuova, e poi sovrascrive `collo.id_ldv` con quella di
  PDB. Correzione pronta sul branch `feature/eurodis-autoproduttore-ldv` di `ldv-pdb-sync` (`10726dd`),
  partito da `svil_eurodis`.
- **Altri due bloccanti, di configurazione**: in svil il codice contratto è vuoto sia nel tracciato sia
  nella configurazione di `ldv-pdb-sync`; sul ramo `svil_eurodis` l'URL di PDB è un segnaposto.
- **Tracing**: la catena è già coerente, tutta in W3C `traceparent` da `-in` fino a `ldv-pdb-sync`. Non
  servono modifiche al codice; resta da verificare in Datadog durante i test integrati.

## Aggiornamento del 10-11 sera: percorso deciso `ldv-pdb` (Diego)

**[DECISO 10-11, Diego]** Per `EUD_INVIOSYSTEM` l'orchestratore resta come l'ha configurato
azzurrazezza (`23bf1dd`): normalizzazione → enrichment_bep → **`ldv-pdb`**, cioè
`ce-dichiarato-ldv-pdb`. La proposta qui sotto di passare a `ldv-bep-sync` è **superata**:
- il branch dell'orchestratore `feature/eurodis-canale-eud-inviosystem` (`a1a3732`, verso
  `ldv-bep-sync`) **non va mergiato**; anche il commit `2d65031` su `develop` è stato annullato;
- `ce-dichiarato-ldv-pdb` è un progetto distinto da `ldv-pdb-sync` (repo
  `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-ldv-pdb`, immagine `ce-dichiarato-ldv`; `ldv-pdb-sync` ha
  immagine e chart propri). Le correzioni per EURODIS sono sul branch
  **`feature/eurodis-canale-eud-inviosystem`** di `ce-dichiarato-ldv-pdb`, commit **`07c13d0`**, partito
  da `develop`:
  - `BepChannel.fromCanale` toglie anche il prefisso `EUD_`: `EUD_INVIOSYSTEM` → `INVIOSYSTEM`,
    `EUD_INVIOFILE` → `INVIOFILE` (prima andava in eccezione). Con `INVIOSYSTEM` la LDV del collo
    (`collo.id_ldv`, da `deliveryPartnerBarcode`) passa a BEP come `code`, come per `PDB_INVIOSYSTEM`;
  - `BepResponseMapper`: con `flag_autoproduttore = S` la LDV già presente sul collo non si sovrascrive
    con quella della response (stessa logica di `10726dd` su `ldv-pdb-sync`); negli altri casi il
    comportamento non cambia;
  - test: `BepChannelTest`, `BepResponseMapperAutoproduttoreTest`, `BepRequestMapperTest` (caso
    `EUD_INVIOSYSTEM`); suite completa 386 verdi.
- È un repository di un altro team: va in merge request su `develop` e poi rilasciato in svil.
- Il branch `feature/eurodis-autoproduttore-ldv` di `ldv-pdb-sync` (`10726dd`) resta utile solo se
  `EUD_INVIOSYSTEM` passasse un giorno da `ldv-bep-sync`.
- Restano validi i punti di configurazione (codice contratto e centro di costo EURODIS, in corso dal
  builder → mapper) e la verifica in svil della codifica del paese.

## 1. Chi riceve cosa

| Servizio | Topic in ingresso | Ruolo |
|---|---|---|
| `ce-dichiarato-eurodis-mapper` (nostro) | `preadvising.eud.pre.build` | spedizione EURODIS → tracciato unico, su `preadvising.pre-enrichment` |
| `ce-dichiarato-validatore` | `preadvising.pre-enrichment` | validazione, poi `preadvising.enrichment`. Il supporto al canale `EUD_INVIOSYSTEM` lo sta verificando il Test Manager (branch locale `feature/eurodis-canale-eud-inviosystem`) |
| `ce-dichiarato-orchestratore` | `preadvising.enrichment` | esegue i passi configurati per canale (`azioni.mappings`), poi `preadvising.completed` |
| normalizzatore | `Preadvising.enrichment.normalizzatore` | passo `normalizzazione` |
| `ce-dichiarato-ldv-pdb` | `preadvising.enrichment.pdb` | passo `ldv-pdb`: canali `PDB_*`, flusso asincrono verso BEP |
| **`ce-dichiarato-ldv-pdb-sync`** | **`preadvising.enrichment.bepsync`** | passo `ldv-bep-sync`: chiamata REST sincrona a PDB `waybillCreate` (canale EURODIS), risposta su `preadvising.enrichment` con `tipo_lavorazione = ldv-bep-sync` |

Il 10-11 extaciq ha scritto che il servizio di integrazione con BEP è `ce-dichiarato-ldv-pdb` e non il
`-sync`. Per i canali `PDB_*` è vero. Per EURODIS invece il servizio giusto è `ldv-pdb-sync`:
`ldv-pdb` risolve il canale con `BepChannel.fromCanale`, che toglie il prefisso `PDB_` e poi fa
`valueOf`, quindi con `EUD_INVIOSYSTEM` lancia eccezione.

Passi dell'orchestratore per canale (`application.yaml`, branch `develop`):

| Canale | Oggi | Proposto |
|---|---|---|
| `EUD_INVIOFILE` | normalizzazione, enrichment_bep, ldv-bep-sync | invariato |
| `EUD_INVIOSYSTEM` | normalizzazione, enrichment_bep, **ldv-pdb** | normalizzazione, enrichment_bep, **ldv-bep-sync** |

`enrichment_bep` non ha un topic di instradamento: l'orchestratore lo salta senza errore. Nel merge
esclude anche `mittente/destinatario.codice_nazione`.

## 2. Contratto in ingresso di `ldv-pdb-sync`

- **Topic**: `preadvising.enrichment.bepsync`. Chiave non usata. Header: contesto W3C (`traceparent`),
  letto da `TraceUtil.extractContext`.
- **Corpo**: `TracciatoUnicoDTO`, con proprietà sconosciute ignorate e campi `null` omessi.
- **Esito**: il tracciato arricchito torna su `preadvising.enrichment` con `result` OK/KO, `id_ldv`,
  `pdf_ldv`, `paperless`. Un KO non solleva eccezione: lo gestisce l'orchestratore.
- **Branch**: `develop`, `master` e `svil_eurodis` divergono. `svil_eurodis` è il più avanti per EURODIS
  (canale `WEBSERVICE`, `fileName`, `shipmentDate`, pesi interi) e contiene `develop` fino al merge
  `5364f30`. Va chiarito quale branch è deployato in svil.

## 3. Compatibilità con il tracciato del mapper (output AC-01, dopo la normalizzazione)

| Campo usato da `ldv-pdb-sync` | Cosa mandiamo | Esito | Note |
|---|---|---|---|
| `collo.id_ldv` → `declared.code` | LDV EURODIS da `deliveryPartnerBarcode` | **bloccante, corretto su branch** | oggi `code` è sempre `null`: PDB genera una LDV nuova invece di registrare quella di EURODIS. Il branch `10726dd` la passa quando `flag_autoproduttore = S` |
| risposta PDB → `collo.id_ldv` | — | **bloccante, corretto su branch** | oggi la LDV restituita da PDB sovrascrive quella di EURODIS; il branch non sovrascrive una LDV già presente |
| `cliente.codice_contratto` → `contractCode` | `""` (configurazione del mapper vuota) | **bloccante (configurazione)** | ripiego su `PDB_SYNC_CONTRACT_CODE`, oggi vuoto in svil su `develop` e segnaposto su `svil_eurodis`. Serve il codice contratto EURODIS, in uno dei due servizi |
| `spedizione.centro_costo` | `""` | degradato | ripiego su `PDB_SYNC_COST_CENTER_CODE`, vuoto in svil |
| `rif_prodotto_cliente` → `product` | `""` | ok | ripiego su `PDB_SYNC_PRODUCT` = `APT000901` |
| URL PDB | — | **bloccante su `svil_eurodis`** | `PDB_SYNC_URL` è un segnaposto; su `develop` è valorizzato |
| `codici_servizi` (spedizione, poi radice) | `APT000918` più i servizi di consegna | ok | contrassegno: `amount` da `importo_contrassegno`, `paymentMode` da `tipo_pagamento_contrassegno` (`CON`); multicollo aggiunto da loro |
| `mittente` / `destinatario` → sender / receiver | campi diretti | ok, con riserva | **`country` = `codice_nazione`**: noi mettiamo l'ISO3 (`ITA`), come l'adapter; PDB secondo DF-12 vuole l'ISO4 (`ITA1`, in `codice_nazione_poste`), mentre l'esempio `EUD_INVIOFILE` ha l'ISO2. Da verificare nel primo giro in svil. Se PDB rifiuta, la correzione è in `ldv-pdb-sync`: usare `codice_nazione_poste` |
| mittente assente (in TEST `shipperAddress` è null) | sender vuoto | degradato o KO | PDB probabilmente rifiuta un mittente vuoto; in produzione da verificare con EURODIS |
| peso, dimensioni | grammi, cm | ok | su `svil_eurodis` il peso è intero |
| `data_spedizione` → `shipmentDate` | `yyyy-MM-dd` | ok | solo su `svil_eurodis` |
| `progressivo` → `fileRecordOrder`; `id_preadvising` → `cdrId` | `1`, UUID | ok | |
| `segnacollo` / `id_collo` → `parcelLabel` | `""` | ok | la risposta si abbina per `cdrId` |
| Punto Poste, assicurazione, internazionale | non valorizzati | ok | fuori dalla fase 1 |

## 4. Proposta

1. **Orchestratore**: `EUD_INVIOSYSTEM` → `normalizzazione`, `enrichment_bep`, `ldv-bep-sync`.
   - Branch `feature/eurodis-canale-eud-inviosystem`, commit `a1a3732`, con test
     `EudInvioSystemAzioniTest`.
   - È una modifica di un repository di un altro team, quindi va in merge request.
2. **`ldv-pdb-sync`**: LDV dell'autoproduttore passata come `code` e non sovrascritta.
   - Branch `feature/eurodis-autoproduttore-ldv`, commit `10726dd`, partito da `svil_eurodis`, test
     `AutoproduttoreLdvTest` (5).
   - Anche questa va in merge request.
3. **Configurazione**: codice contratto e centro di costo EURODIS in `PDB_SYNC_*`, oppure nel mapper
   (`MAPPER_CLIENTE_CONTRATTO`, `MAPPER_CENTRO_COSTO`); URL PDB reale sul branch deployato.
4. **Nessuna modifica al mapper**: il tracciato contiene già tutto quello che `ldv-pdb-sync` legge. Resta
   da verificare in svil la codifica di `country`.

## 5. Catena degli span

Tutti i servizi usano il contesto W3C (`traceparent`) negli header Kafka:

| Salto | Legge | Scrive |
|---|---|---|
| `-in` → `preadvising.eud.pre.build` | — (radice: job di elaborazione) | `traceparent` dallo span PRODUCER |
| mapper | `TraceUtil.estraiContesto`: lo span consumer è figlio di `-in` | `PreEnrichmentProducer`: `traceparent` dallo span PRODUCER |
| validatore | `TraceUtil.extractContext` (W3C) | `injectContext` sul record di uscita |
| orchestratore | `extractContext` (W3C), con ripiego su un contesto sintetico dall'header `trace-id` | `popolateHeader` → `injectContext` su ogni passo instradato, compreso `bepsync` |
| `ldv-pdb-sync` | `TraceUtil.buildSpan` → `extractContext` (W3C) | `injectContext` sull'uscita `preadvising.enrichment` |

La traccia è quindi unica dallo scarico di `-in` fino a `ldv-pdb-sync` e a `preadvising.completed`.
L'agent Datadog (`dd-java-agent`) propaga di default anche `tracecontext`. Verifica: nei test
integrati, cercare in Datadog un solo `trace_id` per un `edReference` di prova dal mapper al
validatore.
