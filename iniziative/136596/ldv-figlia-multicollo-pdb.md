# LDV figlia nel multicollo PDB (verifica in collaudo, 25-11-2026)

Fonte: topic `PACCHI.BEP.ALL.ANAG_LDV` di collaudo (quello che legge `ce-dichiarato-adapter`),
letto con la 9092 in chiaro, senza group id (assign + seek): ultimi ~1.600 messaggi per partizione,
8.037 messaggi in tutto. Il topic `PACCHI.MEDIATION.BEP.INVIOSYSTEMREQUEST` di collaudo era vuoto.
I messaggi letti restano nello scratchpad: qui ci sono solo la regola, i conteggi e i barcode di
esempio, che non sono dati personali.

## Regola

In una spedizione multicollo il collo 1 ha la madre di 13 caratteri. I colli 2..n hanno 22 caratteri:
**figlio di 9 + madre di 13**.

```
figlio (9)  = seme[1:5] + progressivo (4) + seme[0]
progressivo = [M-Z][0-9A-Z]{3}, base 36, cresce per seme
seme        = madre.substring(2,7) = family_printStation
```

| madre | seme | figli |
|---|---|---|
| `3UW2309000090` | `W2309` | `2309MAAQ` `W` + madre, `2309MAAR` `W` + madre |
| `3UW0WQR000107` | `W0WQR` | `0WQRMACS` `W` + madre, `0WQRMACT` `W` + madre |
| `3UW0WTQ078932` | `W0WTQ` | `0WTQMUV1` `W`, `0WTQMUV2` `W`, `0WTQMUV3` `W` (+ madre) |

## Riscontri

- **Conformità:** 667 figli di 22 caratteri su 667 seguono la regola. In ogni figlio:
  - gli ultimi 13 caratteri sono `family_motherCode`;
  - il seme della madre è `family_printStation`;
  - il progressivo comincia sempre con `M`.
- **Campi del messaggio:**
  - nel collo figlio `code_barcode` = `code_scancode` = figlio di 22 caratteri;
  - `family_packageNumber` è il numero di colli;
  - `code_packageNumber` è la posizione del collo (la madre è 1);
  - `family_siblingCodes` elenca gli altri figli. Sulla madre vale `null`.
- **Progressivi:** sono consecutivi dentro la famiglia in 377 madri su 389. Negli altri casi le
  famiglie dello stesso seme si intercalano, perché il serbatoio è per seme e non per madre.
- **Distribuzione:**
  - prefissi della madre: `3U` 523, `8U` 57, `1U` 56, `2U` 14, `4U` 13, `7U` 4. Il prefisso non
    incide sul figlio.
  - canali: WEBSERVICES 620, WEB 43, INVIOFILE 4. Nessun multicollo INVIOSYSTEM nel campione.
- **Analogia con SDA:** la struttura è la stessa dello sticker SDA di `ce-ldv`
  (`cen_progressivi_stikers_cloud`: prefisso + progressivo + suffisso). Somiglia di più allo sticker
  MGCS idcli4, `[0-9]{4}[M-Z][0-9A-Z]{3}A`. Nel figlio PDB, però, il seme di 5 caratteri è ruotato
  (4 caratteri in testa, il primo in coda) e la madre è concatenata. Il figlio PDB lo genera
  PDB/BEP: nelle tabelle SDA non è configurato.
- **Altri scancode non di 13 caratteri** (18, 21, 24, 27; `code_barcode` sempre di 13): sono barcode
  di partner (`JJD…`, `JVGL…`, `JJITA…` in `code_international`), non figli di multicollo.

## Conseguenze per EURODIS (autoproduttore INVIOSYSTEM)

- EURODIS deve generare i figli con questa regola sul seme `W2308`:
  `2308` + progressivo `[M-Z][0-9A-Z]{3}` + `W` + madre. Esempio: madre `3UW2308123456` → figlio
  `2308M000W3UW2308123456`. Va concordato con EURODIS e con Poste/BEP chi garantisce l'unicità del
  progressivo, visto che il serbatoio è per seme.
- **Mock da correggere:** WireMock e `uat/genera_mock_test.py` generano 9 caratteri casuali al posto
  di `seme[1:5]` + progressivo + `seme[0]`.
- **OP-02 / RF-17:** i figli di 22 caratteri sono LDV valide in PDB. Il mapper oggi li scarta
  (`ldv_non_pdb`): la regola RF-17 va estesa a "figlio di 9 conforme + madre PDB di 13".
- **`ce-dichiarato-ldv-pdb`:** per un autoproduttore la LDV non viene sovrascritta e i figli restano
  di 22 caratteri. Così `applyMulticolloIds` trova più di una "madre" e lascia vuoti
  `id_ldv_madre`/`id_ldv_figlio`. È dedotto dal codice e va verificato con un multicollo vero.
- **Da confermare con un caso INVIOSYSTEM:** che BEP accetti il figlio costruito così. Nel campione
  non c'è nessun multicollo INVIOSYSTEM.
