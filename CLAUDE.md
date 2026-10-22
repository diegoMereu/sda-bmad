# sda-iniziative

Gestione delle iniziative SDA (Poste Italiane, ADI `PCL-127`) con BMAD
(moduli `core` + `bmm`).

Configurazione **volutamente minima**: si aggiungono regole, cartelle e
template solo quando nascono dal lavoro reale, non in anticipo.

## Regole

- Lingua degli artefatti: **italiano**. Nomi file e ID: ASCII.
- L'id di un'iniziativa è la numerazione **del cliente** (es. `144208`), mai inventata.
- `iniziative.yaml` è l'unica anagrafica: id, titolo, PRJ, stato, referenti, perimetro.
- Ogni artefatto sta in `iniziative/<id>/` dell'iniziativa a cui appartiene.
- Dati di produzione (nomi, indirizzi, CF, P.IVA) **mai** versionati.
- Ogni iniziativa attiva ha un `iniziative/<id>/PUNTO.md` per il PM. Lo tiene
  l'agente PM (John, `bmad-agent-pm`, voce di menu `PT`), oppure `/punto <id>`.
  È il primo file da leggere per sapere dove siamo.

## Agenti

Gli agenti BMAD sono skill in `.claude/skills/bmad-agent-*`: analyst (Mary),
pm (John), architect (Winston), dev (Amelia), ux-designer (Sally).
Si personalizzano in `_bmad/custom/<skill>.toml`, mai nei file installati.

## Struttura

```
iniziative.yaml        anagrafica
iniziative/<id>/       lavoro per iniziativa (si crea quando serve)
  PUNTO.md             stato per il PM, una pagina (/punto <id>)
contesto/              glossario di dominio CE
_bmad/, .claude/       BMAD installato (non modificare a mano: usa _bmad/custom/)
_bmad-output/          output dei workflow BMAD
```

## Dove trovare cosa

- Glossario dominio (LDV, preadvising, EAD, scarti...): `contesto/glossario-ce.md`
- Storico, campagne di test e difetti della configurazione precedente:
  `C:\Users\diego.mereu\testfactory` (solo riferimento, non si lavora lì).
