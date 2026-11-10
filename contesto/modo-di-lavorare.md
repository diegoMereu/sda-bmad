# Come lavora Diego con gli agenti

- **Delega all'agente giusto**, non fare in prima persona:
  - Mary (analyst): specifiche funzionali per microservizio, mapping, registri dei punti aperti, SF;
  - Winston (architect): architettura, DDL, integrazioni, alert, DP;
  - John (pm): `PUNTO.md` dell'iniziativa;
  - Amelia (dev): sviluppo, anche in più istanze parallele su repo o file diversi;
  - test manager: piano, esecuzione e triage dei test integrati ([test-integrati.md](test-integrati.md)).
- **Autonomia**: nessuna conferma intermedia; dove serve una scelta si prende il default più
  ragionevole, lo si annota e si va avanti.
- **Commit e push autorizzati** su `sda-iniziative` e sui branch di lavoro dei servizi, man mano.
- **Contattare Diego solo per**: una fix da rilasciare (repo, branch, commit, perché) o un blocco che
  solo lui può sciogliere (accessi, credenziali, deploy, decisioni di business). Il resto va in un
  unico riepilogo a fine lavoro.
- Le domande vere (dati che ha solo lui) si raccolgono in fondo al riepilogo, non una per una.
- Restano sempre valide: niente dati di produzione versionati, niente valori di secret nei file,
  niente dati personali nei log.
- Documenti per Poste: SF e DP rigenerati dal master con `contesto/modelli/md2docx.py` e verificati
  pagina per pagina (export PDF con Word e controllo di ogni pagina) prima della consegna.
