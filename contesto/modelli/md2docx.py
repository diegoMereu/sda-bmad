"""Genera SF o DP in Word dal master markdown, sul template Poste.

Uso:  python contesto/modelli/md2docx.py <master.md> [<output.docx>]

Il master ha un front-matter YAML (vedi guida-sf.md / guida-dp.md) e un corpo
markdown ristretto: titoli #..####, paragrafi, elenchi "- " e "1. ", tabelle
pipe, blocchi ``` (resi come riquadro monospazio, come i DTO negli esempi),
immagini ![didascalia](file) e didascalie "Figura n: ..." / "Tabella n: ...".
Inline: **grassetto**, *corsivo*, `codice`.

Dal template si tiene solo la copertina (tutto quello che precede il primo
Heading 1); il sommario si aggiorna all'apertura del file in Word.
Richiede python-docx e PyYAML.
"""
import copy
import re
import sys
from pathlib import Path

import docx
import yaml
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

QUI = Path(__file__).parent
TEMPLATE = {"sf": QUI / "template-sf.docx", "dp": QUI / "template-dp.docx"}


# ---------------------------------------------------------------- template

def taglia_corpo(doc):
    """Rimuove il corpo dal primo Heading 1 in poi, tiene copertina e sectPr."""
    body = doc.element.body
    taglio = False
    for el in list(body):
        if el.tag == qn("w:sectPr"):
            continue
        if el.tag == qn("w:p") and not taglio:
            st = el.find(qn("w:pPr") + "/" + qn("w:pStyle"))
            if st is not None and st.get(qn("w:val")) in ("Heading1", "Titolo1"):
                taglio = True
        if taglio:
            body.remove(el)


def aggiorna_campi_all_apertura(doc):
    settings = doc.settings.element
    el = settings.find(qn("w:updateFields"))
    if el is None:
        el = OxmlElement("w:updateFields")
        settings.append(el)
    el.set(qn("w:val"), "true")


def scrivi(par_or_cell, testo):
    """Sostituisce il testo tenendo la formattazione del primo run."""
    for sdt in par_or_cell._element.findall(".//" + qn("w:sdt")):
        sdt.getparent().remove(sdt)
    pars = par_or_cell.paragraphs if hasattr(par_or_cell, "paragraphs") else [par_or_cell]
    p = pars[0]
    for extra in pars[1:]:
        extra._p.getparent().remove(extra._p)
    if p.runs:
        p.runs[0].text = testo
        for r in p.runs[1:]:
            r._r.getparent().remove(r._r)
    else:
        p.add_run(testo)


def righe_revisioni(tabella, revisioni, campi):
    """Riempie la tabella revisioni: riga 0 intestazione, poi una per revisione."""
    modello = tabella.rows[1]._tr
    for r in list(tabella.rows)[1:]:
        r._tr.getparent().remove(r._tr)
    for rev in revisioni or [{}]:
        tr = copy.deepcopy(modello)
        tabella._tbl.append(tr)
        riga = tabella.rows[-1]
        for i, campo in enumerate(campi):
            if i < len(riga.cells):
                scrivi(riga.cells[i], str(rev.get(campo, "") or ""))


def copertina_sf(doc, fm):
    for p in doc.paragraphs:
        t = p.text.strip()
        if t.startswith("Titolo della Richiesta"):
            scrivi(p, f"Titolo della Richiesta: {fm['titolo']}")
        elif t.startswith("TICKET STS"):
            if fm.get("ticket"):
                scrivi(p, f"TICKET STS: {fm['ticket']}")
            else:
                p._p.getparent().remove(p._p)
        elif t.startswith("Codice Iniziativa"):
            cod = fm["codice_iniziativa"]
            if fm.get("prj"):
                cod += f" ({fm['prj']})"
            scrivi(p, f"Codice Iniziativa: {cod}")
    intest, rev = doc.tables[0], doc.tables[1]
    valori = {
        "Compilato da": fm.get("compilato_da", ""),
        "Verificato da": fm.get("verificato_da", ""),
        "Approvato da": fm.get("approvato_da", ""),
        "Versione": fm.get("versione", ""),
        "Distribuito a": fm.get("distribuito_a", ""),
    }
    for riga in intest.rows:
        chiave = riga.cells[0].text.strip()
        if chiave in valori:
            scrivi(riga.cells[-1], str(valori[chiave] or ""))
    righe_revisioni(rev, fm.get("revisioni"), ["data", "versione", "stato", "descrizione", "autore"])


