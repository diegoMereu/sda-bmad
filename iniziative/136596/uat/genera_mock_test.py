"""Genera i mock WireMock (uno per scenario) dei test EURODIS S01-S61 a partire dal mock base.

Uso: python -I genera_mock_test.py <cartella_output>
I template {{...}} di WireMock restano nel testo (response-template).
"""
import copy
import json
import sys
from pathlib import Path

BASE = json.loads(r"""
{
  "edReference": "88{{randomValue length=11 type='NUMERIC'}}",
  "referencedEurodisShipmentNumber": "{{randomValue length=13 type='NUMERIC'}}",
  "initiatingPartnerId": 1,
  "shipmentTypeIndicator": "N",
  "lineHaulIndicator": "L",
  "clearanceTimestamp": "{{now format='yyyy-MM-dd'}}T00:00:00",
  "entranceTimestamp": "{{now format='yyyy-MM-dd'}}T06:53:55",
  "numberOfHandlingUnits": 1,
  "shipmentWeight": 15,
  "consignorsCustomerNumberAtDispatchPartner": "933499999",
  "consignorsReference": "30151111",
  "dispatchPartnersDomesticShipmentNumber": "30{{randomValue length=6 type='NUMERIC'}}",
  "truckLicensePlate": "LK 773319",
  "termsOfDeliveryText": "EXW",
  "routingCode": "M2012",
  "shipmentFlexField1": null,
  "shipmentFlexField2": null,
  "shipmentFlexField3": null,
  "shipmentFlexField4": null,
  "consigneeAddress": {
    "contactName": "Mario Rossi",
    "contactTelephone": "+390600000001",
    "alternativeContactTelephone": "+390600000002",
    "contactSMS": "+393330000001",
    "contactEMail": "mario.rossi@example.it",
    "companyName": "Poste Italiane S.p.A.",
    "additionalAddressInfo1": "Direzione Generale",
    "additionalAddressInfo2": null,
    "street": "Viale Europa",
    "streetNumber": "190",
    "region": "RM",
    "city": "Roma",
    "zipcode": "00144",
    "countryCode": "IT",
    "additionalConsigneeInfo": "Consegna presso reception",
    "gatewayAssigned": "ROM",
    "pudoID": null
  },
  "returnAddress": null,
  "shipperAddress": {
    "contactName": "Erika Mustermann",
    "contactTelephone": "+990000000001",
    "alternativeContactTelephone": "+990000000002",
    "contactSMS": "+880000000002",
    "contactEMail": "e.mustermann@muster-company.de",
    "companyName": "Muster Company",
    "additionalAddressInfo1": null,
    "additionalAddressInfo2": null,
    "street": "Demo street",
    "streetNumber": "1",
    "region": null,
    "city": "Berlin",
    "zipcode": "12345",
    "countryCode": "IT",
    "additionalConsigneeInfo": null,
    "gatewayAssigned": "GET"
  },
  "remunerationAddress": null,
  "bookingInAddress": null,
  "deliveryService": null,
  "cashOnDeliveryService": null,
  "customsService": null,
  "hazardousADRServices": [],
  "consigneePreAdvice": {
    "smsPreAdvice": false,
    "eMailPreAdvice": false,
    "telephonePreAdvice": false
  },
  "collis": [
    {
      "identifierPalletOrCollo": "C",
      "weightOfUnit": 15,
      "boxType": "8",
      "boxDimensionCategory": "A",
      "boxId": "99887766551",
      "europlateBarcode": "12345{{randomValue length=19 type='NUMERIC'}}",
      "referencedEuroplateBarcode": "123456789012345678901234",
      "volumetric": null,
      "consignorsColloBarcode": "CONS1{{randomValue length=8 type='NUMERIC'}}",
      "length": 33,
      "width": 44,
      "height": 55,
      "volumetricWeight": null,
      "deliveryPartnerBarcode": "3UW2308{{randomValue length=6 type='NUMERIC'}}",
      "dispatchPartnerBarcode": "51200000225059136400000031001",
      "pudoOpeningCode": "1234",
      "colloFlexField1": null,
      "colloFlexField2": null,
      "colloFlexField3": null
    }
  ],
  "hazardousCollis": []
}
""")

