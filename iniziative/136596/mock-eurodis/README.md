# Mock API EURODIS `receive-pan` (136596)

Mock in Python (FastAPI) dell'API `receive-pan`, per testare `ce-dichiarato-eurodis-in`
senza l'ambiente TEST EURODIS. Schema: `../eurodis-receive-pan-swagger-v1.json`.

## Avvio

```
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn mock_eurodis.app:app --port 8080
.venv\Scripts\python -m pytest
```

## Endpoint

| Endpoint | Comportamento |
|---|---|
| `GET /receive-pan/shipments/v1` | Restituisce le spedizioni nuove e le segna consegnate (nessun ack). `404` se non ce ne sono, `401` senza chiave valida |
| `GET /receive-pan/shipment/{edReference}/v1` | Rilettura puntuale. `400`, `404`, `451` (spedizione di un altro partner) |
| `GET /admin/prodotti` | Elenco prodotti configurati (solo mock) |
| `POST /admin/genera?prodotto=X&n=5` | Aggiunge spedizioni alla coda (solo mock) |
| `POST /admin/reset` | Svuota stato e contatori (solo mock) |

Header `X-API-Key`: chiavi in `config/prodotti.yaml` (`test-key-sda`, `test-key-altro`).
Lo stato (coda, contatori LDV) è salvato in `stato.json`, così dopo un riavvio le LDV non si ripetono.

## Configurazione per prodotto: `config/prodotti.yaml`

Ogni prodotto eredita da `default` e ridefinisce solo ciò che cambia (tipo spedizione, servizio
di consegna, numero colli, paesi, contrassegno, dogana, ADR, PUDO, preavviso). Per un nuovo
prodotto si copia un blocco. `seed` decide cosa c'è in coda all'avvio.
Il blocco `anomalie` inietta errori con probabilità 0..1 (LDV vuota, duplicata, con check errato)
per i test negativi.

## LDV

La sintassi è in `ldv_default` (prefisso, cifre, check digit, alfabeto) ed è **provvisoria**:
in attesa della regola SDA (chiesta a Marzilli). Ogni LDV è generata da un progressivo persistente,
quindi univoca anche tra riavvii. Va nel campo `collis[].consignorsColloBarcode`.
Si può dare una sintassi diversa a un singolo prodotto con un blocco `ldv:` nel prodotto.

## Dati

- **Reali**: strade, CAP, città, province e nazioni in `data/indirizzi.yaml`, coerenti tra loro
  (il test verifica il formato del CAP per paese). Luoghi pubblici, nessuna anagrafica di cliente.
- **Generati**: nomi, ragioni sociali, telefoni, email (`@example.com`), pesi, dimensioni,
  numeri spedizione, barcode EURODIS (24 cifre), IBAN di prova.
