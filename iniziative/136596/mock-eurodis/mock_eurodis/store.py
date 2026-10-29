"""Stato del mock: coda delle spedizioni da consegnare, archivio, contatori univoci."""
import json
from pathlib import Path


class Store:
    def __init__(self, percorso: Path | None = None):
        self.percorso = percorso
        self.ed_reference = 7319003746400
        self.progressivo_ldv = 0
        self.ultima_ldv = ""
        self.archivio: dict[int, dict] = {}   # edReference -> {"partner", "spedizione"}
        self.coda: list[int] = []              # edReference non ancora consegnate
        if percorso and percorso.exists():
            self._carica()

    def prossimo_ed_reference(self) -> int:
        self.ed_reference += 1
        return self.ed_reference

    def prossimo_progressivo_ldv(self) -> int:
        self.progressivo_ldv += 1
        return self.progressivo_ldv

    @staticmethod
    def prossimo_europlate(ed_ref: int, n: int) -> str:
        return f"12345{str(ed_ref).zfill(13)}{str(n).zfill(2)}0000"

    def aggiungi(self, spedizione: dict, partner: str) -> None:
        ref = spedizione["edReference"]
        self.archivio[ref] = {"partner": partner, "spedizione": spedizione}
        self.coda.append(ref)

    def consegna_nuove(self, partner: str) -> list[dict]:
        """Semantica EURODIS: restituisce le nuove e le segna consegnate (nessun ack)."""
        mie = [r for r in self.coda if self.archivio[r]["partner"] == partner]
        self.coda = [r for r in self.coda if r not in mie]
        return [self.archivio[r]["spedizione"] for r in mie]

    def reset(self) -> None:
        percorso = self.percorso
        if percorso and percorso.exists():
            percorso.unlink()
        self.__init__(percorso)

    def salva(self) -> None:
        if not self.percorso:
            return
        self.percorso.write_text(json.dumps({
            "ed_reference": self.ed_reference,
            "progressivo_ldv": self.progressivo_ldv,
            "ultima_ldv": self.ultima_ldv,
            "archivio": {str(k): v for k, v in self.archivio.items()},
            "coda": self.coda,
        }), encoding="utf-8")

    def _carica(self) -> None:
        d = json.loads(self.percorso.read_text(encoding="utf-8"))
        self.ed_reference = d["ed_reference"]
        self.progressivo_ldv = d["progressivo_ldv"]
        self.ultima_ldv = d["ultima_ldv"]
        self.archivio = {int(k): v for k, v in d["archivio"].items()}
        self.coda = d["coda"]
