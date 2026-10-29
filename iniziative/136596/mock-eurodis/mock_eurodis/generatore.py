"""Costruzione di una spedizione nel formato GetShipmentResponse2 dello swagger receive-pan."""
import copy
import random
from datetime import datetime, timedelta

from .ldv import corrompi_check, genera_ldv

TIMESTAMP = "%Y-%m-%dT%H:%M:%S"


def unisci(base: dict, extra: dict) -> dict:
    """Merge ricorsivo: extra sovrascrive base."""
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = unisci(out[k], v)
        else:
            out[k] = v
    return out


def _telefono(rnd: random.Random, prefisso: str) -> str:
    return prefisso + "".join(rnd.choice("0123456789") for _ in range(9))


def _indirizzo(rnd, anagrafica, iso, ruolo, p, pudo=False):
    paese = anagrafica["paesi"][iso]
    ind = rnd.choice(paese["indirizzi"])
    nome = f"{rnd.choice(anagrafica['nomi'])} {rnd.choice(anagrafica['cognomi'])}"
    azienda = rnd.choice(anagrafica["ragioni_sociali"])
    ragsoc = azienda if ruolo in ("shipper", "return") else nome
    mail = nome.lower().replace(" ", ".") + "@example.com"
    a = {
        "contactName": nome[:40],
        "contactTelephone": _telefono(rnd, paese["prefisso_tel"]),
        "alternativeContactTelephone": None,
        "contactSMS": _telefono(rnd, paese["prefisso_tel"]),
        "contactEMail": mail[:80],
        "companyName": ragsoc[:40],
        "additionalAddressInfo1": None,
        "additionalAddressInfo2": "PS" if pudo else None,
        "street": ind["street"][:40],
        "streetNumber": ind["streetNumber"],
        "region": ind["region"][:40],
        "city": ind["city"][:35],
        "zipcode": ind["zipcode"][:9],
        "countryCode": iso,
        "additionalConsigneeInfo": None,
        "gatewayAssigned": None,
    }
    if ruolo in ("consignee", "return"):
        a["pudoID"] = f"PUDO-{iso}-{rnd.randint(1000, 9999)}" if pudo else ""
    return a


