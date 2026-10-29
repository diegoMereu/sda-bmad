"""Mock dell'API EURODIS receive-pan (swagger: eurodis-receive-pan-swagger-v1.json).

Avvio:  uvicorn mock_eurodis.app:app --port 8080
"""
import os
import random
from pathlib import Path

import yaml
from fastapi import Depends, FastAPI, Header, HTTPException

from .generatore import costruisci_spedizione, unisci
from .store import Store

RADICE = Path(__file__).resolve().parent.parent
CONFIG = Path(os.environ.get("MOCK_CONFIG", RADICE / "config" / "prodotti.yaml"))
ANAGRAFICA = Path(os.environ.get("MOCK_INDIRIZZI", RADICE / "data" / "indirizzi.yaml"))
STATO = os.environ.get("MOCK_STATO", str(RADICE / "stato.json"))
PARTNER_DEFAULT = "SDA"


def _leggi(percorso: Path) -> dict:
    return yaml.safe_load(percorso.read_text(encoding="utf-8"))


def prodotto_cfg(config: dict, nome: str) -> dict:
    if nome not in config["prodotti"]:
        raise KeyError(nome)
    cfg = unisci(config["default"], config["prodotti"][nome] or {})
    cfg["ldv"] = unisci(config["ldv_default"], cfg.get("ldv", {}))
    return cfg


def crea_app(config_path: Path = CONFIG, anagrafica_path: Path = ANAGRAFICA,
             stato: str | None = STATO, semina: bool = True, seed: int | None = None) -> FastAPI:
    config = _leggi(config_path)
    anagrafica = _leggi(anagrafica_path)
    store = Store(Path(stato) if stato else None)
    rnd = random.Random(seed)
    app = FastAPI(title="EURODIS Platform TEST-API (mock) - receive-pan")

    def genera(prodotto: str, n: int, partner: str) -> list[dict]:
        cfg = prodotto_cfg(config, prodotto)
        out = []
        for _ in range(n):
            s = costruisci_spedizione(prodotto, cfg, anagrafica, store, rnd)
            store.aggiungi(s, partner)
            out.append(s)
        store.salva()
        return out

    if semina and not store.archivio:
        for prodotto, n in (config.get("seed") or {}).items():
            genera(prodotto, n, PARTNER_DEFAULT)

    def partner(x_api_key: str | None = Header(default=None)) -> str:
        p = config["api_keys"].get(x_api_key or "")
        if not p:
            raise HTTPException(401, "Authorization failed (API key missing or invalid)")
        return p

    @app.get("/receive-pan/shipments/v1")
    def shipments(p: str = Depends(partner)):
        nuove = store.consegna_nuove(p)
        store.salva()
        if not nuove:
            raise HTTPException(404, "No new shipments available")
        return nuove

    @app.get("/receive-pan/shipment/{ed_reference}/v1")
    def shipment(ed_reference: int, p: str = Depends(partner)):
        if not 1 <= ed_reference <= 9999999999999:
            raise HTTPException(400, "The ED reference transferred is invalid")
        voce = store.archivio.get(ed_reference)
        if not voce:
            raise HTTPException(404, "Shipment was not found")
        if voce["partner"] != p:
            raise HTTPException(451, "Your partner does not have access to the requested shipment")
        return voce["spedizione"]

    # --- comandi di servizio del mock (non esistono su EURODIS) ---

    @app.get("/admin/prodotti")
    def prodotti():
        return {k: (v or {}).get("descrizione", "") for k, v in config["prodotti"].items()}

    @app.post("/admin/genera")
    def admin_genera(prodotto: str, n: int = 1, partner: str = PARTNER_DEFAULT):
        try:
            return genera(prodotto, n, partner)
        except KeyError:
            raise HTTPException(404, f"Prodotto sconosciuto: {prodotto}")

    @app.post("/admin/reset")
    def admin_reset():
        store.reset()
        return {"ok": True}

    return app


app = crea_app()
