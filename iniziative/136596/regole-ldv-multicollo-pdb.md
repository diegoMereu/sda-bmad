# Regole LDV del multicollo PDB_INVIOSYSTEM (riferimento per EURODIS)

Fonte: esempio reale di multicollo `PDB_INVIOSYSTEM` a 5 colli fornito da Azzurra il 24-11
(madre `1UW0X5B201716`), confrontato con altre due LDV reali (`3UW0WTQ083351` con figlio
`0WTQMVLOW`, `3UW0X5B215655` con figli `0X5BMBAOW`…`0X5BMBARW`). EURODIS (`EUD_INVIOSYSTEM`) deve
seguire la stessa logica.

**Verificato** = letto negli esempi; **dedotto** = regola ricavata da pochi esempi, da confermare con
BEP (ICD Mediation BEP v2.5, non disponibile).

## Campi del collo

| Campo | Madre (collo 1) | Figlio (colli 2…N) | Monocollo | |
|---|---|---|---|---|
| `id_ldv` | LDV madre, 13 caratteri | LDV del figlio, 9 caratteri | LDV, 13 caratteri | verificato |
| `id_ldv_madre` | LDV madre (se stessa) | LDV madre | assente | verificato |
| `id_ldv_figlio` | assente | **`id_ldv` + `id_ldv_madre`**, 22 caratteri | assente | verificato |
| `tipo_collo` | `M` | `F` | assente | verificato (monocollo: dedotto) |
| `numero_colli_parz` | 1 | 2…N | 1 | verificato |
| `id_collo` | riferimento del collo del cliente (`C-OK-C085-OV-01716.1`) | idem (`….2`, `….3`) | idem | verificato; EURODIS usa la LDV intera, vedi sotto |

`id_ldv` è sempre diverso da collo a collo: madre e figli non condividono l'`id_ldv`.

## Formato dei codici

Esempio: madre `1UW0X5B201716`, postazione (seme, `LdvPdb`: caratteri 2-6) `W0X5B`.

| Codice | Struttura | Esempio | |
|---|---|---|---|
| Madre (13) | `[1-8]U` + postazione (5) + 6 cifre | `1U` `W0X5B` `201716` | verificato (regola `LdvPdb`/`ce-ldv`) |
| Figlio (9) | postazione senza il primo carattere (4) + contatore di 4 lettere + primo carattere della postazione | `0X5B` `MBBL` `W` | dedotto da 3 famiglie |
| Figlio completo (22) | figlio (9) + madre (13) | `0X5BMBBLW1UW0X5B201716` | verificato |

Il contatore cresce di uno per figlio (`MBBL`, `MBBM`, `MBBN`, `MBBO`). In tutti gli esempi il
primo carattere della postazione è `W`: non si distingue se l'ultimo carattere del figlio sia `W`
fisso o preso dalla postazione. Non è noto se BEP controlli il contatore rispetto a un range.

## Cosa arriva a BEP

ldv-pdb (`BepRequestMapper`, canale INVIOSYSTEM) manda `code` = `id_ldv` e `parcelLabel` =
`segnacollo` o `id_collo`. Quindi per il figlio `code` = 9 caratteri.

## EURODIS

- EURODIS manda in `collis[].deliveryPartnerBarcode` la madre (13) sul primo collo e il figlio
  completo (22) sugli altri. Il mapper ne ricava i campi della tabella sopra.
- `id_collo` resta la LDV intera (13 o 22): EURODIS non ha un riferimento del collo univoco e
  garantito, e ldv-pdb abbina la risposta di BEP al collo con il `parcelLabel`.
- I figli devono rispettare il formato: il 24-11 (S02, `1110000000002`) figli casuali come
  `HMPJY45P2` hanno dato `BEP:101` "Dati non conformi: barcode" su tutta la waybill (OP-04).