RND = "{{randomValue length=%d type='NUMERIC'}}"
POSTAZIONE = "W2308"
# id_ldv del figlio (ldv-figlia-multicollo-pdb.md, 667 figli reali in collaudo):
# postazione senza il primo carattere + contatore di 4 [M-Z][0-9A-Z]{3} (base 36) + primo carattere.
# Il contatore della famiglia: radice [M-Z][0-9A-Z]{2} fissata sul collo 1, ultimo carattere 1, 2, 3...
# per i colli 2, 3, 4... cosi' i figli sono consecutivi e mai uguali.
B36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
RADICE = ("{{#assign 'radice'}}{{pickRandom %s}}{{randomValue length=2 type='ALPHANUMERIC' uppercase=true}}"
          "{{/assign}}" % " ".join("'%s'" % c for c in "MNOPQRSTUVWXYZ"))


def figlio(i):
    """id_ldv completo del collo i (2..36): figlio di 9 + madre."""
    return POSTAZIONE[1:] + "{{radice}}" + B36[i - 1] + POSTAZIONE[0] + "{{madre}}"
PUDO = "PUDO-IT-00144-ROMA-0001"


def ds(servizio, tipo="S", **kw):
    d = {
        "deliveryService": servizio, "deliveryType": tipo, "secureDeliveryId": None,
        "deliveryBookInRequired": False, "deliveryTimeWindowStart": None,
        "deliveryTimeWindowEnd": None, "deliveryDateWindowStart": None,
        "deliveryDateWindowEnd": None, "completeDeliveryOnly": False,
        "additionalNotification": False,
    }
    d.update(kw)
    return d


def cod(identificativo=3, importo=123.45, valuta="EUR"):
    return {
        "iban": "IT60X0542811101000000123456", "bic": None, "accountHolder": "INTIME",
        "paymentReason": "9990000000001", "paymentReference": "9990000000001",
        "amount": importo, "currency": valuta, "identifierForCODCollection": identificativo,
    }


def spedizione(pesi=(15,), servizio=None, contrassegno=None, **kw):
    s = copy.deepcopy(BASE)
    s["deliveryService"] = servizio
    s["cashOnDeliveryService"] = contrassegno
    s["numberOfHandlingUnits"] = len(pesi)
    s["shipmentWeight"] = round(sum(pesi), 2)
    prefisso = "4U" if contrassegno else "3U"  # regola Poste del 18-11
    colli = []
    for i, p in enumerate(pesi, 1):
        c = copy.deepcopy(BASE["collis"][0])
        c["weightOfUnit"] = p
        c["boxId"] = "9988776655%d" % i
        c["europlateBarcode"] = "12345" + RND % 19
        c["consignorsColloBarcode"] = "CONS%d" % i + RND % 8
        c["dispatchPartnerBarcode"] = "5120000022505913640000003100%d" % i
        if i == 1:
            # multicollo (come PDB_INVIOSYSTEM, regole-ldv-multicollo-pdb.md): il primo collo ha la madre
            # a 13 caratteri, gli altri il figlio a 22 = id_ldv del figlio (9) + la stessa madre
            madre = prefisso + POSTAZIONE + RND % 6
            c["deliveryPartnerBarcode"] = (RADICE + "{{#assign 'madre'}}%s{{/assign}}{{madre}}" % madre
                                           if len(pesi) > 1 else madre)
        else:
            c["deliveryPartnerBarcode"] = figlio(i)
        colli.append(c)
    s["collis"] = colli
    if servizio and servizio["deliveryService"] in ("M", "F"):
        # entro le 12/10: BEP rifiuta il CAP del mittente se non e' un CAP italiano valido
        s["shipperAddress"].update(street="Via Montenapoleone", city="Milano", zipcode="20121", region="MI")
    s.update(kw)
    return s


