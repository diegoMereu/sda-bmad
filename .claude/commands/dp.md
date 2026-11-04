---
description: Scrive o aggiorna il Documento di Progettazione (DP) di un'iniziativa, master markdown + Word nel template Poste
argument-hint: <id iniziativa>
---

Scrivi o aggiorna il Documento di Progettazione dell'iniziativa `$ARGUMENTS`,
per gli architetti e l'infrastruttura di Poste (DTO / ITASCE).

## Passi

1. Leggi `contesto/modelli/guida-dp.md` e seguila: struttura, tabelle, stile,
   regole sui buchi e formato del master sono lì.
2. Leggi la voce `$ARGUMENTS` in `iniziative.yaml`. Se non esiste, fermati e
   chiedi i dati. Non inventare l'id.
3. Leggi la SF dell'iniziativa (`iniziative/$ARGUMENTS/documenti/SF_*.md`) se
   esiste, poi le altre fonti della guida.
4. Se esiste già `iniziative/$ARGUMENTS/documenti/DP_$ARGUMENTS_*.md`,
   aggiornalo: alza la versione e aggiungi una riga alle revisioni.
   Altrimenti crealo, versione 0.1.
5. Genera il Word:
   `python contesto/modelli/md2docx.py iniziative/$ARGUMENTS/documenti/<file>.md`.
   Se fallisce, correggi il master, non il Word.
6. Rispondi con: file prodotti, i `DA DEFINIRE` raggruppati per chi deve
   rispondere (cliente, infrastruttura, team), le incoerenze con la SF, le
   domande per Diego.
