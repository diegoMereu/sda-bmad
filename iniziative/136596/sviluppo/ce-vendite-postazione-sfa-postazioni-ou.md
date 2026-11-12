# ce-vendite — postazione da seme anche da `sfa_postazioni_ou` (postazioni PDB)

**Data**: 2026-11-12 · **Richiesta**: Diego · **Repository**: `ce-vendite`, `develop` commit `d6525c1`

## Come funziona oggi

- `ce-dichiarato-ldv` (`ProcessLdvService.resolveIdPostazioneDaSeme`, flussi SDA e MySDA) chiama
  `GET /vendite/id-postazione-da-seme?idSemeLdv=&idTipoSemeLdv=`, poi
  `GET /vendite/id-anagrafico-da-postazione`. Se la postazione non si trova: errore `144`
  "Postazione non ricavata da seme".
- In `ce-vendite` (`VenditeRepository`):
  - `findIdPostazioneBySeme` cerca in `cen_postazioni` per `id_seme_ldv` + `id_tipo_seme_ldv`;
  - `findConfigurazionePostazioneBySeme` (endpoint `configurazione-postazione-da-seme`) unisce
    `cen_attributi_postazione` (attivi), `cen_postazioni`, `cen_centri_costo_cliente` e `cen_anagrafica`;
  - `findIdAnagraficoDaPostazione` legge `cen_postazioni` e `cen_centri_costo_cliente`.
- Queste ricerche non hanno cache. La cache `postazioneBySeme` è registrata ma non è usata.
- Le postazioni dei clienti PDB non sono in `cen_postazioni`: stanno in `sfa_postazioni_ou`.

## Cosa cambia

Regola: **prima `cen_postazioni`, poi `sfa_postazioni_ou`**, solo se la prima non trova niente. Per i
casi già serviti da `cen_postazioni` il comportamento non cambia.

| Ricerca | Su `sfa_postazioni_ou` |
|---|---|
| id postazione da seme | `id_postazione` per `id_seme_ldv` |
| configurazione da seme | stessi campi del risultato di `cen_postazioni` (tabella sotto) |
| id anagrafico da postazione | `id_anagrafico` per `id_postazione` |

- `sfa_postazioni_ou` non ha il tipo seme: la ricerca usa solo `id_seme_ldv`.
- Con più righe vince la più recente per `data_ins`.
- Un errore su `sfa_postazioni_ou`, per esempio tabella assente in un ambiente, viene registrato con
  log WARN e con la metrica `business_counter_events{event=postazione_da_sfa_postazioni_ou, result=error}`,
  e la risposta resta "non trovata". Esiti normali: `result=found` e `result=not_found`.

### Mapping sui campi di `cen_postazioni`

Colonne di `sfa_postazioni_ou` (nomi indicati da Diego; nessuna DDL nei repository): `id_record`,
`id_postazione`, `id_seme_ldv`, `piva_cfisc`, `codice_cliente_sap`, `codice_centro_costo`,
`codice_contratto_poste`, `data_ins`, `id_anagrafico`, `contractor_code`, `booking_channel`,
`flag_porting_hub`.

| Campo della risposta | Da `sfa_postazioni_ou` |
|---|---|
| `idPostazione` | `id_postazione` |
| `idAnagrafico` | `id_anagrafico` (formato OU…) |
| `idCentroCosto` | `codice_centro_costo` |
| `idContratto` | `codice_contratto_poste`, senza gli spazi a destra |
| `idSemeLdv` | `id_seme_ldv` |
| `idTipoSemeLdv` | quello della richiesta (la tabella non lo ha) |
| `ragioneSociale`, `partitaIva`, `codiceFiscale` | `cen_anagrafica` unita per `id_anagrafico` |
| `idTipoElaborazione`, `idFiliale`, `codIndMittE2`, `idClienteE2`, `idTipoCosto`, `attivoMod`, `idDatiRimessaCtraHomebox`, `noFirma` | nessun corrispondente: vuoti |

Non usate: `id_record`, `piva_cfisc`, `codice_cliente_sap`, `contractor_code`, `booking_channel`,
`flag_porting_hub`.

## Test

`VenditeRepositorySfaPostazioniOuTest`, 7 test verdi, dati inventati:
- trovata in `cen_postazioni` senza interrogare `sfa`;
- trovata solo in `sfa_postazioni_ou`;
- non trovata;
- `sfa` in errore, che risponde "non trovata";
- configurazione da `sfa`: contratto senza spazi, campi senza corrispondente vuoti;
- configurazione da `cen`;
- id anagrafico da `sfa`.

Prima di questo commit il progetto non aveva test.

## Da confermare

1. **Filtri sulla riga.** `flag_porting_hub` e `booking_channel` non sono usati come filtri: va
   chiarito se una riga di `sfa_postazioni_ou` vale solo con un certo valore, come `cap.flag_attivo = 'S'`
   per `cen`.
2. **Tipo seme.** La ricerca per seme senza tipo è corretta solo se `id_seme_ldv` è univoco in
   `sfa_postazioni_ou`, o se lo è almeno la riga più recente.
3. **Join su `cen_anagrafica`.** `cen_anagrafica.id_anagrafico` usa lo stesso formato OU… di
   `sfa_postazioni_ou.id_anagrafico`? Se no, ragione sociale e partita IVA restano vuote, e si
   potrebbe usare `piva_cfisc`.
4. **Campi vuoti.** I campi senza corrispondente, in particolare `idClienteE2`, `codIndMittE2` e
   `idFiliale`, servono a valle per le postazioni PDB? Se sì, va indicato da dove si ricavano.
5. **Permessi.** L'utente del database di `ce-vendite` deve poter leggere `sfa_postazioni_ou`
   (`SELECT`) in svil, collaudo e produzione.