def copertina_dp(doc, fm):
    pars = [p for p in doc.paragraphs if p.text.strip()]
    titolo = f"{fm['codice_iniziativa']} - {fm['titolo']}"
    scrivi(pars[1], titolo)
    ruoli, rev = doc.tables[0], doc.tables[1]
    persone = {
        "Redazione": fm.get("redazione", {}),
        "Verifica": fm.get("verifica", {}),
        "Approvazione": fm.get("approvazione", {}),
    }
    for riga in ruoli.rows:
        chiave = riga.cells[0].text.strip()
        if chiave in persone:
            v = persone[chiave] or {}
            scrivi(riga.cells[1], v.get("nome", ""))
            scrivi(riga.cells[2], v.get("struttura", ""))
    righe_revisioni(rev, fm.get("revisioni"), ["versione", "data", "paragrafi", "motivazioni"])


# ---------------------------------------------------------------- corpo

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*\s][^*]*\*)")


def aggiungi_inline(p, testo):
    for pezzo in INLINE.split(testo):
        if not pezzo:
            continue
        if pezzo.startswith("**") and pezzo.endswith("**"):
            r = p.add_run(pezzo[2:-2])
            r.bold = True
        elif pezzo.startswith("`") and pezzo.endswith("`"):
            r = p.add_run(pezzo[1:-1])
            r.font.name = "Courier New"
            r.font.size = Pt(9)
        elif pezzo.startswith("*") and pezzo.endswith("*"):
            r = p.add_run(pezzo[1:-1])
            r.italic = True
        else:
            r = p.add_run(pezzo)
        if "DA DEFINIRE" in pezzo:
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW


def ombreggia(cella, colore="D9D9D9"):
    tcPr = cella._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), colore)
    tcPr.append(shd)


