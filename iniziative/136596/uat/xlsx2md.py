#!/usr/bin/env python3
"""Estrae dal foglio SpecificaDiTest (template Test Factory 4.5.14) la test list in markdown.

    py xlsx2md.py <specifica.xlsx> [testlist.md]

Struttura del foglio (vedi md2xlsx.py per il verso opposto): per ogni caso di test una riga
TESTPADRE + due righe STEP (P = prerequisiti, 1 = azioni e verifiche). Il testo della colonna M
(Descrizione e note) e' sempre "step P" + riga vuota + "step 1": nel markdown si tiene una volta sola.
Dei fogli matrice_input / Esecuzione / SpecificaDiTest_BACKUP (residui della testlist da file)
non si estrae nulla.
"""
import collections
import sys
import warnings

import openpyxl

warnings.simplefilter("ignore")
sys.stdout.reconfigure(encoding="utf-8")

# colonne del foglio (1-based) usate per i casi di test
COL = dict(iniz=1, id1=4, macro=5, risk=8, id3=9, scenario=10, idt=11, titolo=12, desc=13,
           tipologia=18, livello=19, catena=20, testdata=21, durata=22, pri=23,
           step=24, tipostep=25, nomestep=26, azioni=27, attesi=28,
           sistema=29, fornitore=30, fase=31, note=32, noteesec=16, tiporiga=44)
# campi che nel markdown stanno nel front matter come default e per test solo se diversi
DEFAULTS = ["id1", "macro", "risk", "pri", "durata", "tipologia", "livello"]
# celle di Copertina (campo markdown -> cella)
COPERTINA = dict(nome_file="D3", iniziativa="D4", titolo_iniziativa="E4", piattaforma="D5",
                 test_manager="M6", workpackage="D8", consegna_completa="M8")
FASE_P = ("P", "Attività Preliminari e/o Precondizioni", "Prerequisiti", "prerequisiti soddisfatti")
FASE_1 = ("1", "Azione", "Verifiche varie di PostVendita", "esito ok")


def s(v):
    return "" if v is None else str(v)


def main(src, dst):
    wb = openpyxl.load_workbook(src, data_only=True)
    ws = wb["SpecificaDiTest"]
    cop = wb["Copertina"]
    rows = [r for r in range(4, ws.max_row + 1) if s(ws.cell(r, COL["tiporiga"]).value) == "TESTPADRE"]

    tests = []
    for r in rows:
        g = lambda k, rr=r: s(ws.cell(rr, COL[k]).value)
        p, s1 = r + 1, r + 2
        pa, a1 = s(ws.cell(p, COL["azioni"]).value), s(ws.cell(s1, COL["azioni"]).value)
        assert g("desc") == pa + "\n\n" + a1, f"riga {r}: M != P + S"
        assert (s(ws.cell(p, COL["step"]).value), s(ws.cell(p, COL["tipostep"]).value),
                s(ws.cell(p, COL["nomestep"]).value), s(ws.cell(p, COL["attesi"]).value)) == FASE_P, r
        assert (s(ws.cell(s1, COL["step"]).value), s(ws.cell(s1, COL["tipostep"]).value),
                s(ws.cell(s1, COL["nomestep"]).value), s(ws.cell(s1, COL["attesi"]).value)) == FASE_1, r
        assert g("idt") == g("testdata") and g("catena") == g("id3"), r
        t = {k: g(k) for k in ("id3", "scenario", "idt", "titolo", "sistema", "fornitore", "fase",
                               "note", "noteesec") + tuple(DEFAULTS)}
        t["prereq"], t["azioni"] = pa, a1
        tests.append(t)

    # default = valore piu' frequente
    default = {k: collections.Counter(t[k] for t in tests).most_common(1)[0][0] for k in DEFAULTS}
    iniz = collections.Counter(s(ws.cell(r, 1).value) for r in rows).most_common(1)[0][0]

    out = ["---", f"iniziativa: {iniz}"]
    for k, c in COPERTINA.items():
        if k != "iniziativa":
            out.append(f"{k}: {s(cop[c].value)}")
    for k in DEFAULTS:
        out.append(f"default_{k}: {default[k]}")
    out += ["---", "", "# Test list UAT - EURODIS API (derivata da SpecificaDiTest)", "",
            "<!-- Master della test list. Si modifica qui; l'Excel si rigenera con md2xlsx.py. -->",
            "<!-- Per test: sezione `Prerequisiti` = step P, `Azioni e verifiche` = step 1; -->",
            "<!-- la colonna Descrizione e note dell'Excel e' la loro concatenazione. -->", ""]
    cur = None
    for t in tests:
        if t["id3"] != cur:
            cur = t["id3"]
            out += [f"## {cur} - {t['scenario']}", ""]
        out += [f"### {t['idt']}", "", f"- fase: {t['fase']}", f"- sistema: {t['sistema']}",
                f"- fornitore: {t['fornitore']}"]
        if t["titolo"] != f"{t['scenario']} - {t['fase']}":
            out.append(f"- titolo: {t['titolo']}")
        if t["note"] != "0":
            out.append(f"- note: {t['note']}")
        if t["noteesec"]:
            out.append(f"- note_esecuzione: {t['noteesec']}")
        for k in DEFAULTS:
            if t[k] != default[k]:
                out.append(f"- {k}: {t[k]}")
        out += ["", "#### Prerequisiti", "", t["prereq"], "", "#### Azioni e verifiche", "", t["azioni"], ""]
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    n_sc = len({t["id3"] for t in tests})
    print(f"{dst}: {len(tests)} casi di test in {n_sc} scenari")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "testlist.md")
