"""Genera SF o DP in Word dal master markdown, sul template Poste.

Uso:  python contesto/modelli/md2docx.py <master.md> [<output.docx>]

Il master ha un front-matter YAML (vedi guida-sf.md / guida-dp.md) e un corpo
markdown ristretto: titoli #..####, paragrafi, elenchi "- " e "1. ", tabelle
pipe, blocchi ``` (resi come riquadro monospazio, come i DTO negli esempi),
immagini ![didascalia](file) e didascalie "Figura n: ..." / "Tabella n: ...".
Inline: **grassetto**, *corsivo*, `codice`.
Orientamento: una riga `<!-- orientamento: orizzontale -->` (o `verticale`) apre una
nuova sezione su pagina nuova con quell'orientamento, per le tabelle con molte colonne;
senza questa riga il documento resta tutto verticale.

Dal template si tiene solo la copertina (tutto quello che precede il primo
Heading 1). Il sommario del template viene ricostruito con le voci dei titoli veri e i loro
segnalibri (niente "Errore! Il segnalibro non è definito."); i numeri di pagina li calcola Word
all'apertura del file.
Richiede python-docx e PyYAML.
"""
import copy
import re
import sys
from pathlib import Path

import docx
import yaml
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Pt, RGBColor
from docx.text.paragraph import Paragraph

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
    # immagini del corpo tagliato: restano nel pacchetto se non si tolgono le relazioni
    xml = doc.element.xml
    for rid, rel in list(doc.part.rels.items()):
        if "image" in rel.reltype and f'"{rid}"' not in xml:
            del doc.part.rels[rid]


def aggiorna_campi_all_apertura(doc):
    settings = doc.settings.element
    el = settings.find(qn("w:updateFields"))
    if el is None:
        el = OxmlElement("w:updateFields")
        settings.append(el)
    el.set(qn("w:val"), "true")


def _run(figlio=None, testo=None, campo=None):
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    rpr.append(OxmlElement("w:noProof"))
    r.append(rpr)
    if campo:
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), campo)
        r.append(el)
    elif figlio:
        el = OxmlElement(figlio)
        if testo is not None:
            el.text = testo
            el.set(qn("xml:space"), "preserve")
        r.append(el)
    return r


