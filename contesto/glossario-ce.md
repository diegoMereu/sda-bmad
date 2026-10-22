# Glossario di dominio — Corriere Espresso (CE)

Termini del dominio SDA/CE che compaiono negli artefatti delle tre factory.
Serve a non reinventare il significato di un campo a ogni campagna.

## Spedizione

| Termine | Significato |
|---|---|
| **LDV** | Lettera di Vettura. Documento che accompagna la spedizione; `id_ldv` è la chiave funzionale del dominio. |
| **LDV madre** | LDV che raggruppa più LDV figlie (spedizione multi-collo aggregata). Il campo `id_ldv_madre` esiste in alcune tabelle e non in altre: verificarlo per campagna, non assumerlo. |
| **Collo** | Unità fisica. Una LDV può avere più colli (`numero_colli`). |
| **Preadvising** | Preavviso di consegna: notifica al destinatario prima del tentativo. Il perimetro di 144208. |
| **Preavviso online** | Canale di preadvising verso il destinatario via web/app. |
| **Palmare / PTL** | Terminale in mano al corriere. Consuma i dati di preavviso smistati. |
| **DSX** | Sistema di supporto che consuma gli stessi dati dei palmari. |

## Consegna ed esiti

| Termine | Significato |
|---|---|
| **EAD** | Estimated Arrival Date — data stimata di consegna comunicata al destinatario. Campo `ead`. |
| **Mancata consegna** | Tentativo non andato a buon fine. Campo `mancata_consegna`. |
| **No firma** | Consegna senza raccolta firma. Campo `no_firma`; la sua semantica differisce fra legacy e nuovo (`DEF-144208-002`). |
| **Scarto** | Record respinto dal processo per dato non valido. Non compare nell'output: la sua assenza va letta come scarto, non come perdita. |
| **Fermo deposito / Casella postale** | Modalità di consegna alternative al domicilio. Campi `casellapostale_cliente`, `dest_vicino`. |

## Anagrafica e indirizzo

| Termine | Significato |
|---|---|
| **Intestatario** | Ragione sociale o nome sulla LDV (`mitt_intestatario`, `dest_intestatario`). |
| **Referente** | Persona fisica di contatto presso mittente/destinatario. |
| **Arricchimento anagrafica** | Completamento di `ragione_sociale`, `partita_iva`, `codice_fiscale` da anagrafica cliente. Assente nel nuovo (`DEF-144208-001`). |
| **CAP fittizio** | CAP convenzionale usato per località non normalizzate o estere. Non è un errore di dato: non trattarlo come difformità senza verificare la regola. |
| **Normalizzazione indirizzo** | Riscrittura di via/località/CAP secondo l'anagrafica postale. Divergenze qui sono `ATTESO`, non `FUNZIONALE`. |

## Prodotto e contratto

| Termine | Significato |
|---|---|
| **Servizio / Prodotto** | `id_servizio` (es. S09) e `id_prodotto` (es. XLP, SESP). La mappatura prodotto differisce fra i due sistemi (`DEF-144208-005`). |
| **Contrassegno** | Pagamento alla consegna. `importo_contrass`, `cod_tipo_pagamento`. |
| **Assicurato** | Copertura sul valore. `importo_ass`, `is_ass_percentuale`, `valore_dich`. |
| **Promo FLUS** | Promozione commerciale. Flag `flag_promo_flus`, non riconosciuto dal nuovo (`DEF-144208-007`). |
| **Contratto SDA / Poste** | `id_contratto_sda`, `id_contratto_poste`, `codice_cliente_sap`. |
| **Ufficio frazionario** | Unità organizzativa postale di riferimento. `cod_uff_frazionario`. |
| **VRID / Sortation / Origin** | Attributi di smistamento e instradamento. |

## Tabelle e flussi di 144208

| Oggetto | Ruolo |
|---|---|
| `sew_sped_pre_adv_online_out_tot` | output del sistema **legacy** (74 colonne) |
| `sew_sped_pre_adv_online_out_tot_2` | output del sistema **nuovo** (74 colonne, header identico) |
| `temp_palmari_check` (MongoDB) | collection di confronto palmari in tempo reale |
| `PSDA-20-04.SDA.EVENTTT.ANALDV` (Kafka) | topic di output verso i palmari SDA |
| `preadvising.completed.sda` (Kafka) | topic di preavviso completato, canali IF / MYSDA |

## Parallel run

Esecuzione in parallelo di legacy e nuovo sullo stesso input, per confrontarne
l'output prima del go-live. Due avvertenze di dominio:

- **Le due estrazioni non sono mai simultanee.** Un record presente in un solo
  sistema può essere un artefatto della finestra di estrazione, non un difetto.
  Per questo il perimetro è contabilizzato ma non concorre all'esito.
- **Un record in meno è peggio di uno in più.** Chiavi presenti solo nel legacy
  indicano dati che il nuovo *perde*; chiavi solo nel nuovo indicano più spesso
  un filtro di esclusione mancante. Non trattarle come lo stesso fenomeno.
