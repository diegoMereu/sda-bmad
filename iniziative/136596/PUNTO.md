# 136596 — EURODIS Autoproduttore

**Data**: 2026-11-09 · **Stato**: in_analisi · **Semaforo**: 🟡
**Owner cliente**: Piergentili · **PRJ**: non ancora assegnato

## In una riga
EURODIS ha risposto alle 13 domande: quasi tutte le assunzioni sono confermate, ma restano da chiarire in call errori e rifiuti, fuso orario e rimando dei dati. `-in` è pronto per il deploy in svil, il mapper è parziale, go-live atteso a fine gennaio 2027.

## Fatto dall'ultimo punto
- 2026-11-10 — **Decisioni e risposte di Diego**: la LDV del collo è `deliveryPartnerBarcode` (`consignorsColloBarcode` non si mappa, `europlateBarcode` vuoto o `0` → `""`), destinatario in `consigneeAddress` confermato (DF-02, DF-18, DF-30 chiusi); traduzione degli stati SDA → EURODIS per send-tracking dal foglio "Decodifica Eurodis IN-BOUND" (PA-34 chiuso); risposte EURODIS registrate in `risposte-eurodis-2026-11-10.md` (PA-05, PA-06, PA-09, PA-27 chiusi). Mapping Excel rigenerato, mapper 0.4, send-tracking 0.2.
- 2026-11-09 — **Risposte di EURODIS (via Chiapponi) e documento A03.2**: si riceve solo il non ancora ricevuto; modifiche e annullamenti non rilevano; nessun limite di chiamata; rilettura per `edReference` a 60 giorni; chiavi API senza rotazione; produzione = cambio di endpoint e chiave; dogana e ADR nel perimetro; rollout ibrido, settimana per settimana. Tutto in `assunzioni.md` (13 assunzioni, stato per ciascuna).
- 2026-11-09 — **EURODIS chiede di non rifiutare le spedizioni** e di riprendere il suo sistema di errori e rifiuti (A03.2): la mail di scarto concordata oggi è da riconsiderare.
- 2026-11-06 — Specifica di `-in` 0.5 (file fittizio per scarico, eventi ST_F0002/ST_F0005, header `idFile`) e del mapper 0.2/0.3 (LDV confermate, destinatario obbligatorio, codici nazione da `ce-anagrafica`, cliente da configurazione). Figure di SF e DP.
- 2026-11-05 — SF 0.2 e DP 0.1 per il cliente; client di `ce-eurodis-send-tracking` implementato; canale `EUD_INVIOSYSTEM` confermato da Diego.
- 2026-11-04 — `ce-dichiarato-eurodis-in` implementato (53 test verdi, `a53398c` su `feature/eurodis-base-implementation`); Dockerfile allineato.

## Prossimi passi
- Fissare la call con Chiapponi/EURODIS: errori e rifiuti (A03.2), come si chiede il rimando dei dati, rollout ibrido, `consigneeAddress` e LDV in produzione — Paolo — da fissare
- Verificare il fuso orario sui dati EURODIS del flusso FTP — Paolo — da definire
- Ricavare i volumi giornalieri dal flusso FTP — da assegnare — da definire
- Lanciare su Jenkins `ce-dichiarato-eurodis-in-build` e `-deploy` (svil, scarico disabilitato), poi verifica con Mongo e Kafka veri — Diego / Amelia — da definire
- Decidere se tenere una copia locale del grezzo e un interruttore di pubblicazione separato in `-in` — Diego / Amelia — da definire
- Chiedere all'altro gruppo come consegnare gli scarti al ms di invio mail e come funziona `send-pod` — Paolo — da definire
- Aggiornare i registri PA con le risposte di EURODIS (PA-05, 06, 09, 12, 13, 24, 27, 28) — Mary — da definire
- Completare la specifica del mapper e di send-tracking; sistemare i Dockerfile (AS-24) — Mary / Amelia — da definire
- Risposta di Marzilli sulla sintassi LDV — Marzilli — da definire

