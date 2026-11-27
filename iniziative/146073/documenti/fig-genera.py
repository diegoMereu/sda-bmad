"""Genera le figure della SF e del DP della 146073 (sorgenti drawio ed export PNG).

Uso (dalla radice del repo):
    python iniziative/146073/documenti/fig-genera.py

Scrive fig-1-architettura.drawio e fig-2-flussi-dati.drawio accanto a questo script e, se trova
draw.io desktop, esporta i PNG con la sua riga di comando (draw.io.exe -x -f png). Le figure si
possono poi ritoccare in draw.io: in quel caso rigenerare solo il PNG, non rilanciare lo script.
"""
import os
import subprocess
from xml.sax.saxutils import escape

QUI = os.path.dirname(os.path.abspath(__file__))
DRAWIO = [r"C:\Program Files\draw.io\draw.io.exe", "/c/Program Files/draw.io/draw.io.exe"]

# Stili ripresi dalle figure della 144216
MOD = "rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;"
VERIFICA = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;fontSize=11;strokeWidth=2;"
INV = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=11;"
TRANCHE = "rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=#ffffff;strokeColor=#6c8ebf;fontSize=11;fontColor=#555555;"
TOPIC = "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;"
DB = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;"
DB_MOD = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=10;"
DB_TRANCHE = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;size=10;dashed=1;fillColor=#ffffff;strokeColor=#6c8ebf;fontSize=10;fontColor=#555555;"
NS = "rounded=1;whiteSpace=wrap;html=1;dashed=1;fillColor=none;strokeColor=#6c8ebf;verticalAlign=top;align=left;spacingLeft=8;fontSize=11;fontColor=#6c8ebf;arcSize=2;"
TITOLO = "text;html=1;fontSize=16;fontStyle=1;align=left;verticalAlign=middle;"
TESTO = "text;html=1;align=left;fontSize=10;fontColor=#555555;whiteSpace=wrap;"
FRECCIA = "endArrow=block;html=1;labelBackgroundColor=#ffffff;fontSize=10;"
NUM = "endArrow=block;html=1;labelBackgroundColor=#ffffff;fontSize=11;fontStyle=1;fontColor=#b85450;"

# Nodi comuni: id -> (etichetta, stile, x, y, w, h)
NODI = {
    "ns": ("OpenShift - namespace corriere-espresso-preadvising", NS, 210, 50, 1200, 560),
    "builder": ("<b>ce-dichiarato-builder</b><br>canali a file IF, IS, IE", INV, 20, 70, 170, 70),
    "producer": ("<b>producer-sew-sped</b><br>batch portali e web service<br>invia zonos_account_key,<br>zonos_declaration_id", MOD, 20, 190, 170, 80),
    "adapter": ("<b>ce-dichiarato-adapter</b><br>PDB, PDW, ILP<br>seconda tranche", TRANCHE, 20, 320, 170, 70),
    "t_pre": ("topic<br><b>preadvising.pre-enrichment</b>", TOPIC, 230, 90, 170, 60),
    "validatore": ("<b>ce-dichiarato-validatore</b><br>propaga i campi zonos_*<br>nessuna verifica", MOD, 430, 80, 160, 80),
    "t_enr": ("topic<br><b>preadvising.enrichment</b>", TOPIC, 620, 90, 160, 60),
    "orchestratore": ("<b>ce-dichiarato-orchestratore</b><br>propaga i campi, esclusi<br>dal merge delle lavorazioni", MOD, 810, 80, 180, 80),
    "t_comp": ("topic<br><b>preadvising.completed</b>", TOPIC, 1020, 90, 160, 60),
    "smistatore": ("<b>ce-dichiarato-smistatore</b><br>propaga i campi<br>verso Poste e SDA", MOD, 1210, 80, 170, 80),
    "ldv": ("<b>ce-dichiarato-ldv</b><br>associazione LDV e<br><b>verifica Compliance USA</b><br>processo normale (IS, IF, IE)<br>errori 1320-1323", VERIFICA, 830, 220, 180, 100),
    "ldvpdb": ("<b>ce-dichiarato-ldv-pdb</b>,<br><b>-ldv-pdb-sync</b><br>flussi PDB: nessuna verifica", INV, 1050, 230, 170, 70),
    "mongo": ("MongoDB<br><b>dichiarato_events</b>,<br>enrichment_events", DB, 430, 235, 160, 75),
    "bff": ("<b>ce-dichiarato-bff</b><br>API di consultazione e<br>risottomissione con i campi", MOD, 230, 360, 170, 70),
    "t_evs": ("topic<br><b>preadvising.evensource</b>", TOPIC, 610, 460, 170, 60),
    "eventstore": ("<b>ce-event-handler-event-store</b><br>nessuna modifica", INV, 840, 440, 190, 55),
    "monitoring": ("<b>ce-event-handler-monitoring</b><br>errori 1320-1323 alla console", INV, 840, 520, 190, 55),
    "t_cons": ("topic<br><b>PRE-ADV.MONITORAGGIO-<br>CAMBIO-STATO</b>", TOPIC, 1080, 520, 200, 60),
    "t_sda": ("topic<br><b>preadvising.completed.sda</b>", TOPIC, 1440, 190, 180, 55),
    "t_poste": ("topic<br><b>preadvising.completed.poste</b>", TOPIC, 1440, 300, 180, 55),
    "consumer": ("<b>consumer-sew_sped</b><br>scrive i campi solo<br>se valorizzati", MOD, 1660, 180, 170, 70),
    "sew": ("Informix SDA<br><b>sew_spedizioni_work</b><br>nuove colonne zonos_account_key,<br>zonos_declaration_id", DB_MOD, 1650, 280, 190, 90),
    "consumer_poste": ("<b>consumer-sew_sped_poste</b><br>seconda tranche", TRANCHE, 1660, 400, 170, 60),
    "sew_poste": ("Informix Poste<br><b>sew_spedizioni_poste</b>,<br>sew_spedizioni_poste_inter", DB_TRANCHE, 1650, 490, 190, 80),
}

