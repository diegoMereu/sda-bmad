# 136596 — Campagna `e2e-eurodis-svil`: test integrati fino a `preadvising.completed`

**Owner**: Test Manager · **Ambiente**: svil (mai produzione) · **Aperta**: 2026-11-10
**Metodo**: test factory (`testfactory/factories/test-factory/CLAUDE.md`), solo come riferimento.
Difformità ≠ difetto: un `DEF-136596-nnn` nasce solo dopo triage esplicito, in [triage/](triage/).

## Obiettivo

Una spedizione EURODIS scaricata da `receive-pan` arriva **arricchita** su `preadvising.completed`,
con tutti i salti verificati. Parte dall'assessment di `-in`
([AS-22](../sviluppo/assessment-ce-dichiarato-eurodis-in-2026-11-04.md): mai provato con
PostgreSQL e Kafka veri) e dalle specifiche `-in` 0.7, mapper 0.4.

## Catena verificata (svil)

| Salto | Servizio | Topic / persistenza in uscita |
|---|---|---|
| 1 | `ce-dichiarato-eurodis-in` | PostgreSQL `ce_eud_api_in`; `preadvising.eud.pre.build` (1 spedizione per messaggio, header del contratto); `preadvising.evensource` (`ST_F0002`, `ST_F0005`) |
| 2 | `ce-dichiarato-eurodis-mapper` | `preadvising.pre-enrichment` (tracciato unico ICD v11) |
| 3 | `ce-dichiarato-validatore` | `preadvising.enrichment`; eventi di record su `preadvising.evensource` (`ST_R0002` emesso, `ST_R0006` bloccato, …) |
| 4 | `ce-dichiarato-orchestratore` | azioni per canale (`normalizzazione`, `enrichment_bep`, `ldv-bep-sync` per `EUD_INVIOFILE`), poi `preadvising.completed` |
| 5 | `ce-dichiarato-smistatore` | `preadvising.completed.poste` / `.sda` (fuori dall'obiettivo, osservato) |

Ricostruito dai valori Helm di svil dei servizi (`KAFKA_TOPIC_INPUT` / `_OUTPUT`).

## Ambiente e strumenti

- Kafka svil: `kafka-pcl1.svil.kafka.aztestposte:9092`, `kafka-pcl2…:9092`, in chiaro, raggiungibile
  dalla postazione. I servizi usano la `9094` SASL_SSL. Lettura **senza group id** (nessun offset
  committato); iniezione solo su topic svil.
- PostgreSQL svil `ce_eud_api_in`: **non raggiungibile** dalla postazione (endpoint privato, porta
  5432 chiusa). Le righe si verificano indirettamente (il job di elaborazione legge da lì) finché
  non c'è un accesso.
- `ce-anagrafica` svil: route `ce-anagrafica-corriere-espresso-preadvising.apps.gen3gpazne.cloudsvil.poste.it`.
- Script (`kafka-python` in venv locale): lettura delle code, ricerca per chiave/`id_file`,
  iniezione. Restano fuori dal repo; le catture con dati personali restano in locale.
- **Dati**: EURODIS TEST restituisce sempre gli stessi dati (Diego, 10-11). Le varianti si
  costruiscono a mano partendo da `../esempio-eurodis-spedizione.json`, con dati inventati ed
  `edReference` di test con prefisso `99`. Errori HTTP e anomalie di `receive-pan`: `../mock-eurodis/`
  in locale.

## File

- [TEST-LIST.md](TEST-LIST.md): casi di test.
- [STORICO.md](STORICO.md): run.
- [triage/](triage/): difetti proposti.