def ricostruisci_sommario(doc):
    """Sostituisce le voci del sommario ereditate dal template (PAGEREF a segnalibri _Toc del
    template, che nel documento non esistono: "Errore! Il segnalibro non è definito." appena Word
    aggiorna i numeri di pagina) con le voci dei titoli veri, ciascuno con il suo segnalibro.
    I numeri di pagina restano vuoti e li calcola Word all'apertura (updateFields)."""
    body = doc.element.body
    # il sommario può stare dentro un controllo contenuto (w:sdt): si cercano tutti i paragrafi
    pars = list(body.iter(qn("w:p")))
    inizio = next((p for p in pars if any((t.text or "").strip().startswith("TOC")
                                           for t in p.iter(qn("w:instrText")))), None)
    if inizio is None:
        return
    # paragrafi del campo TOC: dal begin all'end corrispondente (i PAGEREF sono annidati)
    vecchi, livello = [], 0
    for p in pars[pars.index(inizio):]:
        vecchi.append(p)
        for fc in p.iter(qn("w:fldChar")):
            livello += 1 if fc.get(qn("w:fldCharType")) == "begin" else (
                -1 if fc.get(qn("w:fldCharType")) == "end" else 0)
        if livello <= 0:
            break
    istruzione = next(t.text for t in inizio.iter(qn("w:instrText")) if (t.text or "").strip().startswith("TOC"))
    m = re.search(r'\\o\s+"(\d)-(\d)"', istruzione)
    massimo = int(m.group(2)) if m else 3

    titoli, contatori = [], [0] * 9
    for p in doc.paragraphs:
        nome = p.style.name if p.style is not None else ""
        mt = re.match(r"^Heading (\d)$", nome)
        if not mt or not p.text.strip():
            continue
        lv = int(mt.group(1))
        contatori[lv - 1] += 1
        contatori[lv:] = [0] * (9 - lv)
        if lv <= massimo:
            titoli.append((lv, ".".join(str(c) for c in contatori[:lv]), p))

    nuovi = []
    for n, (lv, numero, p) in enumerate(titoli):
        nome_bm = f"_Toc9{n:08d}"
        bs = OxmlElement("w:bookmarkStart")
        bs.set(qn("w:id"), str(9000 + n))
        bs.set(qn("w:name"), nome_bm)
        be = OxmlElement("w:bookmarkEnd")
        be.set(qn("w:id"), str(9000 + n))
        ppr = p._p.find(qn("w:pPr"))
        (ppr.addnext(bs) if ppr is not None else p._p.insert(0, bs))
        p._p.append(be)

        voce = OxmlElement("w:p")
        vppr = OxmlElement("w:pPr")
        st = OxmlElement("w:pStyle")
        st.set(qn("w:val"), f"TOC{lv}")
        vppr.append(st)
        voce.append(vppr)
        if n == 0:
            voce.append(_run(campo="begin"))
            voce.append(_run("w:instrText", istruzione))
            voce.append(_run(campo="separate"))
        link = OxmlElement("w:hyperlink")
        link.set(qn("w:anchor"), nome_bm)
        link.set(qn("w:history"), "1")
        link.append(_run("w:t", numero))
        link.append(_run("w:tab"))
        link.append(_run("w:t", p.text.strip()))
        link.append(_run("w:tab"))
        link.append(_run(campo="begin"))
        link.append(_run("w:instrText", f" PAGEREF {nome_bm} \\h "))
        link.append(_run(campo="separate"))
        link.append(_run(campo="end"))
        voce.append(link)
        if n == len(titoli) - 1:
            voce.append(_run(campo="end"))
        nuovi.append(voce)
    if not nuovi:
        return
    for v in nuovi:
        vecchi[0].addprevious(v)
    for p in vecchi:
        p.getparent().remove(p)


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
                for p in riga.cells[i].paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT


def intestazione(doc, fm):
    """Intestazioni e piè di pagina del template: il segnaposto "xxxx – iniziativa" diventa
    codice e titolo; versione, data e codice documento del piè di pagina (DP) quelli del master."""
    cod = str(fm["codice_iniziativa"])
    titolo = re.sub(r"^\s*" + re.escape(cod) + r"\s*[-–]\s*", "", str(fm.get("titolo", "")))
    testo = f"{cod} – {titolo}" if titolo else cod
    ultima = (fm.get("revisioni") or [{}])[-1]
    versione = str(fm.get("versione") or ultima.get("versione") or "")
    data = str(ultima.get("data") or "")
    sostituzioni = [(r"DDP_\d+", f"DDP_{cod}")]
    if versione:
        sostituzioni.append((r"^ver\. .*$", f"ver. {versione}"))
    if data:
        sostituzioni.append((r"^del: .*$", f"del: {data}"))
    for s in doc.sections:
        for parte in (s.header, s.first_page_header, s.even_page_header,
                      s.footer, s.first_page_footer, s.even_page_footer):
            pars = list(parte.paragraphs)
            for tb in parte.tables:
                for riga in tb.rows:
                    for c in riga.cells:
                        pars.extend(c.paragraphs)
            for p in pars:
                if p.text.strip().lower().startswith("xxxx"):
                    scrivi(p, testo)
                    continue
                for r in p.runs:  # run per run: i campi (numero di pagina) restano intatti
                    for modello, nuovo in sostituzioni:
                        if re.search(modello, r.text.strip()):
                            r.text = re.sub(modello, nuovo, r.text.strip())


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
            testo_run, fmt = pezzo[2:-2], "b"
        elif pezzo.startswith("`") and pezzo.endswith("`"):
            testo_run, fmt = pezzo[1:-1], "c"
        elif pezzo.startswith("*") and pezzo.endswith("*"):
            testo_run, fmt = pezzo[1:-1], "i"
        else:
            testo_run, fmt = pezzo, ""
        for parte in re.split(r"(DA DEFINIRE)", testo_run):
            if not parte:
                continue
            r = p.add_run(parte)
            if fmt == "b":
                r.bold = True
            elif fmt == "i":
                r.italic = True
            elif fmt == "c":
                r.font.name = "Courier New"
                r.font.size = Pt(9)
            if parte == "DA DEFINIRE":
                r.font.highlight_color = WD_COLOR_INDEX.YELLOW