LEGENDA = (
    "Legenda: azzurro = componente modificato (propaga i campi); arancione = verifica Compliance USA; "
    "grigio = invariato o fuori perimetro; tratteggiato = seconda tranche della fase 1 (in attesa delle specifiche)."
)


def cella(cid, valore, stile, x, y, w, h):
    return (f'<mxCell id="{cid}" value="{escape(valore, {chr(34): "&quot;"})}" style="{stile}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" /></mxCell>')


def arco(cid, sorgente, destinazione, etichetta="", stile=FRECCIA, punti=None, extra="", pos=None):
    """pos = (x relativo fra -1 e 1, scostamento dx, scostamento dy) dell'etichetta."""
    if pos:
        geo = f'<mxGeometry x="{pos[0]}" relative="1" as="geometry"><mxPoint x="{pos[1]}" y="{pos[2]}" as="offset" />'
    else:
        geo = '<mxGeometry relative="1" as="geometry">'
    if punti:
        geo += '<Array as="points">' + "".join(f'<mxPoint x="{x}" y="{y}" />' for x, y in punti) + "</Array>"
    geo += "</mxGeometry>"
    return (f'<mxCell id="{cid}" value="{escape(etichetta, {chr(34): "&quot;"})}" style="{stile}{extra}" edge="1" '
            f'parent="1" source="{sorgente}" target="{destinazione}">{geo}</mxCell>')


# Percorso della lettura del producer: dalla tabella SEW al producer, passando sotto la figura
PERCORSO_PRODUCER = [(1630, 325), (1630, 650), (8, 650), (8, 230)]
USCITA_SX = "edgeStyle=orthogonalEdgeStyle;rounded=0;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;"
TRATTEGGIO = "dashed=1;strokeColor=#6c8ebf;"


def figura(titolo, archi, nodi_extra=None, nascondi=()):
    nodi = dict(NODI)
    nodi.update(nodi_extra or {})
    celle = [cella("titolo", titolo, TITOLO, 20, 10, 1400, 30)]
    for cid, (v, s, x, y, w, h) in nodi.items():
        if cid not in nascondi:
            celle.append(cella(cid, v, s, x, y, w, h))
    celle.append(cella("legenda", LEGENDA, TESTO, 20, 680, 1800, 30))
    celle.extend(archi)
    return ('<mxfile host="drawio"><diagram id="fig" name="Figura"><mxGraphModel dx="1860" dy="740" grid="1" '
            'gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
            'pageWidth="1860" pageHeight="720" math="0" shadow="0"><root><mxCell id="0" /><mxCell id="1" parent="0" />'
            + "".join(celle) + "</root></mxGraphModel></diagram></mxfile>")


