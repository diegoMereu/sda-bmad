#!/usr/bin/env python3
"""Genera la Specifica di Test (template Test Factory 4.5.14) dalla test list in markdown.

    py md2xlsx.py <testlist.md> <template.xlsx> <uscita.xlsx>

Il template e' un Excel gia' esistente (es. TOTALE_ST_SDA_136596_Eurodis_Autoproduttore_v1.xlsx):
si riscrive solo il foglio SpecificaDiTest (righe da 4 in poi) e le celle di dati di Copertina;
gli altri fogli restano com'erano. Formato del markdown: vedi xlsx2md.py (front matter con i
default, "## <id scenario> - <titolo>", "### <id test>", elenco `- chiave: valore`, sezioni
"#### Prerequisiti" e "#### Azioni e verifiche").

ATTENZIONE: openpyxl non conserva le validazioni dati "extension" (x14, elenchi a tendina che
puntano ad altri fogli): dopo la generazione riaprire in Excel e verificare le tendine, oppure
copiare le righe generate nel template originale.
"""
import re
import sys
import warnings
from copy import copy

import openpyxl

warnings.simplefilter("ignore")
sys.stdout.reconfigure(encoding="utf-8")

NCOL = 46
FIRST_ROW = 4
C = dict(iniz=1, id1=4, macro=5, risk=8, id3=9, scenario=10, idt=11, titolo=12, desc=13,
         tipologia=18, livello=19, catena=20, testdata=21, durata=22, pri=23,
         step=24, tipostep=25, nomestep=26, azioni=27, attesi=28,
         sistema=29, fornitore=30, fase=31, note=32, noteesec=16, tiporiga=44)
COPERTINA = dict(nome_file="D3", iniziativa="D4", titolo_iniziativa="E4", piattaforma="D5",
                 test_manager="M6", workpackage="D8", consegna_completa="M8")
OVERRIDABLE = ("id1", "macro", "risk", "pri", "durata", "tipologia", "livello")
STEP_P = ("P", "Attività Preliminari e/o Precondizioni", "Prerequisiti", "prerequisiti soddisfatti")
STEP_1 = ("1", "Azione", "Verifiche varie di PostVendita", "esito ok")
BULLET = re.compile(r"^- (\w+): ?(.*)$")


def parse(path):
    text = open(path, encoding="utf-8").read().replace("\r\n", "\n")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    meta = dict(l.split(": ", 1) if ": " in l else (l.rstrip(":"), "") for l in m.group(1).split("\n"))
    body = text[m.end():]
    tests, scen = [], None
    # spezza sui titoli di scenario e di test
    parts = re.split(r"^(## .*|### .*)$", body, flags=re.M)
    i = 1
    while i < len(parts):
        head, content = parts[i], parts[i + 1]
        i += 2
        if head.startswith("## "):
            sid, _, stit = head[3:].partition(" - ")
            scen = (sid.strip(), stit.strip())
            continue
        t = dict(idt=head[4:].strip(), id3=scen[0], scenario=scen[1])
        sec = re.split(r"^#### (Prerequisiti|Azioni e verifiche)$", content, flags=re.M)
        for line in sec[0].split("\n"):
            b = BULLET.match(line)
            if b:
                t[b.group(1)] = b.group(2)
        for name, val in zip(sec[1::2], sec[2::2]):
            t["prereq" if name == "Prerequisiti" else "azioni"] = val.strip("\n")
        for need in ("fase", "sistema", "fornitore", "prereq", "azioni"):
            if need not in t:
                raise SystemExit(f"{t['idt']}: manca `{need}`")
        tests.append(t)
    return meta, tests


def put(ws, r, c, v, proto):
    cell = ws.cell(r, c)
    cell.value = None if v == "" else v
    cell._style = copy(proto[c])


def main(md, template, out):
    meta, tests = parse(md)
    wb = openpyxl.load_workbook(template)
    ws = wb["SpecificaDiTest"]
    # righe prototipo (stile) dal template: TESTPADRE, step P, step 1
    proto = {k: {c: copy(ws.cell(FIRST_ROW + k, c)._style) for c in range(1, NCOL + 1)} for k in range(3)}
    h = {k: ws.row_dimensions[FIRST_ROW + k].height for k in range(3)}
    lvl = {k: ws.row_dimensions[FIRST_ROW + k].outlineLevel for k in range(3)}
    old_last = ws.max_row

    r = FIRST_ROW
    for t in tests:
        d = {k: t.get(k, meta.get("default_" + k, "")) for k in OVERRIDABLE}
        titolo = t.get("titolo", f"{t['scenario']} - {t['fase']}")
        rows = [
            {C["iniz"]: meta["iniziativa"], C["id1"]: d["id1"], C["macro"]: d["macro"], C["risk"]: int(d["risk"]),
             C["id3"]: t["id3"], C["scenario"]: t["scenario"], C["idt"]: t["idt"], C["titolo"]: titolo,
             C["desc"]: t["prereq"] + "\n\n" + t["azioni"], C["tipologia"]: d["tipologia"],
             C["livello"]: d["livello"], C["catena"]: t["id3"], C["testdata"]: t["idt"],
             C["durata"]: d["durata"], C["pri"]: int(d["pri"]), C["sistema"]: t["sistema"],
             C["fornitore"]: t["fornitore"], C["fase"]: t["fase"], C["note"]: int(t.get("note", 0)), C["noteesec"]: t.get("note_esecuzione", ""),
             C["tiporiga"]: "TESTPADRE"},
            {C["step"]: STEP_P[0], C["tipostep"]: STEP_P[1], C["nomestep"]: STEP_P[2],
             C["azioni"]: t["prereq"], C["attesi"]: STEP_P[3], C["tiporiga"]: "STEP"},
            {C["step"]: STEP_1[0], C["tipostep"]: STEP_1[1], C["nomestep"]: STEP_1[2],
             C["azioni"]: t["azioni"], C["attesi"]: STEP_1[3], C["tiporiga"]: "STEP"},
        ]
        for k, vals in enumerate(rows):
            for c in range(1, NCOL + 1):
                put(ws, r, c, vals.get(c, ""), proto[k])
            ws.row_dimensions[r].height = h[k]
            ws.row_dimensions[r].outlineLevel = lvl[k]
            r += 1
    # righe residue del template, se la nuova lista e' piu' corta
    for rr in range(r, old_last + 1):
        for c in range(1, NCOL + 1):
            ws.cell(rr, c).value = None
    ws.auto_filter.ref = f"A3:AT{r - 1}"

    cop = wb["Copertina"]
    for k, cell in COPERTINA.items():
        if k in meta:
            cop[cell].value = meta[k]
    wb.save(out)
    print(f"{out}: {len(tests)} casi di test, {r - FIRST_ROW} righe")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
