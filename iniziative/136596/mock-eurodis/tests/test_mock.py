import re
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from mock_eurodis.app import crea_app, prodotto_cfg
from mock_eurodis.ldv import genera_ldv

RADICE = Path(__file__).resolve().parent.parent
KEY = {"X-API-Key": "test-key-sda"}
SHIPMENTS = "/receive-pan/shipments/v1"


@pytest.fixture
def client():
    return TestClient(crea_app(stato=None, seed=1))


def test_senza_chiave_401(client):
    assert client.get(SHIPMENTS).status_code == 401


def test_consuma_senza_ack_poi_404(client):
    r = client.get(SHIPMENTS, headers=KEY)
    assert r.status_code == 200 and len(r.json()) == 7
    assert client.get(SHIPMENTS, headers=KEY).status_code == 404


def test_rilettura_puntuale_e_451(client):
    ref = client.get(SHIPMENTS, headers=KEY).json()[0]["edReference"]
    assert client.get(f"/receive-pan/shipment/{ref}/v1", headers=KEY).status_code == 200
    altro = {"X-API-Key": "test-key-altro"}
    assert client.get(f"/receive-pan/shipment/{ref}/v1", headers=altro).status_code == 451
    assert client.get("/receive-pan/shipment/1/v1", headers=KEY).status_code == 404


def test_ldv_univoche_e_valide_su_tutti_i_prodotti(client):
    client.get(SHIPMENTS, headers=KEY)
    for p in client.get("/admin/prodotti").json():
        client.post(f"/admin/genera?prodotto={p}&n=5")
    spedizioni = client.get(SHIPMENTS, headers=KEY).json()
    ldv = [c["consignorsColloBarcode"] for s in spedizioni for c in s["collis"]]
    assert len(ldv) == len(set(ldv)) and all(ldv)
    cfg = yaml.safe_load((RADICE / "config" / "prodotti.yaml").read_text(encoding="utf-8"))["ldv_default"]
    for l in ldv:
        assert l == genera_ldv(cfg, int(l[len(cfg["prefisso"]):-1]))


def test_multicollo_coerente(client):
    client.post("/admin/genera?prodotto=multicollo&n=5")
    for s in client.get(SHIPMENTS, headers=KEY).json():
        assert s["numberOfHandlingUnits"] == len(s["collis"])
        assert abs(s["shipmentWeight"] - sum(c["weightOfUnit"] for c in s["collis"])) < 0.01


def test_indirizzi_reali_coerenti(client):
    anag = yaml.safe_load((RADICE / "data" / "indirizzi.yaml").read_text(encoding="utf-8"))["paesi"]
    for s in client.get(SHIPMENTS, headers=KEY).json():
        for k in ("consigneeAddress", "shipperAddress"):
            a = s[k]
            assert re.match(anag[a["countryCode"]]["cap_formato"], a["zipcode"])


def test_prodotto_contrassegno_e_pudo(client):
    s = client.post("/admin/genera?prodotto=contrassegno_assegno").json()[0]
    assert s["cashOnDeliveryService"]["identifierForCODCollection"] == 5
    p = client.post("/admin/genera?prodotto=pudo").json()[0]
    assert p["deliveryService"]["deliveryService"] == "Z" and p["consigneeAddress"]["pudoID"]


def test_prodotto_sconosciuto_404(client):
    assert client.post("/admin/genera?prodotto=boh").status_code == 404


def test_anomalia_ldv_vuota():
    cfg = yaml.safe_load((RADICE / "config" / "prodotti.yaml").read_text(encoding="utf-8"))
    cfg["prodotti"]["rotto"] = {"anomalie": {"consignorsColloBarcode_vuoto": 1}}
    assert prodotto_cfg(cfg, "rotto")["anomalie"]["consignorsColloBarcode_vuoto"] == 1