def ombreggia(cella, colore="D9D9D9"):
    tcPr = cella._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), colore)
    tcPr.append(shd)


CARATTERE = 57150   # larghezza media di un carattere del corpo tabella (9 pt), in EMU
MONO = 1.4          # il monospazio (`codice`) è più largo del testo proporzionale
MARGINE = 2.5       # margini interni della cella, in caratteri
GRASSETTO = 1.2     # l'intestazione è in grassetto, più larga
PAROLA_MAX = 24     # oltre questa larghezza una parola può andare a capo
INLINE_CODICE = re.compile(r"`[^`]+`")


def unita(testo):
    """Larghezza di un testo in caratteri del corpo tabella, contando il monospazio più largo."""
    tot = 0.0
    for pezzo in INLINE.split(testo):
        if pezzo.startswith("`") and pezzo.endswith("`") and len(pezzo) > 1:
            tot += (len(pezzo) - 2) * MONO
        else:
            tot += len(re.sub(r"\*\*|(?<!\w)\*|\*(?!\w)", "", pezzo))
    return tot


def larghezze(intest, dati, totale, corpo_pt=9):
    """Larghezze delle colonne: ogni colonna contiene almeno la sua parola più lunga
    (niente parole spezzate), lo spazio restante va a chi ha più testo."""
    minimi, testo_min, desiderati = [], [], []
    for j, h in enumerate(intest):
        valori = [r[j] if j < len(r) else "" for r in dati]
        parti = [x.replace("\\|", "|") for v in valori for x in v.split("<br>")]
        h = h.replace("\\|", "|")
        parole = [unita(w) for x in parti for w in x.split()]
        parole += [unita(w) * GRASSETTO for w in h.split()]
        # parole di testo normale, senza i `codici`: sono quelle da non spezzare mai
        normali = [len(w) for x in parti for w in INLINE_CODICE.sub(" ", x).split()]
        normali += [len(w) * GRASSETTO for w in INLINE_CODICE.sub(" ", h).split()]
        # una parola lunghissima (un percorso di campo) può andare a capo: non ruba spazio alle altre colonne
        parola = min(max(parole, default=1), PAROLA_MAX)
        lunghi = sorted([unita(x) for x in parti] + [unita(h) * GRASSETTO])
        tipico = lunghi[int(len(lunghi) * 0.8)] if lunghi else 1
        minimi.append(max(parola, 2) + MARGINE)
        testo_min.append(min(max(max(normali, default=1), 2), PAROLA_MAX) + MARGINE)
        desiderati.append(min(max(tipico, parola), 60) + MARGINE)
    disponibile = totale / (CARATTERE * corpo_pt / 9)
    if sum(minimi) >= disponibile:
        # spazio insufficiente: prima si garantiscono le parole normali, i codici vanno a capo
        if sum(testo_min) < disponibile:
            extra = [max(m - t, 0) for m, t in zip(minimi, testo_min)]
            resto = disponibile - sum(testo_min)
            pesi = [t + (resto * e / sum(extra) if sum(extra) else 0) for t, e in zip(testo_min, extra)]
        else:
            pesi = testo_min
    else:
        extra = [max(d - m, 0) for d, m in zip(desiderati, minimi)]
        resto = disponibile - sum(minimi)
        if sum(extra) <= resto or sum(extra) == 0:
            pesi = [m + e for m, e in zip(minimi, extra)]
        else:
            pesi = [m + resto * e / sum(extra) for m, e in zip(minimi, extra)]
    somma = sum(pesi)
    return [int(totale * w / somma) for w in pesi]