def senza_contatti(a):
    for k in ("contactTelephone", "alternativeContactTelephone", "contactSMS", "contactEMail"):
        a[k] = None


def s04():
    s = spedizione()
    senza_contatti(s["shipperAddress"])
    senza_contatti(s["consigneeAddress"])
    return s


def s05():
    s = spedizione()
    a = s["consigneeAddress"]
    # al limite dei campi del validatore: ragione sociale 40, civico 4, localita 30
    a["streetNumber"] = "12/B"
    a["city"] = "Citta Fittizia Di Prova Estesa"
    a["companyName"] = "Azienda Fittizia Di Prova Con Nome Lungo"
    assert len(a["streetNumber"]) == 4 and len(a["city"]) == 30 and len(a["companyName"]) == 40
    return s


def s06():
    s = spedizione((0,))
    for k in ("length", "width", "height"):
        s["collis"][0][k] = None
    return s


def s07():
    s = spedizione()
    s["shipperAddress"].update(city="Wien", zipcode="10100", street="Teststrasse")
    return s


def s08():
    s = spedizione()
    s["consigneePreAdvice"] = {"smsPreAdvice": True, "eMailPreAdvice": True, "telephonePreAdvice": True}
    return s


def s15():
    return spedizione(servizio=ds(
        "W", deliveryTimeWindowStart="09:00:00", deliveryTimeWindowEnd="13:00:00",
        deliveryDateWindowStart="{{now offset='+2 days' format='yyyy-MM-dd'}}",
        deliveryDateWindowEnd="{{now offset='+2 days' format='yyyy-MM-dd'}}"))


def pudo(**kw):
    s = spedizione(servizio=ds("Z"), **kw)
    s["consigneeAddress"]["pudoID"] = PUDO
    return s


def barcode(pesi, **per_collo):
    """per_collo: indice collo -> (campo, valore)"""
    s = spedizione(pesi)
    for i, (campo, valore) in per_collo.items():
        s["collis"][int(i[1:])][campo] = valore
    return s


def s44():
    s = spedizione((3, 5, 7))
    for c in s["collis"]:
        c["consignorsColloBarcode"] = ""
        c["europlateBarcode"] = ""
    return s


def s45():
    s = spedizione()
    del s["entranceTimestamp"]
    return s


def dogana(valuta):
    s = spedizione()
    s["shipperAddress"].update(city="Zurich", zipcode="80010", street="Teststrasse")
    s["customsService"] = {
        "commercialValueOfGoods": 500.0, "currency": valuta, "dutyCode": "9876543210",
        "sign": "AA11-00001", "number": 1, "descriptionOfGoods": "MERCE DI PROVA",
    }
    return s


M3 = (3, 5, 7)
B = dict(deliveryBookInRequired=True)

SC = {}


def add(id_, desc, s):
    SC[id_] = (desc, s)


add("S01", "Standard, un collo", spedizione())
add("S02", "Multi-collo (3 colli, pesi 3/5/7)", spedizione(M3))
add("S03", "Multi-collo, pesi decimali 1.5/2.25/0.4", spedizione((1.5, 2.25, 0.4)))
add("S04", "Senza contatti (telefono, SMS, e-mail) su mittente e destinatario", s04())
add("S05", "Valori al limite (civico 4, citta 30, ragione sociale 40)", s05())
add("S06", "Peso 0, senza dimensioni", s06())
add("S07", "Mittente con citta e CAP austriaci (countryCode IT: BEP rifiuta altrimenti)", s07())
add("S08", "Preavviso destinatario (SMS, e-mail, telefono)", s08())
add("S09-C", "shipmentTypeIndicator = C", spedizione(shipmentTypeIndicator="C"))
add("S09-X", "shipmentTypeIndicator = X", spedizione(shipmentTypeIndicator="X"))
add("S10", "Sabato (6)", spedizione(servizio=ds("6")))
add("S11", "Sera (E)", spedizione(servizio=ds("E")))
add("S12", "Entro le 12 (M)", spedizione(servizio=ds("M")))
add("S13", "Entro le 10 (F)", spedizione(servizio=ds("F")))
add("S14", "Su appuntamento (B, bookIn true, telefono valorizzato)", spedizione(servizio=ds("B", **B)))
add("S15", "Finestra di consegna (W) [da confermare]", s15())
add("S16", "Pomeriggio (A)", spedizione(servizio=ds("A")))
for v in ("D", "7", "T"):
    add("S17-" + v, "deliveryService = %s [da confermare]" % v, spedizione(servizio=ds(v)))
