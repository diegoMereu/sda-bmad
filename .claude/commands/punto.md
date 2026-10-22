---
description: Aggiorna il punto di un'iniziativa per il PM (iniziative/<id>/PUNTO.md)
argument-hint: <id iniziativa>
---

Aggiorna il punto dell'iniziativa `$ARGUMENTS`. Il destinatario è un PM che
deve capire in due minuti dove siamo, senza aprire altri file.

## Passi

1. Leggi la voce `$ARGUMENTS` in `iniziative.yaml`. Se non esiste, fermati e
   chiedi i dati per registrarla (id del cliente, titolo, PRJ, owner, stato,
   perimetro). Non inventare l'id.
2. Leggi `iniziative/$ARGUMENTS/` (tutti i file, compreso il `PUNTO.md`
   precedente se c'è) e `git log --since="2 weeks ago" -- iniziative/$ARGUMENTS/`.
3. Chiedimi cosa è cambiato dall'ultimo punto, in una sola domanda. Se rispondo
   "niente di nuovo", lavora solo su quello che c'è nei file.
4. Riscrivi `iniziative/$ARGUMENTS/PUNTO.md` col formato qui sotto. Sovrascrivi:
   lo storico lo tiene git.

## Formato

```markdown
# <id> — <titolo>

**Data**: <YYYY-MM-DD> · **Stato**: <aperta|in_corso|sospesa|chiusa> · **Semaforo**: 🟢|🟡|🔴
**Owner cliente**: <nome> · **PRJ**: <codice>

## In una riga
<dove siamo, in una frase>

## Fatto dall'ultimo punto
- ...

## Prossimi passi
- <cosa> — <chi> — <entro quando>

## Blocchi e rischi
- ...

## Serve dal cliente
- ...

## Decisioni prese
- <YYYY-MM-DD> — <decisione>
```

## Regole

- Massimo una pagina. Se una sezione è vuota scrivi "nessuno", non toglierla.
- Semaforo: 🟢 nei tempi, 🟡 c'è un rischio da gestire, 🔴 bloccata o fuori tempo.
  Motiva sempre giallo e rosso in "Blocchi e rischi".
- Non dedurre: quello che non sai va in "Serve dal cliente" o chiedilo a me.
- "Decisioni prese" si accumula: riporta quelle del punto precedente.
- Se lo stato cambia, aggiorna anche `iniziative.yaml`.