def imposta_larghezze(t, misure):
    t.autofit = False
    tblPr = t._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:type"), "dxa")
    tblW.set(qn("w:w"), str(int(sum(misure) / 635)))
    griglia = t._tbl.tblGrid
    for col, w in zip(griglia.findall(qn("w:gridCol")), misure):
        col.set(qn("w:w"), str(int(w / 635)))
    for riga in t.rows:
        for c, w in zip(riga.cells, misure):
            c.width = Emu(w)


def riga_opzione(riga, nome):
    trPr = riga._tr.get_or_add_trPr()
    el = OxmlElement(nome)
    trPr.append(el)


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

    def orientamento(self, orizzontale):
        """Nuova sezione su pagina nuova, orizzontale o verticale; intestazioni e piè di pagina
        restano quelli della sezione precedente."""
        prec = self.doc.sections[-1]
        voluto = WD_ORIENT.LANDSCAPE if orizzontale else WD_ORIENT.PORTRAIT
        if prec.orientation == voluto:
            return
        sez = self.doc.add_section(WD_SECTION.NEW_PAGE)
        larga, alta = max(prec.page_width, prec.page_height), min(prec.page_width, prec.page_height)
        sez.orientation = voluto
        sez.page_width, sez.page_height = (larga, alta) if orizzontale else (alta, larga)
        sez.different_first_page_header_footer = False

    def titolo(self, livello, testo):
        p = self.doc.add_paragraph(style=f"Heading {livello}")
        aggiungi_inline(p, testo)
        p.paragraph_format.keep_with_next = True  # il titolo non resta solo in fondo alla pagina

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
        sez = self.doc.sections[-1]
        imposta_larghezze(t, larghezze(intest, dati, sez.page_width - sez.left_margin - sez.right_margin,
                                       corpo.pt))
        riga_opzione(t.rows[0], "w:tblHeader")
        for riga in t.rows:
            riga_opzione(riga, "w:cantSplit")
        for c in t.rows[0].cells:
            for p in c.paragraphs:
                p.paragraph_format.keep_with_next = True
        spazio = self.doc.add_paragraph()
        return t, spazio

    def lega_didascalia(self, t, spazio):
        """La didascalia "Tabella n: ..." resta sulla pagina dell'ultima riga della tabella."""
        for c in t.rows[-1].cells:
            for p in c.paragraphs:
                p.paragraph_format.keep_with_next = True
        spazio.paragraph_format.keep_with_next = True

    def codice(self, linee):
        body = self.doc.element.body
        precedenti = [el for el in body if el.tag == qn("w:p")]
        if precedenti:  # la frase che introduce l'esempio resta con l'esempio
            Paragraph(precedenti[-1], self.doc._body).paragraph_format.keep_with_next = True
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
        if len(linee) <= 40:  # un esempio breve non si spezza fra due pagine
            riga_opzione(t.rows[0], "w:cantSplit")
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
            m = re.match(r"^<!--\s*orientamento:\s*(orizzontale|verticale)\s*-->$", s)
            if m:
                self.orientamento(m.group(1) == "orizzontale")
                i += 1
                continue
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
                t, spazio = self.tabella(righe)
                dopo = next((x.strip() for x in linee[i:] if x.strip()), "")
                if re.match(r"^Tabella\s+\d+\s*[:\-–]", dopo):
                    self.lega_didascalia(t, spazio)
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
    intestazione(doc, fm)
    Corpo(doc, src.parent).scrivi(m.group(2))
    ricostruisci_sommario(doc)
    aggiorna_campi_all_apertura(doc)
    doc.save(str(dst))
    print(dst)


if __name__ == "__main__":
    main()
