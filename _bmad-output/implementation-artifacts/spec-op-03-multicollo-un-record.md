---
title: 'OP-03 (136596): multicollo EURODIS in un solo record verso il pre-enrichment'
type: 'bugfix'
created: '2026-11-24'
status: 'in-progress'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '2f474247994293dd2ac85b7700850e289ada3160' # repo mapper; sda-bmad: 62d3f0cef39581b7dbe1ec8648cc31cdafa18ef4
context:
  - '{project-root}/contesto/linee-guida-sviluppo.md'
  - '{project-root}/iniziative/136596/punti-aperti-diego-2026-11-23.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** il mapper divide un multicollo `EUD_INVIOSYSTEM` in N record (uno per collo, stesso `rif_spedizione`, `id_preadvising` diversi). Il validatore lo valida con le regole PDB: la regola 1162 scarta i colli dal secondo in poi ("Numero Riferimento Spedizione già utilizzato"). ldv-pdb inoltre si aspetta una waybill con N colli (`APT000945` solo se `collo.size() > 1`).

**Approach:** un record per spedizione con tutti i colli, cioè togliere la divisione per collo dal mapper. Restano `id_collo` = LDV su ogni collo e madre/figlio calcolati dal mapper; `id_record_multicollo` non serve più. Decisione confermata da Diego (24-11).

**Decisione (utente, 24-11):** `id_ldv` dei figli come nel flusso PDB attuale. Verificato: `ce-dichiarato-adapter` `PdbMapper.java:368-374` e ldv-pdb `BepResponseMapper` (`truncateIdLdv`, `applyMulticolloIds`) portano il figlio a 22 caratteri a `id_ldv` di 9, con `id_ldv_madre` (13) e `id_ldv_figlio` valorizzati: è già il comportamento del mapper (`97242eb`), che quindi non cambia.

## Boundaries & Constraints

**Always:** un solo `producer.send` per spedizione con l'`id_preadvising` del mapping; `numero_colli_parz` da 1 a N nell'ordine di `collis[]`; il monocollo resta identico a oggi.

**Never:** toccare validatore, ldv-pdb o send-tracking; cambiare la logica madre/figlio (`EurodisToIcdMapper.madreEFiglio`) salvo decisione sulla domanda aperta.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Multicollo | 3 colli: madre 13 car., 2 figli 22 car. | 1 messaggio, `collo` di 3 elementi, `numero_colli` 3, `numero_colli_parz` 1..3, `id_collo` = LDV intera, madre/figlio valorizzati, nessun `id_record_multicollo` | N/A |
| Monocollo | 1 collo | 1 messaggio invariato rispetto a oggi | N/A |
| Errore Kafka | `producer.send` lancia | eccezione propagata come oggi | come oggi |

</frozen-after-approval>

## Code Map

Radici: repo mapper `C:\Users\azzurra.zezza\POSTE_SDA_Project\CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper` (branch `develop`, pacchetto `it.poste.dichiarato.eurodis.mapper`); repo documenti `C:\Users\azzurra.zezza\POSTE_SDA_Project\sda-bmad`. ce-dichiarato-eurodis-in: `C:\Users\azzurra.zezza\POSTE_SDA_Project\CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-in`. Il `git fetch` chiede credenziali interattive: lavorare sul `develop` locale, niente push. Maven: `mvn -o test`.

- `CORRIERE-ESPRESSO_PREADVISING_ce-dichiarato-eurodis-mapper/src/main/java/it/poste/dichiarato/eurodis/mapper/service/impl/EurodisMapperServiceImpl.java:77-84` -- divisione e ciclo di invio da sostituire con un solo invio (come prima di `253fd0d`), log "pubblicata".
- `.../mapper/mapper/DivisioneColli.java` -- da eliminare (unico chiamante il service).
- `.../dto/icd/ColloDTO.java:27-29` -- `id_record_multicollo` da eliminare (usato solo da `DivisioneColli`).
- `.../mapper/mapper/EurodisToIcdMapper.java:534-573` -- `colli` e `madreEFiglio`: non cambiano (salvo opzione B).
- `.../test/.../mapper/DivisioneColliTest.java` -- da eliminare.
- `.../test/.../service/EurodisMapperServiceImplTest.java:113` -- `tre_colli_tre_record_verso_il_pre_enrichment` da riscrivere come un record con 3 colli.
- `sda-bmad/iniziative/136596/nota-rilascio-eurodis.md:8,79` -- testo "un record per collo".
- `sda-bmad/iniziative/136596/sviluppo/ce-dichiarato-eurodis-mapper.md:664` -- riga multicollo.

## Tasks & Acceptance

**Execution:**
- [ ] `EurodisMapperServiceImplTest.java` -- riscrivere il test multicollo (rosso) -- prova del comportamento nuovo
- [ ] `EurodisMapperServiceImpl.java` -- un solo invio per spedizione -- correzione
- [ ] `DivisioneColli.java`, `DivisioneColliTest.java`, `ColloDTO.id_record_multicollo` -- eliminare -- codice inutilizzato (Sonar)
- [ ] nota di rilascio e specifica del mapper -- allineare il testo, nuovo commit da indicare nella nota
- [ ] repo mapper e repo ce-dichiarato-eurodis-in -- eseguire `mvn -o test` in entrambi e controllare che le classi di test descrivano la logica attuale del codice: nomi, commenti ed asserzioni che citano comportamenti superati (es. "un record per collo", E225/317 come motivo di `id_collo`, `id_record_multicollo`), test mancanti per rami principali. Correggere i test superati; riportare (senza correggere) le lacune più ampie -- richiesta utente

**Acceptance Criteria:**
- Given un multicollo di 3 colli, when il mapper lo elabora, then pubblica un solo messaggio con 3 colli e `verify(producer, times(1))`.
- Given la build, when `mvn -o test`, then tutti i test verdi e nessun riferimento residuo a `DivisioneColli`/`id_record_multicollo`.

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Verification

**Commands:**
- `mvn -o test` nel repo del mapper -- expected: BUILD SUCCESS
- `grep -rn "DivisioneColli\|id_record_multicollo" src` -- expected: nessun risultato