def celle(riga):
    riga = riga.strip()
    if riga.startswith("|"):
        riga = riga[1:]
    if riga.endswith("|"):
        riga = riga[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", riga)]


class Corpo:
    def __init__(self, doc, base):
        self.doc = doc
        self.base = base
        self.stili = {s.name for s in doc.styles}

    def stile(self, *nomi):
        for n in nomi:
            if n in self.stili:
                return n
        return None

    def par(self, testo, stile=None):
        p = self.doc.add_paragraph(style=stile)
        aggiungi_inline(p, testo)
        return p

    def titolo(self, livello, testo):
        p = self.doc.add_paragraph(style=f"Heading {livello}")
        aggiungi_inline(p, testo)

    def num_pallini(self):
        """numId della prima lista a pallini (Symbol) definita nel template."""
        n = self.doc.part.numbering_part.element
        astratti = {a.get(qn("w:abstractNumId")): a for a in n.findall(qn("w:abstractNum"))}
        for num in n.findall(qn("w:num")):
            a = astratti[num.find(qn("w:abstractNumId")).get(qn("w:val"))]
            l0 = a.find(qn("w:lvl"))
            if (l0.find(qn("w:numFmt")).get(qn("w:val")) == "bullet"
                    and l0.find(qn("w:lvlText")).get(qn("w:val")) == ""
                    and l0.find(qn("w:pStyle")) is None):
                return num.get(qn("w:numId"))
        return None

    def elenco(self, voci, numerato):
        num_id = None if numerato else self.num_pallini()
        for i, v in enumerate(voci, 1):
            if numerato:
                v = f"{i}. {v}"
            elif num_id is None:
                v = "• " + v
            p = self.par(v, self.stile("List Paragraph"))
            if num_id is not None:
                numPr = OxmlElement("w:numPr")
                ilvl = OxmlElement("w:ilvl")
                ilvl.set(qn("w:val"), "0")
                nid = OxmlElement("w:numId")
                nid.set(qn("w:val"), num_id)
                numPr.append(ilvl)
                numPr.append(nid)
                p._p.get_or_add_pPr().append(numPr)

    def tabella(self, righe):
        intest = celle(righe[0])
        dati = [celle(r) for r in righe[2:]]
        t = self.doc.add_table(rows=1 + len(dati), cols=len(intest))
        t.style = self.stile("Table Grid")
        for j, h in enumerate(intest):
            c = t.rows[0].cells[j]
            c.paragraphs[0].text = ""
            aggiungi_inline(c.paragraphs[0], h)
            for r in c.paragraphs[0].runs:
                r.bold = True
            ombreggia(c)
        for i, riga in enumerate(dati, 1):
            for j in range(len(intest)):
                testo = riga[j] if j < len(riga) else ""
                c = t.rows[i].cells[j]
                parti = testo.replace("\\|", "|").split("<br>")
                aggiungi_inline(c.paragraphs[0], parti[0])
                for extra in parti[1:]:
                    aggiungi_inline(c.add_paragraph(), extra)
        corpo = Pt(9) if len(intest) <= 8 else Pt(7)  # le tabelle HW hanno 12-15 colonne
        for riga in t.rows:
            for c in riga.cells:
                for p in c.paragraphs:
                    for r in p.runs:
                        r.font.size = corpo
        self.doc.add_paragraph()

    def codice(self, linee):
        t = self.doc.add_table(rows=1, cols=1)
        t.style = self.stile("Table Grid")
        c = t.rows[0].cells[0]
        p = c.paragraphs[0]
        for i, l in enumerate(linee):
            r = p.add_run(l)
            r.font.name = "Courier New"
            r.font.size = Pt(8)
            if i < len(linee) - 1:
                r.add_break()
        self.doc.add_paragraph()

    def immagine(self, didascalia, percorso):
        f = (self.base / percorso).resolve()
        if f.exists():
            self.doc.add_picture(str(f), width=self.doc.sections[0].page_width
                                 - self.doc.sections[0].left_margin - self.doc.sections[0].right_margin)
        else:
            p = self.doc.add_paragraph()
            r = p.add_run(f"[FIGURA DA INSERIRE: {percorso}]")
            r.bold = True
            r.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
        if didascalia:
            self.par(didascalia, self.stile("Caption"))

    def scrivi(self, testo):
        linee = testo.splitlines()
        i = 0
        while i < len(linee):
            l = linee[i]
            s = l.strip()
            if not s or s.startswith("<!--"):
                while s.startswith("<!--") and "-->" not in s and i + 1 < len(linee):
                    i += 1
                    s = linee[i].strip()
                i += 1
                continue
            m = re.match(r"^(#{1,4})\s+(.*)$", s)
            if m:
                self.titolo(len(m.group(1)), m.group(2).strip())
                i += 1
                continue
            if s.startswith("```"):
                blocco = []
                i += 1
                while i < len(linee) and not linee[i].strip().startswith("```"):
                    blocco.append(linee[i])
                    i += 1
                self.codice(blocco)
                i += 1
                continue
            if s.startswith("|") and i + 1 < len(linee) and re.match(r"^\|?\s*:?-{2,}", linee[i + 1].strip()):
                righe = []
                while i < len(linee) and linee[i].strip().startswith("|"):
                    righe.append(linee[i])
                    i += 1
                self.tabella(righe)
                continue
            m = re.match(r"^!\[(.*?)\]\((.*?)\)$", s)
            if m:
                self.immagine(m.group(1), m.group(2))
                i += 1
                continue
            if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
                numerato = bool(re.match(r"^\d+\.\s+", s))
                voci = []
                voce = r"^\s*\d+\.\s+" if numerato else r"^\s*[-*]\s+"
                while i < len(linee) and (re.match(voce, linee[i])
                                          or (linee[i].startswith("  ") and linee[i].strip() and voci)):
                    v = linee[i].strip()
                    if re.match(r"^[-*]\s+|^\d+\.\s+", v):
                        voci.append(re.sub(r"^[-*]\s+|^\d+\.\s+", "", v))
                    else:
                        voci[-1] += " " + v
                    i += 1
                self.elenco(voci, numerato)
                continue
            if re.match(r"^(Figura|Tabella)\s+\d+\s*[:\-–]", s):
                self.par(s, self.stile("Caption"))
                i += 1
                continue
            # paragrafo: linee consecutive non vuote
            buf = [s]
            i += 1
            while i < len(linee) and linee[i].strip() and not re.match(r"^(#|\||```|!\[|[-*]\s|\d+\.\s)", linee[i].strip()):
                buf.append(linee[i].strip())
                i += 1
            testo_p = " ".join(buf)
            if testo_p.startswith("> "):
                testo_p = testo_p[2:]
            self.par(testo_p)


# ---------------------------------------------------------------- main

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".docx")
    testo = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", testo, re.S)
    if not m:
        sys.exit("manca il front-matter YAML")
    fm = yaml.safe_load(m.group(1))
    tipo = fm["tipo"]
    doc = docx.Document(str(TEMPLATE[tipo]))
    taglia_corpo(doc)
    (copertina_sf if tipo == "sf" else copertina_dp)(doc, fm)
    Corpo(doc, src.parent).scrivi(m.group(2))
    aggiorna_campi_all_apertura(doc)
    doc.save(str(dst))
    print(dst)


if __name__ == "__main__":
    main()