def costruisci_spedizione(prodotto: str, cfg: dict, anagrafica: dict, store, rnd: random.Random) -> dict:
    ed_ref = store.prossimo_ed_reference()
    ora = datetime.now().replace(microsecond=0)
    n_colli = rnd.randint(*cfg["colli"])
    iso_dest = rnd.choice(cfg["destinatari_paesi"])
    iso_mitt = cfg["mittente_paese"]
    pudo = cfg["pudo"]

    collis = []
    for _ in range(n_colli):
        peso = round(rnd.uniform(*cfg["peso_collo_kg"]), 2)
        lung, larg, alt = (rnd.randint(*cfg["dimensioni_cm"]) for _ in range(3))
        ldv = genera_ldv(cfg["ldv"], store.prossimo_progressivo_ldv())
        an = cfg["anomalie"]
        if rnd.random() < an["ldv_check_errato"]:
            ldv = corrompi_check(ldv)
        if rnd.random() < an["ldv_duplicata"] and store.ultima_ldv:
            ldv = store.ultima_ldv
        if rnd.random() < an["consignorsColloBarcode_vuoto"]:
            ldv = ""
        store.ultima_ldv = ldv or store.ultima_ldv
        collis.append({
            "identifierPalletOrCollo": "C",
            "weightOfUnit": peso,
            "boxType": None,
            "boxDimensionCategory": None,
            "boxId": None,
            "europlateBarcode": store.prossimo_europlate(ed_ref, len(collis) + 1),
            "referencedEuroplateBarcode": None,
            "volumetric": None,
            "consignorsColloBarcode": ldv,
            "length": lung,
            "width": larg,
            "height": alt,
            "volumetricWeight": None,
        })

    tipo = cfg["shipmentTypeIndicator"]
    spedizione = {
        "edReference": ed_ref,
        "referencedEurodisShipmentNumber": store.prossimo_ed_reference() if tipo in ("R", "D", "A") else None,
        "shipmentTypeIndicator": tipo,
        "lineHaulIndicator": cfg["lineHaulIndicator"],
        "clearanceTimestamp": ora.strftime(TIMESTAMP),
        "entranceTimestamp": (ora - timedelta(hours=rnd.randint(1, 12))).strftime(TIMESTAMP),
        "numberOfHandlingUnits": n_colli,
        "shipmentWeight": round(sum(c["weightOfUnit"] for c in collis), 2),
        "consignorsCustomerNumberAtDispatchPartner": str(rnd.randint(900000000, 999999999)),
        "consignorsReference": str(rnd.randint(10000000, 99999999)),
        "dispatchPartnersDomesticShipmentNumber": str(rnd.randint(10000000, 99999999)),
        "truckLicensePlate": None,
        "termsOfDeliveryText": cfg.get("termsOfDeliveryText"),
        "consigneeAddress": _indirizzo(rnd, anagrafica, iso_dest, "consignee", cfg, pudo),
        "returnAddress": None,
        "shipperAddress": _indirizzo(rnd, anagrafica, iso_mitt, "shipper", cfg),
        "remunerationAddress": None,
        "bookingInAddress": None,
        "deliveryService": {
            "deliveryService": cfg["deliveryService"],
            "deliveryType": cfg["deliveryType"],
            "secureDeliveryId": None,
            "deliveryBookInRequired": False,
            "deliveryTimeWindowStart": None,
            "deliveryTimeWindowEnd": None,
            "deliveryDateWindowStart": None,
            "deliveryDateWindowEnd": None,
            "completeDeliveryOnly": n_colli > 1,
            "additionalNotification": False,
        },
        "cashOnDeliveryService": None,
        "customsService": None,
        "hazardousADRServices": None,
        "consigneePreAdvice": {
            "smsPreAdvice": cfg["preavviso"]["sms"],
            "eMailPreAdvice": cfg["preavviso"]["email"],
            "telephonePreAdvice": cfg["preavviso"]["telefono"],
        },
        "collis": collis,
        "hazardousCollis": None,
    }
    if tipo == "R":
        spedizione["returnAddress"] = _indirizzo(rnd, anagrafica, iso_mitt, "return", cfg)
        for c in collis:
            c["referencedEuroplateBarcode"] = store.prossimo_europlate(spedizione["referencedEurodisShipmentNumber"], 1)
    if cfg["contrassegno"]:
        c = cfg["contrassegno"]
        spedizione["cashOnDeliveryService"] = {
            "iban": "IT60X0542811101000000123456" if c["tipo"] == 3 else None,
            "bic": "BCITITMM" if c["tipo"] == 3 else None,
            "accountHolder": "SDA EXPRESS COURIER",
            "paymentReason": str(ed_ref),
            "paymentReference": str(ed_ref)[:12],
            "amount": round(rnd.uniform(*c["importo"]), 2),
            "currency": "EUR",
            "identifierForCODCollection": c["tipo"],
        }
    if cfg["dogana"]:
        spedizione["customsService"] = {
            "commercialValueOfGoods": round(rnd.uniform(50, 2000), 2),
            "currency": "EUR",
            "dutyCode": "6109100010",
            "sign": None,
            "number": None,
            "descriptionOfGoods": "ABBIGLIAMENTO",
        }
    if cfg["adr"]:
        spedizione["hazardousADRServices"] = [{
            "billOfDanger": "3",
            "additionalBillOfDanger1": None,
            "additionalBillOfDanger2": None,
            "additionalBillOfDanger3": None,
            "tunnelLimitationCode": "D/E",
            "packingGroup": 2,
            "adrGrossWeight": spedizione["shipmentWeight"],
            "unNumber": "1993",
            "transportCategory": "2",
            "materialDescription": "UN 1993 LIQUIDO INFIAMMABILE, N.A.S.",
            "technicalName": None,
            "identifierMassOrVolume": "kg",
        }]
        spedizione["hazardousCollis"] = [{"numberOfParcelType": n_colli, "explanationOfParcelType": "Fustino"}]
    return spedizione
