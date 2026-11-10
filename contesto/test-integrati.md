# Test integrati in svil

Ruolo: il test manager definito in `C:\Users\diego.mereu\testfactory\processi\agents\test-manager.md`
(pianifica, delega l'esecuzione, fa il triage, firma lo stato). `testfactory` è solo riferimento:
gli artefatti stanno in `iniziative/<id>/test/`.

## Artefatti

- `CAMPAGNA.md`, `TEST-LIST.md` (casi `TC-<id>-nnn`, dati usati), `STORICO.md` (run
  `RUN-<id>-<ts>` con esito per caso).
- `triage/DEF-<id>-nnn.yaml` (difetti, dopo triage esplicito: difformità ≠ difetto) e
  `triage/BLOCCO-<id>-nnn.yaml` (blocchi di ambiente o di dati).
- Commit e push di ogni run e triage appena prodotti.

## Regole

- Mai scrivere su produzione.
- Consumer Kafka in sola lettura: senza group id (assign + seek) o con un group id nuovo dedicato;
  mai committare offset dei gruppi dei servizi.
- Iniezione consentita solo in svil, con dati inventati e chiavi riconoscibili (es. prefisso `99`),
  rispettando chiave e header del contratto del topic.
- EURODIS TEST restituisce sempre gli stessi dati: i casi particolari e di errore si costruiscono
  (iniezione sui topic, mock locale dell'API, es. `iniziative/136596/mock-eurodis/`).
- Correlare i messaggi lungo la catena per chiave, `rif_spedizione`, `id_file`.
- Verificare anche la copertura dei campi: confrontare i campi valorizzati con quelli di un canale
  già in esercizio (es. PDB, `EUD_INVIOFILE`).
- Evidenze con dati personali solo nello scratchpad; nel repo solo nomi di campo, conteggi, esiti.

## Strumenti

- venv Python nello scratchpad con `kafka-python`; script di lettura degli ultimi N messaggi per
  topic (stampa solo campi non personali).
- Database e cluster spesso non raggiungibili dalla postazione: vedi [ambienti.md](ambienti.md).

## Esito

Al primo difetto che richiede un rilascio o un blocco che solo Diego può sciogliere: report con cosa
rilasciare (repo, branch, commit) e cosa si verificherà dopo. Esempio completo:
`iniziative/136596/test/`.
