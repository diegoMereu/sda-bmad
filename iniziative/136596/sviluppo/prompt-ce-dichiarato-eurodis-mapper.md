# Prompt — documento funzionale `ce-dichiarato-eurodis-mapper`

> Prompt per Mary (analyst): genera il documento funzionale del microservizio
> `ce-dichiarato-eurodis-mapper` (iniziativa 136596).
> Output: `iniziative/136596/sviluppo/ce-dichiarato-eurodis-mapper.md`, da
> passare ad Amelia (dev) per lo sviluppo.
> Regola di progetto: un documento funzionale per microservizio.

---

# Contesto

Sei l'Analyst del progetto. Devi scrivere il **documento funzionale per lo
sviluppatore** del microservizio `ce-dichiarato-eurodis-mapper`, nell'iniziativa
136596 "Eurodis autoproduttore".

Catena: `receive-pan` → `ce-dichiarato-eurodis-in` → `preadvising.eud.pre.build`
→ **`ce-dichiarato-eurodis-mapper`** → `preadvising.pre-enrichment` →
`ce-dichiarato-ldv-pdb-sync` → PDB `waybillCreate`.

Il mapper riceve **una spedizione EURODIS per messaggio**, così come EURODIS
l'ha restituita, e la converte nel tracciato unico ICD v11. È l'unico punto
della catena in cui vive il mapping (decisione del 30-10).

Il servizio esiste ed è in ambiente svil: copre circa 10 dei 73 campi da
valorizzare e il 05-11 Diego ha visto in ambiente un output troppo povero.
Il documento deve permettere ad Amelia di completarlo senza aspettare le
risposte aperte, con un default per ogni punto aperto.

# Fonti (tutte in `iniziative/136596/`)

- `ICD_PREADVISING_LDV_EVENT_SOURCE_v11.xlsx`, fogli "Mapping EURODIS" (regola
  per ogni campo ICD) e "Mapping inverso EURODIS" (colonna Commenti di Diego):
  **è la fonte delle regole di mapping**.
- `sviluppo/verifica-mapper-2026-11-04.md`: cosa fa oggi il codice, cosa manca,
  incongruenze tra le fonti.
- `sviluppo/rapporto-amelia-2026-11-02.md`, rilievi MAP-1…MAP-8.
- `sviluppo/ce-dichiarato-eurodis-in.md`, sezione 3.2: contratto del messaggio
  in ingresso (corpo, chiave, header).
- `accessori-eurodis-pdb-proposta.md`: servizi accessori nel formato PDB.
- `analisi.md` (PA-nn), `punti-aperti-analisi-2026-10-23.md` (DF-nn), `PUNTO.md`.
- `esempio-eud-inviofile.json`: forma del tracciato nel flusso EUD esistente.
- `esempio-eurodis-spedizione.json`: spedizione dell'ambiente TEST EURODIS
  (dati di fantasia), passata da Diego il 05-11 con l'output attuale del mapper.

# Cosa ti chiedo

Scrivi il documento in italiano, con la stessa struttura e le stesse etichette
([FATTO], [IPOTESI], [DECISO], [DA DECIDERE]) del documento di
`ce-dichiarato-eurodis-in`:

1. Scopo e responsabilità: cosa fa e cosa **non** fa (scarico, storico,
   deduplica, chiamate a F1 e ce-rules finché PA-33 è aperto).
2. Posizione nella catena.
3. Interfacce: messaggio in ingresso (corpo, chiave, header di `-in`) e in
   uscita (topic, chiave, header, forma del tracciato).
4. Flusso di elaborazione.
5. Regole funzionali generali (RF-nn).
6. **Regole di mapping per sezione del tracciato**, campo per campo, con
   sorgente EURODIS, regola e riferimento al punto aperto. Ricondurle tutte al
   foglio; quello che il foglio lascia DA DEFINIRE ha un default esplicito.
7. Gestione errori: messaggio non leggibile, `edReference` assente, spedizione
   incompleta (per esempio destinatario assente), errore tecnico, Kafka giù.
8. Configurazione, 9. Osservabilità, 10. Requisiti non funzionali.
11. Criteri di accettazione Given/When/Then, con l'**output atteso per la
    spedizione di esempio** del 05-11.
12. Punti aperti e default provvisori, 13. Riferimenti, domande per Diego.

# Regole

- Non inventare regole: se il foglio, una decisione o un commento di Diego non
  la danno, è DA DECIDERE con una proposta.
- Le decisioni di Diego valgono anche quando creano un problema a valle: si
  applicano e il problema si segnala come domanda.
- Nessun dato di produzione negli esempi; nessun dato personale nei log.
- Lo sviluppo deve poter partire subito: ogni punto aperto ha un default.
