---
description: Scrive o aggiorna la Specifica Funzionale (SF) di un'iniziativa, master markdown + Word nel template Poste
argument-hint: <id iniziativa>
---

Scrivi o aggiorna la Specifica Funzionale dell'iniziativa `$ARGUMENTS`, per
Poste (DTO / IT AS Corriere Espresso), che la verifica e la approva.

## Passi

1. Leggi `contesto/modelli/guida-sf.md` e seguila: struttura, stile, regole
   sui buchi e formato del master sono lì.
2. Leggi la voce `$ARGUMENTS` in `iniziative.yaml`. Se non esiste, fermati e
   chiedi i dati. Non inventare l'id.
3. Leggi le fonti elencate nella guida: `iniziative/$ARGUMENTS/` (PUNTO,
   analisi, registri dei punti aperti, `sviluppo/*.md`), poi il glossario.
   Controlla con `git log -5 -- iniziative/$ARGUMENTS/sviluppo/` che le
   specifiche di sviluppo non siano regredite (versione in intestazione più
   bassa di un commit precedente): se succede, segnalalo e usa l'ultima
   versione buona.
4. Se esiste già `iniziative/$ARGUMENTS/documenti/SF_$ARGUMENTS_*.md`,
   aggiornalo: alza la versione e aggiungi una riga alle revisioni.
   Altrimenti crealo, versione 0.1.
5. Genera il Word:
   `python contesto/modelli/md2docx.py iniziative/$ARGUMENTS/documenti/<file>.md`.
   Se fallisce, correggi il master, non il Word.
6. Rispondi con: file prodotti, cosa è `DA DEFINIRE` e da chi dipende, le
   divergenze trovate fra le fonti, le domande per Diego.