for t in ("S", "N", "D"):
    add("S18-" + t, "Gestione firma, deliveryType = %s, nessun altro servizio" % t,
        spedizione(servizio=ds(None, t)))
add("S19", "Punto di ritiro (Z + pudoID) [da confermare]", pudo())
add("S20", "Contrassegno contanti 123.45 EUR (id 3)", spedizione(contrassegno=cod(3, 123.45)))
add("S21", "Contrassegno assegno 250.00 EUR (id 5)", spedizione(contrassegno=cod(5, 250.0)))
add("S22", "Contrassegno importo 0", spedizione(contrassegno=cod(3, 0)))
add("S23", "Contrassegno in CHF 100.00", spedizione(contrassegno=cod(3, 100.0, "CHF")))
add("S30", "Entro le 12 + contrassegno", spedizione(servizio=ds("M"), contrassegno=cod()))
add("S31", "Entro le 10 + contrassegno", spedizione(servizio=ds("F"), contrassegno=cod()))
add("S32", "Appuntamento + contrassegno", spedizione(servizio=ds("B", **B), contrassegno=cod()))
add("S33", "Entro le 12 + multi-collo", spedizione(M3, servizio=ds("M")))
add("S34", "Contrassegno + multi-collo", spedizione(M3, contrassegno=cod()))
add("S35", "Entro le 10 + contrassegno + multi-collo", spedizione(M3, servizio=ds("F"), contrassegno=cod()))
add("S36", "Appuntamento + multi-collo", spedizione(M3, servizio=ds("B", **B)))
add("S37", "Punto di ritiro + contrassegno [da confermare]", pudo(contrassegno=cod()))
add("S40", "consignorsColloBarcode vuoto", barcode((15,), c0=("consignorsColloBarcode", "")))
add("S41", "europlateBarcode vuoto", barcode((15,), c0=("europlateBarcode", "")))
add("S42", "europlateBarcode = \"0\"", barcode((15,), c0=("europlateBarcode", "0")))
add("S43", "Multi-collo, primo europlate vuoto", barcode(M3, c0=("europlateBarcode", "")))
add("S44", "Multi-collo, consignor ed europlate vuoti", s44())
add("S45", "entranceTimestamp assente", s45())
add("S60", "Dogana 500.00 EUR, mittente con citta e CAP svizzeri (countryCode IT)", dogana("EUR"))
add("S61", "Dogana 500.00 CHF, mittente con citta e CAP svizzeri (countryCode IT)", dogana("CHF"))

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
for id_, (desc, s) in SC.items():
    assert s["numberOfHandlingUnits"] == len(s["collis"])
    (out / ("%s.json" % id_)).write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
righe = ["# Mock di test EURODIS (S01-S61)", "",
         "Un file per scenario, stesso formato del mock base. Generati da `../genera_mock_test.py`.", "",
         "| File | Scenario |", "|---|---|"]
righe += ["| %s.json | %s |" % (i, d) for i, (d, _) in SC.items()]
(out / "INDICE.md").write_text("\n".join(righe) + "\n", encoding="utf-8")
print(len(SC), "file in", out)