## Blocchi e rischi
- 🟡 Errori e rifiuti: EURODIS dice di non rifiutare, ma non è chiaro cosa significhi «riprendere» il loro sistema; senza chiarimento non si chiude PA-32 né la mail di scarto.
- 🟡 Perdita di un lotto tra la risposta HTTP e il salvataggio su Mongo: il recupero è un rimando totale su richiesta a EURODIS, ma il modo di chiederlo è da concordare.
- 🟡 `-in` mai avviato con Mongo e Kafka veri: la prima verifica reale è il deploy in svil.
- 🟡 Il destinatario (`consigneeAddress`) è `null` in TEST e LDV del collo vuota: EURODIS non ha detto se in produzione sono valorizzati.
- 🟡 Fuso orario dei timestamp non noto; sintassi LDV non nota (il mock genera LDV inventate).
- 🟡 Perimetro e PRJ non definiti: non si può stimare né pianificare. Go-live a fine gennaio 2027.
- 🟡 Il ms `ce-dichiarato-ldv-pdb-sync` è ancora in test e alcune osservazioni toccano i nostri dati.

## Serve dal cliente
- Codice PRJ.
- Call con Chiapponi/EURODIS su errori e rifiuti, rimando dei dati e rollout ibrido.
- Data di consegna della chiave API di produzione.
- Conferma che `deliveryPartnerBarcode` (la LDV del collo, schema non referenziato) è valorizzato in produzione. `consigneeAddress` confermato lato Poste il 10-11 (DF-30 chiuso).
- Regola di validità e univocità delle LDV SDA (chiesta a Marzilli).
- Conferma dei valori del contrassegno e di come arriva il nome del Punto Poste.
- Conferma se `centro_costo` e `rif_prodotto_cliente` sono costanti di contratto.
- Dall'altro gruppo: come si consegnano gli scarti al ms di invio mail e come funziona `send-pod`.

## Decisioni prese
- 2026-11-10 — Frequenza: in produzione scarico ed elaborazione ogni 10 minuti (EURODIS consiglia 15-20), in svil e coll restano 2 minuti. LDV del collo = `deliveryPartnerBarcode`. Stati di tracking tradotti con il foglio "Decodifica Eurodis IN-BOUND", eventi di collo.
- 2026-11-09 — Scarico ogni 2 minuti, nonostante EURODIS consigli 15-20. Storico arretrato della prima chiamata elaborato tutto. Rilettura per `edReference` solo come recupero manuale (già implementata). Chiave API in secret OpenShift.
- 2026-11-09 — Scarti: mail come in `EUD_INVIOFILE` tramite il ms esistente dell'altro gruppo, insieme agli errori di `INVIOFILE`; **da riconsiderare** dopo la risposta di EURODIS.
- 2026-11-06 — Mapper senza F1: cliente e contratto da configurazione per ambiente, codici nazione da `ce-anagrafica`, ce-rules a valle (chiude PA-33). `consignorsColloBarcode` → `collo.id_ldv` confermato (superato il 10-11: la LDV è `deliveryPartnerBarcode`). Ogni scarico è un file fittizio con `idFile`.
- 2026-11-05 — Canale `EUD_INVIOSYSTEM`. Tracking nel perimetro: tre ms, un documento funzionale ciascuno.
- 2026-11-04 — Spring Boot 3.5.14 per tutta la catena. `-in` in due fasi, grezzo su Mongo, nessun filtro duplicati, nessun endpoint applicativo. Contratto su `preadvising.eud.pre.build`: corpo = spedizione così com'è, chiave `edReference`.
- 2026-10-30 — Due livelli di ingestione: `-in` legge, salva e scompone; il mapper converte nell'ICD. Il mapping vive solo nel mapper.
- 2026-10-29 — Mock dell'API in Python (FastAPI). Test integrati solo su `receive-pan`. Catena: lettura API → mapping → ms sync → PDB `waybillCreate`.
- 2026-10-22 — Analisi prima di PRD e stima. Il ms di raccolta salva lo storico. Prodotto e servizi dalla LDV con ce-rules (rivista il 29-10). Contratto, codice cliente e AUC da F1 (rivisto il 06-11). Nessun troncamento dei campi lunghi. `id_preadvising` = UUID. `europlateBarcode` → `internazionale.id_ldv_itz`.
