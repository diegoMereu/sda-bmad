# 136596 — Verifica del mapper rispetto alle decisioni (04-11)

**Autrice**: Amelia (dev), in sola lettura · **Destinataria**: Mary, che la usa per scrivere la
specifica di `ce-dichiarato-eurodis-mapper`
**Repository**: `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper`, branch
`feature/eurodis-base-implementation`, commit `beb8fd6`. Test `mvn test`: **13/13 verdi**.
**Fonti confrontate**: foglio "Mapping EURODIS" (ME rN) e "Mapping inverso EURODIS" (MI rN, colonna
Commenti di Diego), `analisi.md`, `punti-aperti-analisi-2026-10-23.md`,
`accessori-eurodis-pdb-proposta.md`, `PUNTO.md`, `esempio-eud-inviofile.json`, specifica di `-in` §3.2.

## Esito

Il mapper copre circa **10 dei 73 campi** DIRETTO/TRASFORMATO/COSTANTE/GENERATO, e quelli che copre
seguono la regola giusta. Mancano quasi tutte le regole già decise: mittente, destinatario, date,
pesi, `no_firma`, note, contrassegno, costanti. C'è anche un **bug**: con `collis: null` va in
NullPointerException.

## Implementato e conforme

`progressivo` = 1, `versione_tracciato` = 1, `flag_autoproduttore` = "S", `id_preadvising` UUID,
`rif_spedizione` = `edReference` senza decimali, `numero_colli`, `collo[].id_ldv` ←
`consignorsColloBarcode`, `internazionale.id_ldv_itz` ← primo `europlateBarcode` non vuoto
(provvisorio, DF-03), `canale` configurabile con default `EURODIS` (DF-04 aperto). Topic e
at-least-once conformi. Nessun dato personale nei log.

## Mancante o divergente

| Campo / decisione | Cosa fa il codice | Gravità | Bloccato da |
|---|---|---|---|
| `mittente.*` e `destinatario.*` DIRETTI senza troncamento (cap e località del destinatario obbligatori ICD) | assenti | alta | — |
| `codice_nazione_iso_2` ← `countryCode`, solo lì; `cellulare` ← `contactSMS` intero | assenti | alta | — |
| `data_spedizione` (yyyy-MM-dd) e `ora_spedizione` da `entranceTimestamp` | assenti; il DTO non ha i timestamp | alta (obbligatoria per BEP) | fallback DF-01 |
| `collo.peso` ×1000, dimensioni, `numero_colli_parz`; `internazionale.peso` ×1000 | assenti | alta (obbligatori per BEP) | — |
| Convenzione EUD: stringhe `""` e importi `0` su tutta la struttura | DTO con 8 campi, `NON_NULL` omette il resto | alta | — |
| **`collis: null`** | NPE (`EurodisToIcdMapper.java:56/66`), poi i tentativi di default di Spring e il messaggio saltato | **alta (bug)** | — |
| Messaggi non validi: nessuna DLT; nessun `DefaultErrorHandler` esplicito | scarto con log | alta | PA-32 |
| `id_preadvising` casuale + at-least-once: rielaborando arrivano due preadvising (MAP-2) | — | alta | da decidere. NB: dal 04-11 anche `-in` non filtra i duplicati |
| `cliente.ragione_sociale`, `id_ldv_partner_master` (MAP-6), `cliente.no_firma`, `contrassegno.flag` | assenti | media | — |
| `consegna.data_consegna`, orari, `consegna.note` (concatenazione) | assenti | media | separatore della concatenazione non specificato |
| COSTANTI `flag_stampa_ldv`="N", `flag_attivazione_ritiro`="N", `internazionale.vettore`="EURODIS" | assenti | media | — |
| Header di `-in` (`ricevutoIl` → `upload_time`, `idEsecuzione` → `id_file`, `rifGrezzo` → `link_file_fisico_inviato`) | il consumer non legge né header né chiave | media | contratto deciso il 04-11 (D2): ora si può fare |
| `contrassegno` importo e tipo, `codici_servizi`, Punto Poste | assenti | media | DF-24, PA-03, DF-14/23 |
| `id_ldv_associata`, `tipo_collo`, madre e figlio, `id_collo` | assenti | — | DF-10, PA-11 |
| Dogana e articoli | assenti | bassa | PA-13, PA-22 |
| `edReference.toBigInteger()` tronca un decimale ≠ 0 (MAP-5) | — | bassa | — |
| Riferimenti PA/DF nei commenti del codice (MAP-7) | presenti in 8 file | bassa | — |

## Implementabile subito, in ordine

1. Bug `collis` null.
2. DTO completi con convenzione `""`/`0`.
3. Mittente e destinatario.
4. Date da `entranceTimestamp`.
5. Collo e pesi.
6. `cliente.ragione_sociale`, `id_ldv_partner_master`.
7. `no_firma`, `contrassegno.flag`.
8. Consegna (dopo aver fissato il separatore).
9. Costanti.
10. Error handler con backoff, MAP-5, MAP-7.
11. Lettura degli header di `-in`, ora che il contratto è deciso.

## Incongruenze tra le fonti, da sciogliere nella specifica del mapper

- **Codice nazione**:
  - analisi Note 4 ed esempio EUD: ISO2 in `codice_nazione`;
  - Diego ed Excel: solo in `codice_nazione_iso_2`;
  - il ms sync legge `codice_nazione`, quindi con la regola di Diego gli arriva vuoto (DF-12/27).
- **`progressivo`**: per il foglio è "1..n nel batch", per il codice è 1 per messaggio.
- **`id_file`**: per l'Excel è GENERATO, per analisi PA-15 è ancora aperto.
- **`dataInizioFlusso` / `instantInizioFlusso`**: nessun header di `-in` porta l'inizio del batch. Possibile proposta: `avviatoIl` dello scarico.
- **`pudoID`**:
  - Diego: "da non mappare, gravità bassa";
  - Excel e proposta accessori: APT000947 e `codice_frazionario`.
- **Prodotto e servizi**:
  - Diego: ce-rules con `id_ldv`;
  - proposta del 29-10: `codici_servizi` nel mapper.
- **Data di spedizione**:
  - Diego: `entranceTimestamp`;
  - riscontro SDA: `clearanceTimestamp` (DF-01).
- **Preavviso**:
  - DF-09: true→S, false→N;
  - proposta: non si mappa;
  - Excel: DA DEFINIRE.
- **Assicurazione**:
  - DF-08: importo da `commercialValueOfGoods`;
  - proposta ed Excel: fuori perimetro.
- **Dimensioni ICD**: `data_spedizione` 8 (yyyy-MM-dd = 10), `id_preadvising` 15 (UUID = 36), `id_ldv_associata` 3 (barcode = 24), `valore` dichiarato string ma con valore numerico nell'esempio.
- **Troncamento**: la Legenda Excel cita il "troncamento" tra le trasformazioni, contro PA-16.
- **`codici_servizi`**: nell'ICD è in `spedizione`, nell'esempio alla radice.