def fig1():
    a = [
        arco("e1", "builder", "t_pre"),
        arco("e2", "producer", "t_pre"),
        arco("e3", "adapter", "t_pre", extra=TRATTEGGIO),
        arco("e4", "t_pre", "validatore"),
        arco("e5", "validatore", "t_enr"),
        arco("e6", "t_enr", "orchestratore"),
        arco("e7", "orchestratore", "t_comp"),
        arco("e8", "t_comp", "smistatore"),
        arco("e9", "orchestratore", "ldv", "preadvising.<br>enrichment.ldv", extra="exitX=0.7;exitY=1;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;", pos=(0, 45, 0)),
        arco("e10", "ldv", "t_enr", "esito OK / KO<br>(1320-1323)", extra="exitX=0;exitY=0.4;exitDx=0;exitDy=0;", pos=(0.3, -10, 15)),
        arco("e11", "orchestratore", "ldvpdb"),
        arco("e12", "validatore", "mongo"),
        arco("e13", "orchestratore", "mongo", extra="exitX=0.1;exitY=1;exitDx=0;exitDy=0;"),
        arco("e14", "bff", "mongo"),
        arco("e15", "validatore", "t_evs", extra="exitX=1;exitY=1;exitDx=0;exitDy=0;"),
        arco("e16", "orchestratore", "t_evs", "scarto", extra="exitX=0;exitY=0.9;exitDx=0;exitDy=0;"),
        arco("e17", "t_evs", "eventstore"),
        arco("e18", "t_evs", "monitoring"),
        arco("e19", "monitoring", "t_cons"),
        arco("e20", "smistatore", "t_sda"),
        arco("e21", "smistatore", "t_poste"),
        arco("e22", "t_sda", "consumer"),
        arco("e23", "consumer", "sew"),
        arco("e24", "t_poste", "consumer_poste", extra=TRATTEGGIO),
        arco("e25", "consumer_poste", "sew_poste", extra=TRATTEGGIO),
        arco("e26", "sew", "producer", "lettura batch (portali e web service)", punti=PERCORSO_PRODUCER, extra=USCITA_SX),
        arco("e27", "smistatore", "palmari", "tracciato invariato"),
    ]
    extra = {"palmari": ("<b>Palmari</b><br>senza i campi zonos_*", INV, 1440, 80, 180, 55)}
    return figura("146073 - Compliance USA Entry Type 13, fase 1: catena di preadvising e punti di intervento", a, extra)


def fig2():
    a = [
        arco("f1", "builder", "t_pre", "1", NUM),
        arco("f2", "sew", "producer", "2", NUM, punti=PERCORSO_PRODUCER, extra=USCITA_SX),
        arco("f3", "producer", "t_pre", "3", NUM),
        arco("f3b", "adapter", "t_pre", "", FRECCIA, extra=TRATTEGGIO),
        arco("f4", "t_pre", "validatore", "4", NUM),
        arco("f5", "validatore", "mongo", "5", NUM),
        arco("f6", "validatore", "t_enr", "6", NUM),
        arco("f7", "t_enr", "orchestratore", "7", NUM),
        arco("f8", "orchestratore", "mongo", "8", NUM, extra="exitX=0.1;exitY=1;exitDx=0;exitDy=0;"),
        arco("f9", "orchestratore", "ldv", "9", NUM, extra="exitX=0.7;exitY=1;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;"),
        arco("f10", "ldv", "cerules", "10", NUM),
        arco("f11", "ldv", "t_enr", "11", NUM, extra="exitX=0;exitY=0.4;exitDx=0;exitDy=0;"),
        arco("f12", "orchestratore", "ldvpdb", "12", NUM),
        arco("f13", "orchestratore", "t_evs", "13", NUM, extra="exitX=0;exitY=0.9;exitDx=0;exitDy=0;"),
        arco("f14a", "t_evs", "eventstore", "14", NUM),
        arco("f14b", "t_evs", "monitoring", "14", NUM),
        arco("f15", "orchestratore", "t_comp", "15", NUM),
        arco("f16", "t_comp", "smistatore", "16", NUM),
        arco("f17a", "smistatore", "t_sda", "17", NUM),
        arco("f17b", "smistatore", "t_poste", "17", NUM),
        arco("f18", "t_sda", "consumer", "18", NUM),
        arco("f19", "consumer", "sew", "19", NUM),
        arco("f20", "bff", "mongo", "20", NUM),
        arco("f21", "validatore", "t_evs", "21", NUM, extra="exitX=1;exitY=1;exitDx=0;exitDy=0;"),
        arco("f22", "monitoring", "t_cons", "22", NUM),
        arco("f23", "t_poste", "consumer_poste", "", FRECCIA, extra=TRATTEGGIO),
        arco("f24", "consumer_poste", "sew_poste", "", FRECCIA, extra=TRATTEGGIO),
    ]
    extra = {"cerules": ("<b>ce-rules</b><br>codice prodotto (invariato)", INV, 850, 350, 160, 50)}
    return figura("146073 - Compliance USA Entry Type 13, fase 1: flussi dati (numerazione del DP)", a, extra)


def esporta(nome):
    exe = next((p for p in DRAWIO if os.path.exists(p)), None)
    sorgente = os.path.join(QUI, nome + ".drawio")
    if not exe:
        print(f"draw.io non trovato: esportare a mano {sorgente} in PNG")
        return
    subprocess.run([exe, "-x", "-f", "png", "-s", "2", "-b", "10", "-o", os.path.join(QUI, nome + ".png"), sorgente],
                   check=True)


if __name__ == "__main__":
    for nome, contenuto in (("fig-1-architettura", fig1()), ("fig-2-flussi-dati", fig2())):
        with open(os.path.join(QUI, nome + ".drawio"), "w", encoding="utf-8") as f:
            f.write(contenuto)
        esporta(nome)
        print("ok", nome)
